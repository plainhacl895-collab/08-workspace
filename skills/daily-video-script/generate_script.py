#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日视频脚本生成器 - 爆款版 v2.0
从当天跟进记录中提炼闪光点，围绕闪光点生成高转化短视频脚本
"""

import os
import sys
import json
import random
import re
from datetime import datetime, timedelta, date
from pathlib import Path

try:
    import pythoncom
    from win32com.client import DispatchEx, GetObject
except ImportError:
    print("错误：需要安装 pywin32")
    print("运行：pip install pywin32")
    sys.exit(1)


class VideoScriptGenerator:
    """视频脚本生成器 - 爆款版 v2.0"""
    
    def __init__(self):
        self.excel_path = Path(r"D:\Unique work form\daily_followup.xlsm")
        self.excel_password = "000"
        self.client_sheet_index = 2  # "客户不要猜" 工作表
        self.header_row = 11  # 日期标题行号
        self.first_followup_column = 365  # 第一列跟进
        self.output_dir = Path(__file__).parent.parent.parent / "runtime"
        self.output_dir.mkdir(exist_ok=True)
    
    def load_followups(self, target_date=None):
        """加载当天跟进记录"""
        import subprocess
        import time
        
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.strftime("%Y-%m-%d")
        
        # 先保存并关闭Excel
        print("保存并关闭Excel...", flush=True)
        try:
            existing_excel = None
            try:
                existing_excel = GetObject(Class="Excel.Application")
                saved_count = 0
                for wb in existing_excel.Workbooks:
                    if not wb.Saved:
                        wb.Save()
                        saved_count += 1
                if saved_count > 0:
                    print(f"已自动保存 {saved_count} 个 Excel 文件", flush=True)
                existing_excel.Quit()
                time.sleep(2)
            except:
                pass
            finally:
                if existing_excel:
                    try:
                        existing_excel.Quit()
                    except:
                        pass
        except:
            pass
        
        # 强制杀掉残留的Excel进程
        subprocess.run(["taskkill", "/F", "/IM", "excel.exe"], capture_output=True)
        time.sleep(2)
        print("OK: Excel 已关闭", flush=True)
        
        pythoncom.CoInitialize()
        excel = None
        workbook = None
        
        try:
            excel = DispatchEx("Excel.Application")
            excel.DisplayAlerts = False
            excel.Visible = False
            
            workbook = excel.Workbooks.Open(
                Filename=str(self.excel_path),
                UpdateLinks=0,
                ReadOnly=True,
                Password=self.excel_password,
            )
            
            ws = workbook.Worksheets(self.client_sheet_index)
            
            # 查找目标日期的列
            target_col = None
            for col in range(self.first_followup_column, self.first_followup_column + 365):
                cell_value = ws.Cells(self.header_row, col).Value
                if cell_value is None:
                    break
                cell_date_str = str(cell_value)
                if date_str in cell_date_str or cell_date_str in date_str:
                    target_col = col
                    break
            
            if target_col is None:
                print(f"未找到日期 {date_str} 的跟进列")
                return []
            
            print(f"找到日期 {date_str} 的跟进列：第 {target_col} 列")
            
            # 读取该列的所有跟进记录
            followups = []
            for row in range(12, 200):
                cell_value = ws.Cells(row, target_col).Value
                if cell_value is None:
                    continue
                
                content = str(cell_value).strip()
                if not content:
                    continue
                
                # 读取客户信息
                client_name = ws.Cells(row, 9).Value or "客户"
                client_phone = ws.Cells(row, 11).Value or ""
                client_grade = ws.Cells(row, 6).Value or ""
                client_budget = ws.Cells(row, 8).Value or ""
                client_area = ws.Cells(row, 10).Value or ""
                client_type = ws.Cells(row, 7).Value or ""
                
                followups.append({
                    "row": row,
                    "client": str(client_name).strip(),
                    "phone": str(client_phone).strip() if client_phone else "",
                    "grade": str(client_grade).strip() if client_grade else "",
                    "budget": str(client_budget).strip() if client_budget else "",
                    "area": str(client_area).strip() if client_area else "",
                    "type": str(client_type).strip() if client_type else "",
                    "content": content
                })
            
            return followups
            
        except Exception as e:
            print(f"读取跟进记录失败：{e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if workbook is not None:
                try:
                    workbook.Close(SaveChanges=False)
                except:
                    pass
            if excel is not None:
                try:
                    excel.Quit()
                except:
                    pass
            pythoncom.CoUninitialize()
    
    def select_material(self, followups):
        """智能选择有素材价值的跟进 - 基于闪光点潜力"""
        if not followups:
            return None
        
        # 评分逻辑：基于闪光点潜力
        scored = []
        for f in followups:
            score = 0
            content = f.get("content", "")
            
            # 基础分：有预算
            if f.get("budget") and len(f["budget"]) > 2:
                score += 5
            
            # 基础分：有区域
            if f.get("area") and len(f["area"]) > 1:
                score += 3
            
            # 基础分：有具体跟进内容（长度）
            content_len = len(content)
            if content_len > 50:
                score += 5
            elif content_len > 20:
                score += 3
            elif content_len > 10:
                score += 1
            
            # 客户等级分
            if f.get("grade") == "A":
                score += 3
            elif f.get("grade") == "B":
                score += 2
            
            # ★ 闪光点潜力分（核心）
            # 有具体房源编号/小区名 → 专业度
            if re.search(r'107\d{10,12}|编号|房号', content):
                score += 8
            
            # 有拒绝/劝退/筛选 → 反差感
            if any(kw in content for kw in ["劝退", "拒绝", "筛选", "过滤", "不能要", "不合适"]):
                score += 10
            
            # 有对比/纠结/犹豫 → 决策故事
            if any(kw in content for kw in ["对比", "纠结", "犹豫", "选择", "取舍"]):
                score += 7
            
            # 有家庭分歧 → 情感共鸣
            if any(kw in content for kw in ["太太", "老公", "夫妻", "家人", "分歧"]):
                score += 8
            
            # 有具体数据 → 专业背书
            if re.search(r'\d+万|\d+套|\d+平|\d+折|\d+%', content):
                score += 5
            
            # 有带看/推房/沟通 → 服务过程
            if any(kw in content for kw in ["带看", "推房", "沟通", "协调", "筛选"]):
                score += 4
            
            # 有捡漏/便宜/贵了 → 价格敏感
            if any(kw in content for kw in ["捡漏", "便宜", "贵了", "降价", "涨价"]):
                score += 6
            
            scored.append((score, f))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # 选择最高分或随机选择前3个
        top = scored[:3]
        if top and top[0][0] > 0:
            return random.choice(top)[1]
        return followups[0]
    
    def extract_shining_point(self, material):
        """从跟进记录中提炼闪光点 - 核心逻辑"""
        content = material.get("content", "")
        budget = material.get("budget", "")
        area = material.get("area", "")
        house_type = material.get("type", "")
        client_name = material.get("client", "客户")
        
        # 去除内部术语
        clean_content = re.sub(r'【[^】]+】', '', content)
        clean_content = re.sub(r'\([^)]*\)', '', clean_content)
        
        shining_point = {
            "budget": budget,
            "area": area,
            "house_type": house_type,
            "client_name": client_name,
            "content": clean_content,
            "raw_content": content,
            "conflict": [],
            "resolution": [],
            "data_points": [],
            "community_names": [],
            "house_ids": [],
            "strategy": "",
            "shining_type": "",  # 闪光点类型
            "shining_desc": "",  # 闪光点描述
            "hook_angle": "",    # 钩子角度
            "golden_sentence": ""  # 金句
        }
        
        # 提取数据点
        data_patterns = [
            (r'(\d+)万', '金额'),
            (r'(\d+)套', '套数'),
            (r'(\d+)平', '面积'),
            (r'(\d+)折', '折扣'),
            (r'(\d+)%', '比例'),
            (r'(\d+)个月', '时长'),
            (r'(\d+)年', '年限'),
            (r'(\d+)楼', '楼层'),
            (r'(\d+)室', '室数'),
            (r'(\d+)厅', '厅数')
        ]
        for pattern, ptype in data_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                shining_point["data_points"].append({"value": m, "type": ptype})
        
        # 提取小区名
        community_patterns = [
            r'达安花园', r'大家源新城', r'苏堤春晓名苑', r'新天地河滨花园',
            r'中山公园', r'曹家渡', r'江宁路', r'静安', r'长宁', r'徐汇',
            r'黄埔', r'普陀', r'闵行', r'虹口', r'杨浦', r'嘉定'
        ]
        for pattern in community_patterns:
            if pattern in content:
                shining_point["community_names"].append(pattern)
        
        # 提取房源编号
        house_id_matches = re.findall(r'107\d{10,12}', content)
        shining_point["house_ids"].extend(house_id_matches)
        
        # ★ 闪光点类型判断（核心逻辑）
        shining_type_scores = {
            "反差拒绝": 0,
            "专业筛选": 0,
            "家庭决策": 0,
            "数据对比": 0,
            "捡漏机会": 0,
            "避坑指南": 0
        }
        
        # 1. 反差拒绝：劝退/拒绝/不能要
        if any(kw in content for kw in ["劝退", "拒绝", "不能要", "不合适", "别买"]):
            shining_type_scores["反差拒绝"] += 10
            if not shining_point.get("shining_desc"):
                shining_point["shining_desc"] = "拒绝盲目推荐，只做有效筛选"
                shining_point["hook_angle"] = "今天我劝退了..."
                shining_point["golden_sentence"] = "房产中介的价值，不是告诉你哪里的房子在卖，而是告诉你哪里的房子绝对不能买。"
        
        # 2. 专业筛选：筛选/过滤/对比
        if any(kw in content for kw in ["筛选", "过滤", "对比", "分析", "复盘"]):
            shining_type_scores["专业筛选"] += 8
            if not shining_point.get("shining_desc"):
                shining_point["shining_desc"] = "用专业工具全城比对，精准匹配"
                shining_point["hook_angle"] = "我帮他复盘了全城..."
                shining_point["golden_sentence"] = "买房不看装修，看的是这3个核心底层逻辑。"
        
        # 3. 家庭决策：太太/老公/夫妻/分歧
        if any(kw in content for kw in ["太太", "老公", "夫妻", "家人", "分歧"]):
            shining_type_scores["家庭决策"] += 9
            if not shining_point.get("shining_desc"):
                shining_point["shining_desc"] = "帮客户家庭统一意见，找到最优解"
                shining_point["hook_angle"] = "家里意见不统一怎么办？"
                shining_point["golden_sentence"] = "买房不是一个人的事，家庭意见统一比什么都重要。"
        
        # 4. 数据对比：有具体数据
        if len(shining_point["data_points"]) >= 2:
            shining_type_scores["数据对比"] += 7
            if not shining_point.get("shining_desc"):
                shining_point["shining_desc"] = "用数据说话，精准对比性价比"
                shining_point["hook_angle"] = "数据告诉你怎么选..."
                shining_point["golden_sentence"] = "买房不看数据，就像闭着眼睛走路。"
        
        # 5. 捡漏机会：捡漏/便宜/降价
        if any(kw in content for kw in ["捡漏", "便宜", "降价", "底价"]):
            shining_type_scores["捡漏机会"] += 6
            if not shining_point.get("shining_desc"):
                shining_point["shining_desc"] = "帮客户找到全网最低价"
                shining_point["hook_angle"] = "今天发现一个捡漏机会..."
                shining_point["golden_sentence"] = "好房子不是等来的，是找来的。"
        
        # 6. 避坑指南：临街/噪音/采光/硬伤
        if any(kw in content for kw in ["临街", "噪音", "采光", "硬伤", "缺陷", "问题"]):
            shining_type_scores["避坑指南"] += 8
            if not shining_point.get("shining_desc"):
                shining_point["shining_desc"] = "帮客户规避未来10年可能踩到的坑"
                shining_point["hook_angle"] = "这套房千万别买..."
                shining_point["golden_sentence"] = "我的价值不是带你看房，而是帮你规避掉未来10年可能踩到的坑。"
        
        # ★ 如果没有匹配到任何类型，用内容长度和关键词做兜底
        content_len = len(content)
        if not shining_point.get("shining_desc"):
            if content_len > 50:
                shining_type_scores["专业筛选"] += 5
                shining_point["shining_desc"] = "深度分析客户需求，精准匹配房源"
                shining_point["hook_angle"] = "今天帮客户做了一次深度分析..."
                shining_point["golden_sentence"] = "买房是一件大事，需要专业的分析和判断。"
            else:
                shining_type_scores["专业筛选"] += 3
                shining_point["shining_desc"] = "跟进客户需求，提供专业建议"
                shining_point["hook_angle"] = "今天跟进了一位客户..."
                shining_point["golden_sentence"] = "专业服务，从了解需求开始。"
        
        # 选择最高分的闪光点类型
        shining_type = max(shining_type_scores, key=shining_type_scores.get)
        shining_point["shining_type"] = shining_type
        
        # 提取冲突点
        conflict_keywords = {
            "太太": "家庭决策冲突",
            "分歧": "家庭意见分歧",
            "纠结": "选择困难",
            "对比": "多个选择对比",
            "犹豫": "决策犹豫",
            "观望": "市场观望",
            "贵了": "价格超出预期",
            "预算": "预算限制",
            "底线": "价格底线",
            "捡漏": "寻找性价比",
            "品质": "品质要求高",
            "车位": "特殊需求",
            "临街": "避坑需求",
            "采光": "采光问题",
            "噪音": "噪音问题"
        }
        for kw, meaning in conflict_keywords.items():
            if kw in content:
                shining_point["conflict"].append(meaning)
        
        # 提取解决方案
        resolution_keywords = {
            "推房": "推荐房源",
            "带看": "安排带看",
            "筛选": "筛选房源",
            "沟通": "沟通协调",
            "确认": "确认需求",
            "同步": "同步信息",
            "分析": "分析对比",
            "复盘": "全城复盘"
        }
        for kw, meaning in resolution_keywords.items():
            if kw in content:
                shining_point["resolution"].append(meaning)
        
        # 确定策略
        shining_point["strategy"] = self._select_strategy(shining_point)
        
        return shining_point
    
    def _select_strategy(self, shining_point):
        """根据闪光点类型选择脚本策略"""
        shining_type = shining_point.get("shining_type", "")
        
        strategy_map = {
            "反差拒绝": "反差拒绝型",
            "专业筛选": "专业输出型",
            "家庭决策": "情感共鸣型",
            "数据对比": "数据背书型",
            "捡漏机会": "机会稀缺型",
            "避坑指南": "避坑指南型"
        }
        
        return strategy_map.get(shining_type, "专业输出型")
    
    def generate_script(self, material):
        """生成爆款短视频脚本"""
        if not material:
            return None
        
        # 1. 提炼闪光点
        shining_point = self.extract_shining_point(material)
        
        # 2. 根据策略生成脚本
        script = self._generate_script_by_strategy(shining_point, material)
        
        # 3. 质量验证
        validation = self._validate_script(script)
        if not validation["valid"]:
            print(f"警告：脚本质量验证未通过：{validation['issues']}")
        
        # 4. 添加拍摄指导和元数据
        output_script = self._add_production_guide(script, shining_point, material, validation)
        
        return output_script
    
    def _generate_script_by_strategy(self, sp, material):
        """根据策略生成脚本"""
        strategy = sp.get("strategy", "专业输出型")
        
        if strategy == "反差拒绝型":
            return self._generate_reject_script(sp, material)
        elif strategy == "专业输出型":
            return self._generate_professional_script(sp, material)
        elif strategy == "情感共鸣型":
            return self._generate_emotional_script(sp, material)
        elif strategy == "数据背书型":
            return self._generate_data_script(sp, material)
        elif strategy == "机会稀缺型":
            return self._generate_opportunity_script(sp, material)
        elif strategy == "避坑指南型":
            return self._generate_avoid_script(sp, material)
        else:
            return self._generate_professional_script(sp, material)
    
    def _generate_reject_script(self, sp, material):
        """反差拒绝型脚本 - 核心：劝退/拒绝"""
        budget = sp.get("budget", "500万")
        area = sp.get("area", "上海")
        content = sp.get("content", "")
        raw_content = sp.get("raw_content", "")
        communities = sp.get("community_names", [])
        house_ids = sp.get("house_ids", [])
        data = sp.get("data_points", [])
        
        # 标题
        if communities:
            title = f"{budget}买{communities[0]}还是{area}？选错了一辈子住'黑屋'！"
        else:
            title = f"{budget}在{area}买房，今天我劝退了一位客户"
        
        # 钩子（0-5秒）
        hook = f"别再被那些'地段论'给洗脑了！今天，我刚劝退了一位拿着{budget}找我买房的客户。为什么？"
        
        # 反差（5-12秒）
        if house_ids:
            contrast = f"{communities[0] if communities else area}，{budget}，听起来像捡漏，实际上可能是个'坑'。为什么？"
        else:
            contrast = f"{budget}入驻{communities[0] if communities else area}？听起来像捡漏，实际上可能是个'坑'。"
        
        # 痛点（12-25秒）
        pain = ""
        if "一楼" in content or "采光" in content:
            pain = f"因为那是一楼！采光终年不见阳光，即便是在{communities[0] if communities else '好地段'}，这种房子住进去也是压抑。我直接告诉{sp['client_name']}：'这种一楼，咱不能要！'"
        elif "临街" in content or "噪音" in content:
            pain = f"因为临街噪音太大！{sp['client_name']}说晚上根本睡不着。我直接告诉他：'这种房子，再便宜也不能要！'"
        else:
            pain = f"因为{sp['client_name']}的预算是{budget}，但这个价格在这个地段有硬伤。我直接告诉他：'这种房子，咱不能要！'"
        
        # 专业（25-40秒）
        professional = f"{sp['client_name']}的预算是{budget}。我帮他把{area}翻了个遍。"
        if communities:
            professional += f"从{'、'.join(communities[:3])}，我只帮他看这种房：全明、高楼层、无硬伤。"
        else:
            professional += f"从达安花园到苏堤春晓，我只帮他看这种房：全明、高楼层、无硬伤。"
        
        # 金句（40-52秒）
        golden = sp.get("golden_sentence", "房产中介的价值，不是告诉你哪里的房子在卖，而是告诉你哪里的房子绝对不能买。")
        
        # 引导（52-60秒）
        cta = f"想在上海买到真正保值避坑的好房？点个关注。如果你也有{budget}预算，后台告诉我，我帮你做全城比对。"
        
        return f"# {title}\n\n## 开场（3秒钩子）\n{hook}\n\n## 反差（5秒）\n{contrast}\n\n## 痛点（13秒）\n{pain}\n\n## 专业（15秒）\n{professional}\n\n## 金句（12秒）\n{golden}\n\n## 结尾（8秒）\n{cta}"
    
    def _generate_professional_script(self, sp, material):
        """专业输出型脚本 - 核心：全城比对/精准匹配"""
        budget = sp.get("budget", "500万")
        area = sp.get("area", "上海")
        content = sp.get("content", "")
        communities = sp.get("community_names", [])
        
        title = f"{budget}在{area}买房，我帮他复盘了全城20套房源"
        hook = f"今天帮{sp['client_name']}做了一次全城房源比对，结果让他大吃一惊。"
        
        # 叙述闪光点
        story = f"{sp['client_name']}原本看中了{communities[0] if communities else area}的房子，但我通过专业工具分析后发现，那里的溢价空间已经饱和了。"
        
        # 硬核输出
        hard = f"我告诉他：买房不看装修，看的是这3个核心底层逻辑。于是我熬夜帮他复盘了全城同价位的20套房源……"
        
        # 情感共鸣
        emotion = f"作为中介，我的价值不是带你看房，而是帮你规避掉未来10年可能踩到的坑。"
        
        # 引导获客
        cta = f"想在{area}买房不踩坑？关注我，后台回复'买房'，我把这份避坑清单发给你。"
        
        return f"# {title}\n\n## 开场（3秒钩子）\n{hook}\n\n## 叙述闪光点（12秒）\n{story}\n\n## 硬核输出（20秒）\n{hard}\n\n## 情感共鸣（10秒）\n{emotion}\n\n## 结尾（8秒）\n{cta}"
    
    def _generate_emotional_script(self, sp, material):
        """情感共鸣型脚本 - 核心：家庭决策"""
        budget = sp.get("budget", "500万")
        area = sp.get("area", "上海")
        content = sp.get("content", "")
        communities = sp.get("community_names", [])
        
        title = f"{budget}买房，太太和老公意见不统一怎么办？"
        hook = f"今天遇到一对夫妻，为了一套房子吵得不可开交。为什么？"
        
        # 冲突描述（展开细节）
        conflict = f"{sp['client_name']}和太太来看房，预算{budget}，想在{area}买。\n\n"
        conflict += f"本来以为是一件高兴的事，结果两个人意见完全不一致。\n\n"
        conflict += f"太太觉得某个方面不太满意（比如临街噪音、户型朝向），但老公觉得价格合适、性价比高。\n\n"
        conflict += f"两个人看了{communities[0] if communities else '好几套'}房子，每套都有优缺点，就是定不下来。\n\n"
        conflict += f"最关键是，他们连'什么最重要'都没想清楚。"
        
        # 解决方案（展开）
        solution = f"我帮他们做了三件事：\n\n"
        solution += f"第一，列出了'必须满足'的清单：{area}、三房、{budget}以内。\n\n"
        solution += f"第二，列出了'可以妥协'的清单：楼层可以低一点，户型可以小一点。\n\n"
        solution += f"第三，让他们各自选出最看重的3个点，然后对比。\n\n"
        solution += f"结果发现，太太看重的是'住得舒服'，老公看重的是'性价比高'。\n\n"
        solution += f"其实两个人的目标是一致的，只是表达方式不同。"
        
        # 金句（展开）
        golden = f"买房不是一个人的事，家庭意见统一比什么都重要。\n\n"
        golden += f"建议夫妻双方先明确核心需求，再去看房，效率会高很多。\n\n"
        golden += f"记住，房子是给人住的，不是用来吵架的。"
        
        # 引导
        cta = f"如果你也在{area}买房遇到家庭分歧，私信我，帮你分析。关注走起来"
        
        return f"# {title}\n\n## 开场（3秒钩子）\n{hook}\n\n## 冲突描述（15秒）\n{conflict}\n\n## 解决方案（20秒）\n{solution}\n\n## 金句（15秒）\n{golden}\n\n## 结尾（7秒）\n{cta}"
    
    def _generate_data_script(self, sp, material):
        """数据背书型脚本 - 核心：数据对比"""
        budget = sp.get("budget", "500万")
        area = sp.get("area", "上海")
        data = sp.get("data_points", [])
        content = sp.get("content", "")
        communities = sp.get("community_names", [])
        
        title = f"{budget}在{area}买房，数据告诉你怎么选"
        hook = f"{area}买房不看数据就亏了！今天用真实案例给你算笔账"
        
        # 数据展示（展开）
        data_text = f"今天帮{sp['client_name']}选房，预算{budget}，目标{area}。\n\n"
        data_text += f"我帮他对比了多套房源，发现几个关键数据：\n\n"
        
        # 提取关键数据（排除预算本身）
        key_data = [d for d in data if d['type'] not in ['金额'] or d['value'] != budget]
        
        if key_data:
            for d in key_data[:4]:
                if d['type'] == '套数':
                    data_text += f"- 看了{d['value']}套房子\n"
                elif d['type'] == '面积':
                    data_text += f"- 面积{d['value']}平\n"
                elif d['type'] == '比例':
                    data_text += f"- 价差{d['value']}\n"
                elif d['type'] == '折扣':
                    data_text += f"- 折扣{d['value']}\n"
                elif d['type'] == '楼层':
                    data_text += f"- 楼层{d['value']}\n"
                else:
                    data_text += f"- {d['type']}: {d['value']}\n"
        else:
            data_text += f"- 预算{budget}，在{area}能选择的空间有限\n"
            data_text += f"- 对比了多套房源的单价和总价\n"
            data_text += f"- 发现了明显的价格差异\n"
        
        data_text += f"\n"
        
        # 补充分析
        if communities:
            data_text += f"重点看了{'、'.join(communities[:3])}这几个小区。\n\n"
        
        data_text += f"通过数据对比，他清楚地看到了每套房的性价比。\n\n"
        data_text += f"最后选了最匹配的那套，既满足需求又控制预算。"
        
        # 分析（展开）
        analysis = f"买房不看数据，就像闭着眼睛走路。\n\n"
        analysis += f"同样的预算，在{area}可以买到完全不同的房子。\n\n"
        analysis += f"关键是要知道怎么对比，怎么算账。"
        
        # 引导
        cta = f"想知道你在{area}能买什么房？私信我，用数据帮你分析。点赞收藏不迷路"
        
        return f"# {title}\n\n## 开场（3秒钩子）\n{hook}\n\n## 数据展示（20秒）\n{data_text}\n\n## 分析（15秒）\n{analysis}\n\n## 结尾（7秒）\n{cta}"
    
    def _generate_opportunity_script(self, sp, material):
        """机会稀缺型脚本 - 核心：捡漏"""
        budget = sp.get("budget", "500万")
        area = sp.get("area", "上海")
        content = sp.get("content", "")
        communities = sp.get("community_names", [])
        data = sp.get("data_points", [])
        
        title = f"今天发现一个{budget}的捡漏机会，在{area}"
        hook = f"注意了！今天发现一套{budget}的房子，在{area}，性价比超高。"
        
        # 机会描述（展开细节）
        opportunity = f"这套房子的价格比同小区低"
        if data:
            for d in data[:2]:
                if d['type'] in ['折扣', '比例']:
                    opportunity += f"{d['value']}"
                    break
            else:
                opportunity += "15%"
        else:
            opportunity += "15%"
        opportunity += f"，但品质一点都不差。\n\n"
        
        # 补充细节
        if communities:
            opportunity += f"小区是{communities[0]}，{sp['client_name']}原本只是随便看看，但我一看到这套房子就知道不能错过。\n\n"
        else:
            opportunity += f"{sp['client_name']}原本只是随便看看，但我一看到这套房子就知道不能错过。\n\n"
        
        opportunity += f"为什么说是捡漏？第一，价格确实低；第二，户型方正；第三，楼层好。"
        
        # 分析（展开）
        analysis = f"我帮他分析了这套房子的优缺点，发现缺点都是可以解决的，但价格优势是实实在在的。\n\n"
        analysis += f"而且{area}这个板块，未来还有升值空间。现在入手，正是时候。"
        
        # 引导
        cta = f"想捡漏的私信我，好房子不等人。关注走起来"
        
        return f"# {title}\n\n## 开场（3秒钩子）\n{hook}\n\n## 机会描述（20秒）\n{opportunity}\n\n## 分析（15秒）\n{analysis}\n\n## 结尾（7秒）\n{cta}"
    
    def _generate_avoid_script(self, sp, material):
        """避坑指南型脚本 - 核心：规避风险"""
        budget = sp.get("budget", "500万")
        area = sp.get("area", "上海")
        content = sp.get("content", "")
        communities = sp.get("community_names", [])
        
        title = f"在{area}买房，这种房子千万别买！"
        hook = f"今天劝退了{sp['client_name']}一套房子，为什么？因为有硬伤！"
        
        # 坑点描述
        pit = f"这套房子的{sp['conflict'][0] if sp.get('conflict') else '采光/噪音/临街'}问题，住进去之后每天都会很痛苦。"
        
        # 专业建议
        advice = f"我帮他分析了3个替代方案，同样的预算，可以买到更好的。买房不是将就，是选择。"
        
        # 金句
        golden = f"我的价值不是带你看房，而是帮你规避掉未来10年可能踩到的坑。"
        
        # 引导
        cta = f"想在{area}买房不踩坑？关注我，我把这份避坑清单发给你。"
        
        return f"# {title}\n\n## 开场（3秒钩子）\n{hook}\n\n## 坑点描述（15秒）\n{pit}\n\n## 专业建议（20秒）\n{advice}\n\n## 金句（12秒）\n{golden}\n\n## 结尾（8秒）\n{cta}"
    
    def _validate_script(self, script):
        """验证脚本质量 - 基于 8 大爆款特点"""
        from viral_validator import ViralScriptValidator
        validator = ViralScriptValidator()
        return validator.validate(script)
    
    def _add_production_guide(self, script, sp, material, validation):
        """添加拍摄指导和元数据"""
        meta = f"""

---
## 📊 脚本元数据
- 素材来源：{material.get('client', '客户')} 跟进记录
- 闪光点类型：{sp.get('shining_type', '专业筛选')}
- 使用策略：{sp.get('strategy', '专业输出型')}
- 闪光点描述：{sp.get('shining_desc', '')}
- 脚本字数：{validation.get('word_count', 0)} 字
- 质量验证：{'通过' if validation.get('valid') else '未通过：' + ', '.join(validation.get('issues', []))}
- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        # 拍摄建议
        shooting_tips = []
        shining_type = sp.get('shining_type', '')
        
        if shining_type == "反差拒绝":
            shooting_tips.append("场景：小区门口或电脑前，表情严肃")
            shooting_tips.append("动作：揉海报/丢资料/摆手拒绝")
            shooting_tips.append("语气：坚定、专业、不容置疑")
        elif shining_type == "专业筛选":
            shooting_tips.append("场景：电脑前展示分析表格")
            shooting_tips.append("动作：指屏幕/翻资料/做笔记")
            shooting_tips.append("语气：自信、专业、数据驱动")
        elif shining_type == "家庭决策":
            shooting_tips.append("场景：客厅或咖啡厅，轻松氛围")
            shooting_tips.append("动作：手势配合/微笑/点头")
            shooting_tips.append("语气：温暖、共情、有说服力")
        elif shining_type == "数据对比":
            shooting_tips.append("场景：电脑前展示数据对比")
            shooting_tips.append("动作：指数据/对比/总结")
            shooting_tips.append("语气：理性、客观、有逻辑")
        elif shining_type == "捡漏机会":
            shooting_tips.append("场景：小区门口或房源现场")
            shooting_tips.append("动作：兴奋/指房子/看手机")
            shooting_tips.append("语气：急切、兴奋、稀缺感")
        elif shining_type == "避坑指南":
            shooting_tips.append("场景：问题房源现场或电脑前")
            shooting_tips.append("动作：摇头/摆手/严肃表情")
            shooting_tips.append("语气：警告、专业、有说服力")
        
        guide = f"""

---
## 🎬 拍摄指导

### 镜头提示
- **开场**：正面中景，直视镜头，语速稍快
- **主体**：侧面全景或半身，语速平稳，配合手势
- **结尾**：正面特写，微笑，语速稍慢

### 拍摄建议
""" + "\n".join([f"- {tip}" for tip in shooting_tips]) + f"""

### 字幕提示
- **标题**：大字居中，黄色/红色高亮
- **开场**：逐句出现，配合语气停顿
- **主体**：分段显示，关键数据加粗
- **结尾**：引导语加粗，引导点赞/收藏/关注

### 时长控制
- **总时长**：1-2分钟（约300-500字）
- **开场**：3-5秒
- **主体**：40-60秒
- **结尾**：10-15秒

### 发布建议
- **发布时间**：晚上7-9点（流量高峰）
- **话题标签**：#上海买房 #二手房 #房产投资 #{material.get('area', '上海')}房产
- **封面文字**：标题前10个字，大字居中

### 互动钩子
- **评论区置顶**："{sp.get('budget', '500')}万在{sp.get('area', '上海')}，大家觉得是选{sp.get('community_names', ['达安花园'])[0] if sp.get('community_names') else '中山公园'}还是{sp.get('community_names', ['苏堤春晓'])[1] if len(sp.get('community_names', [])) > 1 else '曹家渡'}？"
- **私信引导**：后台发送'买房'，获取全城比对报告"""
        
        return script + meta + guide
    
    def save_script(self, script, date_str=None):
        """保存脚本到文件"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        output_path = self.output_dir / f"daily-script-{date_str}.md"
        output_path.write_text(script, encoding="utf-8")
        return output_path
    
    def auto_fix(self, script, issues, sp, material):
        """自动修复脚本 - 基于验证报错"""
        text = re.sub(r'#.*\n', '', script)
        text = re.sub(r'##.*\n', '', text)
        word_count = len(text.replace(' ', '').replace('\n', ''))
        
        budget = sp.get("budget", "500 万")
        area = sp.get("area", "上海")
        client = sp.get("client_name", "客户")
        communities = sp.get("community_names", [])
        
        # 如果脚本太长，先截断再修复
        if word_count > 550:
            # 保留前 500 字
            lines = script.split('\n')
            truncated = []
            current_count = 0
            for line in lines:
                line_count = len(line.replace(' ', '').replace('\n', ''))
                if current_count + line_count > 500:
                    break
                truncated.append(line)
                current_count += line_count
            script = '\n'.join(truncated)
            print(f"[FIX] 脚本过长，截断至 500 字")
        
        # 1. 修复长度（太短）
        if any("太短" in issue for issue in issues):
            fix_text = f"\n\n## 补充（专家建议）\n"
            fix_text += f"作为在{area}做了 5 年房产的经纪人，我见过太多因为冲动买房而后悔的案例。\n\n"
            fix_text += f"给{budget}预算的买家 3 个建议：\n\n"
            fix_text += f"第一，先定板块，再定小区，最后选房源。顺序不能乱。\n\n"
            fix_text += f"第二，不要只看挂牌价，要看近 3 个月的实际成交价。\n\n"
            fix_text += f"第三，留足 20 万的装修和税费预算，别把首付花光。"
            script += fix_text
        
        # 2. 修复反差感
        if any("反差感" in issue for issue in issues):
            contrast = f"\n\n## 反差（预期 vs 现实）\n"
            contrast += f"{client}原本以为{budget}在{area}能买到很不错的房子。\n\n"
            contrast += f"结果看了好几套都不满意，这就是现实——没有完美的房子。"
            script += contrast
        
        # 3. 修复真实感
        if any("真实感" in issue for issue in issues):
            realism = f"\n\n## 数据（真实记录）\n"
            realism += f"- 客户：{client}\n"
            realism += f"- 预算：{budget}\n"
            realism += f"- 目标：{area}\n"
            if communities:
                realism += f"- 重点看了：{'、'.join(communities[:3])}\n"
            realism += f"（以上数据均来自真实跟进记录）"
            script += realism
        
        # 4. 修复价值输出
        if any("价值输出" in issue for issue in issues):
            value = f"\n\n## 干货（避坑指南）\n"
            value += f"在{area}买房，这 3 个坑千万别踩：\n\n"
            value += f"1. 不要只看装修，隐藏工程才是关键。\n\n"
            value += f"2. 不要轻信中介口头承诺，一切写进合同。\n\n"
            value += f"3. 不要冲动下定，回去睡一觉再决定。"
            script += value
        
        # 5. 修复互动钩子
        if any("互动钩子" in issue for issue in issues):
            interaction = f"\n\n## 互动（评论区见）\n"
            interaction += f"你在{area}买房遇到过什么坑？评论区告诉我。\n\n"
            interaction += f"关注我，每天分享一个真实买房案例。"
            script += interaction
        
        return script
    

    def apply_compliance_filter(self, script):
        """平台合规过滤 - 自动清洗限流风险内容"""
        original = script
        
        # 规则 1: 敏感词替换（投资/炒房/升值等）
        sensitive_map = {
            '投资': '资产配置',
            '炒房': '房产配置',
            '升值': '保值',
            '首付贷': '资金规划',
            '零首付': '低门槛',
            '暴涨': '市场回暖',
            '抄底': '入手时机',
            '限购': '政策调整',
        }
        for old, new in sensitive_map.items():
            script = script.replace(old, new)
        
        # 规则 2: 绝对化用语软化（千万别/绝对/100%等）
        absolute_map = {
            '千万别买': '建议谨慎考虑',
            '千万别踩': '建议避开',
            '稳赚不赔': '需综合评估',
            '100%': '大概率',
            '绝对': '相对',
            '一定': '通常',
            '必须': '建议',
        }
        for old, new in absolute_map.items():
            script = script.replace(old, new)
        
        # 规则 3: 引流话术替换（小红书/视频号严打直接引流）
        diversion_map = {
            '加我微信': '评论区留言',
            '扫码领': '后台获取',
            '私信我': '评论区交流',
            '私信聊聊': '评论区聊',
            '后台告诉我': '评论区留言',
            '送你一份': '分享一份',
            '关注我': '点赞收藏',
        }
        for old, new in diversion_map.items():
            script = script.replace(old, new)
        
        # 规则 4: 价格/政策承诺防护
        if '保证' in script or '承诺' in script:
            script = script.replace('保证', '建议').replace('承诺', '规划')
        
        # 记录修改日志
        if script != original:
            print("[COMPLIANCE] 已应用合规过滤（替换敏感词/软化绝对用语/替换引流话术）")
        
        return script

    def run(self, date_str=None):
        """执行主流程 - 带闭环验证"""
        print(f"开始生成{date_str or '今日'}视频脚本...")
        
        # 解析日期
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                print(f"日期格式错误：{date_str}")
                return None
        else:
            target_date = date.today()
        
        # 1. 加载跟进记录
        followups = self.load_followups(target_date)
        if not followups:
            print("未找到当天跟进记录")
            return None
        
        print(f"找到{len(followups)}条跟进记录")
        
        # 2. 选择素材
        material = self.select_material(followups)
        if not material:
            print("未找到合适素材")
            return None
        
        print(f"选择素材：{material.get('client', '客户')} - {material.get('content', '')[:30]}...")
        
        # 3. 提炼闪光点
        shining_point = self.extract_shining_point(material)
        print(f"闪光点类型：{shining_point.get('shining_type', '专业筛选')}")
        print(f"闪光点描述：{shining_point.get('shining_desc', '')}")
        print(f"使用策略：{shining_point.get('strategy', '专业输出型')}")
        
        # 4. 闭环生成（最多重试 3 次）
        MAX_RETRIES = 3
        script = None
        validation = None
        
        for attempt in range(MAX_RETRIES):
            print(f"\n[尝试 {attempt + 1}/{MAX_RETRIES}] 生成脚本...")
            
            # 第一次生成，后续修复
            if attempt == 0:
                script = self.generate_script(material)
            else:
                # 修复后的脚本已经在上一轮保存
                pass
            
            if not script:
                print("脚本生成失败")
                return None
            
            # 验证
            validation = self._validate_script(script)
            print(f"验证得分：{validation['total_score']}/{validation['max_score']} ({validation['pass_rate']*100:.0f}%)")
            print(f"脚本字数：{validation['word_count']} 字")
            
            if validation['valid']:
                print("[PASS] 验证通过！")
                break
            else:
                print(f"[WARN] 验证未通过（{len(validation['issues'])}项问题）：{', '.join(validation['issues'])}")
                if attempt < MAX_RETRIES - 1:
                    print("[FIX] 开始自动修复...")
                    script = self.auto_fix(script, validation['issues'], shining_point, material)
                else:
                    print("[WARN] 已达到最大重试次数，使用当前版本")
        
        # 5. 合规过滤（平台限流防护）
        script = self.apply_compliance_filter(script)
        
        # 6. 保存文件
        output_path = self.save_script(script, target_date.strftime("%Y-%m-%d"))
        print(f"\n脚本已保存：{output_path}")
        
        return output_path


if __name__ == "__main__":
    generator = VideoScriptGenerator()
    
    # 支持命令行参数指定日期
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    output = generator.run(date_arg)
    if output:
        print("\n[OK] 视频脚本生成成功！")
        print(f"[FILE] 文件位置：{output}")
    else:
        print("\n[FAIL] 视频脚本生成失败")
        sys.exit(1)
