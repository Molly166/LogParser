"""
测试脚本 - 验证日志解析器功能
"""
import sys
import io
from pathlib import Path

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from log_parser import LogParser


def test_single_line():
    """测试单行日志解析"""
    log_line = '00:06:24.854 [task-65221] INFO  modelAnalysis - [saveModelAnalysisLog,789] - {"analysisParam":"{\"user_id\":1638,\"query\":\"垃圾袋0.99\",\"history\":[],\"session_id\":\"1328ea00b5604d359c4d671c07c411a7\"}","analysisResult":"{\"action\": \"add\", \"user_intention\": \"新增账单\", \"message\": [{\"bill_type_name\": \"支出\", \"parent_name\": \"购物\", \"classify_name\": \"日用品\", \"bill_amount\": \"0.99\", \"bill_time\": \"2025-12-16 00:06:18\", \"remark\": \"买垃圾袋\", \"abled_expense\": \"false\", \"is_expensed\": 0}], \"message_interpretation\": \"账单:[{\'类别\': \'支出\', \'一级类目\': \'购物\', \'二级类目\': \'日用品\', \'金额\': \'0.99\', \'时间\': \'2025-12-16 00:06:18\', \'是否需要报销\': \'无需报销\', \'是否报销\': \'无需报销账单\'}]已为您记录成功\", \"status\": \"success\"}","messageUser":"垃圾袋0.99","promptParam":"{\"user_id\":1638,\"session_id\":\"1328ea00b5604d671c07c411a7\",\"query\":\"垃圾袋0.99\",\"history\":[],\"reference\":\"账单:[{\'类别\': \'支出\', \'一级类目\': \'购物\', \'二级类目\': \'日用品\', \'金额\': \'0.99\', \'时间\': \'2025-12-16 00:06:18\', \'是否需要报销\': \'无需报销\', \'是否报销\': \'无需报销账单\'}]已为您记录成功\",\"customer_profile_prompt\":\"{\\\"昵称\\\":\\\"小橙\\\"}\",\"NPC_describe\":\"用轻松诙谐的语言陪伴你记账\",\"user_intention\":\"新增账单\",\"action\":\"add\"}","promptResult":"{\"status\": \"success\", \"prompt\": \"\\n**输入数据**：\\n1.当前消息message：[垃圾袋0.99]\\n\\n2.会话上下文history（仅辅助）：[[]]  # 截断显示\\n\\n3.用户意图：新增账单\\n\\n4.AI客服助理的处理结果reference（仅作为原始参考语料）：账单:[{\'类别\': \'支出\', \'一级类目\': \'购物\', \'二级类目\': \'日用品\', \'金额\': \'0.99\', \'时间\': \'2025-12-16 00:06:18\', \'是否需要报销\': \'无需报销\', \'是否报销\': \'无需报销账单\'}]已为您记录成功\",\"context_id\": \"ctx-20251216000003-7xjnc\"}","reply":"嘿呀，小橙！买垃圾袋的这笔0.99元支出账单，已为您安排得妥妥当当啦，一级类目是"购物"，二级类目属于"日用品"，就等着踏踏实实记在账本里咯！","sessionId":"1328ea00b5604d359c4d671c07c411a7","successFlag":1,"userAction":"add","userId":1638,"userIntention":"新增账单"}'
    
    parser = LogParser()
    result = parser.parse_log_line(log_line)
    
    if result:
        print("[OK] 单行日志解析成功")
        print(f"  用户输入 (query): {result.get('query')}")
        print(f"  账单信息: {result.get('bill_info')}")
        print(f"  大模型回复 (reply): {result.get('reply')}")
        
        # 验证关键字段
        assert result.get('query') == '垃圾袋0.99', "query字段提取错误"
        assert result.get('bill_info') is not None, "账单信息未提取到"
        assert '支出' in result.get('bill_info', ''), "账单信息内容不完整"
        assert result.get('reply') is not None and len(result.get('reply', '')) > 0, "reply字段提取错误"
        print("[OK] 所有字段验证通过")
        return True
    else:
        print("[FAIL] 单行日志解析失败")
        return False


def test_file_parsing():
    """测试文件解析"""
    test_file = Path(__file__).parent / 'test_log.txt'
    
    if not test_file.exists():
        print(f"[FAIL] 测试文件不存在: {test_file}")
        return False
    
    parser = LogParser()
    results = parser.parse_log_file(test_file)
    
    if results:
        print(f"[OK] 文件解析成功，共 {len(results)} 条记录")
        return True
    else:
        print("[FAIL] 文件解析失败")
        return False


if __name__ == '__main__':
    print("开始测试日志解析器...")
    print("\n1. 测试单行日志解析")
    test1 = test_single_line()
    
    print("\n2. 测试文件解析")
    test2 = test_file_parsing()
    
    print("\n" + "="*50)
    if test1 and test2:
        print("[OK] 所有测试通过！")
    else:
        print("[FAIL] 部分测试失败")
