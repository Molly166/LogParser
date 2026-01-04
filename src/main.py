"""
主程序入口 - 日志解析器MVP
支持单文件处理和批量处理
"""
import argparse
import sys
import io
from pathlib import Path
from log_parser import LogParser

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def process_single_file(log_parser: LogParser, input_path: Path, output_path: Path, 
                       format: str, show: bool, use_stream: bool = False):
    """
    处理单个日志文件
    
    Args:
        log_parser: 日志解析器实例
        input_path: 输入文件路径
        output_path: 输出文件路径
        format: 输出格式
        show: 是否显示预览
        use_stream: 是否使用流式处理
    """
    try:
        print(f"正在解析: {input_path.name}")
        
        if use_stream:
            # 使用流式处理
            results_stream = log_parser.parse_log_file_stream(input_path)
            log_parser.save_results_stream(results_stream, output_path, format=format)
            # 流式处理无法显示预览（因为生成器只能消费一次）
            if show:
                print("  注意: 流式处理模式无法显示预览")
        else:
            # 使用内存模式
            results = log_parser.parse_log_file(input_path)
            
            if not results:
                print(f"  警告: {input_path.name} 没有解析到任何数据")
                return
            
            print(f"  [OK] 成功解析 {len(results)} 条记录")
            
            # 显示结果预览
            if show:
                print(f"\n  === {input_path.name} 解析结果预览 ===")
                for idx, result in enumerate(results[:3], 1):  # 每个文件只显示前3条
                    print(f"\n  记录 {idx}:")
                    print(f"    用户输入 (query): {result.get('query', '') or '(缺失)'}")
                    bill_info = result.get('bill_info')
                    if bill_info:
                        bill_preview = bill_info[:50] + '...' if len(bill_info) > 50 else bill_info
                        print(f"    账单信息: {bill_preview}")
                    else:
                        print(f"    账单信息: (缺失)")
                    reply = result.get('reply')
                    if reply:
                        reply_preview = reply[:50] + '...' if len(reply) > 50 else reply
                        print(f"    大模型回复: {reply_preview}")
                    else:
                        print(f"    大模型回复: (缺失)")
                if len(results) > 3:
                    print(f"\n    ... 还有 {len(results) - 3} 条记录")
            
            # 保存结果
            log_parser.save_results(results, output_path, format=format)
        
    except Exception as e:
        print(f"  [FAIL] 处理失败: {e}")


def find_log_files(directory: Path, pattern: str = "*.log") -> list:
    """
    查找目录下的所有日志文件
    
    Args:
        directory: 目录路径
        pattern: 文件匹配模式
        
    Returns:
        日志文件列表
    """
    log_files = []
    
    # 支持的日志文件扩展名
    extensions = ['*.log', '*.txt', '*.json']
    
    for ext in extensions:
        log_files.extend(directory.glob(ext))
    
    # 去重并排序
    log_files = sorted(set(log_files))
    
    return log_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='日志解析器 - 提取query、账单信息、reply等关键字段（支持批量处理）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 处理单个文件
  python src/main.py logs/app.log
  
  # 批量处理logs文件夹下的所有日志文件
  python src/main.py
  
  # 批量处理并指定输出格式
  python src/main.py -f csv
  
  # 批量处理并显示预览
  python src/main.py --show
        """
    )
    
    parser.add_argument(
        'input_file',
        type=str,
        nargs='?',  # 可选参数
        default=None,
        help='输入的日志文件路径（如果省略，则批量处理logs文件夹下的所有日志文件）'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出文件路径（仅单文件模式有效，批量模式下自动命名）'
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
        help='在控制台显示解析结果预览'
    )
    
    parser.add_argument(
        '--stream',
        action='store_true',
        help='使用流式处理模式（适用于大文件，节省内存）'
    )
    
    parser.add_argument(
        '--logs-dir',
        type=str,
        default='logs',
        help='日志文件目录（默认: logs）'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='输出文件目录（默认: output）'
    )
    
    args = parser.parse_args()
    
    # 创建解析器
    log_parser = LogParser()
    
    # 确定工作目录（脚本所在目录的父目录）
    script_dir = Path(__file__).parent.parent
    logs_dir = script_dir / args.logs_dir
    output_dir = script_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 判断是单文件模式还是批量模式
    if args.input_file:
        # 单文件模式
        input_path = Path(args.input_file)
        
        # 如果是相对路径，尝试从工作目录和logs目录查找
        if not input_path.is_absolute():
            if not input_path.exists():
                # 尝试在logs目录中查找
                potential_path = logs_dir / input_path.name
                if potential_path.exists():
                    input_path = potential_path
                else:
                    # 尝试从当前工作目录
                    potential_path = Path.cwd() / input_path
                    if potential_path.exists():
                        input_path = potential_path
        
        if not input_path.exists():
            print(f"错误: 文件不存在 - {input_path}")
            sys.exit(1)
        
        # 确定输出路径
        if args.output:
            output_path = Path(args.output)
        else:
            # 默认输出到output目录
            output_path = output_dir / f"{input_path.stem}_result.{args.format}"
        
        print("=" * 60)
        print("单文件处理模式")
        print("=" * 60)
        process_single_file(log_parser, input_path, output_path, args.format, args.show, args.stream)
        
    else:
        # 批量处理模式
        if not logs_dir.exists():
            print(f"错误: 日志目录不存在 - {logs_dir}")
            print(f"提示: 请创建 {logs_dir} 目录并放入日志文件")
            sys.exit(1)
        
        # 查找所有日志文件
        log_files = find_log_files(logs_dir)
        
        if not log_files:
            print(f"提示: 在 {logs_dir} 目录下未找到日志文件")
            print(f"支持的格式: .log, .txt, .json")
            sys.exit(0)
        
        print("=" * 60)
        print(f"批量处理模式 - 找到 {len(log_files)} 个日志文件")
        print("=" * 60)
        print()
        
        # 统计信息
        total_files = len(log_files)
        success_count = 0
        fail_count = 0
        total_records = 0
        
        # 处理每个文件
        for idx, log_file in enumerate(log_files, 1):
            print(f"[{idx}/{total_files}] {log_file.name}")
            
            # 生成输出文件名
            output_file = output_dir / f"{log_file.stem}_result.{args.format}"
            
            try:
                if args.stream:
                    # 流式处理
                    results_stream = log_parser.parse_log_file_stream(log_file)
                    log_parser.save_results_stream(results_stream, output_file, format=args.format)
                    success_count += 1
                    # 流式处理无法统计记录数
                    print(f"  [OK] 处理完成: {output_file.name}")
                else:
                    # 内存模式
                    results = log_parser.parse_log_file(log_file)
                    
                    if results:
                        log_parser.save_results(results, output_file, format=args.format)
                        success_count += 1
                        total_records += len(results)
                        
                        # 显示预览（只对第一个文件显示详细预览）
                        if args.show and idx == 1:
                            print(f"\n  === 解析结果预览（{log_file.name}） ===")
                            for result_idx, result in enumerate(results[:2], 1):
                                print(f"\n  记录 {result_idx}:")
                                print(f"    用户输入: {result.get('query') or '(缺失)'}")
                                print(f"    账单信息: {'存在' if result.get('bill_info') else '(缺失)'}")
                                print(f"    大模型回复: {result.get('reply')[:50] + '...' if result.get('reply') else '(缺失)'}")
                            if len(results) > 2:
                                print(f"\n    ... 还有 {len(results) - 2} 条记录")
                    else:
                        print(f"  [WARN] 警告: 没有解析到任何数据")
                        fail_count += 1
                        
            except Exception as e:
                print(f"  [FAIL] 处理失败: {e}")
                fail_count += 1
            
            print()  # 空行分隔
        
        # 显示汇总信息
        print("=" * 60)
        print("批量处理完成")
        print("=" * 60)
        print(f"总文件数: {total_files}")
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        if not args.stream:
            print(f"总记录数: {total_records}")
        print(f"输出目录: {output_dir}")
        print()


if __name__ == '__main__':
    main()
