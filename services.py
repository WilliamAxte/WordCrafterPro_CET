import json
import re
import urllib.request
import urllib.parse
import urllib.error
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

class FreeDictService:
    @classmethod
    def lookup(cls, word):
        word_clean = word.strip().lower()
        if not word_clean:
            return {"word": word, "phonetic": "", "pos_def": "未输入有效单词", "example": ""}

        try:
            url = f"https://cn.bing.com/dict/search?q={urllib.parse.quote(word_clean)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            phonetic = ""
            us_match = re.search(r'class="hd_prUS"[^>]*>\\[(.*?)\\]', html)
            if us_match:
                phonetic = f"美 [{us_match.group(1)}]"
            else:
                pr_match = re.search(r'class="hd_pr"[^>]*>\\[(.*?)\\]', html)
                if pr_match:
                    phonetic = f"[{pr_match.group(1)}]"

            defs = []
            pos_matches = re.findall(r'<span class="pos[^"]*">([^<]+)</span><span class="def[^"]*"><span>([^<]+)</span></span>', html)
            for pos, definition in pos_matches[:4]:
                defs.append(f"{pos} {definition}")
            pos_def_str = "\n".join(defs) if defs else ""

            example_str = ""
            en_sen = re.search(r'<div class="sen_en">([^<]+)</div>', html)
            cn_sen = re.search(r'<div class="sen_cn">([^<]+)</div>', html)
            if en_sen and cn_sen:
                example_str = f"{en_sen.group(1)}\n{cn_sen.group(1)}"

            if pos_def_str:
                return {
                    "word": word,
                    "phonetic": phonetic or "[必应词典]",
                    "pos_def": pos_def_str,
                    "example": example_str or "暂无典型例句"
                }
        except Exception:
            pass

        return {
            "word": word,
            "phonetic": "[公共词典]",
            "pos_def": f"词条: {word} 的基本释义",
            "example": f"This is an example sentence for {word}."
        }


class AIService:
    @staticmethod
    def request_llm(prompt, api_key, api_url, model_name, temp=0.6):
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a professional English tutor, literary scholar, and ACG editorial writer. Follow all structure and length instructions strictly."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temp
        }
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=75) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @classmethod
    def generate_vocab_story(cls, words, extra_count, length_target, difficulty, api_key, api_url, model_name):
        if not api_key:
            words_fmt = ", ".join([f"【{w}】" for w in words])
            en = f"Tom was an ordinary student with a simple daily routine. However, whenever he had to face a big decision, he would often {' and '.join(words_fmt)} in unexpected ways.\n\nOne afternoon, he realized that learning does not require complicated methods—just patience and curiosity. By embracing these moments, everything became clear."
            zh = f"Tom 是一个生活规律的普通学生。然而每当面对重大决定时，他总会以意想不到的方式经历 {', '.join(words)}。\n\n一个下午，他意识到学习不需要复杂的方法——只需要耐心和好奇心。拥抱这些时刻，一切都豁然开朗。"
            return en, zh

        extra_instruction = ""
        if extra_count > 0:
            extra_instruction = f"4. 随机未学词拓展：请在故事中额外自然引入 {extra_count} 个地道实用的中高级新单词（用 〖*word*〗 格式标出），帮助读者在阅读中拓展词汇。"

        prompt = f"""
请根据【目标生词列表】编写一段通俗生动的短文与中文翻译。

【核心目标词汇】：{", ".join(words)} (共 {len(words)} 个词)
【目标生成字数篇幅】：严格要求生成大约 {length_target} 个英文单词（请务必充实细节与故事情节，字数必须达标！）
【难度标准】：{difficulty}

【严格要求】：
1. 词汇门槛控制：除【核心目标词汇】和拓展生词外，全文其他词汇必须使用初高中/日常高频简单词，严禁生僻词与晦涩长难句。
2. 英文短文中每次出现核心目标生词，必须用 【word】 醒目标出。
3. 篇幅严控：请根据 {length_target} 字的要求充分展开叙事或场景描写，切勿写得过短！
{extra_instruction}
5. 严格使用指定标记输出，严禁输出任何 Markdown 标题符号（如 ###）：

<<<ENGLISH_STORY>>>
(这里输出纯英文故事)
<<<CHINESE_TRANSLATION>>>
(这里输出流畅中文翻译，重点词对应使用【中文】或〖拓展中文〗标出)
"""
        res = cls.request_llm(prompt, api_key, api_url, model_name)
        return cls._split_content(res)

    @classmethod
    def generate_acg_story(cls, words, extra_count, length_target, category, topic, difficulty, api_key, api_url, model_name):
        if not api_key:
            en = f"Title: The World of {topic}\n\nIn modern animation, creators know how to 【{words[0]}】 in moments of intense drama. Works like {topic} highlight deep emotion and artful music."
            zh = f"标题：《{topic}》的艺术世界\n\n在现代动漫中，创作者懂得如何在剧烈冲突中展现【{words[0]}】。如《{topic}》这般作品凸显了深层情感与配乐魅力。"
            return en, zh

        extra_instruction = ""
        if extra_count > 0:
            extra_instruction = f"4. 随机未学词拓展：请在专栏中额外融入 {extra_count} 个与影视/动画/艺术鉴赏相关的地道新词汇（用 〖*word*〗 标出）。"

        prompt = f"""
请以二次元专栏特稿/漫评随笔风格，围绕主题撰写一篇充满 ACG 氛围的英文深度报道并提供双语翻译。

【专栏类型】：{category}
【作品/焦点主题】：{topic}
【融入核心生词】：{", ".join(words)} (共 {len(words)} 个词)
【目标生成字数】：严格生成大约 {length_target} 个英文单词（论述深刻、细节充分，切勿敷衍简短！）
【难度标准】：{difficulty}

【严格要求】：
1. 文风地道生动，结合作品设定、视听艺术或受众心境深度展开。
2. 核心生词使用 【WORD】 醒目标注。
3. 篇幅严控：必须达到大约 {length_target} 字的深度专栏体量。
{extra_instruction}
5. 严格使用指定标记输出，严禁输出任何 Markdown 标题符号（如 ###）：

<<<ENGLISH_STORY>>>
(这里输出英文专栏特稿)
<<<CHINESE_TRANSLATION>>>
(这里输出中文对照翻译，目标词对应使用【中文】标出)
"""
        res = cls.request_llm(prompt, api_key, api_url, model_name)
        return cls._split_content(res)

    @classmethod
    def fetch_authentic_reading(cls, source_type, custom_work, length_target, difficulty, api_key, api_url, model_name):
        if not api_key:
            en = (
                "Title: Stay Hungry, Stay Foolish (Steve Jobs)\n\n"
                "Your time is limited, so don't waste it living someone else's life. "
                "Don't be trapped by dogma — which is living with the results of other people's thinking. "
                "Don't let the noise of others' opinions drown out your own inner voice. "
                "And most importantly, have the courage to follow your heart and intuition."
            )
            zh = (
                "标题：求知若饥，虚心若愚（史蒂夫·乔布斯）\n\n"
                "你们的时间很有限，所以不要浪费时间去过别人的生活。"
                "不要被教条所束缚——那是在按别人的思考结果活着。"
                "不要让别人的意见噪音淹没你自己内心的声音。"
                "最重要的是，要有勇气去跟随你的内心和直觉。"
            )
            return en, zh

        prompt = f"""
你是一位世界文学与英语经典名篇研究专家。请从【{source_type}】中挑选或节选一段经典段落（若指定了作品：{custom_work}，则优先围绕该作品），并提供精准流畅的全文双语对照。

【选篇来源类型】：{source_type}
【指定作品/演讲者】：{custom_work or '挑选该领域最具代表性的经典篇目'}
【目标字数】：生成约 {length_target} 词的经典原著/演讲节选精读
【语言难度】：{difficulty}

【严格要求】：
1. 保持原文地道原汁原味的文采与语言节奏。
2. 提炼出文中最核心、最具启发性的经典修辞与句式。
3. 严格使用指定标记输出，严禁输出任何多余的 Markdown 标题（如 ###）：

<<<ENGLISH_STORY>>>
(这里输出经典篇章英文正文，首行附带篇名与作者)
<<<CHINESE_TRANSLATION>>>
(这里输出全文流畅优美的中文对照翻译)
"""
        res = cls.request_llm(prompt, api_key, api_url, model_name)
        return cls._split_content(res)

    @staticmethod
    def _split_content(raw):
        if "<<<ENGLISH_STORY>>>" in raw and "<<<CHINESE_TRANSLATION>>>" in raw:
            parts = raw.split("<<<CHINESE_TRANSLATION>>>")
            en = parts[0].replace("<<<ENGLISH_STORY>>>", "").strip()
            zh = parts[1].strip()
        else:
            en, zh = raw.strip(), "（未能自动切分翻译部分，请直接阅读原文）"
        en = re.sub(r'^```[a-zA-Z]*\n', '', en)
        en = re.sub(r'\n```$', '', en).strip()
        zh = re.sub(r'^```[a-zA-Z]*\n', '', zh)
        zh = re.sub(r'\n```$', '', zh).strip()
        return en, zh
