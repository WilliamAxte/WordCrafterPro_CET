# ==============================================================================
# 文件路径: tab_settings.py
# 包含页面: SettingsTab (含 GitHub 检查更新与关于卡片)
# ==============================================================================
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
from services import MicrosoftSpeechService, MicrosoftTranslatorService
from ui_components import UpdateDialog
from update_service import CURRENT_VERSION, UpdateService


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app_ref):
        super().__init__(master, fg_color="transparent")
        self.app_ref = app_ref
        cfg = app_ref.config

        # 状态绑定
        self.var_theme = ctk.StringVar(value=cfg.config_repo.data.get("appearance_mode", "深色模式"))
        self.var_font_scale = ctk.StringVar(value=cfg.config_repo.data.get("font_size_scale", "标准 (100%)"))
        self.var_gpu = ctk.BooleanVar(value=cfg.gpu_enabled)

        # 壁纸与毛玻璃状态
        self.var_wallpaper_path = ctk.StringVar(value=cfg.wallpaper_path)
        self.var_wallpaper_blur = ctk.IntVar(value=cfg.wallpaper_blur)
        self.var_wallpaper_opacity = ctk.DoubleVar(value=cfg.wallpaper_opacity)

        # 微软服务状态
        self.var_engine = ctk.StringVar(value=cfg.translate_engine)
        self.var_ms_key = ctk.StringVar(value=cfg.ms_translator_key)
        self.var_ms_region = ctk.StringVar(value=cfg.ms_translator_region)
        self.var_speech_key = ctk.StringVar(value=cfg.ms_speech_key)
        self.var_speech_region = ctk.StringVar(value=cfg.ms_speech_region)
        self.var_voice_name = ctk.StringVar(value=cfg.ms_voice_name)

        self.setup_ui()

    def setup_ui(self):
        cfg = self.app_ref.config
        self.grid_columnconfigure(0, weight=1)

        scroll_box = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            fg_color=cfg.c_surface,
            border_width=1,
            border_color=cfg.c_border
        )
        scroll_box.pack(fill="both", expand=True, padx=2, pady=2)
        scroll_box.grid_columnconfigure(0, weight=1)

        # 1. 全局字体与外观设置
        self._build_header(scroll_box, "界面外观与全局字体大小 (Appearance & Typography)")
        grp_app = self._create_group(scroll_box)

        r_theme = ctk.CTkFrame(grp_app, fg_color="transparent")
        r_theme.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(r_theme, text="色彩主题模式", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left")

        self.seg_theme = ctk.CTkSegmentedButton(
            r_theme,
            values=["深色模式", "浅色模式", "跟随系统"],
            variable=self.var_theme,
            font=cfg.font_small,
            corner_radius=6,
            selected_color=cfg.c_primary,
            unselected_color=cfg.c_surface_variant,
            text_color=cfg.c_text,
            command=self.on_theme_change
        )
        self.seg_theme.pack(side="right")

        self._add_divider(grp_app)

        r_font = ctk.CTkFrame(grp_app, fg_color="transparent")
        r_font.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(r_font, text="全局字体大小快捷调节", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left")

        ctk.CTkButton(
            r_font,
            text="A+",
            width=36,
            height=26,
            corner_radius=6,
            font=cfg.font_bold,
            fg_color=cfg.c_primary,
            text_color=cfg.c_on_primary,
            command=self.increase_font
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            r_font,
            text="A-",
            width=36,
            height=26,
            corner_radius=6,
            font=cfg.font_bold,
            fg_color=cfg.c_btn,
            text_color=cfg.c_text,
            command=self.decrease_font
        ).pack(side="right")

        self.lbl_font_status = ctk.CTkLabel(
            r_font, text=self.var_font_scale.get(), font=cfg.font_small, text_color=cfg.c_primary
        )
        self.lbl_font_status.pack(side="right", padx=14)

        # 2. 自定义全景毛玻璃壁纸
        self._build_header(scroll_box, "自定义全景毛玻璃壁纸 (Frosted Glass Wallpaper)")
        grp_wp = self._create_group(scroll_box)

        r_wp = ctk.CTkFrame(grp_wp, fg_color="transparent")
        r_wp.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(r_wp, text="全景背景壁纸", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left")

        name = os.path.basename(self.var_wallpaper_path.get()) if self.var_wallpaper_path.get() else "未设置壁纸"
        self.lbl_wp_name = ctk.CTkLabel(r_wp, text=name, font=cfg.font_small, text_color=cfg.c_primary)
        self.lbl_wp_name.pack(side="left", padx=10)

        ctk.CTkButton(
            r_wp,
            text="清除壁纸",
            width=70,
            height=26,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn_del,
            hover_color=cfg.c_btn_del_hover,
            text_color=cfg.c_error,
            command=self.clear_wallpaper
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            r_wp,
            text="选择图片...",
            width=95,
            height=26,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.choose_wallpaper
        ).pack(side="right")

        r_blur = ctk.CTkFrame(grp_wp, fg_color="transparent")
        r_blur.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(r_blur, text="毛玻璃磨砂程度 (模糊半径)", font=cfg.font_normal, text_color=cfg.c_text).pack(side="left")

        self.lbl_blur_val = ctk.CTkLabel(
            r_blur, text=f"{self.var_wallpaper_blur.get()} px", font=cfg.font_bold, text_color=cfg.c_primary, width=50
        )
        self.lbl_blur_val.pack(side="right")

        self.slider_blur = ctk.CTkSlider(
            r_blur,
            from_=0,
            to=30,
            number_of_steps=30,
            variable=self.var_wallpaper_blur,
            width=220,
            button_color=cfg.c_primary,
            progress_color=cfg.c_primary,
            command=self.on_blur_change
        )
        self.slider_blur.pack(side="right", padx=10)

        r_op = ctk.CTkFrame(grp_wp, fg_color="transparent")
        r_op.pack(fill="x", padx=14, pady=(6, 10))
        ctk.CTkLabel(r_op, text="壁纸显示通透度 (磨砂通透率)", font=cfg.font_normal, text_color=cfg.c_text).pack(side="left")

        pct = int(self.var_wallpaper_opacity.get() * 100)
        self.lbl_opacity_val = ctk.CTkLabel(
            r_op, text=f"{pct}%", font=cfg.font_bold, text_color=cfg.c_primary, width=50
        )
        self.lbl_opacity_val.pack(side="right")

        self.slider_opacity = ctk.CTkSlider(
            r_op,
            from_=0.10,
            to=0.90,
            number_of_steps=80,
            variable=self.var_wallpaper_opacity,
            width=220,
            button_color=cfg.c_primary,
            progress_color=cfg.c_primary,
            command=self.on_opacity_change
        )
        self.slider_opacity.pack(side="right", padx=10)

        # 3. 硬件加速引擎
        self._build_header(scroll_box, "硬件加速引擎 (GPU Acceleration)")
        grp_gpu = self._create_group(scroll_box)

        r_gpu = ctk.CTkFrame(grp_gpu, fg_color="transparent")
        r_gpu.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(r_gpu, text="全平台 GPU 图形硬件加速", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left")
        ctk.CTkLabel(
            r_gpu,
            text="支持 NVIDIA / AMD Radeon / Intel Arc 硬件渲染管线",
            font=cfg.font_small,
            text_color=cfg.c_text_secondary
        ).pack(side="left", padx=10)

        self.sw_gpu = ctk.CTkSwitch(
            r_gpu, text="", variable=self.var_gpu, width=42, height=22, progress_color=cfg.c_primary, command=self.on_gpu_toggle
        )
        self.sw_gpu.pack(side="right")

        # 4. 微软必应翻译与语音服务
        self._build_header(scroll_box, "微软必应翻译与语音 (Microsoft Azure Cognitive Services)")
        grp_ms = self._create_group(scroll_box)

        r0 = ctk.CTkFrame(grp_ms, fg_color="transparent")
        r0.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(r0, text="查词与翻译引擎", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left")

        self.seg_engine = ctk.CTkSegmentedButton(
            r0,
            values=["AI 智能模型", "微软必应翻译"],
            variable=self.var_engine,
            font=cfg.font_normal,
            corner_radius=6,
            selected_color=cfg.c_primary,
            unselected_color=cfg.c_surface_variant,
            text_color=cfg.c_text,
            command=self.on_engine_change
        )
        self.seg_engine.pack(side="right")

        r1 = ctk.CTkFrame(grp_ms, fg_color="transparent")
        r1.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(r1, text="Translator API Key", font=cfg.font_normal, text_color=cfg.c_text, width=140, anchor="w").pack(side="left")
        ctk.CTkEntry(
            r1,
            textvariable=self.var_ms_key,
            show="*",
            placeholder_text="粘贴 Azure Translator 密钥",
            height=28,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(r1, text="Region", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(
            r1,
            textvariable=self.var_ms_region,
            placeholder_text="global 或 eastasia",
            width=100,
            height=28,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        ).pack(side="left")

        r2 = ctk.CTkFrame(grp_ms, fg_color="transparent")
        r2.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(r2, text="微软语音音色 (TTS)", font=cfg.font_normal, text_color=cfg.c_text, width=140, anchor="w").pack(side="left")

        ctk.CTkComboBox(
            r2,
            values=[
                "en-US-JennyNeural (美音·女声·自然)",
                "en-US-GuyNeural (美音·男声·沉稳)",
                "en-US-AriaNeural (美音·女声·新闻)",
                "en-GB-SoniaNeural (英音·女声·优雅)",
                "en-GB-RyanNeural (英音·男声·清脆)"
            ],
            variable=self.var_voice_name,
            width=260,
            height=28,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            dropdown_fg_color=cfg.c_surface,
            dropdown_text_color=cfg.c_text,
            font=cfg.font_normal,
            dropdown_font=cfg.font_normal
        ).pack(side="left")

        ctk.CTkButton(
            r2,
            text="🔊 试听发音",
            width=85,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.test_voice
        ).pack(side="left", padx=10)

        # 5. 关于软件与 GitHub 版本更新
        self._build_header(scroll_box, "关于与版本更新 (About & Software Update)")
        grp_about = self._create_group(scroll_box)

        r_about = ctk.CTkFrame(grp_about, fg_color="transparent")
        r_about.pack(fill="x", padx=14, pady=10)

        info_box = ctk.CTkFrame(r_about, fg_color="transparent")
        info_box.pack(side="left")

        ctk.CTkLabel(
            info_box, text=f"WordCrafter Pro · {CURRENT_VERSION}", font=cfg.font_bold, text_color=cfg.c_primary, anchor="w"
        ).pack(anchor="w")

        self.lbl_update_status = ctk.CTkLabel(
            info_box, text="开源 AI 双语伴读与情境背词工作台", font=cfg.font_small, text_color=cfg.c_text_secondary, anchor="w"
        )
        self.lbl_update_status.pack(anchor="w")

        btn_box = ctk.CTkFrame(r_about, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="🌐 GitHub 仓库",
            width=105,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=UpdateService.open_github_home
        ).pack(side="left", padx=(0, 8))

        self.btn_check_update = ctk.CTkButton(
            btn_box,
            text="⚡ 检查更新",
            width=95,
            height=28,
            corner_radius=6,
            font=cfg.font_bold,
            fg_color=cfg.c_primary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary,
            command=self.check_for_updates
        )
        self.btn_check_update.pack(side="left")

        # 自动保存变更监听
        self.var_ms_key.trace_add("write", lambda *args: self.save_ms_settings())
        self.var_ms_region.trace_add("write", lambda *args: self.save_ms_settings())
        self.var_speech_key.trace_add("write", lambda *args: self.save_ms_settings())
        self.var_speech_region.trace_add("write", lambda *args: self.save_ms_settings())
        self.var_voice_name.trace_add("write", lambda *args: self.save_ms_settings())

    def _build_header(self, parent, title):
        cfg = self.app_ref.config
        ctk.CTkLabel(parent, text=title, font=cfg.font_bold, text_color=cfg.c_primary, anchor="w").pack(
            fill="x", padx=14, pady=(14, 4)
        )

    def _create_group(self, parent):
        cfg = self.app_ref.config
        f = ctk.CTkFrame(parent, corner_radius=8, fg_color=cfg.c_input_bg, border_width=1, border_color=cfg.c_border)
        f.pack(fill="x", padx=14, pady=(0, 4))
        return f

    def _add_divider(self, parent):
        cfg = self.app_ref.config
        ctk.CTkFrame(parent, height=1, fg_color=cfg.c_border).pack(fill="x", padx=14, pady=2)

    def check_for_updates(self):
        self.btn_check_update.configure(state="disabled", text="正在检查...")
        self.lbl_update_status.configure(text="正在连接 GitHub 校验最新版本号...")

        def _on_result(status, data):
            self.after(0, self._handle_update_result, status, data)

        UpdateService.check_update_async(_on_result)

    def _handle_update_result(self, status, data):
        self.btn_check_update.configure(state="normal", text="⚡ 检查更新")
        if status == "update_available":
            self.lbl_update_status.configure(
                text=f"发现新版本: {data.get('tag')} (当前为 {CURRENT_VERSION})",
                text_color=self.app_ref.config.c_primary
            )
            UpdateDialog(self.winfo_toplevel(), self.app_ref, data)
        elif status == "latest":
            self.lbl_update_status.configure(
                text=f"✓ 当前已是最新版本 ({CURRENT_VERSION})",
                text_color=self.app_ref.config.c_success
            )
            messagebox.showinfo("检查更新", f"您使用的是最新版本 {CURRENT_VERSION}！")
        else:
            self.lbl_update_status.configure(
                text="✕ 无法连接到 GitHub 检查更新",
                text_color=self.app_ref.config.c_error
            )
            messagebox.showerror("网络错误", f"检查更新失败：\n{data}")

    def choose_wallpaper(self):
        path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
        if path:
            self.var_wallpaper_path.set(path)
            self.lbl_wp_name.configure(text=os.path.basename(path))
            self.app_ref.config.config_repo.save_all({"wallpaper_path": path})
            self.app_ref.update_wallpaper_source()

    def clear_wallpaper(self):
        self.var_wallpaper_path.set("")
        self.lbl_wp_name.configure(text="未设置壁纸")
        self.app_ref.config.config_repo.save_all({"wallpaper_path": ""})
        self.app_ref.update_wallpaper_source()

    def on_blur_change(self, val):
        b_val = int(val)
        self.lbl_blur_val.configure(text=f"{b_val} px")
        self.app_ref.config.config_repo.save_all({"wallpaper_blur": b_val})
        self.app_ref.render_frosted_wallpaper()

    def on_opacity_change(self, val):
        self.lbl_opacity_val.configure(text=f"{int(val * 100)}%")
        self.app_ref.config.config_repo.save_all({"wallpaper_opacity": round(val, 2)})
        self.app_ref.render_frosted_wallpaper()

    def on_gpu_toggle(self):
        val = self.var_gpu.get()
        self.app_ref.config.config_repo.save_all({"gpu_acceleration": val})
        self.app_ref.config.apply_gpu_acceleration()
        state = "已开启 (硬件管线就绪)" if val else "已关闭"
        messagebox.showinfo("GPU 加速", f"图形硬件加速 {state}。")

    def increase_font(self):
        scales = ["精小 (90%)", "标准 (100%)", "放大 (112%)", "特大 (125%)"]
        curr = self.var_font_scale.get()
        idx = scales.index(curr) if curr in scales else 1
        if idx < len(scales) - 1:
            new_scale = scales[idx + 1]
            self.var_font_scale.set(new_scale)
            self.lbl_font_status.configure(text=new_scale)
            self.app_ref.config.config_repo.save_all({"font_size_scale": new_scale})
            self.app_ref.config.update_font_metrics()
            messagebox.showinfo("字号已调整", f"全局字号已放大至：{new_scale}\n重启软件后各主视图将完全以新字号渲染。")

    def decrease_font(self):
        scales = ["精小 (90%)", "标准 (100%)", "放大 (112%)", "特大 (125%)"]
        curr = self.var_font_scale.get()
        idx = scales.index(curr) if curr in scales else 1
        if idx > 0:
            new_scale = scales[idx - 1]
            self.var_font_scale.set(new_scale)
            self.lbl_font_status.configure(text=new_scale)
            self.app_ref.config.config_repo.save_all({"font_size_scale": new_scale})
            self.app_ref.config.update_font_metrics()
            messagebox.showinfo("字号已调整", f"全局字号已缩小至：{new_scale}\n重启软件后各主视图将完全以新字号渲染。")

    def on_engine_change(self, val):
        self.app_ref.config.config_repo.save_all({"translate_engine": val})

    def save_ms_settings(self):
        raw_voice = self.var_voice_name.get().split(" ")[0]
        self.app_ref.config.config_repo.save_all({
            "ms_translator_key": self.var_ms_key.get().strip(),
            "ms_translator_region": self.var_ms_region.get().strip() or "global",
            "ms_speech_key": self.var_speech_key.get().strip(),
            "ms_speech_region": self.var_speech_region.get().strip() or "eastasia",
            "ms_voice_name": raw_voice
        })

    def test_voice(self):
        raw_voice = self.var_voice_name.get().split(" ")[0]
        MicrosoftSpeechService.speak_async(
            "Serendipity and persist.",
            self.var_speech_key.get().strip(),
            self.var_speech_region.get().strip(),
            raw_voice
        )

    def on_theme_change(self, val):
        self.app_ref.config.config_repo.save_all({"appearance_mode": val})
        ctk.set_appearance_mode(self.app_ref.config.appearance_mode)
        self.app_ref.render_frosted_wallpaper()