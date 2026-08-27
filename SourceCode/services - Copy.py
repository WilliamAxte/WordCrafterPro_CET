import json
import urllib.request
import urllib.error
import urllib.parse
import threading
import sys
import os
import re
import time
import ctypes
import subprocess


class StreamRouter:
    """高可用流式分流路由器：精准识别中英文分界标签，杜绝中文串入英文框"""
    def __init__(self, txt_en, txt_zh):
        self.txt_en = txt_en
        self.txt_zh = txt_zh
        self.buffer = ""
        self.mode = "INIT"
        self.has_switched_to_zh = False

    def feed(self, token):
        self.buffer += token

        while True:
            if self.mode == "INIT":
                if "[ENGLISH_START]" in self.buffer:
                    _, self.buffer = self.buffer.split("[ENGLISH_START]", 1)
                    self.mode = "EN"
                    continue
                elif len(self.buffer) > 20 and "[" not in self.buffer:
                    self.mode = "EN"
                    continue
                break

            if self.mode == "EN":
                if "[ENGLISH_END]" in self.buffer:
                    en_part, self.buffer = self.buffer.split("[ENGLISH_END]", 1)
                    if en_part:
                        self.txt_en.insert("end", en_part)
                    self.mode = "WAIT_ZH"
                    continue
                elif "[CHINESE_START]" in self.buffer:
                    en_part, self.buffer = self.buffer.split("[CHINESE_START]", 1)
                    if en_part:
                        self.txt_en.insert("end", en_part)
                    self.mode = "ZH"
                    self.has_switched_to_zh = True
                    continue

                if "[" in self.buffer:
                    idx = self.buffer.find("[")
                    if idx > 0:
                        self.txt_en.insert("end", self.buffer[:idx])
                        self.buffer = self.buffer[idx:]
                    break
                else:
                    self.txt_en.insert("end", self.buffer)
                    self.buffer = ""
                    break

            if self.mode == "WAIT_ZH":
                if "[CHINESE_START]" in self.buffer:
                    _, self.buffer = self.buffer.split("[CHINESE_START]", 1)
                    self.mode = "ZH"
                    self.has_switched_to_zh = True
                    continue
                elif any('\u4e00' <= c <= '\u9fff' for c in self.buffer):
                    self.mode = "ZH"
                    self.has_switched_to_zh = True
                    continue
                break

            if self.mode == "ZH":
                if "[CHINESE_END]" in self.buffer:
                    zh_part, self.buffer = self.buffer.split("[CHINESE_END]", 1)
                    if zh_part:
                        self.txt_zh.insert("end", zh_part)
                    self.mode = "DONE"
                    continue

                if "[" in self.buffer:
                    idx = self.buffer.find("[")
                    if idx > 0:
                        self.txt_zh.insert("end", self.buffer[:idx])
                        self.buffer = self.buffer[idx:]
                    break
                else:
                    self.txt_zh.insert("end", self.buffer)
                    self.buffer = ""
                    break

            if self.mode == "DONE":
                break

    def close(self):
        if self.buffer:
            clean = re.sub(r'\[/?(ENGLISH|CHINESE)_(START|END)\]', '', self.buffer).strip()
            if clean:
                if self.mode == "ZH" or self.has_switched_to_zh or any('\u4e00' <= c <= '\u9fff' for c in clean):
                    self.txt_zh.insert("end", clean)
                else:
                    self.txt_en.insert("end", clean)
        self.buffer = ""


class AIService:
    @staticmethod
    def generate_vocab_story_stream(words, extra_cnt, target_len, difficulty, api_key, api_url, model_name, on_token):
        prompt = f"""You are a professional English tutor. Write a coherent, engaging story using the target vocabulary.

Target Words: {', '.join(words)}
Length: {target_len}
Difficulty: {difficulty}
Extra expansion vocabulary: {extra_cnt} words.

CRITICAL INSTRUCTIONS:
1. You MUST separate the English story and Chinese translation strictly using the tags below.
2. DO NOT include any conversational greetings or introductory text.

[ENGLISH_START]
(Write the pure English story text here)
[ENGLISH_END]
[CHINESE_START]
(Write the accurate, natural Chinese translation here)
[CHINESE_END]"""
        AIService._stream_request(prompt, api_key, api_url, model_name, on_token)

    @staticmethod
    def generate_acg_story_stream(words, extra_cnt, target_len, category, topic, difficulty, api_key, api_url, model_name, on_token):
        prompt = f"""You are an elite ACG / Anime & Gaming culture columnist. Write an in-depth essay or review.

Category: {category}
Topic: {topic}
Mandatory Vocabulary: {', '.join(words)}
Length: {target_len}
Difficulty: {difficulty}
Extra Words: {extra_cnt}

CRITICAL FORMAT REQUIREMENT:
[ENGLISH_START]
(Write the pure English ACG essay text here)
[ENGLISH_END]
[CHINESE_START]
(Write the pure Chinese translation here)
[CHINESE_END]"""
        AIService._stream_request(prompt, api_key, api_url, model_name, on_token)

    @staticmethod
    def fetch_authentic_reading_stream(source_type, work_name, target_len, difficulty, api_key, api_url, model_name, on_token):
        prompt = f"""You are a literary reading assistant. Provide an authentic reading excerpt.

Source Type: {source_type}
Work/Speaker: {work_name}
Excerpt Length: {target_len}
Difficulty: {difficulty}

CRITICAL FORMAT REQUIREMENT:
[ENGLISH_START]
(Write the authentic English reading text here)
[ENGLISH_END]
[CHINESE_START]
(Write the Chinese translation here)
[CHINESE_END]"""
        AIService._stream_request(prompt, api_key, api_url, model_name, on_token)

    @staticmethod
    def _stream_request(prompt, api_key, api_url, model_name, on_token):
        if not api_key:
            raise ValueError("API Key 为空，请在顶部或设置中配置。")
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a bilingual teaching engine. Strictly adhere to formatting tags."},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "temperature": 0.7
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}"
        }
        req = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            on_token(token)
                except Exception:
                    pass


class MicrosoftTranslatorService:
    @staticmethod
    def translate_text(text, api_key, region="global", target_lang="zh-Hans"):
        if not api_key:
            raise ValueError("未配置微软翻译 API Key。")

        endpoint = "https://api.cognitive.microsofttranslator.com/translate"
        params = f"?api-version=3.0&to={target_lang}"
        url = endpoint + params

        headers = {
            "Ocp-Apim-Subscription-Key": api_key.strip(),
            "Content-Type": "application/json; charset=UTF-8"
        }
        if region and region.strip() != "global":
            headers["Ocp-Apim-Subscription-Region"] = region.strip()

        body = json.dumps([{"Text": text}]).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result and isinstance(result, list):
                translations = result[0].get("translations", [])
                if translations:
                    return translations[0].get("text", "")
        return ""

    @staticmethod
    def lookup_word(word, api_key, region="global"):
        if not api_key:
            raise ValueError("微软翻译 API Key 未设置。")

        lookup_url = "https://api.cognitive.microsofttranslator.com/dictionary/lookup?api-version=3.0&from=en&to=zh-Hans"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key.strip(),
            "Content-Type": "application/json; charset=UTF-8"
        }
        if region and region.strip() != "global":
            headers["Ocp-Apim-Subscription-Region"] = region.strip()

        body = json.dumps([{"Text": word}]).encode("utf-8")
        req = urllib.request.Request(lookup_url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                defs = []
                if res and isinstance(res, list) and res[0].get("translations"):
                    for tr in res[0]["translations"][:4]:
                        pos = tr.get("posTag", "").lower()
                        display_target = tr.get("displayTarget", "")
                        defs.append(f"{pos}. {display_target}")
                pos_def = "\n".join(defs) if defs else "微软翻译释义"
                if not defs:
                    trans = MicrosoftTranslatorService.translate_text(word, api_key, region)
                    pos_def = f"n./v. {trans}"

                return {
                    "phonetic": "[Microsoft Azure Translator]",
                    "pos_def": pos_def,
                    "example": f"Example sentence containing '{word}'."
                }
        except Exception:
            trans = MicrosoftTranslatorService.translate_text(word, api_key, region)
            return {
                "phonetic": "[Microsoft Translator]",
                "pos_def": f"释义: {trans}",
                "example": f"Example sentence using {word}."
            }


class MicrosoftSpeechService:
    @staticmethod
    def speak_async(text, speech_key="", region="eastasia", voice="en-US-JennyNeural"):
        threading.Thread(
            target=MicrosoftSpeechService._speak_worker,
            args=(text, speech_key, region, voice),
            daemon=True
        ).start()

    @staticmethod
    def _speak_worker(text, speech_key, region, voice):
        if speech_key and speech_key.strip():
            try:
                url = f"https://{region.strip()}.tts.speech.microsoft.com/cognitiveservices/v1"
                headers = {
                    "Ocp-Apim-Subscription-Key": speech_key.strip(),
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
                    "User-Agent": "WordCrafterPro"
                }
                ssml = f"""<speak version='1.0' xml:lang='en-US'><voice name='{voice}'>{text}</voice></speak>"""
                req = urllib.request.Request(url, data=ssml.encode("utf-8"), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=8) as resp:
                    audio_data = resp.read()
                    import winsound
                    winsound.PlaySound(audio_data, winsound.SND_MEMORY)
                    return
            except Exception:
                pass

        try:
            if sys.platform == "win32":
                clean = text.replace('"', ' ').replace("'", " ")
                cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{clean}\')"'
                os.system(cmd)
        except Exception:
            pass


class FreeDictService:
    @staticmethod
    def lookup(word):
        clean_word = word.strip().lower()
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_word}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    entry = data[0]
                    phonetic = entry.get("phonetic", "")
                    if not phonetic and entry.get("phonetics"):
                        for p in entry["phonetics"]:
                            if p.get("text"):
                                phonetic = p["text"]
                                break
                    meanings = entry.get("meanings", [])
                    pos_def_list = []
                    example_sentence = ""
                    for m in meanings:
                        pos = m.get("partOfSpeech", "")
                        defs = m.get("definitions", [])
                        if defs:
                            def_text = defs[0].get("definition", "")
                            pos_def_list.append(f"{pos}. {def_text}")
                            if not example_sentence and defs[0].get("example"):
                                example_sentence = defs[0]["example"]
                    return {
                        "phonetic": phonetic or "[No phonetic]",
                        "pos_def": "\n".join(pos_def_list) if pos_def_list else "暂无释义",
                        "example": example_sentence or f"This is an authentic example containing '{clean_word}'."
                    }
        except Exception:
            pass
        return {
            "phonetic": "[离线词库]",
            "pos_def": "未查询到释义，可在设置中配置微软翻译/AI模型",
            "example": f"Example sentence using {clean_word}."
        }

    @staticmethod
    def submit_lookup(word, callback):
        def _run():
            res = FreeDictService.lookup(word)
            callback(res)
        threading.Thread(target=_run, daemon=True).start()


class AppleMusicStoreService:
    """
    针对 Windows 10/11 微软商店版 Apple Music 的专属媒体控制与数据抓取服务
    支持提取：实时歌名、歌手、专辑名、高清专辑封面 Base64、播放状态及系统级音量联动
    """
    VK_MEDIA_NEXT = 0xB0
    VK_MEDIA_PREV = 0xB1
    VK_MEDIA_PLAY_PAUSE = 0xB3

    _listener = None
    _is_running = False
    _current_volume = 70

    PS_MEDIA_EXTRACTOR = (
        "$ErrorActionPreference = 'SilentlyContinue'; "
        "[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType = WindowsRuntime] | Out-Null; "
        "[Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null; "
        "$mgrOp = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync(); "
        "while ($mgrOp.Status -eq 'Started') { Start-Sleep -Milliseconds 15 }; "
        "$mgr = $mgrOp.GetResults(); "
        "if ($mgr) { "
        "  $sessions = $mgr.GetSessions(); "
        "  $target = $null; "
        "  foreach ($s in $sessions) { "
        "    if ($s.SourceAppUserModelId -match 'AppleMusic|AppleInc') { $target = $s; break } "
        "  }; "
        "  if (-not $target) { $target = $mgr.GetCurrentSession() }; "
        "  if ($target) { "
        "    $pOp = $target.TryGetMediaPropertiesAsync(); "
        "    while ($pOp.Status -eq 'Started') { Start-Sleep -Milliseconds 15 }; "
        "    $p = $pOp.GetResults(); "
        "    $pb = $target.GetPlaybackInfo(); "
        "    $isPlaying = ($pb -and $pb.PlaybackStatus -eq 'Playing'); "
        "    $artB64 = ''; "
        "    if ($p -and $p.Thumbnail) { "
        "      try { "
        "        $sOp = $p.Thumbnail.OpenReadAsync(); "
        "        while ($sOp.Status -eq 'Started') { Start-Sleep -Milliseconds 15 }; "
        "        $stream = $sOp.GetResults(); "
        "        if ($stream -and $stream.Size -gt 0) { "
        "          $reader = [Windows.Storage.Streams.DataReader]::new($stream.GetInputStreamAt(0)); "
        "          $rOp = $reader.LoadAsync($stream.Size); "
        "          while ($rOp.Status -eq 'Started') { Start-Sleep -Milliseconds 15 }; "
        "          $bytes = New-Object byte[] $stream.Size; "
        "          $reader.ReadBytes($bytes); "
        "          $artB64 = [Convert]::ToBase64String($bytes); "
        "          $reader.Dispose(); "
        "        } "
        "      } catch {} "
        "    }; "
        "    Write-Output ('#MEDIA#' + (@{ "
        "      connected = $true; "
        "      is_playing = $isPlaying; "
        "      title = if ($p -and $p.Title) { $p.Title } else { '正在播放' }; "
        "      artist = if ($p -and $p.Artist) { $p.Artist } else { 'Apple Music' }; "
        "      album = if ($p -and $p.AlbumTitle) { $p.AlbumTitle } else { 'Apple Music 专辑' }; "
        "      artwork = $artB64 "
        "    } | ConvertTo-Json -Compress)); "
        "  } else { Write-Output '#MEDIA#null' } "
        "} else { Write-Output '#MEDIA#null' }"
    )

    @classmethod
    def launch_store_app(cls):
        """精准唤起微软商店版 Apple Music 原生客户端"""
        try:
            subprocess.Popen("explorer.exe shell:AppsFolder\\AppleInc.AppleMusicWin_nzyj5cx40ttqa!App", shell=True)
        except Exception:
            try:
                subprocess.Popen("start applemusic:", shell=True)
            except Exception:
                pass

    @classmethod
    def toggle_play(cls):
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PLAY_PAUSE, 0, 2, 0)

    @classmethod
    def next_track(cls):
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_NEXT, 0, 0, 0)
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_NEXT, 0, 2, 0)

    @classmethod
    def prev_track(cls):
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PREV, 0, 0, 0)
        ctypes.windll.user32.keybd_event(cls.VK_MEDIA_PREV, 0, 2, 0)

    @classmethod
    def set_volume(cls, val):
        cls._current_volume = max(0, min(100, int(val)))
        if sys.platform == "win32":
            vol_val = int((cls._current_volume / 100.0) * 65535)
            full_vol = (vol_val & 0xFFFF) | ((vol_val & 0xFFFF) << 16)
            try:
                ctypes.windll.winmm.waveOutSetVolume(0, full_vol)
            except Exception:
                pass

    @classmethod
    def set_state_listener(cls, callback):
        cls._listener = callback
        if not cls._is_running:
            cls._is_running = True
            threading.Thread(target=cls._sync_worker, daemon=True).start()

    @classmethod
    def _sync_worker(cls):
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            creationflags = subprocess.CREATE_NO_WINDOW

        while True:
            try:
                proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", cls.PS_MEDIA_EXTRACTOR],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
                stdout, _ = proc.communicate(timeout=3)

                if "#MEDIA#" in stdout:
                    raw_json = stdout.split("#MEDIA#")[1].strip()
                    if raw_json == "null":
                        if cls._listener:
                            cls._listener({
                                "connected": False,
                                "is_playing": False,
                                "title": "未检测到 Apple Music 会话",
                                "artist": "点击右侧【唤起 Apple Music】启动客户端并播放歌曲",
                                "album": "",
                                "artwork": ""
                            })
                    else:
                        data = json.loads(raw_json)
                        if cls._listener:
                            cls._listener({
                                "connected": True,
                                "is_playing": data.get("is_playing", False),
                                "title": data.get("title", "未知歌曲"),
                                "artist": data.get("artist", "Apple Music"),
                                "album": data.get("album", ""),
                                "artwork": data.get("artwork", "")
                            })
            except Exception:
                pass
            time.sleep(1.2)
