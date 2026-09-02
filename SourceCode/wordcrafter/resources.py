# ==============================================================================
# 文件路径: wordcrafter/resources.py
# 资源路径解析（源码运行 / PyInstaller 打包均可用）
#   assets/：app_icon.png/.ico（软件图标）、web_icon.png（Web UI 按钮图标）
# ==============================================================================
import os
import sys


def bundle_root():
    """打包运行时返回解包目录，源码运行返回 wordcrafter 所在的项目根目录。"""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset(name):
    """返回 assets 下资源的绝对路径；文件缺失时返回 None。"""
    path = os.path.join(bundle_root(), "assets", name)
    return path if os.path.exists(path) else None


def icon_paths():
    return {"app": asset("app_icon.png") or asset("app_icon.ico"),
            "web": asset("web_icon.png")}
