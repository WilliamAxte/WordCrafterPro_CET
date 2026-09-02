# WordCrafter Pro 2.0

WordCrafter Pro 是一款面向英语学习者的 Windows 双语阅读与词汇工作台。它把 AI 情境生成、双语精读、间隔复习和本地生词管理放在同一个清爽的 Qt6 桌面应用中。

## 主要功能

- 情境词汇：将目标词汇编织成连贯的英文短文，并提供中文对照。
- ACG 英语：围绕动画、游戏、音乐等兴趣主题生成英语阅读素材。
- 双语精读：支持双语、纯英文、纯中文和沉浸式全屏阅读。
- 间隔复习：内置 SRS 复习流程，支持新词、到期复习、每日上限和学习日志。
- 多源词典：在线词典与本地导入词库结合，支持 TXT 和 JSON 词书。
- 发音与翻译：支持 Microsoft 服务配置和本地缓存；没有网络时仍可使用离线词库。
- 本地 Web UI：可选开启局域网 Web 界面，使用令牌保护访问。
- 主题与阅读体验：深浅色主题、强调色、字号调整、报纸式多栏阅读和背景效果。

## 下载使用

在 Releases 页面下载 WordCrafterPro_v2.0_Windows_x64.zip，解压后运行其中的 WordCrafterPro.exe。
这是 Windows x64 免安装便携版。首次使用时，在设置中填入兼容 OpenAI Chat Completions API 的地址、模型和 API Key。
词典查询与本地复习不要求配置 AI Key。系统要求：Windows 10 或 Windows 11 64 位。

## 从源码运行

项目依赖 PySide6，入口文件为 main.py，测试位于 tests 目录。详细构建配置见 build.spec。

## 许可证

本项目采用 MIT License。
