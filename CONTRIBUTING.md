# 参与贡献 (Contributing)

感谢您对 Knowra 项目的关注。欢迎通过提 Issue 或是提交 Pull Request 来参与贡献！

## 👨‍💻 开发规范
1. **统一编码风格**：Python 代码建议遵循 PEP-8 标准，并尽量保留清晰的方法注释。
2. **遵守技术栈限制**：本项目固定技术栈为 PyQt6, peewee, chromadb, loguru, requests/httpx 等。请勿引入与当前功能重复的庞杂第三方库。
3. **不上传凭据或隐私文件**：请确保您的 `git commit` 不会携带 `.env` 等包含 API Key 或是用户文档的内容。

## 🐛 提交 Issue
如果您在使用当中遇到 Bug 或有新功能设想，请提供：
- 您的系统环境 (Windows/Mac/Linux) 以及 Python 版本。
- 复现 Bug 的详细步骤及对应的日志 (位于 `%APPDATA%/Knowra/logs/app.log`)。

## 💡 提交 Pull Request
1. Fork 本仓库并切换到新分支（如 `feature/your-feature-name`）。
2. 在您的本地分支中进行撰写代码并完成测试。
3. 本项目要求至少在提交前确保核心类在解耦状况下通过测试（参见 `tests/` 目录），不要破坏原有的 GUI 主线程。
4. 推送变更并创建一个 Pull Request。
