# -*- coding: utf-8 -*-
"""缓存管理工具函数"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import pythoncom
    from win32com.client import DispatchEx, GetObject
except ImportError:
    pythoncom = None
    DispatchEx = None
    GetObject = None

# 配置
WORKBOOK_PATH = Path(r"D:\Unique work form\daily_followup.xlsm")
WORKBOOK_PASSWORD = "000"
CLIENT_SHEET_INDEX = 2  # "客户不要猜" 工作表
PROPERTY_SHEET_INDEX = 4
RUNTIME_DIR = Path(r"C:\Users\Huawei\.openclaw\workspace-tuantuan\runtime")
CACHE_FILE = RUNTIME_DIR / "tuantuan_cache.json"


def ensure_cache(force: bool = False) -> dict[str, Any]:
    """获取缓存。优先使用现有缓存，即使不新鲜也比报错好。"""
    if force:
        return build_cache()
    
    cache = load_cache()
    
    # 如果有缓存，优先使用（即使不新鲜）
    if cache and cache_has_required_payload(cache):
        if not cache_is_fresh(cache):
            cache_age_hours = cache_age_in_hours(cache)
            if cache_age_hours > 24:
                pass  # 超过 24 小时，继续使用但不阻断
        return cache
    
    # 没有缓存时，检查 Excel 是否占用
    if is_workbook_open():
        raise RuntimeError(
            f"Excel 正在占用主表且没有可用缓存，请先关闭 Excel 文件后再重试：{WORKBOOK_PATH}"
        )
    
    # Excel 未占用，重建缓存
    return build_cache()


def load_cache() -> Optional[dict[str, Any]]:
    """加载缓存"""
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_cache() -> dict[str, Any]:
    """构建缓存"""
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(f"主表不存在：{WORKBOOK_PATH}")
    
    # 先强制关闭 Excel 进程
    _kill_excel_process()
    import time
    time.sleep(1)
    
    if pythoncom is None or DispatchEx is None or GetObject is None:
        raise RuntimeError("win32com 不可用，无法读取带密码的 Excel 文件。")
    
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    
    try:
        excel = DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        workbook = excel.Workbooks.Open(
            Filename=str(WORKBOOK_PATH),
            UpdateLinks=0,
            ReadOnly=True,
            Password=WORKBOOK_PASSWORD,
        )
        
        client_sheet = workbook.Worksheets(CLIENT_SHEET_INDEX)
        property_sheet = workbook.Worksheets(PROPERTY_SHEET_INDEX)
        
        clients = parse_clients(client_sheet)
        properties = parse_properties(property_sheet)
        
        business_experiences = []
        technical_experiences = []
        for i in range(1, workbook.Worksheets.Count + 1):
            ws_name = workbook.Worksheets(i).Name
            if ws_name == "Experience":
                business_experiences = parse_business_experiences(workbook.Worksheets(i))
            elif ws_name == "Technical":
                technical_experiences = parse_technical_experiences(workbook.Worksheets(i))
        
        cache = {
            "generated_at": iso_now(),
            "source": {
                "workbook_path": str(WORKBOOK_PATH),
                "workbook_mtime": workbook_mtime(),
            },
            "clients": clients,
            "properties": properties,
            "business_experiences": business_experiences,
            "technical_experiences": technical_experiences,
        }
        
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        return cache
        
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


def parse_clients(ws, include_followups: bool = True) -> list[dict[str, Any]]:
    """解析客户数据
    
    Args:
        ws: Excel 工作表对象
        include_followups: 是否读取跟进记录（日期列），False 时速度更快
    """
    clients = []
    header_row = 11
    
    # 列映射（根据实际表格结构 - "客户不要猜" 工作表）:
    # A(1)=最优经验，B(2)=15 条经验，C(3)=向量，D(4)=客户情况，E(5)=推送房源
    # F(6)=等级，G(7)=户型，H(8)=预算，I(9)=姓名，J(10)=区域，K(11)=电话
    # L(12)=解读，M(13)=决策速度，N(14)=信息处理方式，O(15)=互动态度
    # P(16)=需求，Q(17)=最想说的话，R(18)=痛点，S(19)=备注
    # T(20) 开始是日期列，每个日期列与客户行交叉点是跟进记录
    
    # 读取日期列并扫描"建议"/"检查"列
    date_columns = []
    suggestion_col = None
    check_col = None
    
    if include_followups:
        for col in range(1, ws.UsedRange.Columns.Count + 1):
            header_val = ws.Cells(header_row, col).Value
            if header_val:
                s = str(header_val).strip()
                # 识别日期列（跟进记录）
                if s.startswith("20") and "-" in s[:10]:
                    date_columns.append((col, s[:10]))
                # 识别AI建议列（实际表头是 AI-XXXX 格式，如 AI-0425）
                if s.startswith("AI-"):
                    suggestion_col = col
                # 识别AI检查列（脚本写入时带"检查"二字，如 2026-04-25 检查）
                if "检查" in s:
                    check_col = col
    
    # 优化：批量读取跟进数据区域（使用 Range 对象）
    followup_matrix = None
    if include_followups and date_columns:
        try:
            start_row, end_row = 12, ws.UsedRange.Rows.Count
            start_col, end_col = 20, ws.UsedRange.Columns.Count
            range_obj = ws.Range(ws.Cells(start_row, start_col), ws.Cells(end_row, end_col))
            followup_matrix = range_obj.Value  # 二维元组
        except Exception as e:
            followup_matrix = None
    
    for row in range(12, ws.UsedRange.Rows.Count + 1):
        try:
            name = clean_text(ws.Cells(row, 9).Value)  # I 列 = 姓名
            if not name:
                continue
            
            client = {
                "row": row,
                "name": name,
                "phone": clean_text(ws.Cells(row, 11).Value),  # K 列 = 电话
                "grade": clean_text(ws.Cells(row, 6).Value),   # F 列 = 等级
                "rooms": clean_text(ws.Cells(row, 7).Value),   # G 列 = 户型
                "budget": clean_text(ws.Cells(row, 8).Value),  # H 列 = 预算
                "district": clean_text(ws.Cells(row, 10).Value),  # J 列 = 区域
                "pushed_houses": clean_text(ws.Cells(row, 5).Value),  # E 列 = 推送房源编号
                # 客户画像字段
                "decode": clean_text(ws.Cells(row, 12).Value),  # L 列 = 解读
                "decision_speed": clean_text(ws.Cells(row, 13).Value),  # M 列 = 决策速度
                "info_style": clean_text(ws.Cells(row, 14).Value),  # N 列 = 信息处理方式
                "interaction_style": clean_text(ws.Cells(row, 15).Value),  # O 列 = 互动态度
                "need": clean_text(ws.Cells(row, 16).Value),  # P 列 = 需求
                "ideal_phrase": clean_text(ws.Cells(row, 17).Value),  # Q 列 = 最想说的话
                "pain": clean_text(ws.Cells(row, 18).Value),  # R 列 = 痛点
                "notes": clean_text(ws.Cells(row, 19).Value),  # S 列 = 备注
                # 跟进记录
                "followup_status": clean_text(ws.Cells(row, 4).Value) if include_followups else None,
                "followup_count": 0,
                "last_followup_date": None,
                "followups": [],
            }
            
            # 读取建议和检查列
            if suggestion_col:
                v = ws.Cells(row, suggestion_col).Value
                client["ai_suggestion"] = clean_text(v)
            if check_col:
                v = ws.Cells(row, check_col).Value
                client["ai_check"] = clean_text(v)
            
            # 使用批量读取的跟进数据
            if include_followups and date_columns and followup_matrix:
                followups = []
                matrix_row_idx = row - 12  # 矩阵中的行索引
                for col, date_str in date_columns:
                    matrix_col_idx = col - 20  # 矩阵中的列索引
                    if 0 <= matrix_row_idx < len(followup_matrix) and 0 <= matrix_col_idx < len(followup_matrix[0]):
                        followup_val = followup_matrix[matrix_row_idx][matrix_col_idx]
                        if followup_val and str(followup_val).strip():
                            followups.append({
                                "date": date_str,
                                "content": clean_text(followup_val),
                            })
                client["followup_count"] = len(followups)
                client["last_followup_date"] = followups[-1]["date"] if followups else None
                client["followups"] = followups[-5:]  # 最近 5 条
            
            clients.append(client)
        except:
            continue
    
    return clients


def parse_properties(ws) -> list[dict[str, Any]]:
    """解析房源数据 - 完整字段"""
    properties = []
    
    start_row, end_row = 4, ws.UsedRange.Rows.Count
    if start_row > end_row:
        return properties
    
    # 批量读取所需列
    # 列 1: 行政区，列 2: 标题，列 3: 小区，列 4: 户型，列 5: 面积
    # 列 6: 总价，列 7: 单价，列 8: 楼层，列 9: 房源分，列 10: 创建时间
    # 列 11: 维护人，列 12: 房龄，列 13: house_id, 列 14: detail_url
    try:
        col_a = ws.Range(ws.Cells(start_row, 1), ws.Cells(end_row, 1)).Value  # 行政区
        col_b = ws.Range(ws.Cells(start_row, 2), ws.Cells(end_row, 2)).Value  # 标题
        col_c = ws.Range(ws.Cells(start_row, 3), ws.Cells(end_row, 3)).Value  # 小区
        col_d = ws.Range(ws.Cells(start_row, 4), ws.Cells(end_row, 4)).Value  # 户型
        col_e = ws.Range(ws.Cells(start_row, 5), ws.Cells(end_row, 5)).Value  # 面积
        col_f = ws.Range(ws.Cells(start_row, 6), ws.Cells(end_row, 6)).Value  # 总价
        col_g = ws.Range(ws.Cells(start_row, 7), ws.Cells(end_row, 7)).Value  # 单价
        col_h = ws.Range(ws.Cells(start_row, 8), ws.Cells(end_row, 8)).Value  # 楼层
        col_i = ws.Range(ws.Cells(start_row, 9), ws.Cells(end_row, 9)).Value  # 房源分
        col_j = ws.Range(ws.Cells(start_row, 10), ws.Cells(end_row, 10)).Value  # 创建时间
        col_k = ws.Range(ws.Cells(start_row, 11), ws.Cells(end_row, 11)).Value  # 维护人
        col_l = ws.Range(ws.Cells(start_row, 12), ws.Cells(end_row, 12)).Value  # 房龄
        col_m = ws.Range(ws.Cells(start_row, 13), ws.Cells(end_row, 13)).Value  # house_id
        col_n = ws.Range(ws.Cells(start_row, 14), ws.Cells(end_row, 14)).Value  # detail_url
    except:
        col_a = col_b = col_c = col_d = col_e = col_f = col_g = col_h = col_i = col_j = col_k = col_l = col_m = col_n = [None] * (end_row - start_row + 1)
    
    # 确保是列表形式
    if not isinstance(col_b, (list, tuple)):
        col_b = [col_b]
    if not isinstance(col_e, (list, tuple)):
        col_e = [col_e]
    if not isinstance(col_f, (list, tuple)):
        col_f = [col_f]
    if not isinstance(col_a, (list, tuple)):
        col_a = [col_a]
    if not isinstance(col_m, (list, tuple)):
        col_m = [col_m]
    
    # 处理单行情况
    if len(col_b) == 1 and end_row > start_row:
        # 可能是单值而非列表
        pass
    
    max_len = max(len(col_b), len(col_e), len(col_f), len(col_a), len(col_m))
    
    for i in range(max_len):
        row = start_row + i
        try:
            # 辅助函数：从元组或值中提取数据
            def get_val(col, idx):
                val = col[idx] if idx < len(col) else None
                if isinstance(val, tuple):
                    return val[0] if val else None
                return val
            
            house_id = clean_text(get_val(col_m, i))
            if not house_id:
                continue
            
            property_data = {
                "row": row,
                "house_id": clean_text(get_val(col_m, i)),
                "district": clean_text(get_val(col_a, i)),  # 行政区
                "plate": clean_text(get_val(col_b, i)).split(clean_text(get_val(col_m, i)))[0] if clean_text(get_val(col_m, i)) and clean_text(get_val(col_m, i)) in str(get_val(col_b, i)) else clean_text(get_val(col_b, i)),  # 板块
                "community": clean_text(get_val(col_c, i)),  # 小区名
                "layout": clean_text(get_val(col_d, i)),  # 户型
                "area": clean_text(get_val(col_e, i)),  # 面积
                "price": clean_text(get_val(col_f, i)),  # 总价
                "unit_price": clean_text(get_val(col_g, i)),  # 单价
                "floor": clean_text(get_val(col_h, i)),  # 楼层
                "score": clean_text(get_val(col_i, i)),  # 房源分
                "create_time": clean_text(get_val(col_j, i)),  # 创建时间
                "agent": clean_text(get_val(col_k, i)),  # 维护人
                "building_age": clean_text(get_val(col_l, i)),  # 房龄
                "url": clean_text(get_val(col_n, i)),  # detail_url
            }
            properties.append(property_data)
        except:
            continue
    
    return properties


def parse_business_experiences(ws) -> list[dict[str, Any]]:
    """解析业务经验"""
    experiences = []
    for row in range(2, ws.UsedRange.Rows.Count + 1):
        try:
            content = clean_text(ws.Cells(row, 1).Value)
            if content:
                experiences.append({"content": content, "row": row})
        except:
            continue
    return experiences


def parse_technical_experiences(ws) -> list[dict[str, Any]]:
    """解析技术经验"""
    experiences = []
    for row in range(2, ws.UsedRange.Rows.Count + 1):
        try:
            content = clean_text(ws.Cells(row, 1).Value)
            if content:
                experiences.append({"content": content, "row": row})
        except:
            continue
    return experiences


def cache_has_required_payload(cache: dict[str, Any]) -> bool:
    """检查缓存是否有必需的数据"""
    return (
        "clients" in cache and
        "properties" in cache and
        "generated_at" in cache
    )


def cache_is_fresh(cache: dict[str, Any]) -> bool:
    """检查缓存是否新鲜"""
    if not cache_has_required_payload(cache):
        return False
    if not WORKBOOK_PATH.exists():
        return False
    source = cache.get("source", {})
    return source.get("workbook_mtime") == workbook_mtime()


def cache_age_in_hours(cache: dict[str, Any]) -> float:
    """计算缓存生成到现在的小时数"""
    generated_at = cache.get("generated_at", "")
    if not generated_at:
        return 999.0
    try:
        gen_time = datetime.fromisoformat(generated_at)
        age = datetime.now() - gen_time
        return age.total_seconds() / 3600.0
    except:
        return 999.0


def workbook_mtime() -> str:
    """获取工作簿最后修改时间"""
    return datetime.fromtimestamp(WORKBOOK_PATH.stat().st_mtime).isoformat(timespec="seconds")


def iso_now() -> str:
    """返回当前时间的 ISO 格式"""
    return datetime.now().isoformat(timespec="seconds")


def is_workbook_open(target_path: Optional[Path] = None) -> bool:
    """检查 Excel 是否打开"""
    if pythoncom is None or GetObject is None:
        return False
    
    resolved_target = (target_path or WORKBOOK_PATH).resolve()
    try:
        pythoncom.CoInitialize()
        excel = GetObject(Class="Excel.Application")
        for wb in excel.Workbooks:
            try:
                if Path(wb.FullName).resolve() == resolved_target:
                    return True
            except:
                continue
    except:
        return False
    return False


def wait_excel_closed(timeout_seconds: int = 60, kill_on_timeout: bool = False) -> None:
    """等待 Excel 关闭"""
    if pythoncom is None or DispatchEx is None:
        return
    
    import time
    start_time = time.time()
    while True:
        if not is_workbook_open():
            return
        
        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            if kill_on_timeout:
                _kill_excel_process()
                return
            raise RuntimeError(
                f"等待 Excel 关闭超时（{timeout_seconds}秒）"
            )
        time.sleep(1)


def _kill_excel_process() -> None:
    """强制关闭 Excel 进程"""
    result = subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode('gbk', errors='ignore')
        # 忽略"没有找到进程"和"拒绝访问"（僵尸进程杀不掉但不影响新建实例）
        if "没有找到进程" not in stderr and "no running instance" not in stderr.lower():
            if "拒绝访问" not in stderr and "Access is denied" not in stderr:
                raise RuntimeError(f"关闭 Excel 失败：{stderr}")
            # 部分进程杀不掉，继续执行不影响


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    return str(text).strip()
