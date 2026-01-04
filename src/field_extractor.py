"""
字段提取器 - 从解析后的日志数据中提取关键字段
"""
from typing import Dict, Any, Optional


def extract_fields_from_log_data(log_data: Dict[str, Any], extract_bill_info_func) -> Dict[str, Any]:
    """
    从解析后的日志数据字典中提取所有字段
    
    Args:
        log_data: 解析后的日志数据字典
        extract_bill_info_func: 提取账单信息的函数（LogParser._extract_bill_info方法）
        
    Returns:
        提取后的字段字典，包含所有关键字段
    """
    result = {}
    
    # 1. 提取query（用户输入）- 缺失时设为None
    result['query'] = log_data.get('messageUser') or None
    
    # 2. 提取账单信息 - 缺失时设为None
    result['bill_info'] = extract_bill_info_func(log_data)
    
    # 3. 提取reply（大模型回复）- 缺失时设为None
    result['reply'] = log_data.get('reply') or None
    
    # 4. 提取其他可能有用的字段（可扩展）
    result['user_id'] = log_data.get('userId', None)
    result['session_id'] = log_data.get('sessionId', '') or None
    result['user_intention'] = log_data.get('userIntention', '') or None
    result['success_flag'] = log_data.get('successFlag', None)
    
    return result


def create_empty_result() -> Dict[str, Any]:
    """
    创建空的结果结构（所有核心字段为None）
    
    Returns:
        空的结果字典
    """
    return {
        'query': None,
        'bill_info': None,
        'reply': None
    }

