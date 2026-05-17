# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
经验库查询触发脚本
当用户对回答不满意时自动执行：
1. 定位问题和不满点
2. 打标签
3. 查询经验库
4. 输出解决方案
"""
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

# ==================== 标签关键词映射 ====================

S_TAGS = {
    'S1': ['刚接触', '第一次', '初次', '新客', '刚加', '刚认识'],
    'S2': ['初步接触', '了解中', '还在看', '随便看看', '不着急'],
    'S3': ['带看', '看房', '实地看', '约看', '陪看'],
    'S4': ['谈判', '谈价格', '出价', '议价', '谈价', '签约', '成交'],
    'S5': ['跟进中', '持续跟进', '定期联系', '保持联系'],
    'S6': ['意向强烈', '想买', '准备买', '要定了', '确定要'],
    'S7': ['休眠', '暂停', '不买了', '放弃', '搁置', '冷却'],
}

C_TAGS = {
    'C1': ['无需求', '不需要', '不买房', '暂时不买', '没需求'],
    'C2': ['需求不清', '不知道', '不清楚', '没想好', '不确定'],
    'C3': ['不信任', '怀疑', '防备', '怕被忽悠', '怕骗', '中介', '不相信'],
    'C4': ['竞品对比', '别家', '其他中介', '对比', '比较'],
    'C5': ['决策困难', '犹豫', '纠结', '难决定', '拿不定'],
    'C6': ['信息验证', '查证', '核实', '确认', '验证'],
    'C7': ['信息不全', '不了解', '不知道', '信息少', '资料缺'],
    'C8': ['预算', '钱', '资金', '贷款', '首付', '返佣', '费用', '贵', '便宜'],
}

B_TAGS = {
    'B1': ['不回复', '不回消息', '不接电话', '拉黑', '拒接'],
    'B2': ['敷衍', '随便', '看看再说', '再想想', '考虑考虑'],
    'B3': ['消极', '冷淡', '没兴趣', '不积极', '被动'],
    'B4': ['从不回复', '没反应', '石沉大海'],
    'B5': ['浏览', '看了', '点击', '关注', '收藏'],
    'B6': ['低意愿', '不想买', '没意向', '意愿低'],
    'B8': ['防御', '防备心', '敏感', '谨慎', '小心'],
    'B9': ['信任建立', '信任', '认可', '放心', '靠谱'],
    'B10': ['竞争', '有人谈', '有人买', '抢手', '多人看'],
    'B13': ['带看宝宝', '带看', '复看', '二看'],
    'B14': ['感动', '感谢', '认可', '谢谢', '辛苦'],
    'B15': ['出价', '报价', '还价', '出价了'],
    'B16': ['成交', '买了', '定了', '签约', '过户'],
}

T_TAGS = {
    'T1': ['读取', '查询', '获取', '打开', '加载', '导入'],
    'T2': ['写入', '更新', '修改', '保存', '添加', '删除'],
    'T3': ['Excel', '表格', 'csv', 'xlsm', 'xls'],
    'T4': ['超时', '卡住', '失败', '错误', '报错', '异常', '进程', 'kill'],
    'T5': ['脚本', '代码', '程序', '运行', '执行', 'python', 'vbs'],
    'T6': ['文件', '路径', '目录', '文件夹', '复制', '移动'],
}

# 不满信号
COMPLAINT_SIGNALS = [
    '不对', '错了', '不是这样', '不准确', '有问题',
    '不对的', '不是这样的', '不是这个意思', '理解错了',
    '你错了', '你说的不对', '不是这样的', '不太对',
]

# ==================== 函数 ====================

def detect_complaint(user_input):
    """检测用户是否表达不满"""
    for signal in COMPLAINT_SIGNALS:
        if signal in user_input:
            return True
    return False

def classify(problem):
    """根据问题内容打标签"""
    tags = []
    problem_lower = problem.lower()
    
    # 判断是业务问题还是技术问题
    is_technical = False
    technical_keywords = ['脚本', '代码', 'Excel', '表格', '文件', '路径', '进程', '超时', '报错', 'python', 'vbs', 'csv']
    for kw in technical_keywords:
        if kw.lower() in problem_lower:
            is_technical = True
            break
    
    if is_technical:
        for tag, keywords in T_TAGS.items():
            for kw in keywords:
                if kw.lower() in problem_lower:
                    if tag not in tags:
                        tags.append(tag)
                    break
        if not tags:
            tags.append('T6')
    else:
        for tag, keywords in S_TAGS.items():
            for kw in keywords:
                if kw in problem_lower:
                    if tag not in tags:
                        tags.append(tag)
                    break
        
        for tag, keywords in C_TAGS.items():
            for kw in keywords:
                if kw in problem_lower:
                    if tag not in tags:
                        tags.append(tag)
                    break
        
        for tag, keywords in B_TAGS.items():
            for kw in keywords:
                if kw in problem_lower:
                    if tag not in tags:
                        tags.append(tag)
                    break
    
    return tags

def format_query(tags):
    """生成查询命令"""
    s_val = next((t for t in tags if t.startswith('S')), '')
    c_val = next((t for t in tags if t.startswith('C')), '')
    b_val = next((t for t in tags if t.startswith('B')), '')
    t_val = next((t for t in tags if t.startswith('T')), '')
    
    if t_val:
        return f"python technical.py query \"{t_val}\" \"\" \"\" \"关键词\""
    else:
        return f"python experience.py query \"{s_val}\" \"{c_val}\" \"{b_val}\" \"关键词\""

def analyze(original_question, complaint):
    """
    分析用户不满，输出查询方案
    """
    # 检测是否是不满
    is_complaint = detect_complaint(complaint)
    
    print("=" * 50)
    print("🔍 经验库查询触发")
    print("=" * 50)
    print(f"原始问题：{original_question}")
    print(f"用户反馈：{complaint}")
    print(f"不满检测：{'✅ 是' if is_complaint else '❌ 否'}")
    print()
    
    if not is_complaint:
        print("⚠️  未检测到不满信号，不触发经验库查询")
        return None
    
    # 打标签
    tags = classify(original_question)
    print(f"识别标签：{' '.join(tags) if tags else '无匹配'}")
    print()
    
    # 生成查询命令
    query_cmd = format_query(tags)
    print(f"📋 查询命令：")
    print(f"   {query_cmd}")
    print()
    
    return {
        'tags': tags,
        'query': query_cmd,
        'is_technical': any(t.startswith('T') for t in tags)
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：python query_experience.py <原始问题> <用户不满反馈>")
        print("示例：python query_experience.py \"客户不信任我怎么办\" \"你说的不对，不是这样的\"")
        sys.exit(1)
    
    original = sys.argv[1]
    complaint = " ".join(sys.argv[2:])
    
    result = analyze(original, complaint)
    
    if result:
        print("=" * 50)
        print("✅ 已生成查询命令，请执行以获取经验")
        print("=" * 50)
