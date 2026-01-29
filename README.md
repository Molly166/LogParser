# 日志解析器 MVP

从日志文件中提取关键信息的Python工具，主要用于提取用户输入(query)、账单信息、大模型回复(reply)等字段。

## 功能特性

- ✅ 提取三个核心字段：
  - `query`: 用户输入（从 `messageUser` 字段提取）
  - `bill_info`: 账单信息（从 `analysisResult` 或 `promptParam` 中的 `message_interpretation`/`reference` 提取）
  - `reply`: 大模型回复（从 `reply` 字段提取）
- ✅ **智能缺失处理**：即使三个核心字段部分或全部缺失，也会输出已有部分，缺失字段显示为 `null`
- ✅ **自动命名**：默认输出文件名为 `日志文件名_result.json`，方便区分
- ✅ **流式处理支持**：支持大文件的流式处理，节省内存（新增功能）
- ✅ 支持多种输出格式：JSON、CSV、TXT
- ✅ 灵活的解析机制：标准JSON解析失败时自动使用正则表达式备用方案
- ✅ 处理特殊字符：正确处理中文引号和转义字符
- ✅ 可扩展设计：代码结构清晰，模块化设计，易于添加新字段

## 项目结构

```
GETLOG/
├── src/
│   ├── log_parser.py       # 核心解析器类
│   ├── field_extractor.py  # 字段提取模块（独立模块）
│   └── main.py             # 主程序入口
├── tests/
│   ├── test_log.txt        # 示例日志文件
│   ├── test_parser.py      # 测试脚本
│   └── test_stream.py      # 流式处理测试
├── logs/                   # 日志文件目录（用户放置日志文件）
├── output/                 # 输出文件目录
├── DESIGN.md               # 设计文档
├── 项目合理性分析.md       # 项目分析报告
├── USAGE.md                # 详细使用指南
└── README.md
```

## 安装要求

- Python 3.7+
- 无需额外依赖包（仅使用Python标准库）

## 使用方法

### 命令行使用

#### 批量处理模式（推荐）

```bash
# 批量处理logs文件夹下的所有日志文件
python src/main.py

# 批量处理并指定输出格式（CSV格式）
python src/main.py -f csv

# 批量处理并显示解析结果预览
python src/main.py --show

# 批量处理大文件（使用流式处理，节省内存）
python src/main.py --stream

# 指定日志目录和输出目录
python src/main.py --logs-dir logs --output-dir output
```

#### 单文件处理模式

```bash
# 解析单个日志文件并输出JSON格式
# 输出文件名自动为：日志文件名_result.json
python src/main.py logs/your_log_file.log

# 指定输出文件
python src/main.py logs/your_log_file.log -o output/result.json

# 指定输出格式（json/csv/txt）
python src/main.py logs/your_log_file.log -f csv -o output/result.csv

# 在控制台显示解析结果
python src/main.py logs/your_log_file.log --show

# 使用流式处理（大文件）
python src/main.py logs/large_file.log --stream
```

### 可视化界面（GUI）

使用 Python 自带的 Tkinter，无需额外依赖：

```bash
python src/gui.py
```

GUI 支持：
- 单文件/批量目录处理
- 选择输出目录与输出格式（json/csv/txt）
- 可选流式处理（大文件）
- 界面内查看运行日志与前3条结果预览

**注意**：
- 如果不指定 `input_file` 参数，程序会自动批量处理 `logs/` 文件夹下的所有日志文件
- 批量处理时，每个日志文件会在 `output/` 目录下生成对应的结果文件
- 支持的文件格式：`.log`, `.txt`, `.json`

### Python代码中使用

#### 基本用法（内存模式）

```python
from pathlib import Path
from src.log_parser import LogParser

# 创建解析器
parser = LogParser()

# 解析单行日志
log_line = "...你的日志行..."
result = parser.parse_log_line(log_line)
print(f"用户输入: {result['query']}")
print(f"账单信息: {result['bill_info']}")
print(f"大模型回复: {result['reply']}")

# 解析整个文件（加载所有结果到内存）
results = parser.parse_log_file(Path("logs/your_log_file.log"))

# 保存结果
parser.save_results(results, Path("output/result.json"), format='json')
```

#### 流式处理（大文件，节省内存）

```python
from pathlib import Path
from src.log_parser import LogParser

# 创建解析器
parser = LogParser()

# 流式解析文件（生成器，逐条返回，节省内存）
results_stream = parser.parse_log_file_stream(Path("logs/large_file.log"))

# 流式保存结果
parser.save_results_stream(results_stream, Path("output/result.csv"), format='csv')

# 或者逐条处理
for result in results_stream:
    # 处理每条记录
    print(f"Query: {result.get('query')}")
    # ... 其他处理逻辑
```

## 日志格式说明

解析器支持的日志格式：

```
时间 [任务] 级别 类 - [方法,行号] - {JSON数据}
```

其中JSON数据包含以下关键字段：
- `messageUser`: 用户输入
- `analysisResult`: 分析结果（包含 `message_interpretation` 字段，其中有账单信息）
- `promptParam`: 提示参数（包含 `reference` 字段，其中可能有账单信息）
- `reply`: 大模型回复

账单信息的提取逻辑：
1. 优先从 `analysisResult.message_interpretation` 中提取"账单:[...]"部分
2. 如果未找到，从 `promptParam.reference` 中提取
3. 支持多个账单的情况，会提取最后一个完整的账单列表

## 输出格式

### JSON格式
```json
[
  {
    "query": "垃圾袋0.99",
    "bill_info": "[{'类别': '支出', '一级类目': '购物', '二级类目': '日用品', ...}]",
    "reply": "嘿呀，小橙！买垃圾袋的这笔0.99元支出账单...",
    "user_id": 1638,
    "session_id": "1328ea00b5604d671c07c411a7",
    "user_intention": "新增账单",
    "success_flag": 1,
    "line_number": 1
  },
  {
    "query": "测试输入",
    "bill_info": null,
    "reply": null,
    "user_id": 1639,
    "session_id": null,
    "user_intention": null,
    "success_flag": null,
    "line_number": 2
  }
]
```

**注意**：如果三个核心字段（`query`、`bill_info`、`reply`）缺失，会显示为 `null`，但记录仍会被保存。

### CSV格式
所有字段作为列输出，便于Excel等工具打开。缺失字段显示为空字符串。

### TXT格式
人类可读的文本格式，每条记录单独显示。缺失字段显示为 `(缺失)`。

## 内存使用策略

### 内存模式（默认）
- 适用于中小型文件（< 100MB）
- 所有结果加载到内存，便于后续处理
- 使用 `parse_log_file()` 和 `save_results()`

### 流式处理模式（大文件）
- 适用于大型文件（> 100MB）
- 逐条处理，内存占用恒定
- 使用 `parse_log_file_stream()` 和 `save_results_stream()`

**选择建议：**
- 文件较小或需要完整结果列表：使用内存模式
- 文件较大或内存有限：使用流式处理模式

## 测试

运行测试脚本：

```bash
# 基本功能测试
python tests/test_parser.py

# 流式处理测试
python tests/test_stream.py
```

## 代码架构

### 模块化设计

项目采用模块化设计，主要模块：

1. **log_parser.py** - 核心解析器类
   - `LogParser`: 日志解析器主类
   - 提供解析、保存等核心功能
   - 支持内存模式和流式处理模式

2. **field_extractor.py** - 字段提取模块
   - `extract_fields_from_log_data()`: 从解析后的数据中提取字段
   - `create_empty_result()`: 创建空结果结构
   - 统一的字段提取逻辑，便于维护和扩展

3. **main.py** - 命令行接口
   - 处理命令行参数
   - 调用解析器并保存结果

### 扩展字段

如需提取其他字段，有两种方式：

#### 方式1：修改 field_extractor.py（推荐）

```python
# 在 extract_fields_from_log_data 函数中添加
def extract_fields_from_log_data(log_data: Dict[str, Any], extract_bill_info_func) -> Dict[str, Any]:
    result = {}
    # ... 现有字段 ...
    
    # 添加新字段
    result['new_field'] = log_data.get('newField') or None
    return result
```

#### 方式2：直接在 log_parser.py 中修改

在 `parse_log_line` 方法或 `_fallback_parse` 方法中添加新字段提取逻辑。

## 注意事项

1. 日志文件必须是UTF-8编码
2. 如果JSON解析失败，解析器会自动使用正则表达式备用方案
3. 账单信息提取会优先提取最后一个完整的账单列表（如果有多个）
4. **缺失字段处理**：即使三个核心字段部分或全部缺失，解析器仍会输出该记录，缺失字段显示为 `null`
5. **输出文件命名**：默认输出文件名为 `日志文件名_result.json`（例如：`test.log` → `test_result.json`）
6. **内存使用**：大文件建议使用流式处理模式，避免内存溢出
7. 代码设计灵活，不写死，便于后续扩展

## 性能优化

### 已实现的优化

1. **模块化设计**：字段提取逻辑独立为模块，代码复用性高
2. **流式处理**：支持大文件的流式处理，内存占用恒定
3. **双重解析策略**：标准JSON解析优先，失败时使用正则表达式备用方案

### 性能建议

- **小文件（< 10MB）**：使用默认的内存模式
- **中等文件（10-100MB）**：根据内存情况选择模式
- **大文件（> 100MB）**：建议使用流式处理模式

## 更新日志

### v1.1.0 (最新)
- ✅ 重构字段提取逻辑，提取为独立模块 `field_extractor.py`
- ✅ 添加流式处理支持，优化大文件内存使用
- ✅ 代码结构优化，消除代码重复
- ✅ 向后兼容，原有接口保持不变

### v1.0.0
- ✅ 初始版本发布
- ✅ 核心功能实现（query、bill_info、reply字段提取）
- ✅ 支持JSON/CSV/TXT三种输出格式
- ✅ 缺失字段容错处理

## 相关文档

- [设计文档](DESIGN.md) - 详细的设计思路和架构说明
- [使用指南](USAGE.md) - 详细的使用说明和示例
- [批量处理说明](BATCH_PROCESSING.md) - 批量处理功能详细说明

## 许可证

MIT License
