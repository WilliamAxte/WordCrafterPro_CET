# WordCrafterPro-大学英语等级考试
练习阅读能力
基于 CustomTkinter 与大语言模型的智能英语语境工坊：支持情境短文定制（200~1000字）、二次元 ACG 特稿随笔、经典名篇原著精读、动效卡片流生词库及微软必应免 Key 即时划词翻译。
# 📖 WordCrafter Pro - 英语情境短文、ACG 特稿与原著精读工坊

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-blue?style=flat" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/LLM-DeepSeek%20%7C%20GPT--4o%20%7C%20Claude-purple?style=flat" alt="LLM Supported" />
  <img src="https://img.shields.io/badge/Dict-Bing%20Dictionary-008373?style=flat" alt="Bing Dict" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License" />
</p>

**WordCrafter Pro** 是一款专为英语学习者、二次元爱好者及原著读者打造的沉浸式 AI 辅助阅读与词汇习得桌面应用。通过将生词融入通俗情境故事、动漫/游戏深度专栏或名家经典演讲，告别死记硬背，在真实语境中高效记忆。

---

## ✨ 核心特色

<img width="899" height="725" alt="image" src="https://github.com/user-attachments/assets/d7d2828c-6869-4c72-a44c-741b43de2e27" />



### 1. 📝 单词情境短文工坊
* **自定义长篇生成**：支持 200 词、400 词、600 词至 **1000 词长篇** 故事，叙事连贯、情节丰富。
* **灵活抽词策略**：支持全部使用、随机抽取 3/5/8 个或自定义抽词量。
* **🎲 随机未学词拓展**：可勾选引入地道中高级拓展生词（标注为 `〖*word*〗`），实现“以熟带生”。
* **严格难度分级**：除目标生词外，周围辅助词汇严格控制在初高中/日常高频水平，阅读无门槛。

* <img width="641" height="518" alt="image" src="https://github.com/user-attachments/assets/a9a2a487-daf8-43c5-a7a1-3c31b4dafbd9" />


### 2. 🌸 二次元 ACG 特稿与漫评专栏
* **丰富题材覆盖**：涵盖深度漫评、游戏世界观评测、动漫音乐/Galgame 配乐 OST 赏析、赛博朋克科幻随笔及行业观察。
* **沉浸文化氛围**：自然结合作品剧情、视听艺术与玩家心境，寓教于乐。
* **多渠道词汇导入**：支持从本地历史词库随机抽取、抽取近期学习词汇或从第一页输入框提取。

### 3. 📖 名篇名作与经典演讲精读
* **海量经典选段**：内置乔布斯斯坦福演讲、马丁·路德·金、丘吉尔演讲，以及《1984》、《了不起的盖茨比》等世界名著片段。
* **原汁原味双语对照**：保留大师级文采与修辞节奏，支持自定义篇幅精读。

### 4. 📚 动效卡片流本地生词库
* **拟态卡片流布局**：告别单调文本列表，每个生词独立封装为圆角卡片。
* **平滑视觉动效**：支持阶梯式级联入场动画（Staggered Animation）与鼠标悬浮发光变色（Hover Glow）。
* **微软必应免 Key 查词**：多线程异步拉取英/美音标、精准词性中文释义及双语例句，结果本地缓存秒开。
* **词库管理中心**：实时统计学习总词数与字符量，支持关键词即时筛选、单卡移除、TXT 批量导入与导出。

### 5. 🔍 沉浸式阅读辅助工具
* **右键划词即时翻译**：阅读过程中鼠标划词右键即可调出必应词典弹窗，一键收藏至生词库。
* **全屏专注阅读模式**：支持一键切换「双语对照」、「纯英文沉浸」与「中文对照」，快捷键 `Esc` 快速退出。

---

## 🛠️ 技术栈

* **GUI 框架**：[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (现代化暗黑/明亮自适应桌面 UI)
* **字典引擎**：微软必应词典公开接口 (免配置 API Key、毫秒级响应)
* **AI 驱动**：兼容 OpenAI API 规范的大语言模型接口（DeepSeek-V3/R1、GPT-4o、Claude 3.7、Qwen 等）
* **打包分发**：PyInstaller + Inno Setup (支持单文件安装向导、自定义路径与桌面快捷方式)

---

## 🚀 快速上手

### 环境准备
确保电脑已安装 **Python 3.10+**。

```bash
# 克隆仓库
git clone [https://github.com/your-username/WordCrafterPro.git](https://github.com/your-username/WordCrafterPro.git)
cd WordCrafterPro

# 安装依赖
pip install customtkinter -i [https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)

# 启动
python main.py

