# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
客户完整跟进记录读取分析工具（优化版）
策略：优先读取 CSV 缓存，如果不存在则直接读取 Excel
作者：团团助手
日期：2026-04-17
版本：v2.0
"""

import win32com.client as win32
import json
import sys
import os
from datetime import datetime
from collections import Counter
from pathlib import Path

# ==================== 配置区域 ====================

EXCEL_PATH = r'D:\Unique work form\daily_followup.xlsm'
CACHE_DIR = r'C:\Users\Huawei\.openclaw\workspace-tuantuan\runtime\client_cache'
SHEET_INDEX = 1
FOLLOWUP_START_COL = 200
FOLLOWUP_END_COL = 500

# ==================== 缓存管理 ====================

def get_cache_file(row):
    """获取缓存文件路径"""
    return os.path.join(CACHE_DIR, f'client_{row}_followups.json')

def is_cache_valid(cache_file, max_age_minutes=30):
    """检查缓存是否有效（30 分钟内）"""
    if not os.path.exists(cache_file):
        return False
    
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
        age = datetime.now() - mtime
        return age.total_seconds() < max_age_minutes * 60
    except:
        return False

def read_from_cache(row):
    """从缓存读取"""
    cache_file = get_cache_file(row)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return None

def write_to_cache(row, data):
    """写入缓存"""
    cache_file = get_cache_file(row)
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ 写入缓存失败：{e}")
        return False

# ==================== Excel 读取 ====================

def read_from_excel(row, force_refresh=False):
    """从 Excel 直接读取"""
    excel = None
    wb = None
    try:
        excel = win32.Dispatch('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(EXCEL_PATH)
        ws = wb.Worksheets[SHEET_INDEX]
        
        # 读取客户信息
        client = {
            'row': row,
            'name': ws.Cells(row, 2).Value or '',
            'phone': ws.Cells(row, 3).Value or '',
            'grade': ws.Cells(row, 8).Value or '',
            'rooms': ws.Cells(row, 9).Value or '',
            'budget': ws.Cells(row, 6).Value or '',
            'district': ws.Cells(row, 10).Value or '',
            'followup_count': ws.Cells(row, 35).Value or 0,
            'last_followup_date': ws.Cells(row, 366).Value or ''
        }
        
        # 读取跟进记录
        followups = []
        for col in range(FOLLOWUP_END_COL, FOLLOWUP_START_COL - 1, -1):
            date = ws.Cells(row, col - 1).Value
            content = ws.Cells(row, col).Value
            
            if date and content and str(date).strip():
                try:
                    followups.append({
                        'date': str(date).strip(),
                        'content': str(content).strip(),
                        'column': col
                    })
                except:
                    pass
        
        # 保存并关闭
        wb.Save()  # 保持.xlsm 格式，保护宏
        wb.Close(SaveChanges=False)
        excel.Quit()
        
        return {
            'client': client,
            'followups': followups,
            'source': 'excel',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Excel 读取失败：{e}")
        return None
    finally:
        try:
            if wb: wb.Close(SaveChanges=False)
            if excel: excel.Quit()
        except:
            pass

# ==================== 分析功能 ====================

def analyze_followups(followups):
    """分析跟进记录"""
    if not followups:
        return None
    
    # 月度统计
    monthly_stats = Counter()
    for f in followups:
        try:
            date_obj = datetime.strptime(f['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            monthly_stats[month_key] += 1
        except:
            pass
    
    # 关键词统计
    keywords = {
        '带看': 0, '电话': 0, '微信': 0, '解读': 0,
        '通电话': 0, '面谈': 0, '邀约': 0, '推荐': 0
    }
    
    for f in followups:
        for kw in keywords:
            if kw in f['content']:
                keywords[kw] += 1
    
    return {
        'total_count': len(followups),
        'time_span': {
            'earliest': followups[-1]['date'] if followups else '',
            'latest': followups[0]['date'] if followups else ''
        },
        'monthly_stats': dict(monthly_stats),
        'keywords': keywords
    }

# ==================== 主程序 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='客户完整跟进记录读取分析工具 v2.0')
    parser.add_argument('--row', type=int, required=True, help='客户行号')
    parser.add_argument('--all', action='store_true', help='显示所有跟进记录')
    parser.add_argument('--limit', type=int, default=20, help='显示最近 N 条')
    parser.add_argument('--export', action='store_true', help='导出到文件')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--quiet', action='store_true', help='安静模式')
    parser.add_argument('--force', action='store_true', help='强制从 Excel 读取（忽略缓存）')
    parser.add_argument('--refresh', action='store_true', help='刷新缓存')
    
    args = parser.parse_args()
    
    try:
        data = None
        source = ''
        
        # 策略：优先缓存，失败则读 Excel
        if not args.force:
            if not args.quiet:
                print("检查缓存...")
            
            if args.refresh or not is_cache_valid(get_cache_file(args.row)):
                cache_data = read_from_cache(args.row)
                if cache_data:
                    data = cache_data
                    source = 'cache (valid)'
        
        # 如果缓存无效或强制读取 Excel
        if not data:
            if not args.quiet:
                print("从 Excel 读取...")
            
            data = read_from_excel(args.row)
            
            if data:
                source = 'excel'
                # 写入缓存
                write_to_cache(args.row, data)
                if not args.quiet:
                    print("✅ 已更新缓存")
        
        if not data:
            print("❌ 无法读取数据")
            sys.exit(1)
        
        # 分析
        analysis = analyze_followups(data['followups'])
        
        # 输出
        if args.json:
            output = {
                **data,
                'analysis': analysis,
                'source': source
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            if not args.quiet:
                # 文本格式
                print("=" * 80)
                print(f"客户：{data['client']['name']} (行号:{data['client']['row']})")
                print(f"等级：{data['client']['grade']} | 预算：{data['client']['budget']}万")
                print(f"数据来源：{source}")
                print("=" * 80)
                print()
                
                # 显示跟进记录
                display_count = len(data['followups']) if args.all else min(args.limit, len(data['followups']))
                print(f"跟进记录（共{len(data['followups'])}条，显示{display_count}条）:")
                print("=" * 80)
                
                for i in range(display_count):
                    f = data['followups'][i]
                    print(f"[{i+1:3}] {f['date']}")
                    content = f['content'][:150] + "..." if len(f['content']) > 150 else f['content']
                    print(f"    {content}")
                    print()
                
                if analysis:
                    print("=" * 80)
                    print(f"分析：总计{analysis['total_count']}条 | {analysis['time_span']['earliest']} 至 {analysis['time_span']['latest']}")
                    print("月度统计:")
                    for month, count in sorted(analysis['monthly_stats'].items(), reverse=True):
                        print(f"  {month}: {count}条")
            
            else:
                # 安静模式
                print(f"{data['client']['name']} | {len(data['followups'])}条 | {source}")
        
        # 导出
        if args.export:
            output_file = os.path.join(os.path.expanduser('~'), 'Desktop', f"client_{args.row}_followups.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, followup in enumerate(data['followups'], 1):
                    f.write(f"[{i}] {followup['date']}\n{followup['content']}\n\n")
            print(f"✅ 已导出：{output_file}")
        
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
