<div align="center">
  <img src="SourceCode/assets/app_icon.png" width="112" alt="WordCrafter Pro icon">
  <h1>WordCrafter Pro 2.0</h1>
  <p><strong>把阅读、生成、词典与记忆曲线，编译进同一台 Windows 学习终端。</strong></p>
  <p>
    <a href="https://github.com/WilliamAxte/WordCrafterPro_CET/releases/tag/v2.0"><img src="https://img.shields.io/github/v/release/WilliamAxte/WordCrafterPro_CET?style=flat-square&label=release" alt="release"></a>
    <a href="https://github.com/WilliamAxte/WordCrafterPro_CET/releases/tag/v2.0"><img src="https://img.shields.io/badge/platform-Windows%20x64-2563EB?style=flat-square" alt="Windows x64"></a>
    <img src="https://img.shields.io/badge/UI-PySide6%20%7C%20Qt6-41CD52?style=flat-square" alt="PySide6 Qt6">
    <img src="https://img.shields.io/badge/tests-34%20passed-16A34A?style=flat-square" alt="34 tests passed">
    <img src="https://img.shields.io/badge/license-MIT-64748B?style=flat-square" alt="MIT License">
  </p>
  <p>
    <a href="https://github.com/WilliamAxte/WordCrafterPro_CET/releases/download/v2.0/WordCrafterPro_v2.0_Setup.exe">⬇️ 下载安装版</a>
    ·
    <a href="https://github.com/WilliamAxte/WordCrafterPro_CET/releases/tag/v2.0">查看 Release 2.0</a>
  </p>
</div>

---

## 这不是一个“单词本”，而是一套本地优先的语言学习引擎

WordCrafter Pro 面向真正需要长期积累的人：把 AI 生成的上下文、双语精读、词典解析、发音辅助和间隔重复学习串成一条完整闭环。

**输入兴趣与目标词 → 生成可读内容 → 阅读中沉淀词汇 → SRS 安排复习 → 数据本地持久化 → Web 端继续学习。**

它是一款原生 Windows 桌面应用，也是一套可以从源码审阅、测试、打包和扩展的工程化产品。

<img width="991" height="680" alt="image" src="https://github.com/user-attachments/assets/db319e56-e797-49cf-9e0b-ec902eafab6e" />



## 技术力一览

| 层 | 实现 | 解决的问题 |
|---|---|---|
| Desktop Shell | PySide6 / Qt6、无控制台窗口、原生 x64 打包 | 流畅、稳定、可安装的 Windows 桌面体验 |
| UI Architecture | 页面化导航、共享 `QtConfig` 上下文、QSS token 主题系统 | 让阅读、词典、复习、设置和历史保持一致 |
| AI Pipeline | OpenAI Chat Completions 兼容接口 + SSE 流式响应 | 生成内容逐 token 到达，英文/中文实时分流渲染 |
| Learning Core | SM-2 类间隔重复调度器 | 新词、学习中、复习、重学、掌握状态可追踪 |
| Dictionary Layer | 在线查询 + 本地 JSON/TXT 词库 + 缓存 | 网络可用时增强，离线时仍可工作 |
| Persistence | 轻量 JSON 仓储、会话历史、学习日志、词库/计划 | 数据可读、可备份、无需数据库服务 |
| Local Web | Python 标准库 `http.server` + Token 鉴权 | 局域网设备共享同一份学习状态 |
| Delivery | PyInstaller portable + Inno Setup installer | 一键安装或解压即用 |

## 核心能力

### AI 情境生成，不是机械例句

- 根据目标词、难度、篇幅生成连贯英文故事或 ACG 主题特稿。
- 支持 OpenAI 兼容 API，可配置地址、模型和 Key，适配不同服务商。
- SSE 流式输出，英文与中文通过标记路由器实时进入对应阅读面板。
- 对输入和输出进行清晰分层，AI 服务不会侵入 UI 和学习核心。

### 一套阅读引擎，四种沉浸模式

- 中英对照、纯英文、纯中文、沉浸式全屏。
- 报纸式多栏排版、字号/字体/行距控制、深浅主题和强调色。
- 阅读内容以会话形式保存，可回看、导出 TXT/Markdown。
- 支持词典查词和将词汇加入本地生词库。

### 可解释的 SRS，而不是黑盒提醒

学习卡片持久化保存 `state`、`repetitions`、`interval_days`、`stability`、`difficulty`、`lapse_count` 等字段。

反馈从「忘记 / 困难 / 认识 / 简单」映射为可追踪的调度变化，覆盖：

- NEW → LEARNING → REVIEW → MASTERED
- 失败后的 RELEARNING 回退
- 每日新词上限、到期优先、复习日志与学习计划

### 多源词典与离线容错

- 在线词典结果进入本地缓存，减少重复请求。
- 支持导入 TXT/JSON 词典和词书，适合自建词库。
- 在线服务不可用时自动保留本地查询路径。
- 词典、发音、翻译等外部服务均为可选能力，不阻塞本地复习。

<img width="985" height="680" alt="image" src="https://github.com/user-attachments/assets/46277fe1-25f9-4f11-9efd-3b73b804c02c" />


### 可选的局域网 Web 工作台

桌面端启动本地 Web 服务后，可以在同一局域网的手机或平板继续查看总览、生词库、学习计划、复习队列和历史记录。接口使用 Token 保护，前端与桌面端共享同一份状态仓储。

<img width="986" height="685" alt="image" src="https://github.com/user-attachments/assets/13021a93-e95e-4104-b7c4-20039988d3b4" />


## 架构总览

```text
┌────────────────────────── WordCrafter Pro ──────────────────────────┐
│  PySide6 / Qt6 Desktop                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Reading      │  │ Dictionary   │  │ Study / SRS  │               │
│  │ bilingual    │  │ lookup/cache │  │ decks/logs   │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         └──────────────────┼──────────────────┘                       │
│                    Shared QtConfig Context                           │
├───────────────────────────┼─────────────────────────────────────────┤
│  Core                     Services                    Web             │
│  repository / session     AI streaming                Token API       │
│  srs / deck / logs        dictionary / definitions    responsive UI   │
│  folders / text utils     Microsoft / pronunciation   shared state   │
├───────────────────────────┴─────────────────────────────────────────┤
│  JSON persistence · cache · imported wordbooks · export               │
└─────────────────────────────────────────────────────────────────────┘
```

项目按职责拆分为 `core`、`services`、`qt`、`theme` 与 `webui`，业务逻辑可以脱离界面测试；Web 后端使用 Python 标准库，不额外引入服务端框架。

## 2.0 发布物

前往 [Release v2.0](https://github.com/WilliamAxte/WordCrafterPro_CET/releases/tag/v2.0)：

- **安装版**：`WordCrafterPro_v2.0_Setup.exe`，推荐普通用户使用。
- **便携版**：`WordCrafterPro_v2.0_Windows_x64.zip`，解压后运行 `WordCrafterPro.exe`。
- **当前源码包**：`WordCrafterPro_v2.0_Source.zip`。

系统要求：Windows 10/11 64 位。安装版默认安装到当前用户目录，不需要管理员权限；便携版请放在可写目录，以便保存配置、生词、缓存和学习记录。

## 快速开始

1. 下载并运行安装版，或解压便携版。
2. 打开“设置”，填入 OpenAI 兼容接口地址、模型与 API Key。
3. 在词汇、ACG 或阅读页面生成内容；选中词汇加入生词库。
4. 在学习页面按每日计划复习，或从设置启动局域网 Web UI。

词典查询、本地词书和 SRS 复习不依赖 AI Key。

## 从源码运行

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

运行完整测试套件（Qt 使用 offscreen 模式）：

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

当前版本已覆盖核心算法、Qt 页面初始化、Web 鉴权、词典/生词、学习计划、复习、历史导出等流程，共 **34 项测试通过**。

## 构建与发布

```powershell
.venv\Scripts\python.exe -m PyInstaller build.spec --clean --noconfirm
& "D:\Program Files\Inno Setup 7\ISCC.exe" installer.iss
```

便携版位于 `dist/WordCrafterPro/`；Inno Setup 安装包位于 `installer-output/`。

## 数据与隐私

学习记录、配置、缓存和会话保存在本地 JSON 文件中。只有在你主动配置并调用相应服务时，文本或查询才会发送给外部 API；API Key 不写入 README 或发布包。

## 项目结构

```text
app/
├─ main.py                 # 应用入口
├─ wordcrafter/
│  ├─ core/                # 仓储、会话、词库、学习计划、SRS
│  ├─ services/            # AI、词典、发音、翻译、更新服务
│  ├─ qt/                  # Qt6 壳层、页面、阅读器与控件
│  ├─ theme/               # 主题色板、token、预设
│  └─ webui.py             # Token 保护的局域网 Web UI
├─ tests/                  # 核心、Qt、Web 端到端测试
├─ assets/                 # neko 应用图标及 Web 资源
├─ build.spec              # PyInstaller 配置
└─ installer.iss           # Inno Setup 配置
```

## License

[MIT License](LICENSE) · Made by [WilliamAxte](https://github.com/WilliamAxte)
