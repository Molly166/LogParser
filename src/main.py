"""
主程序入口 - 日志解析器MVP
"""
import argparse
from pathlib import Path
from log_parser import LogParser


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='日志解析器 - 提取query、账单信息、reply等关键字段'
    )
    
    parser.add_argument(
        'input_file',
        type=str,
        help='输入的日志文件路径'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出文件路径（默认为输入文件名_extracted.json）'
    )
    
    parser.add_argument(
        '-f', '--format',
        type=str,
        choices=['json', 'csv', 'txt'],
        default='json',
        help='输出格式 (json/csv/txt，默认: json)'
    )
    
    parser.add_argument(
        '--show',
        action='store_true',
        help='在控制台显示解析结果'
    )
    
    args = parser.parse_args()
    
    # 创建解析器
    log_parser = LogParser()
    
    # 解析日志文件
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"错误: 文件不存在 - {input_path}")
        return
    
    print(f"正在解析日志文件: {input_path}")
    results = log_parser.parse_log_file(input_path)
    
    if not results:
        print("警告: 没有解析到任何数据")
        return
    
    print(f"成功解析 {len(results)} 条记录")
    
    # 显示结果
    if args.show:
        print("\n=== 解析结果预览 ===")
        for idx, result in enumerate(results[:5], 1):  # 只显示前5条
            print(f"\n记录 {idx}:")
            print(f"  用户输入 (query): {result.get('query', '')}")
            print(f"  账单信息: {result.get('bill_info', 'N/A')}")
            print(f"  大模型回复 (reply): {result.get('reply', '')}")
        if len(results) > 5:
            print(f"\n... 还有 {len(results) - 5} 条记录")
    
    # 保存结果
    if args.output:
        output_path = Path(args.output)
    else:
        # 默认输出路径：日志文件名 + _result.扩展名
        output_path = input_path.parent / f"{input_path.stem}_result.{args.format}"
    
    log_parser.save_results(results, output_path, format=args.format)


if __name__ == '__main__':
    main()
