# -*- coding: utf-8 -*-
"""
YouTube字幕抓取脚本 v3 - 双后端策略
优先使用 youtube-transcript-api（直接获取JSON，最快）
备选使用 yt-dlp（下载VTT字幕）

Windows本地运行，绕过YouTube对云服务器IP的封锁
支持手动字幕和自动生成字幕

用法:
    python youtube_transcript.py <URL或视频ID> [--language zh,en] [--text-only] [--timestamps]
"""

import argparse
import json
import re
import subprocess
import sys
import os
import tempfile

# Windows下强制UTF-8输出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    os.environ['PYTHONIOENCODING'] = 'utf-8'


def extract_video_id(url_or_id):
    """从各种YouTube URL格式中提取11位视频ID"""
    url_or_id = url_or_id.strip()
    patterns = [
        r'(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def parse_vtt(vtt_path):
    """解析VTT字幕文件，返回段落列表"""
    segments = []
    if not os.path.exists(vtt_path):
        return segments
    
    with open(vtt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == '' and i > 0:
            i += 1
            break
        i += 1
    
    while i < len(lines):
        if '-->' in lines[i]:
            parts = lines[i].split('-->')
            if len(parts) == 2:
                start_str = parts[0].strip()
                try:
                    h, m, s = start_str.split(':')
                    start_sec = int(h) * 3600 + int(m) * 60 + float(s)
                except:
                    i += 1
                    continue
                
                text_lines = []
                i += 1
                while i < len(lines) and lines[i].strip() != '':
                    text_lines.append(lines[i].strip())
                    i += 1
                
                text = ' '.join(text_lines)
                if text:
                    segments.append({'text': text, 'start': start_sec})
        i += 1
    
    return segments


def format_timestamp(seconds):
    """将秒数转换为 MM:SS 或 HH:MM:SS 格式"""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fetch_with_api(video_id, languages=None):
    """
    策略A: 使用 youtube-transcript-api 直接获取字幕
    支持 1.x 新版API（YouTubeTranscriptApi实例方法）
    也兼容 0.6.x 旧版API（YouTubeTranscriptApi类方法）
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, "youtube-transcript-api未安装"

    # 构建语言优先级列表
    if languages:
        lang_list = []
        for lang in languages:
            if lang == 'zh' or lang.startswith('zh'):
                lang_list.extend(['zh-Hans', 'zh', 'zh-Hant', 'zh-CN', 'zh-TW'])
            elif lang == 'en':
                lang_list.extend(['en', 'en-US', 'en-GB'])
            else:
                lang_list.append(lang)
    else:
        # 默认：中文字幕优先，其次英文
        lang_list = ['zh-Hans', 'zh', 'zh-CN', 'en', 'en-US']

    try:
        api = YouTubeTranscriptApi()
        
        # 1.x 版本API: 使用实例方法
        try:
            result = api.fetch(video_id, languages=lang_list)
            segments = []
            for seg in result:
                if hasattr(seg, 'text'):
                    segments.append({
                        'text': seg.text,
                        'start': seg.start,
                        'duration': seg.duration
                    })
                elif isinstance(seg, dict):
                    segments.append(seg)
            
            if segments:
                print(f"[API] 使用 youtube-transcript-api (v1.x) 成功获取 {len(segments)} 段字幕", file=sys.stderr)
                return segments, None
        except AttributeError:
            pass  # 不是1.x版本，继续尝试旧版
        
        # 0.6.x 版本API: 使用类方法
        try:
            result = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_list)
            if result:
                print(f"[API] 使用 youtube-transcript-api (v0.6.x) 成功获取 {len(result)} 段字幕", file=sys.stderr)
                return result, None
        except AttributeError:
            pass

        return None, "API调用失败"
        
    except Exception as e:
        error_msg = str(e)
        if 'disabled' in error_msg.lower() or 'subtitles' in error_msg.lower():
            return None, "该视频已关闭字幕功能"
        elif 'no transcript' in error_msg.lower() or 'not found' in error_msg.lower():
            return None, f"未找到字幕。可用语言: {', '.join(lang_list)}"
        elif 'blocked' in error_msg.lower() or 'RequestBlocked' in error_msg:
            return None, "IP被YouTube封锁，尝试备用方案..."
        elif 'Could not retrieve' in error_msg:
            return None, "获取失败，尝试备用方案..."
        else:
            return None, f"API错误: {error_msg[:150]}"


def fetch_with_ytdlp(video_id, languages=None, use_browser_cookie=False):
    """策略B: 使用 yt-dlp 下载VTT字幕"""
    try:
        result = subprocess.run(
            ['yt-dlp', '--version'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None, "yt-dlp未安装"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None, "yt-dlp未安装"

    # 语言参数
    lang_str = 'zh,eng,en'
    if languages:
        mapped = []
        for lang in languages:
            if lang == 'zh' or lang.startswith('zh'):
                mapped.extend(['zh', 'zh-Hans', 'zh-Hant'])
            elif lang == 'en':
                mapped.extend(['en', 'eng'])
            else:
                mapped.append(lang)
        lang_str = ','.join(mapped)

    tmp_base = os.path.join(tempfile.gettempdir(), f"yt_{video_id}")
    
    cmd = [
        'yt-dlp',
        '--write-auto-sub',
        '--write-sub',
        '--sub-lang', lang_str,
        '--sub-format', 'vtt',
        '--skip-download',
        '--no-playlist',
        '--quiet',
        '--no-warnings',
        '--output', tmp_base,
        f'https://www.youtube.com/watch?v={video_id}'
    ]

    # 浏览器Cookie（大幅提升稳定性，避免IP封锁）
    if use_browser_cookie:
        cmd.insert(1, '--cookies-from-browser')
        cmd.insert(2, 'chrome')

    auth_info = " (已通过Chrome登录)" if use_browser_cookie else ""
    print(f"[ytdlp] 正在获取视频 {video_id} 的字幕 (语言: {lang_str}){auth_info}...", file=sys.stderr)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        vtt_file = None
        tmp_dir = tempfile.gettempdir()
        for f in os.listdir(tmp_dir):
            if f.startswith(f"yt_{video_id}") and f.endswith('.vtt'):
                vtt_file = os.path.join(tmp_dir, f)
                break
        
        if not vtt_file or not os.path.exists(vtt_file):
            stderr = result.stderr or ''
            if 'Video unavailable' in stderr or 'unavailable' in stderr.lower():
                return None, "视频不可用或已被删除"
            elif 'private' in stderr.lower():
                return None, "该视频是私有的"
            elif 'members-only' in stderr.lower():
                return None, "该视频仅限会员观看"
            else:
                return None, f"yt-dlp失败: {stderr[:200]}"
        
        segments = parse_vtt(vtt_file)
        try:
            os.remove(vtt_file)
        except:
            pass
        
        if not segments:
            return None, "该视频没有可用的字幕"
        
        print(f"[ytdlp] 成功获取 {len(segments)} 段字幕", file=sys.stderr)
        return segments, None
        
    except subprocess.TimeoutExpired:
        return None, "请求超时"
    except Exception as e:
        return None, f"错误: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="YouTube字幕抓取工具 v3")
    parser.add_argument("url", help="YouTube视频链接或11位视频ID")
    parser.add_argument("--language", "-l", default=None,
                        help="语言代码，逗号分隔 (如 zh,en)。默认优先中文")
    parser.add_argument("--timestamps", "-t", action="store_true",
                        help="输出带时间戳的文本")
    parser.add_argument("--text-only", action="store_true",
                        help="只输出纯文本，不输出JSON")
    parser.add_argument("--browser-cookie", "-b", action="store_true",
                        help="使用Chrome浏览器Cookie登录（防封锁，大幅提升稳定性）")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    languages = [l.strip() for l in args.language.split(",")] if args.language else None

    # 策略A: 优先用API
    segments, error = fetch_with_api(video_id, languages)
    
    # 策略B: API失败则用yt-dlp
    if error or not segments:
        print(f"[INFO] API失败 ({error})，切换到yt-dlp备用方案...", file=sys.stderr)
        segments, error = fetch_with_ytdlp(video_id, languages, use_browser_cookie=args.browser_cookie)
    
    if error or not segments:
        result = {"error": error or "未获取到字幕", "video_id": video_id}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    full_text = " ".join(seg["text"] for seg in segments)
    timestamped = "\n".join(
        f"{format_timestamp(seg['start'])} {seg['text']}" for seg in segments
    )

    if args.text_only:
        print(timestamped if args.timestamps else full_text)
        return

    result = {
        "video_id": video_id,
        "segment_count": len(segments),
        "full_text": full_text,
    }
    if args.timestamps:
        result["timestamped_text"] = timestamped

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
