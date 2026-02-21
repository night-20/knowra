# Knowra

Knowra 是一个基于本地大模型（LLM）的私人知识库和检索增强生成（RAG）桌面应用程序。本项目使用 Python 3.11+ 开发，搭配 PyQt6 构建深色主题的现代化界面，在本地处理文档切分、向量存储与检索，保证数据的绝对隐私安全。

## 🌟 核心特性
1. **纯本地离线执行**：使用 `ChromaDB` 和本地 SQLite FTS5，以及 `sentence-transformers` 进行中文语义向量化，无隐私数据出域。
2. **多源文档摄入**：支持拖拽导入 `.txt`, `.md`, `.pdf` (基于 PyMuPDF) 文件并自动建立切片 and 向量索引。
3. **混合检索 (RRF)**：结合 `ChromaDB` 的向量搜索与 `SQLite` 的纯文本匹配，大幅提升寻找出处的准确度。
4. **LLM 问答**：无缝对接本地模型的 OpenAI 兼容 REST API (`Ollama`) 或公网大模型，流式回答，并在回答后附带资料来源引用。

## 🚀 快速启动

### 1. 环境准备
推荐使用 Python 3.11+ ，可以通过虚拟环境或 Conda 安装依赖：
```bash
pip install -r requirements.txt
```

### 2. 初始化与配置
首次运行将自动在用户家目录 `%APPDATA%/Knowra` 创建所需的数据集和配置文件。
你可以提前检查环境：
```bash
python test_phase1.py
```

### 3. 运行主程序
*目前主程序正在开发迭代中。*
```bash
python src/main.py
```

## 🏗️ 架构阶段 (Implementation Phases)
项目正在分阶段推进开发：
- [x] **Phase 1**: 系统基础配置、日志模块 (loguru) 及安全凭据模块 (Keyring)。
- [ ] **Phase 2**: 数据底座建设，包含 Peewee ORM、SQLite FTS5 与 ChromaDB 连接引擎。
- [ ] **Phase 3**: RAG 组件装配与切分代理模块。
- [ ] **Phase 4**: 基于 PyQt6 的 GUI 展示栈。
- [ ] **Phase 5**: 完整联调与系统交付。

## 📄 许可协议
本项目采用 [MIT License](LICENSE) 许可协议。
