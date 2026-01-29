"""
日志解析器 - 从日志文件中提取关键信息
提取字段：query（用户输入）、账单信息、reply（大模型回复）
"""
import json
import re
from typing import Dict, List, Optional, Any, Iterator
from pathlib import Path
from field_extractor import extract_fields_from_log_data, create_empty_result


class LogParser:
    """日志解析器类"""
    
    def __init__(self):
        """初始化解析器"""
        # 账单信息匹配模式：匹配"账单:"关键字
        # 实际的列表提取会在_extract_bill_info中使用更智能的方法
    
    def parse_log_line(self, log_line: str) -> Optional[Dict[str, Any]]:
        """
        解析单条日志行
        
        Args:
            log_line: 日志行字符串
            
        Returns:
            解析后的数据字典，如果解析失败返回None
        """
        try:
            # 提取JSON部分
            # 日志格式通常是: "时间 [任务] 级别 类 - [方法,行号] - {JSON}"
            log_line = log_line.strip()
            
            # 方法1: 查找最后一个 " - " 后的JSON
            last_dash_pos = log_line.rfind(' - ')
            if last_dash_pos != -1:
                json_start = last_dash_pos + 3  # 跳过 " - "
                json_str = log_line[json_start:]
            else:
                # 方法2: 如果找不到 " - "，查找第一个 '{' 开始的位置
                json_start = log_line.find('{')
                if json_start == -1:
                    return None
                json_str = log_line[json_start:]
            
            # 使用括号匹配找到完整的JSON
            # 从第一个'{'开始，找到匹配的最后一个'}'
            brace_count = 0
            json_end = len(json_str)
            for i, char in enumerate(json_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            json_str = json_str[:json_end]
            
            # 尝试解析JSON
            try:
                log_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                # JSON解析失败，使用备用方法（正则表达式提取）
                fallback_result = self._fallback_parse(log_line)
                if fallback_result is not None:
                    return fallback_result
                # 如果备用方法也失败，返回一个空的结果结构（三个字段都为None）
                return create_empty_result()
            
            # 提取关键字段（使用独立的字段提取器）
            result = extract_fields_from_log_data(log_data, self._extract_bill_info)
            return result
            
        except json.JSONDecodeError as e:
            # 尝试更宽松的解析方式
            try:
                # 尝试修复常见的JSON格式问题
                json_str_fixed = json_str.replace("'", '"')
                log_data = json.loads(json_str_fixed)
                # 如果修复成功，继续提取字段（使用独立的字段提取器）
                result = extract_fields_from_log_data(log_data, self._extract_bill_info)
                return result
            except:
                # 所有方法都失败，返回空结果结构
                return create_empty_result()
        except Exception as e:
            # 发生异常，返回空结果结构而不是None
            return create_empty_result()
    
    def _extract_bill_info(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        从日志数据中提取账单信息
        优先从analysisResult的message_interpretation提取，其次从promptParam的reference提取
        支持提取多个账单，会提取最后一个完整的账单列表
        
        Args:
            log_data: 解析后的日志数据字典
            
        Returns:
            账单信息字符串（Python列表格式），如果未找到返回None
        """
        bill_matches = []
        
        # 方法1: 从analysisResult的message_interpretation提取
        analysis_result_str = log_data.get('analysisResult', '')
        if analysis_result_str:
            try:
                analysis_result = json.loads(analysis_result_str)
                message_interpretation = analysis_result.get('message_interpretation', '')
                if message_interpretation:
                    bill_info = self._find_bill_list(message_interpretation)
                    if bill_info:
                        bill_matches.append(bill_info)
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # 方法2: 从promptParam的reference提取
        prompt_param_str = log_data.get('promptParam', '')
        if prompt_param_str:
            try:
                prompt_param = json.loads(prompt_param_str)
                reference = prompt_param.get('reference', '')
                if reference:
                    bill_info = self._find_bill_list(reference)
                    if bill_info:
                        bill_matches.append(bill_info)
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # 如果有多个匹配，返回最后一个（最完整的）
        if bill_matches:
            # 返回最后一个匹配的账单信息
            return bill_matches[-1]
        
        return None
    
    def _find_bill_list(self, text: str) -> Optional[str]:
        """
        从文本中查找"账单:"后的完整列表结构
        使用括号匹配算法确保提取完整的列表
        
        Args:
            text: 要搜索的文本
            
        Returns:
            账单列表字符串，如果未找到返回None
        """
        # 找到所有"账单:"的位置
        bill_keyword = "账单:"
        start_positions = []
        pos = text.find(bill_keyword)
        while pos != -1:
            start_positions.append(pos + len(bill_keyword))
            pos = text.find(bill_keyword, pos + 1)
        
        # 从后往前查找，找到最后一个完整的列表
        for start_pos in reversed(start_positions):
            # 跳过空白字符
            while start_pos < len(text) and text[start_pos].isspace():
                start_pos += 1
            
            if start_pos >= len(text):
                continue
            
            # 如果找到了左方括号，开始匹配
            if text[start_pos] == '[':
                # 使用栈来匹配括号
                bracket_count = 0
                end_pos = start_pos
                
                for i in range(start_pos, len(text)):
                    if text[i] == '[':
                        bracket_count += 1
                    elif text[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            # 提取完整的列表字符串
                            bill_str = text[start_pos:end_pos]
                            return bill_str.strip()
        
        return None
    
    def _fallback_parse(self, log_line: str) -> Optional[Dict[str, Any]]:
        """
        备用解析方法：当标准JSON解析失败时使用正则表达式提取关键字段
        
        Args:
            log_line: 日志行字符串
            
        Returns:
            解析后的数据字典
        """
        import re
        result = {}
        
        # 提取messageUser (query)
        query_match = re.search(r'"messageUser"\s*:\s*"([^"]*)"', log_line)
        if query_match:
            result['query'] = query_match.group(1)
        
        # 提取reply（需要处理可能包含特殊字符的情况，包括中文引号）
        # 从"reply":"开始，找到匹配的结束引号（考虑转义）
        reply_start = log_line.find('"reply":')
        if reply_start != -1:
            # 找到第一个引号后的开始位置
            value_start = log_line.find('"', reply_start + 8) + 1
            if value_start > 0:
                # 从value_start开始，找到未转义的结束引号（ASCII双引号）
                # 需要区分ASCII双引号(")和中文引号("")
                value_end = value_start
                escaped = False
                while value_end < len(log_line):
                    char = log_line[value_end]
                    if char == '\\':
                        escaped = not escaped
                    elif char == '"' and not escaped:
                        # 找到ASCII双引号，检查后面是否是逗号或大括号
                        # 如果是中文引号(")，则继续
                        next_char_pos = value_end + 1
                        while next_char_pos < len(log_line) and log_line[next_char_pos].isspace():
                            next_char_pos += 1
                        if next_char_pos < len(log_line):
                            next_char = log_line[next_char_pos]
                            if next_char in [',', '}', '\n']:
                                break
                    value_end += 1
                
                if value_end < len(log_line):
                    reply_value = log_line[value_start:value_end]
                    # 处理转义字符
                    reply_value = reply_value.replace('\\"', '"').replace('\\\\', '\\')
                    result['reply'] = reply_value
        
        # 提取账单信息
        bill_match = re.search(r'账单:\s*(\[.*?\])', log_line, re.DOTALL)
        if bill_match:
            result['bill_info'] = bill_match.group(1)
        
        # 提取其他字段
        user_id_match = re.search(r'"userId"\s*:\s*(\d+)', log_line)
        if user_id_match:
            result['user_id'] = int(user_id_match.group(1))
        
        session_match = re.search(r'"sessionId"\s*:\s*"([^"]*)"', log_line)
        if session_match:
            result['session_id'] = session_match.group(1)
        
        intention_match = re.search(r'"userIntention"\s*:\s*"([^"]*)"', log_line)
        if intention_match:
            result['user_intention'] = intention_match.group(1)
        
        # 确保三个核心字段存在（即使为None）
        if 'query' not in result:
            result['query'] = None
        if 'bill_info' not in result:
            result['bill_info'] = None
        if 'reply' not in result:
            result['reply'] = None
        
        # 总是返回结果，即使所有字段都为None
        return result
    
    def _parse_bill_string(self, bill_str: str) -> Optional[List[Dict[str, Any]]]:
        """
        解析账单字符串为Python对象
        尝试将字符串形式的列表转换为实际的列表对象
        
        Args:
            bill_str: 账单信息字符串
            
        Returns:
            解析后的账单列表，如果解析失败返回None
        """
        try:
            # 尝试使用eval解析（注意：需要确保安全性）
            # 由于这是内部使用且数据来源可控，可以使用eval
            # 但为了安全，也可以使用ast.literal_eval
            import ast
            return ast.literal_eval(bill_str)
        except (ValueError, SyntaxError):
            # 如果解析失败，返回原始字符串
            return None
    
    def parse_log_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析整个日志文件
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            解析后的数据列表
        """
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parsed_data = self.parse_log_line(line)
                    # 现在parse_log_line总是返回结果字典（可能字段为None）
                    if parsed_data is not None:
                        parsed_data['line_number'] = line_num
                        results.append(parsed_data)
                    else:
                        # 这不应该发生，但为了安全起见保留
                        print(f"警告: 第{line_num}行解析失败")
        
        except FileNotFoundError:
            print(f"错误: 文件不存在 - {file_path}")
        except Exception as e:
            print(f"读取文件错误: {e}")
        
        return results
    
    def parse_log_file_stream(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        流式解析日志文件（生成器，逐条返回结果，节省内存）
        
        Args:
            file_path: 日志文件路径
            
        Yields:
            解析后的数据字典（包含line_number字段）
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parsed_data = self.parse_log_line(line)
                    if parsed_data is not None:
                        parsed_data['line_number'] = line_num
                        yield parsed_data
                    else:
                        print(f"警告: 第{line_num}行解析失败")
        
        except FileNotFoundError:
            print(f"错误: 文件不存在 - {file_path}")
        except Exception as e:
            print(f"读取文件错误: {e}")
    
    def save_results(self, results: List[Dict[str, Any]], output_path: Path, 
                     format: str = 'json'):
        """
        保存解析结果到文件
        
        Args:
            results: 解析结果列表
            output_path: 输出文件路径
            format: 输出格式 ('json', 'csv', 'txt')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {output_path} ({len(results)} 条记录)")
        
        elif format == 'csv':
            import csv
            if not results:
                print(f"结果已保存到: {output_path} (0 条记录)")
                return
            
            # 获取所有可能的字段
            fieldnames = set()
            for result in results:
                fieldnames.update(result.keys())
            
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                for result in results:
                    # 将None转换为空字符串（保持三个核心字段为空字符串而不是None）
                    row = {}
                    for k, v in result.items():
                        if v is None:
                            row[k] = ''
                        else:
                            row[k] = v
                    writer.writerow(row)
            print(f"结果已保存到: {output_path} ({len(results)} 条记录)")
        
        elif format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for idx, result in enumerate(results, 1):
                    f.write(f"=== 记录 {idx} ===\n")
                    f.write(f"行号: {result.get('line_number', 'N/A')}\n")
                    query = result.get('query')
                    f.write(f"用户输入 (query): {query if query is not None else '(缺失)'}\n")
                    bill_info = result.get('bill_info')
                    f.write(f"账单信息: {bill_info if bill_info is not None else '(缺失)'}\n")
                    reply = result.get('reply')
                    f.write(f"大模型回复 (reply): {reply if reply is not None else '(缺失)'}\n")
                    if result.get('user_id'):
                        f.write(f"用户ID: {result.get('user_id')}\n")
                    f.write("\n")
            print(f"结果已保存到: {output_path} ({len(results)} 条记录)")
    
    def save_results_stream(self, results_stream: Iterator[Dict[str, Any]], 
                           output_path: Path, format: str = 'json'):
        """
        流式保存解析结果到文件（适用于大文件，节省内存）
        
        Args:
            results_stream: 解析结果生成器（Iterator）
            output_path: 输出文件路径
            format: 输出格式 ('json', 'csv', 'txt')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        
        if format == 'json':
            # JSON格式需要先收集所有数据（或使用jsonlines格式）
            # 这里使用数组格式，需要先写入开始标记
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('[\n')
                first = True
                for result in results_stream:
                    if not first:
                        f.write(',\n')
                    json.dump(result, f, ensure_ascii=False, indent=2)
                    first = False
                    count += 1
                f.write('\n]')
            print(f"结果已保存到: {output_path} ({count} 条记录)")
        
        elif format == 'csv':
            import csv
            fieldnames = None
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = None
                for result in results_stream:
                    if fieldnames is None:
                        # 第一行确定字段名
                        fieldnames = sorted(result.keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                    
                    # 将None转换为空字符串
                    row = {}
                    for k, v in result.items():
                        if v is None:
                            row[k] = ''
                        else:
                            row[k] = v
                    writer.writerow(row)
                    count += 1
            print(f"结果已保存到: {output_path} ({count} 条记录)")
        
        elif format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for idx, result in enumerate(results_stream, 1):
                    f.write(f"=== 记录 {idx} ===\n")
                    f.write(f"行号: {result.get('line_number', 'N/A')}\n")
                    query = result.get('query')
                    f.write(f"用户输入 (query): {query if query is not None else '(缺失)'}\n")
                    bill_info = result.get('bill_info')
                    f.write(f"账单信息: {bill_info if bill_info is not None else '(缺失)'}\n")
                    reply = result.get('reply')
                    f.write(f"大模型回复 (reply): {reply if reply is not None else '(缺失)'}\n")
                    if result.get('user_id'):
                        f.write(f"用户ID: {result.get('user_id')}\n")
                    f.write("\n")
                    count += 1
            print(f"结果已保存到: {output_path} ({count} 条记录)")
