# .gitignore 文件说明

本项目的 `.gitignore` 文件已配置，用于防止敏感和临时文件被提交到 Git 仓库。

## 主要忽略内容

### 1. Python 相关
- `__pycache__/` - Python 字节码缓存
- `*.pyc`, `*.pyo` - 编译后的 Python 文件
- `venv/`, `.venv/` - 虚拟环境目录
- `.env` - 环境变量文件（可能包含密钥）

### 2. 日志和数据文件（**重要**）
- `logs/` - 日志文件目录（可能包含用户数据）
- `*.log` - 所有日志文件
- `output/` - 输出文件目录（解析结果，包含用户数据）
- `*.result.json`, `*.result.csv` - 解析结果文件

### 3. 配置文件
- `config/` - 配置目录（可能包含密钥）
- `*.conf`, `*.config`, `*.ini` - 配置文件

### 4. 敏感信息文件
- `*.secret`, `*.key` - 密钥文件
- `*.pem`, `*.p12` - 证书文件
- `*.credentials` - 凭证文件

### 5. IDE 和编辑器文件
- `.idea/` - PyCharm 配置
- `.vscode/` - VS Code 配置
- `*.sublime-*` - Sublime Text 配置

### 6. 系统文件
- `.DS_Store` - macOS 系统文件
- `Thumbs.db` - Windows 缩略图
- `Desktop.ini` - Windows 系统文件

## 注意事项

### ⚠️ 重要提醒

1. **日志文件**：`logs/` 目录和所有 `*.log` 文件都会被忽略，因为这些文件可能包含：
   - 用户输入的敏感信息
   - 用户ID、会话ID等隐私数据
   - 业务逻辑相关的敏感信息

2. **输出文件**：`output/` 目录和所有 `*.result.*` 文件都会被忽略，因为：
   - 这些是解析后的用户数据
   - 包含用户的查询、账单信息等隐私数据

3. **配置文件**：如果配置文件包含密钥或敏感信息，应：
   - 将配置文件添加到 `.gitignore`
   - 提供示例配置文件（如 `config.example.yml`）
   - 在 README 中说明如何配置

4. **测试文件**：测试结果文件（`tests/*_result.*`）也会被忽略

### 如果需要在仓库中包含示例文件

如果需要将某些文件作为示例保留在仓库中，可以：

1. **使用示例文件命名**：
   - `logs/example.log` （不会被忽略，因为不是 `*.log` 或 `logs/` 目录）
   - `output/example_result.json`

2. **使用 `!` 强制包含**：
   ```gitignore
   # 忽略所有输出文件
   output/*
   # 但包含示例文件
   !output/example_result.json
   ```

3. **创建示例目录**：
   - `examples/` - 存放示例文件，不受 `.gitignore` 影响

## 检查忽略的文件

使用以下命令检查哪些文件被忽略：

```bash
# 查看所有被忽略的文件
git status --ignored

# 检查特定文件是否被忽略
git check-ignore -v logs/app.log
```

## 如果文件已经被跟踪

如果某些文件在添加 `.gitignore` 之前已经被 Git 跟踪，需要先从 Git 中移除（但保留本地文件）：

```bash
# 移除文件但保留本地副本
git rm --cached logs/app.log
git rm --cached output/result.json

# 移除整个目录
git rm -r --cached logs/
git rm -r --cached output/

# 提交更改
git commit -m "Remove tracked files that should be ignored"
```

## 自定义忽略规则

如果需要添加项目特定的忽略规则，可以在 `.gitignore` 文件末尾添加：

```gitignore
# 项目特定规则
my_custom_directory/
*.custom_extension
```

## 最佳实践

1. ✅ **尽早配置**：项目开始时就应该配置 `.gitignore`
2. ✅ **定期检查**：提交前检查 `git status`，确保没有敏感文件
3. ✅ **使用示例文件**：提供示例配置文件，而不是真实的配置文件
4. ✅ **文档说明**：在 README 中说明哪些文件被忽略及其原因
5. ✅ **团队共享**：确保团队成员都使用相同的 `.gitignore` 规则

