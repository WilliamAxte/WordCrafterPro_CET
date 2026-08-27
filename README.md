<div align="center">

# 🌌 WordCrafter Pro
### *The Next-Generation AI Contextual Reading & Lexicon Studio*

<p align="center">
  <b>极光青蓝微光美学 · 大模型智能情境重塑 · Windows 原生媒体总线沉浸伴读工作台</b>
</p>

[![Release Version](https://img.shields.io/badge/Release-v1.1-38BDF8?style=flat-square&logo=github&logoColor=white)](https://github.com/WilliamAxte/WordCrafterPro_CET/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-0284C7?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D4?style=flat-square&logo=windows&logoColor=white)](https://microsoft.com/windows)
[![UI Engine](https://img.shields.io/badge/UI-CustomTkinter-6366F1?style=flat-square&logo=target&logoColor=white)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-10B981?style=flat-square)](LICENSE)

---

</div>

> **💡 设计哲学 (Design Philosophy)**  
> 语言习得不应是孤立枯燥的机械抽认，而应置身于优美且生动的语境中[cite: 9]。**WordCrafter Pro** 将前沿大语言模型（LLM）的生成能力、地道语篇精读与操作系统底层媒体总线融合[cite: 4, 7]，在拟真微光磨砂面板与悠扬旋律中，重塑双语输入与情境记忆体验[cite: 1, 8]。

<img width="929" height="725" alt="image" src="https://github.com/user-attachments/assets/2b72c95f-a0b7-4f16-ae49-707b3b4db2ec" />

---

## 💎 核心特性

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🚀 AI 语境编织引擎</h3>
      <p>告别死记硬背。输入目标生词，大模型自动将词汇编织进情节连贯的长篇短文中[cite: 4, 9]。</p>
      <ul>
        <li><b>流式分流路由器</b>：自研 <code>StreamRouter</code> 协议，实现中英文双流实时解析。</li>
        <li><b>四阶语境难度</b>：初高中日常 / 四级 / 六级 / 考研雅思动态匹配[cite: 1, 2]。</li>
        <li><b>拓展词汇探索</b>：智能衍生高频派生词与同义表达[cite: 4, 5, 9]。</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🎬 ACG 文化专栏与名篇精读</h3>
      <p>用最感兴趣的题材学英语，精读真正有思想深度的经典原著[cite: 5, 7]。</p>
      <ul>
        <li><b>二次元特稿矩阵</b>：动画深度漫评、游戏世界观评测、Galgame/OST 音乐赏析[cite: 5]。</li>
        <li><b>世界名著原声精读</b>：乔布斯演讲、奥威尔《1984》、《了不起的盖茨比》等经典篇目[cite: 7]。</li>
        <li><b>沉浸全屏阅读器</b>：双语对照 / 纯英 / 纯中三模态自由切换[cite: 6, 10]。</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>🎵 Windows 原生 Apple Music 伴读</h3>
      <p>专为专注学习打造的系统级流媒体控制中枢。</p>
      <ul>
        <li><b>WinRT 媒体总线直连</b>：基于 C# 桥接技术，原生对接微软商店版 Apple Music。</li>
        <li><b>高品质封面元数据</b>：实时抓取渲染高清专辑封面 Base64、曲目名与艺术家信息。</li>
        <li><b>双向总线控制</b>：上一曲/下一曲、播放/暂停与系统主音量无级调节。</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🌌 极光微光美学 (Nordic Cyan)</h3>
      <p>极简克制，通透灵动的现代化交互界面[cite: 1]。</p>
      <ul>
        <li><b>全景拟真磨砂</b>：0-30px 动态高斯模糊与背景透光率无级调节[cite: 1, 8]。</li>
        <li><b>抽屉式折叠卡片</b>：参数面板一键收纳，把最大视野留给双语阅读。</li>
        <li><b>无级字体缩放</b>：4 档全局字号等比动态缩放体系[cite: 1, 8]。</li>
      </ul>
    </td>
  </tr>
</table>

<img width="927" height="727" alt="image" src="https://github.com/user-attachments/assets/1cc55a5e-8a2e-4d14-9105-111d4e55cf0c" />

---

## 🔍 即时划词与生词生态

```text
  [ 划选英文单词 / 短语 ]
            │
            ├─► 🔍 智能多源词典：Microsoft Azure 认知翻译 / 离线备用词库降级容灾
            ├─► 🔊 微软高保真 TTS：预置 Jenny / Guy / Aria / Sonia / Ryan 自然原声音色
            └─► ➕ 本地生词管理：分页浏览、多条件检索、导入/导出纯文本 TXT 备份[cite: 10]

```

---

## 🏗️ 工业级系统架构

```text
WordCrafterPro/
├── app_config.py          # 运行时配置中心 (色彩主题、字体度量衡矩阵、GPU 硬件加速)[cite: 1]
├── repository.py          # 本地数据仓储 (配置持久化、生词库历史与释义缓存池)[cite: 3]
├── services.py            # AI 流式路由器、Azure 翻译/TTS 引擎、离线词典服务[cite: 4]
├── music_service.py       # C# WinRT SMTC 系统媒体总线互操作网桥
├── update_service.py      # GitHub Releases API 自动版本检测与更新通道
│
├── ui_components.py       # UI 统一对外导出网关
├── ui_base.py             # 划词文本框、翻译弹窗、全屏阅读器、版本更新卡片[cite: 10]
├── ui_cards.py            # 抽屉式折叠容器 (CollapsibleCard)
├── ui_vocab_manager.py    # 本地生词库多维检索与卡片流界面[cite: 10]
├── ui_music.py            # Apple Music 伴读底栏组件
│
├── tab_vocab.py           # Page 1: 单词情境短文生成[cite: 2, 9]
├── tab_acg.py             # Page 2: 二次元深度文化专栏 (ACG)[cite: 2, 5]
├── tab_reading.py         # Page 3: 经典名篇与原著精读[cite: 2, 7]
├── tab_settings.py        # Page 4: 视觉偏好、壁纸磨砂引擎与关于更新[cite: 2, 8]
└── main.py                # 程序入口 & 全景毛玻璃图层渲染总调度[cite: 2]

```

---

## 🚀 快速上手

### 方式一：下载 Windows 安装程序 (推荐)

前往 [Releases 页面](https://www.google.com/url?sa=E&source=gmail&q=https://github.com/WilliamAxte/WordCrafterPro_CET/releases) 下载最新发布的 `WordCrafterPro_v1.1_Setup.exe`，按向导安装即可使用。

### 方式二：从源码运行开发环境

**系统要求**：Windows 10 (1809+) 或 Windows 11，Python 3.10+。

```bash
# 1. 克隆代码仓库
git clone [https://github.com/WilliamAxte/WordCrafterPro_CET.git](https://github.com/WilliamAxte/WordCrafterPro_CET.git)
cd WordCrafterPro_CET

# 2. 安装核心图形与图像处理依赖
pip install customtkinter pillow

# 3. 启动应用
python main.py

```

---

## ⚙️ 模型与服务接口集成

支持国内外所有兼容标准 OpenAI 协议的大语言模型端点：

| 服务类别 | 兼容服务商 / 方案 | 说明 |
| --- | --- | --- |
| **大语言模型 (LLM)** | DeepSeek / OpenAI (GPT-4o) / Claude / 通义千问

 | 填入 `API Key` 与 `API URL` 即可直接流式调用

 |
| **翻译与释义引擎** | Microsoft Azure Translator / 内置词典

 | 每月免费 200 万字符翻译额度

 |
| **自然语音合成 (TTS)** | Microsoft Azure Speech (Neural Voice) / Win32 SAPI

 | 沉浸式母语级纯正朗读

 |
| **伴读音频流** | Windows 微软商店版 Apple Music (WinUI 3) | 零 Token 门槛，系统总线原生联动 |

---

## 📦 生产环境打包发布

项目自带经过优化的 `build.spec` 与 `installer.iss` 规范文件：

```powershell
# 1. 编译可执行程序目录
python -m PyInstaller build.spec --clean

# 2. 生成标准 Windows 安装向导 (需安装 Inno Setup 6)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

```

打包产物将输出至 `Output/WordCrafterPro_v1.1_Setup.exe`。

---

## 📄 开源许可证

本项目依据 [MIT License](https://www.google.com/search?q=LICENSE) 协议完全开源。
