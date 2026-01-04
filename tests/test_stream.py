"""
测试流式处理功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from log_parser import LogParser


def test_stream_processing():
    """测试流式处理"""
    parser = LogParser()
    test_file = Path(__file__).parent / 'test_log.txt'
    
    print("测试流式处理...")
    results_stream = parser.parse_log_file_stream(test_file)
    
    count = 0
    for result in results_stream:
        count += 1
        print(f"记录 {count}: query={result.get('query')}, bill_info存在={result.get('bill_info') is not None}")
        if count >= 2:  # 只测试前2条
            break
    
    print(f"\n流式处理测试完成，处理了 {count} 条记录")


def test_stream_save():
    """测试流式保存"""
    parser = LogParser()
    test_file = Path(__file__).parent / 'test_log.txt'
    output_file = Path(__file__).parent.parent / 'output' / 'test_stream_output.csv'
    
    print("\n测试流式保存...")
    results_stream = parser.parse_log_file_stream(test_file)
    parser.save_results_stream(results_stream, output_file, format='csv')
    
    print("流式保存测试完成")


if __name__ == '__main__':
    test_stream_processing()
    test_stream_save()

