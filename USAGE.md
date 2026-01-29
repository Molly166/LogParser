# 使用指南

## 快速开始

### 1. 基本用法（最常用）

```bash
# 解析日志文件，自动生成 日志名_result.json
python src/main.py 日志文件路径

# 示例
python src/main.py logs/app.log
# 会生成: logs/app_result.json
```

### 2. 指定输出文件

```bash
# 自定义输出文件路径和名称
python src/main.py logs/app.log -o output/my_result.json
```

### 3. 指定输出格式

```bash
# 输出为JSON格式（默认）
python src/main.py logs/app.log -f json

# 输出为CSV格式（Excel可打开）
python src/main.py logs/app.log -f csv -o output/result.csv

# 输出为TXT格式（人类可读）
python src/main.py logs/app.log -f txt -o output/result.txt
```

### 4. 预览解析结果

```bash
# 在控制台显示前5条解析结果
python src/main.py logs/app.log --show
```

### 5. 可视化界面（GUI）

项目提供一个基于 Tkinter 的可视化界面（无需额外依赖）：

```bash
python src/gui.py
```

在界面中可以：
- 选择单个日志文件，或选择一个目录进行批量处理
- 选择输出目录、输出格式（json/csv/txt）
- 勾选“流式处理”以适配大文件
- 查看运行日志与前3条解析结果预览

## 完整命令示例

### 示例1：解析日志文件并查看结果

```bash
# 解析日志
python src/main.py logs/2024-01-01.log

# 查看生成的结果文件
python src/main.py logs/2024-01-01.log --show
```

### 示例2：解析并输出到指定目录

```bash
# 解析并保存到output目录
python src/main.py logs/app.log -o output/app_result.json
```

### 示例3：批量处理多个日志文件

```bash
# Windows PowerShell
python src/main.py logs\log1.log
python src/main.py logs\log2.log
python src/main.py logs\log3.log

# Linux/Mac
python src/main.py logs/log1.log
python src/main.py logs/log2.log
python src/main.py logs/log3.log
```

## 输出文件说明

### 默认输出位置
- 输出文件保存在**日志文件同一目录**
- 文件名格式：`原日志文件名_result.json`
- 例如：`app.log` → `app_result.json`

### 输出内容
- 每条日志记录会被解析并提取：
  - `query`: 用户输入
  - `bill_info`: 账单信息
  - `reply`: 大模型回复
  - 其他字段：`user_id`, `session_id`, `user_intention` 等
- 如果字段缺失，会显示为 `null`

## 实际使用场景

### 场景1：解析单个日志文件

```bash
# 假设你的日志文件在 D:\logs\application.log
python src/main.py D:\logs\application.log

# 结果会保存在 D:\logs\application_result.json
```

### 场景2：解析并导出为Excel

```bash
# 导出为CSV格式，可用Excel打开
python src/main.py logs/app.log -f csv -o output/result.csv
```

### 场景3：快速查看解析结果

```bash
# 解析并立即在控制台查看前5条结果
python src/main.py logs/app.log --show
```

## 命令行参数说明

```
python src/main.py <输入文件> [选项]

必需参数:
  输入文件           日志文件路径

可选参数:
  -o, --output      指定输出文件路径
  -f, --format      输出格式 (json/csv/txt)，默认: json
  --show           在控制台显示解析结果
  -h, --help        显示帮助信息
```

## 常见问题

### Q: 如何解析当前目录下的日志文件？
```bash
# 直接指定文件名
python src/main.py my_log.log
```

### Q: 如何解析不同目录的日志文件？
```bash
# 使用绝对路径或相对路径
python src/main.py C:\Users\Desktop\logs\app.log
python src/main.py ../logs/app.log
```

### Q: 输出文件会覆盖之前的吗？
```bash
# 是的，如果文件名相同会覆盖
# 建议每次使用不同的输出文件名
python src/main.py logs/app.log -o output/app_2024-01-01.json
```

## 在Python代码中使用

```python
from pathlib import Path
from src.log_parser import LogParser

# 创建解析器
parser = LogParser()

# 解析文件
results = parser.parse_log_file(Path("logs/app.log"))

# 保存结果
parser.save_results(results, Path("output/result.json"), format='json')
```

