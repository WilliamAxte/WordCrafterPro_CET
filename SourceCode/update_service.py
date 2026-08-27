import json
import re
import threading
import urllib.error
import urllib.request
import webbrowser

# -------------------------------------------------------------
# 软件当前本地版本与 GitHub 仓库配置
# -------------------------------------------------------------
CURRENT_VERSION = "v1.1.0"
GITHUB_OWNER = "WilliamAxte"
GITHUB_REPO = "WordCrafterPro_CET"
GITHUB_HOME_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"


class UpdateService:
    @staticmethod
    def _parse_version(v_str):
        clean = re.sub(r"[^\d.]", "", v_str)
        try:
            return tuple(map(int, clean.split(".")))
        except Exception:
            return (0, 0, 0)

    @classmethod
    def check_update_async(cls, callback):
        def _worker():
            # GitHub 官方最新版本 API
            api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            headers = {
                "User-Agent": "WordCrafterPro-Updater",
                "Accept": "application/vnd.github.v3+json"
            }
            try:
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                    remote_tag = data.get("tag_name", "v0.0.0")
                    remote_ver = cls._parse_version(remote_tag)
                    local_ver = cls._parse_version(CURRENT_VERSION)

                    release_info = {
                        "tag": remote_tag,
                        "name": data.get("name", remote_tag),
                        "body": data.get("body", "暂无更新日志说明。"),
                        "html_url": data.get("html_url", f"{GITHUB_HOME_URL}/releases"),
                        "published_at": data.get("published_at", "")[:10]
                    }

                    # 版本号比对 (如 v1.0.1 > v1.0.0)
                    if remote_ver > local_ver:
                        callback("update_available", release_info)
                    else:
                        callback("latest", release_info)
            except urllib.error.HTTPError as he:
                if he.code == 404:
                    callback("latest", {"tag": CURRENT_VERSION, "body": ""})
                else:
                    callback("error", f"HTTP {he.code}: {he.reason}")
            except Exception as e:
                callback("error", str(e))

        threading.Thread(target=_worker, daemon=True).start()

    @staticmethod
    def open_github_home():
        webbrowser.open(GITHUB_HOME_URL)

    @staticmethod
    def open_release_page(url=None):
        webbrowser.open(url or f"{GITHUB_HOME_URL}/releases")
