from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk, messagebox

BASE = Path(__file__).resolve().parent
ASSETS_DIR = BASE / "assets"
GEN = BASE / "generate_words.py"
CHECK = BASE / "tg_fragment_username_checker.py"
PAUSE_FILE = BASE / ".checker_paused"
STOP_FILE = BASE / ".checker_stop"
CONFIGS_DIR = BASE / "configs"
VENV_PY = BASE / ".venv" / "Scripts" / "python.exe"
VISUALIZER_INTERVAL_MS = 1500
VISUALIZER_SAMPLES = 45
VISUALIZER_AMPLIFY = 1.5

LATEST_CONFIG_PATH = CONFIGS_DIR / "latest.json"
GITHUB_URL = "https://github.com/S3lfuve"
GITHUB_ICON_PNG = ASSETS_DIR / "github-mark.png"

TRANSLATIONS = {
    "ru": {
        "tab_generator": "Генератор",
        "tab_check": "Подбор",
        "tab_config": "Конфиг",
        "tab_settings": "Настройки",
        "action_generate": "Генерить",
        "action_start": "Старт",
        "action_continue": "Продолжить",
        "action_stop": "Стоп",
        "action_pause": "Пауза",
        "action_clear_log": "Очистить лог",
        "action_folder": "Папка",
        "settings_title": "Настройки интерфейса",
        "settings_language": "Язык",
        "settings_debug": "Режим отладки",
        "settings_autosave": "Автосохранять настройки в latest.json",
        "language_ru": "Русский",
        "language_en": "Английский",
        "generator_output": "Вывод",
        "generator_words": "Слова",
        "generator_advanced": "Дополнительно",
        "field_file": "файл",
        "field_count": "кол-во",
        "field_quality": "качество",
        "field_length": "длина",
        "field_words_in_username": "слов в юзернейме",
        "field_scan": "скан",
        "field_seed": "сид",
        "field_prefix": "префикс",
        "field_suffix": "суффикс",
        "field_wordlist": "список",
        "field_workers": "воркеры",
        "field_limit": "лимит",
        "field_delay": "задержка",
        "generator_mode": "Режим",
        "generator_mode_english_words": "Англ. слова",
        "generator_mode_translit": "Транслит",
        "generator_mode_random_letters": "Случайные буквы",
        "generator_add_articles": "Артикли",
        "generator_dedupe_letters": "Убрать дубли букв",
        "generator_delete_file": "Удалить файл",
        "log_continue_check": "Продолжаю проверку.",
        "log_stopping_check": "Останавливаю проверку...",
        "check_order": "Порядок проверки",
        "check_order_in_order": "По порядку",
        "check_order_random": "Случайно",
        "check_order_short_first": "Сначала короткие",
        "check_order_long_first": "Сначала длинные",
        "check_checks": "Проверки",
        "check_output": "Вывод",
        "check_export_found": "Экспорт FREE в found.txt",
        "check_hide_busy": "Скрывать BUSY",
        "check_delete_found": "Удалить found.txt",
        "warning_reserved": "Предупреждение: Программа может ошибочно помечать зарезервированные платформой юзернеймы как свободные, требуется ручная проверка",
        "config_save_group": "Сохранить конфиг",
        "config_name": "Название",
        "config_save": "Сохранить",
        "config_load_group": "Загрузить конфиг",
        "config_existing": "Существующие",
        "config_refresh": "Обновить",
        "config_load": "Загрузить",
        "config_empty_title": "Пустое имя",
        "config_empty_message": "Введи название конфига",
        "config_missing_title": "Нет конфига",
        "config_missing_message": "Выбери существующий конфиг",
        "config_saved": "Конфиг сохранен",
        "config_loaded": "Конфиг загружен",
        "config_save_failed": "Не смог сохранить конфиг",
        "config_load_failed": "Не смог загрузить конфиг",
        "config_note": "Конфиг хранит все настройки вкладок Генератор, Подбор и Settings, кроме путей words.txt и found.txt.",
        "tip_output_file": "Куда сохранить список. При генерации файл будет перезаписан.",
        "tip_output_count": "Сколько юзернеймов сохранить в файл.",
        "tip_quality": "Насколько редкими должны быть отдельные слова: 1 = частые вроде error, 5 = редкие вроде bouquet.",
        "tip_length": "Итоговая длина всего юзернейма, включая prefix/suffix и все склеенные слова.",
        "tip_words_in_username": "Сколько слов склеивать в один юзернейм. Например, 3..3 = всегда ровно три слова.",
        "tip_generator_mode": "Англ. слова = английские слова из wordfreq. Транслит = русские слова, переведенные в латиницу. Случайные буквы = случайные строки a-z без словаря.",
        "tip_add_articles": "Пытается добавлять a/an/the в начало или между словами, например thegrave или reaperthegrave.",
        "tip_dedupe_letters": "Сжимает повторяющиеся буквы внутри каждого отдельного слова до склейки: spontannyh -> spontanyh. Границы между словами не трогает.",
        "tip_scan": "Сколько слов взять из wordfreq на перебор. Больше scan = больше вариантов, но генерация медленнее.",
        "tip_seed": "Фиксирует случайность. Один и тот же seed дает повторяемый результат.",
        "tip_prefix": "Текст, который будет добавляться в начало каждого юзернейма.",
        "tip_suffix": "Текст, который будет добавляться в конец каждого юзернейма.",
        "tip_wordlist": "Файл со словами или готовыми юзернеймами для проверки.",
        "tip_workers": "Сколько запросов запускать параллельно. Слишком большое значение чаще упирается в лимиты.",
        "tip_limit": "Сколько строк проверить. 0 означает проверить весь файл.",
        "tip_delay": "Небольшая случайная пауза между запросами на каждом worker, чтобы реже ловить лимиты.",
        "tip_check_order": "В каком порядке обходить список: как в файле, случайно, от коротких к длинным или наоборот.",
    },
    "en": {
        "tab_generator": "Generator",
        "tab_check": "Checker",
        "tab_config": "Config",
        "tab_settings": "Settings",
        "action_generate": "Generate",
        "action_start": "Start",
        "action_continue": "Continue",
        "action_stop": "Stop",
        "action_pause": "Pause",
        "action_clear_log": "Clear log",
        "action_folder": "Folder",
        "settings_title": "Interface settings",
        "settings_language": "Language",
        "settings_debug": "Debug mode",
        "settings_autosave": "Autosave settings to latest.json",
        "language_ru": "Russian",
        "language_en": "English",
        "generator_output": "Output",
        "generator_words": "Words",
        "generator_advanced": "Advanced",
        "field_file": "file",
        "field_count": "count",
        "field_quality": "quality",
        "field_length": "length",
        "field_words_in_username": "words in username",
        "field_scan": "scan",
        "field_seed": "seed",
        "field_prefix": "prefix",
        "field_suffix": "suffix",
        "field_wordlist": "wordlist",
        "field_workers": "workers",
        "field_limit": "limit",
        "field_delay": "delay",
        "generator_mode": "Mode",
        "generator_mode_english_words": "English words",
        "generator_mode_translit": "Translit",
        "generator_mode_random_letters": "Random letters",
        "generator_add_articles": "Articles",
        "generator_dedupe_letters": "Remove duplicate letters",
        "generator_delete_file": "Delete file",
        "log_continue_check": "Continuing check.",
        "log_stopping_check": "Stopping check...",
        "check_order": "Check order",
        "check_order_in_order": "In order",
        "check_order_random": "Random",
        "check_order_short_first": "Shortest first",
        "check_order_long_first": "Longest first",
        "check_checks": "Checks",
        "check_output": "Output",
        "check_export_found": "Export FREE to found.txt",
        "check_hide_busy": "Hide BUSY",
        "check_delete_found": "Delete found.txt",
        "warning_reserved": "Warning: The program may mistakenly mark platform-reserved usernames as free. Manual verification is required.",
        "config_save_group": "Save config",
        "config_name": "Name",
        "config_save": "Save",
        "config_load_group": "Load config",
        "config_existing": "Existing",
        "config_refresh": "Refresh",
        "config_load": "Load",
        "config_empty_title": "Empty name",
        "config_empty_message": "Enter a config name",
        "config_missing_title": "No config",
        "config_missing_message": "Select an existing config",
        "config_saved": "Config saved",
        "config_loaded": "Config loaded",
        "config_save_failed": "Could not save config",
        "config_load_failed": "Could not load config",
        "config_note": "The config stores settings for the Generator, Checker, and Settings tabs, except the words.txt and found.txt paths.",
        "tip_output_file": "Where to save the generated list. The file will be overwritten on each run.",
        "tip_output_count": "How many usernames to save to the file.",
        "tip_quality": "How rare each individual word should be: 1 = common words like error, 5 = rarer ones like bouquet.",
        "tip_length": "The total username length, including any prefix, suffix, and all combined words.",
        "tip_words_in_username": "How many words to combine into one username. For example, 3..3 always produces exactly three words.",
        "tip_generator_mode": "English words uses the English wordfreq list. Translit uses Russian words converted to Latin letters. Random letters generates plain a-z strings with no dictionary.",
        "tip_add_articles": "Tries to add a/an/the at the start or between words, for example thegrave or reaperthegrave.",
        "tip_dedupe_letters": "Collapses repeated letters inside each source word before joining, for example spontannyh -> spontanyh. Word boundaries stay untouched.",
        "tip_scan": "How many wordfreq entries to scan. Higher scan values give you more options, but generation takes longer.",
        "tip_seed": "Locks the randomizer. Using the same seed gives you repeatable output.",
        "tip_prefix": "Text to prepend to every generated username.",
        "tip_suffix": "Text to append to every generated username.",
        "tip_wordlist": "The file containing words or ready-made usernames to check.",
        "tip_workers": "How many requests to run in parallel. Setting this too high makes rate limits more likely.",
        "tip_limit": "How many lines to check. 0 means the whole file.",
        "tip_delay": "Adds a small randomized pause between requests on each worker so rate limits trigger less often.",
        "tip_check_order": "How to walk through the list: keep file order, shuffle it, start with shorter names, or start with longer ones.",
    },
}

DEFAULT_PALETTE = {
    "window_bg": "#f0f0f0",
    "surface_bg": "#f0f0f0",
    "text": "#000000",
    "muted": "#555555",
    "input_bg": "#ffffff",
    "input_fg": "#000000",
    "log_bg": "#111111",
    "log_fg": "#dddddd",
    "visual_bg": "#000000",
    "visual_border": "#2d2d2d",
    "warning": "#666666",
}


def launcher_python() -> str:
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        py = exe.with_name("python.exe")
        if py.exists():
            return str(py)
    return sys.executable


def real_python() -> str:
    if VENV_PY.exists():
        return str(VENV_PY)
    return launcher_python()


class ToolTip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.hermes_tooltip = self
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + 22
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=self.text,
            justify="left",
            bg="#fff8c6",
            fg="#111",
            relief="solid",
            borderwidth=1,
            padx=7,
            pady=4,
            wraplength=360,
        )
        label.pack()

    def hide(self, _event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class RangeSlider(ttk.Frame):
    def __init__(self, parent, label: str, min_value: int, max_value: int, left_var: tk.IntVar, right_var: tk.IntVar, width: int = 292, tip: str = "", label_key: str | None = None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.left_var = left_var
        self.right_var = right_var
        self.width = width
        self.pad = 18
        self.active = None
        self.enabled = True
        self.label_key = label_key
        self.tooltip = None

        head = ttk.Frame(self)
        head.grid(row=0, column=0, sticky="ew")
        self.title_label = ttk.Label(head, text=label)
        self.title_label.pack(side="left")
        if tip:
            q = ttk.Label(head, text=" ? ", foreground="#236ad8", cursor="question_arrow")
            q.pack(side="left")
            self.tooltip = ToolTip(q, tip)
        self.value_label = ttk.Label(head, width=12, anchor="e")
        self.value_label.pack(side="right")

        self.canvas = tk.Canvas(self, width=width, height=56, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="ew", pady=(1, 0))

        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", lambda _e: setattr(self, "active", None))
        self.left_var.trace_add("write", lambda *_: self.draw())
        self.right_var.trace_add("write", lambda *_: self.draw())
        self.draw()

    def _x_for_value(self, value: int) -> float:
        span = self.max_value - self.min_value
        return self.pad + (value - self.min_value) / span * (self.width - self.pad * 2)

    def _value_for_x(self, x: float) -> int:
        x = min(max(x, self.pad), self.width - self.pad)
        span = self.max_value - self.min_value
        raw = self.min_value + (x - self.pad) / (self.width - self.pad * 2) * span
        return int(round(raw))

    def _click(self, event):
        if not self.enabled:
            return
        lx = self._x_for_value(self.left_var.get())
        rx = self._x_for_value(self.right_var.get())
        if self.left_var.get() == self.right_var.get():
            self.active = "right" if event.x >= rx else "left"
        else:
            self.active = "left" if abs(event.x - lx) <= abs(event.x - rx) else "right"
        self._drag(event)

    def _drag(self, event):
        if not self.enabled:
            return
        value = self._value_for_x(event.x)
        if self.active == "left":
            self.left_var.set(min(value, self.right_var.get()))
        else:
            self.right_var.set(max(value, self.left_var.get()))
        self.draw()

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self.draw()

    def set_tip(self, text: str):
        if self.tooltip:
            self.tooltip.text = text

    def draw(self):
        left = max(self.min_value, min(self.left_var.get(), self.max_value))
        right = max(left, min(self.right_var.get(), self.max_value))
        if left != self.left_var.get():
            self.left_var.set(left)
            return
        if right != self.right_var.get():
            self.right_var.set(right)
            return

        c = self.canvas
        c.delete("all")
        y = 22
        lx = self._x_for_value(left)
        rx = self._x_for_value(right)
        base_fill = "#d0d0d0" if self.enabled else "#e2e2e2"
        active_fill = "#4d8cff" if self.enabled else "#bdbdbd"
        knob_fill = "#ffffff" if self.enabled else "#f1f1f1"
        knob_outline = "#236ad8" if self.enabled else "#b3b3b3"
        text_fill = "#333" if self.enabled else "#9a9a9a"
        label_fg = "#000000" if self.enabled else "#9a9a9a"
        c.create_line(self.pad, y, self.width - self.pad, y, width=5, fill=base_fill, capstyle="round")
        c.create_line(lx, y, rx, y, width=5, fill=active_fill, capstyle="round")
        for x, v in ((lx, left), (rx, right)):
            c.create_oval(x - 8, y - 8, x + 8, y + 8, fill=knob_fill, outline=knob_outline, width=2)
            c.create_text(x, y + 24, text=str(v), fill=text_fill, anchor="center")
        self.title_label.configure(foreground=label_fg)
        self.value_label.configure(foreground=text_fill)
        self.value_label.config(text=f"{left}..{right}")

    def set_label(self, text: str):
        self.title_label.config(text=text)


class PulseVisualizer(tk.Frame):
    def __init__(self, parent, stats_var: tk.StringVar):
        super().__init__(parent, bg="#000000", highlightbackground="#1f1f1f", highlightthickness=1)
        top = tk.Frame(self, bg="#000000")
        top.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(top, text="", bg="#000000").pack(side="left")
        self.stats_label = tk.Label(top, textvariable=stats_var, bg="#000000", fg="#f5f5f5", font=("Segoe UI", 10, "bold"))
        self.stats_label.pack(side="right")
        self.canvas = tk.Canvas(self, height=110, bg="#000000", highlightthickness=0, bd=0)
        self.canvas.pack(fill="x", expand=True, padx=8, pady=(0, 8))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TG Names Roller")
        self.geometry("760x620")
        self.minsize(700, 560)
        self.style = ttk.Style(self)
        CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        self.q: queue.Queue[str] = queue.Queue()
        self.proc: subprocess.Popen | None = None
        self._vars()
        self._ui()
        self.load_latest_config()
        self.apply_language()
        self.apply_theme()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(VISUALIZER_INTERVAL_MS, self._animate_visualizer)
        self.after(100, self._drain_log)
        self.after(350, self.ensure_deps_on_start)

    def _vars(self):
        self.out_file = tk.StringVar(value="words.txt")
        self.count = tk.StringVar(value="200")
        self.min_quality = tk.IntVar(value=1)
        self.max_quality = tk.IntVar(value=5)
        self.min_len = tk.IntVar(value=5)
        self.max_len = tk.IntVar(value=10)
        self.min_words = tk.IntVar(value=1)
        self.max_words = tk.IntVar(value=1)
        self.generator_mode = tk.StringVar(value="english_words")
        self.add_articles = tk.BooleanVar(value=False)
        self.dedupe_letters = tk.BooleanVar(value=False)
        self.prefix = tk.StringVar(value="")
        self.suffix = tk.StringVar(value="")
        self.scan = tk.StringVar(value="200000")
        self.seed = tk.StringVar(value="")
        self.wordlist = tk.StringVar(value="words.txt")
        self.workers = tk.StringVar(value="10")
        self.limit = tk.StringVar(value="0")
        self.delay = tk.StringVar(value="0.2")
        self.check_order = tk.StringVar(value="По порядку")
        self.check_tme = tk.BooleanVar(value=True)
        self.check_fragment = tk.BooleanVar(value=True)
        self.check_instagram = tk.BooleanVar(value=False)
        self.check_x = tk.BooleanVar(value=False)
        self.check_tiktok = tk.BooleanVar(value=False)
        self.check_youtube = tk.BooleanVar(value=False)
        self.check_github = tk.BooleanVar(value=False)
        self.export_found = tk.BooleanVar(value=False)
        self.hide_busy = tk.BooleanVar(value=False)
        self.config_name = tk.StringVar(value="")
        self.selected_config = tk.StringVar(value="")
        self.ui_language = tk.StringVar(value="ru")
        self.debug_mode = tk.BooleanVar(value=False)
        self.autosave_latest = tk.BooleanVar(value=True)
        self.progress_text = tk.StringVar(value="Checked: 0/0   found: 0")
        self.progress_total = 0
        self.progress_checked = 0
        self.progress_found = 0
        self.free_busy_text = tk.StringVar(value="FREE: 0%   BUSY: 0%")
        self.visualizer_samples = [0.0] * VISUALIZER_SAMPLES
        self.visualizer_colors = ["#f5f5f5"] * VISUALIZER_SAMPLES
        self.visualizer_level = 0.0
        self.visualizer_target = 0.0
        self.visualizer_free = 0
        self.visualizer_busy = 0
        self.visualizer_current_color = "#f5f5f5"
        self.paused = False
        self.check_running = False
        self.github_icon_image = None
        self.field_labels: dict[str, ttk.Label] = {}
        self.generator_sliders: dict[str, RangeSlider] = {}
        self.localized_tooltips: dict[str, object] = {}

    def tr(self, key: str) -> str:
        lang = self._serialize_ui_language()
        return TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)

    def current_palette(self) -> dict:
        return DEFAULT_PALETTE

    def check_order_labels(self) -> dict[str, str]:
        return {
            "in_order": self.tr("check_order_in_order"),
            "random": self.tr("check_order_random"),
            "short_first": self.tr("check_order_short_first"),
            "long_first": self.tr("check_order_long_first"),
        }

    def check_order_value(self) -> str:
        labels = self.check_order_labels()
        reverse = {label: value for value, label in labels.items()}
        current = self.check_order.get().strip()
        return reverse.get(current, current if current in labels else "in_order")

    def set_check_order_from_value(self, value: str):
        labels = self.check_order_labels()
        self.check_order.set(labels.get(value, labels["in_order"]))

    def _ui(self):
        root = ttk.Frame(self, padding=8)
        root.pack(fill="both", expand=True)
        self.root_frame = root
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="x")
        gen_tab = ttk.Frame(self.tabs, padding=8)
        check_tab = ttk.Frame(self.tabs, padding=8)
        config_tab = ttk.Frame(self.tabs, padding=8)
        settings_tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(gen_tab, text=self.tr("tab_generator"))
        self.tabs.add(check_tab, text=self.tr("tab_check"))
        self.tabs.add(config_tab, text=self.tr("tab_config"))
        self.tabs.add(settings_tab, text=self.tr("tab_settings"))
        self.tab_refs = {
            "tab_generator": gen_tab,
            "tab_check": check_tab,
            "tab_config": config_tab,
            "tab_settings": settings_tab,
        }
        self._gen_tab(gen_tab)
        self._check_tab(check_tab)
        self._config_tab(config_tab)
        self._settings_tab(settings_tab)
        self.tabs.bind("<<NotebookTabChanged>>", lambda _e: self.update_action_bar())
        bar = ttk.Frame(root)
        bar.pack(fill="x", pady=(6, 4))
        self.gen_btn = ttk.Button(bar, text=self.tr("action_generate"), command=self.generate_words)
        self.start_btn = ttk.Button(bar, text=self.tr("action_start"), command=self.start_or_continue_check)
        self.stop_btn = ttk.Button(bar, text=self.tr("action_stop"), command=self.stop_proc)
        self.pause_btn = ttk.Button(bar, text=self.tr("action_pause"), command=self.pause_check)
        self.clear_btn = ttk.Button(bar, text=self.tr("action_clear_log"), command=self.clear_log)
        self.progress_label = ttk.Label(bar, textvariable=self.progress_text, anchor="w")
        self.folder_btn = ttk.Button(bar, text=self.tr("action_folder"), command=self.open_folder)
        self.gen_btn.pack(side="left")
        self.stop_btn.pack(side="left", padx=(5, 0))
        self.pause_btn.pack(side="left", padx=(5, 0))
        self.start_btn.pack(side="left", padx=(5, 0))
        self.clear_btn.pack(side="left", padx=5)
        self.progress_label.pack(side="left", padx=(10, 0))
        self.folder_btn.pack(side="right")
        self.update_action_bar()
        self.log = tk.Text(root, height=10, wrap="word", bg="#111", fg="#ddd", insertbackground="#ddd", relief="flat", borderwidth=1)
        self.log.tag_configure("free", foreground="#4ade80")
        self.log.tag_configure("busy", foreground="#ff5c5c")
        self.log.tag_configure("warn", foreground="#facc15")
        self.log.pack(fill="both", expand=True)
        self.log_line("Библиотеки установлены.\n")

    def _help_label(self, parent, text: str = "", tip_key: str | None = None):
        q = ttk.Label(parent, text=" ? ", foreground="#236ad8", cursor="question_arrow")
        tooltip = ToolTip(q, self.tr(tip_key) if tip_key else text)
        if tip_key:
            self.localized_tooltips[tip_key] = tooltip
        return q

    def _row(self, parent, r, c, label, var, width=12, tip: str = "", tip_key: str | None = None):
        box = ttk.Frame(parent)
        box.grid(row=r, column=c, sticky="w", padx=(0, 4), pady=3)
        label_widget = ttk.Label(box, text=self.tr(f"field_{label}"))
        label_widget.pack(side="left")
        self.field_labels[label] = label_widget
        if tip or tip_key:
            self._help_label(box, tip, tip_key=tip_key).pack(side="left")
        ent = ttk.Entry(parent, textvariable=var, width=width)
        ent.grid(row=r, column=c + 1, sticky="ew", padx=(0, 12), pady=3)
        return ent

    def clear_log(self):
        self.log.delete("1.0", "end")
        self._reset_visualizer()

    def update_action_bar(self):
        if not hasattr(self, "gen_btn"):
            return
        for btn in (self.gen_btn, self.start_btn, self.stop_btn, self.pause_btn, self.clear_btn):
            btn.pack_forget()
        self.progress_label.pack_forget()
        current = self.tabs.select() if hasattr(self, "tabs") else ""
        generator_tab = str(self.tab_refs.get("tab_generator")) if hasattr(self, "tab_refs") else ""
        config_tab = str(self.tab_refs.get("tab_config")) if hasattr(self, "tab_refs") else ""
        settings_tab = str(self.tab_refs.get("tab_settings")) if hasattr(self, "tab_refs") else ""
        if current == generator_tab:
            self.gen_btn.pack(side="left")
            if self.proc and self.proc.poll() is None:
                self.stop_btn.pack(side="left", padx=(5, 0))
            self.clear_btn.pack(side="left", padx=5)
            return

        if current in {config_tab, settings_tab}:
            self.clear_btn.pack(side="left", padx=5)
            return

        if self.check_running:
            self.stop_btn.pack(side="left")
            if self.paused:
                self.start_btn.config(text=self.tr("action_continue"))
                self.start_btn.pack(side="left", padx=(5, 0))
            else:
                self.pause_btn.pack(side="left", padx=(5, 0))
        else:
            self.start_btn.config(text=self.tr("action_start"))
            self.start_btn.pack(side="left")
        self.clear_btn.pack(side="left", padx=5)
        self.progress_label.pack(side="left", padx=(10, 0))

    def _gen_tab(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

        output = ttk.LabelFrame(tab, text=self.tr("generator_output"), padding=8)
        output.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.generator_output_frame = output
        output.columnconfigure(1, weight=1)
        self._row(output, 0, 0, "file", self.out_file, width=24, tip_key="tip_output_file")
        self._row(output, 0, 2, "count", self.count, width=10, tip_key="tip_output_count")
        self.delete_words_btn = ttk.Button(output, text=self.tr("generator_delete_file"), command=self.delete_words_file)
        self.delete_words_btn.grid(row=1, column=0, sticky="w", pady=(5, 0))

        words = ttk.LabelFrame(tab, text=self.tr("generator_words"), padding=8)
        words.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.generator_words_frame = words
        self.quality_slider = RangeSlider(words, self.tr("field_quality"), 1, 5, self.min_quality, self.max_quality, tip=self.tr("tip_quality"), label_key="field_quality")
        self.quality_slider.grid(row=0, column=0, sticky="w")
        self.length_slider = RangeSlider(words, self.tr("field_length"), 5, 32, self.min_len, self.max_len, tip=self.tr("tip_length"), label_key="field_length")
        self.length_slider.grid(row=0, column=1, sticky="w", padx=(18, 0))
        self.words_slider = RangeSlider(words, self.tr("field_words_in_username"), 1, 10, self.min_words, self.max_words, tip=self.tr("tip_words_in_username"), label_key="field_words_in_username")
        self.words_slider.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.generator_sliders = {
            "field_quality": self.quality_slider,
            "field_length": self.length_slider,
            "field_words_in_username": self.words_slider,
        }
        opts = ttk.Frame(words)
        opts.grid(row=1, column=1, sticky="w", padx=(18, 0), pady=(6, 0))
        self.generator_mode_label = ttk.Label(opts, text=self.tr("generator_mode"))
        self.generator_mode_label.grid(row=0, column=0, sticky="w")
        self.generator_mode_english = ttk.Radiobutton(opts, text=self.tr("generator_mode_english_words"), variable=self.generator_mode, value="english_words", command=self._update_generator_mode_ui)
        self.generator_mode_english.grid(row=1, column=0, sticky="w")
        self.generator_mode_translit = ttk.Radiobutton(opts, text=self.tr("generator_mode_translit"), variable=self.generator_mode, value="translit", command=self._update_generator_mode_ui)
        self.generator_mode_translit.grid(row=2, column=0, sticky="w")
        self.generator_mode_random = ttk.Radiobutton(opts, text=self.tr("generator_mode_random_letters"), variable=self.generator_mode, value="random_letters", command=self._update_generator_mode_ui)
        self.generator_mode_random.grid(row=3, column=0, sticky="w")
        self._help_label(opts, tip_key="tip_generator_mode").grid(row=0, column=1, rowspan=4, sticky="nw", padx=(8, 0))
        self.articles_check = ttk.Checkbutton(opts, text=self.tr("generator_add_articles"), variable=self.add_articles)
        self.articles_check.grid(row=4, column=0, sticky="w", pady=(4, 0))
        self._help_label(opts, tip_key="tip_add_articles").grid(row=4, column=1, sticky="w")
        self.dedupe_check = ttk.Checkbutton(opts, text=self.tr("generator_dedupe_letters"), variable=self.dedupe_letters)
        self.dedupe_check.grid(row=5, column=0, sticky="w")
        self._help_label(opts, tip_key="tip_dedupe_letters").grid(row=5, column=1, sticky="w")

        advanced = ttk.LabelFrame(tab, text=self.tr("generator_advanced"), padding=8)
        advanced.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.generator_advanced_frame = advanced
        self._row(advanced, 0, 0, "scan", self.scan, width=12, tip_key="tip_scan")
        self._row(advanced, 0, 2, "seed", self.seed, width=12, tip_key="tip_seed")
        self._row(advanced, 1, 0, "prefix", self.prefix, width=16, tip_key="tip_prefix")
        self._row(advanced, 1, 2, "suffix", self.suffix, width=16, tip_key="tip_suffix")


    def _check_tab(self, tab):
        tab.columnconfigure(1, weight=1)
        self._row(tab, 0, 0, "wordlist", self.wordlist, width=24, tip_key="tip_wordlist")
        self._row(tab, 0, 2, "workers", self.workers, width=10, tip_key="tip_workers")
        self._row(tab, 1, 0, "limit", self.limit, width=10, tip_key="tip_limit")
        self._row(tab, 1, 2, "delay", self.delay, width=10, tip_key="tip_delay")
        order_box = ttk.Frame(tab)
        order_box.grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 4))
        self.check_order_label = ttk.Label(order_box, text=self.tr("check_order"))
        self.check_order_label.pack(side="left")
        self._help_label(order_box, tip_key="tip_check_order").pack(side="left")
        self.check_order_combo = ttk.Combobox(order_box, textvariable=self.check_order, values=list(self.check_order_labels().values()), width=20, state="readonly")
        self.check_order_combo.pack(side="left", padx=(8, 0))
        checks = ttk.LabelFrame(tab, text=self.tr("check_checks"), padding=8)
        checks.grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 4))
        self.checks_frame = checks
        ttk.Checkbutton(checks, text="check telegram", variable=self.check_tme).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(checks, text="check fragment (telegram)", variable=self.check_fragment).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(checks, text="instagram", variable=self.check_instagram).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(checks, text="x (twitter)", variable=self.check_x).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(checks, text="tiktok", variable=self.check_tiktok).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(checks, text="youtube", variable=self.check_youtube).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(checks, text="github", variable=self.check_github).pack(side="left")
        options = ttk.LabelFrame(tab, text=self.tr("check_output"), padding=8)
        options.grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 4))
        self.check_output_frame = options
        self.export_found_check = ttk.Checkbutton(options, text=self.tr("check_export_found"), variable=self.export_found)
        self.export_found_check.pack(side="left", padx=(0, 14))
        self.hide_busy_check = ttk.Checkbutton(options, text=self.tr("check_hide_busy"), variable=self.hide_busy)
        self.hide_busy_check.pack(side="left", padx=(0, 14))
        self.delete_found_btn = ttk.Button(options, text=self.tr("check_delete_found"), command=self.delete_found_file)
        self.delete_found_btn.pack(side="left")

        self.pulse_visualizer = PulseVisualizer(tab, self.free_busy_text)
        self.pulse_visualizer.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        self.pulse_visualizer.canvas.bind("<Configure>", lambda _e: self._draw_visualizer())
        self.warning_label = ttk.Label(tab, text=self.tr("warning_reserved"), wraplength=680, justify="left")
        self.warning_label.grid(row=6, column=0, columnspan=4, sticky="w", pady=(8, 0))

    def _config_tab(self, tab):
        tab.columnconfigure(0, weight=1)
        save_box = ttk.LabelFrame(tab, text=self.tr("config_save_group"), padding=8)
        save_box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        save_box.columnconfigure(1, weight=1)
        self.config_save_frame = save_box
        self.config_name_label = ttk.Label(save_box, text=self.tr("config_name"))
        self.config_name_label.grid(row=0, column=0, sticky="w")
        ttk.Entry(save_box, textvariable=self.config_name).grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.config_save_btn = ttk.Button(save_box, text=self.tr("config_save"), command=self.save_config)
        self.config_save_btn.grid(row=0, column=2, sticky="e")

        load_box = ttk.LabelFrame(tab, text=self.tr("config_load_group"), padding=8)
        load_box.grid(row=1, column=0, sticky="ew")
        load_box.columnconfigure(1, weight=1)
        self.config_load_frame = load_box
        self.config_existing_label = ttk.Label(load_box, text=self.tr("config_existing"))
        self.config_existing_label.grid(row=0, column=0, sticky="w")
        self.config_combo = ttk.Combobox(load_box, textvariable=self.selected_config, state="readonly")
        self.config_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.config_refresh_btn = ttk.Button(load_box, text=self.tr("config_refresh"), command=self.refresh_configs)
        self.config_refresh_btn.grid(row=0, column=2, sticky="e", padx=(0, 8))
        self.config_load_btn = ttk.Button(load_box, text=self.tr("config_load"), command=self.load_selected_config)
        self.config_load_btn.grid(row=0, column=3, sticky="e")

        note = ttk.Label(
            tab,
            text=self.tr("config_note"),
            foreground="#555",
            wraplength=620,
            justify="left",
        )
        note.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.config_note_label = note
        self.refresh_configs()
        self._update_generator_mode_ui()

    def _settings_tab(self, tab):
        tab.columnconfigure(0, weight=1)
        prefs = ttk.LabelFrame(tab, text=self.tr("settings_title"), padding=10)
        prefs.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        prefs.columnconfigure(1, weight=1)
        prefs.columnconfigure(2, weight=0)
        self.settings_frame = prefs
        self.settings_language_label = ttk.Label(prefs, text=self.tr("settings_language"))
        self.settings_language_label.grid(row=0, column=0, sticky="w")
        self.lang_combo = ttk.Combobox(prefs, textvariable=self.ui_language, state="readonly", values=["ru", "en"], width=16)
        self.lang_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 8))
        self.lang_combo.bind("<<ComboboxSelected>>", lambda _e: self.apply_language())

        self.settings_debug_check = ttk.Checkbutton(prefs, text=self.tr("settings_debug"), variable=self.debug_mode)
        self.settings_debug_check.grid(row=1, column=0, columnspan=2, sticky="w")
        self.settings_autosave_check = ttk.Checkbutton(prefs, text=self.tr("settings_autosave"), variable=self.autosave_latest)
        self.settings_autosave_check.grid(row=2, column=0, columnspan=2, sticky="w")

        self.github_badge = tk.Label(prefs, cursor="hand2", bd=0, highlightthickness=0)
        self.github_badge.grid(row=0, column=2, rowspan=3, sticky="ne", padx=(0, 12), pady=(14, 0))
        self.github_badge.bind("<Button-1>", lambda _e: self.open_github())
        self._load_github_icon()

    def _update_generator_mode_ui(self):
        random_mode = self.generator_mode.get() == "random_letters"
        if random_mode:
            self.add_articles.set(False)
        if hasattr(self, "quality_slider"):
            self.quality_slider.set_enabled(not random_mode)
        if hasattr(self, "words_slider"):
            self.words_slider.set_enabled(not random_mode)
        if hasattr(self, "articles_check"):
            self.articles_check.state(["disabled"] if random_mode else ["!disabled"])

    def apply_language(self):
        lang = self._serialize_ui_language()
        if lang not in TRANSLATIONS:
            lang = "ru"
        self.ui_language.set(lang)
        order_value = self.check_order_value()
        self.tabs.tab(self.tab_refs["tab_generator"], text=self.tr("tab_generator"))
        self.tabs.tab(self.tab_refs["tab_check"], text=self.tr("tab_check"))
        self.tabs.tab(self.tab_refs["tab_config"], text=self.tr("tab_config"))
        self.tabs.tab(self.tab_refs["tab_settings"], text=self.tr("tab_settings"))
        self.gen_btn.config(text=self.tr("action_generate"))
        self.stop_btn.config(text=self.tr("action_stop"))
        self.pause_btn.config(text=self.tr("action_pause"))
        self.clear_btn.config(text=self.tr("action_clear_log"))
        self.folder_btn.config(text=self.tr("action_folder"))
        self.settings_frame.config(text=self.tr("settings_title"))
        self.settings_language_label.config(text=self.tr("settings_language"))
        self.settings_debug_check.config(text=self.tr("settings_debug"))
        self.settings_autosave_check.config(text=self.tr("settings_autosave"))
        self.config_save_frame.config(text=self.tr("config_save_group"))
        self.config_name_label.config(text=self.tr("config_name"))
        self.config_save_btn.config(text=self.tr("config_save"))
        self.config_load_frame.config(text=self.tr("config_load_group"))
        self.config_existing_label.config(text=self.tr("config_existing"))
        self.config_refresh_btn.config(text=self.tr("config_refresh"))
        self.config_load_btn.config(text=self.tr("config_load"))
        self.warning_label.config(text=self.tr("warning_reserved"))
        self.config_note_label.config(text=self.tr("config_note"))
        self.generator_output_frame.config(text=self.tr("generator_output"))
        self.generator_words_frame.config(text=self.tr("generator_words"))
        self.generator_advanced_frame.config(text=self.tr("generator_advanced"))
        self.generator_mode_label.config(text=self.tr("generator_mode"))
        self.generator_mode_english.config(text=self.tr("generator_mode_english_words"))
        self.generator_mode_translit.config(text=self.tr("generator_mode_translit"))
        self.generator_mode_random.config(text=self.tr("generator_mode_random_letters"))
        self.articles_check.config(text=self.tr("generator_add_articles"))
        self.dedupe_check.config(text=self.tr("generator_dedupe_letters"))
        self.delete_words_btn.config(text=self.tr("generator_delete_file"))
        for key, widget in self.field_labels.items():
            widget.config(text=self.tr(f"field_{key}"))
        for key, slider in self.generator_sliders.items():
            slider.set_label(self.tr(key))
        for tip_key, tooltip in self.localized_tooltips.items():
            tooltip.text = self.tr(tip_key)
        self.quality_slider.set_tip(self.tr("tip_quality"))
        self.length_slider.set_tip(self.tr("tip_length"))
        self.words_slider.set_tip(self.tr("tip_words_in_username"))
        self.check_order_label.config(text=self.tr("check_order"))
        self.check_order_combo.config(values=list(self.check_order_labels().values()))
        self.set_check_order_from_value(order_value)
        self.checks_frame.config(text=self.tr("check_checks"))
        self.check_output_frame.config(text=self.tr("check_output"))
        self.export_found_check.config(text=self.tr("check_export_found"))
        self.hide_busy_check.config(text=self.tr("check_hide_busy"))
        self.delete_found_btn.config(text=self.tr("check_delete_found"))
        self.lang_combo["values"] = ["ru | " + self.tr("language_ru"), "en | " + self.tr("language_en")]
        self.lang_combo.set(f"{self.ui_language.get()} | {self.tr('language_ru' if self.ui_language.get() == 'ru' else 'language_en')}")
        self.update_action_bar()

    def _apply_palette_recursive(self, widget, palette: dict):
        try:
            if isinstance(widget, tk.Text):
                widget.configure(bg=palette["log_bg"], fg=palette["log_fg"], insertbackground=palette["log_fg"])
            elif isinstance(widget, tk.Label) and widget is not getattr(self, "github_badge", None):
                widget.configure(bg=palette["surface_bg"], fg=palette["text"])
            elif isinstance(widget, tk.Frame) and widget is not getattr(self, "pulse_visualizer", None):
                widget.configure(bg=palette["surface_bg"], highlightbackground=palette["visual_border"])
        except Exception:
            pass
        if widget is getattr(self, "pulse_visualizer", None):
            return
        for child in widget.winfo_children():
            self._apply_palette_recursive(child, palette)

    def apply_theme(self):
        palette = self.current_palette()
        self.configure(bg=palette["window_bg"])
        self.style.configure("TFrame", background=palette["surface_bg"])
        self.style.configure("TLabel", background=palette["surface_bg"], foreground=palette["text"])
        self.style.configure("TCheckbutton", background=palette["surface_bg"], foreground=palette["text"])
        self.style.configure("TRadiobutton", background=palette["surface_bg"], foreground=palette["text"])
        self.style.configure("TLabelframe", background=palette["surface_bg"], foreground=palette["text"])
        self.style.configure("TLabelframe.Label", background=palette["surface_bg"], foreground=palette["text"])
        self.style.configure("TEntry", fieldbackground=palette["input_bg"], foreground=palette["input_fg"], insertcolor=palette["input_fg"])
        self.style.configure("TCombobox", fieldbackground=palette["input_bg"], foreground=palette["input_fg"], arrowcolor=palette["text"])
        if hasattr(self, "root_frame"):
            self._apply_palette_recursive(self.root_frame, palette)
        self.log.configure(bg=palette["log_bg"], fg=palette["log_fg"], insertbackground=palette["log_fg"])
        self.log.tag_configure("free", foreground="#4ade80")
        self.log.tag_configure("busy", foreground="#ff5c5c")
        self.log.tag_configure("warn", foreground="#facc15")
        self.pulse_visualizer.configure(bg=palette["visual_bg"], highlightbackground=palette["visual_border"])
        self.pulse_visualizer.stats_label.configure(bg=palette["visual_bg"], fg="#f5f5f5")
        self.pulse_visualizer.canvas.configure(bg=palette["visual_bg"])
        self.warning_label.configure(foreground=palette["warning"])
        self.config_note_label.configure(foreground=palette["muted"])
        self.github_badge.configure(bg=palette["surface_bg"])
        self._draw_visualizer()

    def _load_github_icon(self):
        if GITHUB_ICON_PNG.exists():
            try:
                self.github_icon_image = tk.PhotoImage(file=str(GITHUB_ICON_PNG))
                self.github_badge.configure(image=self.github_icon_image, text="", width=self.github_icon_image.width(), height=self.github_icon_image.height())
                return
            except Exception:
                self.github_icon_image = None
        self.github_badge.configure(text="GitHub", font=("Segoe UI", 9), padx=4, pady=2)

    def _serialize_ui_language(self) -> str:
        return self.ui_language.get().split("|")[0].strip().lower()

    def save_latest_config(self):
        if not self.autosave_latest.get():
            return
        self.ui_language.set(self._serialize_ui_language())
        payload = self._config_payload()
        try:
            LATEST_CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self.q.put(f"Не смог сохранить latest.json: {type(e).__name__}: {e}\n")

    def load_latest_config(self):
        if not LATEST_CONFIG_PATH.exists():
            return
        try:
            self.apply_config(json.loads(LATEST_CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception as e:
            self.q.put(f"Не смог загрузить latest.json: {type(e).__name__}: {e}\n")

    def open_github(self):
        webbrowser.open(GITHUB_URL)

    def on_close(self):
        self.save_latest_config()
        self.destroy()

    def _rgb_to_hex(self, rgb: tuple[float, float, float]) -> str:
        return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(part)))) for part in rgb)

    def _mix_rgb(self, current: tuple[float, float, float], target: tuple[float, float, float], speed: float) -> tuple[float, float, float]:
        return tuple(current[i] + (target[i] - current[i]) * speed for i in range(3))

    def _update_free_busy_text(self):
        total = self.visualizer_free + self.visualizer_busy
        if total <= 0:
            self.free_busy_text.set("FREE: 0%   BUSY: 0%")
            return
        free_pct = round(self.visualizer_free * 100 / total)
        busy_pct = 100 - free_pct
        self.free_busy_text.set(f"FREE: {free_pct}%   BUSY: {busy_pct}%")

    def _update_visualizer_target(self):
        total = self.visualizer_free + self.visualizer_busy
        if total <= 0:
            self.visualizer_target = 0.0
            return
        free_ratio = self.visualizer_free / total
        busy_ratio = self.visualizer_busy / total
        balance = busy_ratio - free_ratio
        self.visualizer_target = max(-1.0, min(1.0, balance * VISUALIZER_AMPLIFY))

    def _reset_visualizer(self):
        self.visualizer_samples = [0.0] * VISUALIZER_SAMPLES
        self.visualizer_colors = ["#f5f5f5"] * VISUALIZER_SAMPLES
        self.visualizer_level = 0.0
        self.visualizer_target = 0.0
        self.visualizer_free = 0
        self.visualizer_busy = 0
        self.visualizer_current_color = "#f5f5f5"
        self._update_free_busy_text()
        self._draw_visualizer()

    def _feed_visualizer(self, status: str):
        if status == "free":
            self.visualizer_free += 1
            self.visualizer_current_color = "#4ade80"
        elif status == "busy":
            self.visualizer_busy += 1
            self.visualizer_current_color = "#ff3b4f"
        else:
            return
        self._update_free_busy_text()
        self._update_visualizer_target()
        self.visualizer_level = self.visualizer_target

    def _draw_visualizer(self):
        if not hasattr(self, "pulse_visualizer"):
            return
        canvas = self.pulse_visualizer.canvas
        width = max(8, canvas.winfo_width())
        height = max(32, canvas.winfo_height())
        mid = height / 2
        margin = 14
        canvas.delete("all")
        canvas.create_rectangle(0, 0, width, height, fill="#000000", outline="#000000")

        samples = self.visualizer_samples
        colors = self.visualizer_colors
        if len(samples) < 2:
            return
        max_offset = max(0.0, (height / 2) - margin)
        step = (width - margin * 2) / max(1, len(samples) - 1)
        points: list[tuple[float, float]] = []
        for i, level in enumerate(samples):
            y = mid + level * max_offset
            y = max(margin, min(height - margin, y))
            points.append((margin + i * step, y))

        prev_x, prev_y = points[0]
        prev_color = colors[0] if colors else "#f5f5f5"
        for i, (x, y) in enumerate(points[1:], start=1):
            current_color = colors[i] if i < len(colors) else prev_color
            canvas.create_line(prev_x, prev_y, x, prev_y, fill=prev_color, width=4, capstyle="butt", joinstyle="miter")
            if abs(y - prev_y) > 0.1:
                canvas.create_line(x, prev_y, x, y, fill=current_color, width=7, capstyle="butt", joinstyle="miter")
            prev_x, prev_y = x, y
            prev_color = current_color

    def _animate_visualizer(self):
        if self.paused:
            self.after(VISUALIZER_INTERVAL_MS, self._animate_visualizer)
            return
        if self.check_running:
            self.visualizer_samples.append(self.visualizer_level)
            self.visualizer_colors.append(self.visualizer_current_color)
            if len(self.visualizer_samples) > VISUALIZER_SAMPLES:
                self.visualizer_samples.pop(0)
            if len(self.visualizer_colors) > VISUALIZER_SAMPLES:
                self.visualizer_colors.pop(0)
        self._draw_visualizer()
        self.after(VISUALIZER_INTERVAL_MS, self._animate_visualizer)

    def _config_payload(self) -> dict:
        return {
            "version": 3,
            "generator": {
                "count": self.count.get(),
                "min_quality": self.min_quality.get(),
                "max_quality": self.max_quality.get(),
                "min_len": self.min_len.get(),
                "max_len": self.max_len.get(),
                "min_words": self.min_words.get(),
                "max_words": self.max_words.get(),
                "generator_mode": self.generator_mode.get(),
                "add_articles": self.add_articles.get(),
                "dedupe_letters": self.dedupe_letters.get(),
                "prefix": self.prefix.get(),
                "suffix": self.suffix.get(),
                "scan": self.scan.get(),
                "seed": self.seed.get(),
            },
            "check": {
                "workers": self.workers.get(),
                "limit": self.limit.get(),
                "delay": self.delay.get(),
                "check_order": self.check_order_value(),
                "check_tme": self.check_tme.get(),
                "check_fragment": self.check_fragment.get(),
                "check_instagram": self.check_instagram.get(),
                "check_x": self.check_x.get(),
                "check_tiktok": self.check_tiktok.get(),
                "check_youtube": self.check_youtube.get(),
                "check_github": self.check_github.get(),
                "export_found": self.export_found.get(),
                "hide_busy": self.hide_busy.get(),
            },
            "ui": {
                "language": self._serialize_ui_language(),
                "debug_mode": self.debug_mode.get(),
                "autosave_latest": self.autosave_latest.get(),
            },
        }

    def _sanitize_config_name(self, raw_name: str) -> str:
        name = raw_name.strip()
        name = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in name)
        name = name.strip(" .")
        return name

    def _config_path(self, raw_name: str) -> Path | None:
        name = self._sanitize_config_name(raw_name)
        if not name:
            return None
        return CONFIGS_DIR / f"{name}.json"

    def refresh_configs(self):
        CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(path.stem for path in CONFIGS_DIR.glob("*.json"))
        self.config_combo["values"] = files
        current = self.selected_config.get().strip()
        if current in files:
            return
        self.selected_config.set(files[0] if files else "")

    def save_config(self):
        path = self._config_path(self.config_name.get())
        if path is None:
            messagebox.showwarning(self.tr("config_empty_title"), self.tr("config_empty_message"))
            return
        payload = self._config_payload()
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.selected_config.set(path.stem)
            self.refresh_configs()
            self.q.put(f"{self.tr('config_saved')}: {path.name}\n")
        except Exception as e:
            self.q.put(f"{self.tr('config_save_failed')} {path.name}: {type(e).__name__}: {e}\n")

    def load_selected_config(self):
        name = self.selected_config.get().strip()
        path = self._config_path(name)
        if path is None or not path.exists():
            messagebox.showwarning(self.tr("config_missing_title"), self.tr("config_missing_message"))
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.apply_config(data)
            self.apply_language()
            self.apply_theme()
            self.config_name.set(path.stem)
            self.q.put(f"{self.tr('config_loaded')}: {path.name}\n")
        except Exception as e:
            self.q.put(f"{self.tr('config_load_failed')} {path.name}: {type(e).__name__}: {e}\n")

    def apply_config(self, data: dict):
        generator = data.get("generator", {})
        check = data.get("check", {})
        ui = data.get("ui", {})
        self.count.set(str(generator.get("count", self.count.get())))
        self.min_quality.set(int(generator.get("min_quality", self.min_quality.get())))
        self.max_quality.set(int(generator.get("max_quality", self.max_quality.get())))
        self.min_len.set(int(generator.get("min_len", self.min_len.get())))
        self.max_len.set(int(generator.get("max_len", self.max_len.get())))
        self.min_words.set(int(generator.get("min_words", self.min_words.get())))
        self.max_words.set(int(generator.get("max_words", self.max_words.get())))
        mode = str(generator.get("generator_mode", "")).strip()
        if mode not in {"english_words", "translit", "random_letters"}:
            mode = "translit" if bool(generator.get("include_translit", False)) else "english_words"
        self.generator_mode.set(mode)
        self.add_articles.set(bool(generator.get("add_articles", self.add_articles.get())))
        self.dedupe_letters.set(bool(generator.get("dedupe_letters", self.dedupe_letters.get())))
        self.prefix.set(str(generator.get("prefix", self.prefix.get())))
        self.suffix.set(str(generator.get("suffix", self.suffix.get())))
        self.scan.set(str(generator.get("scan", self.scan.get())))
        self.seed.set(str(generator.get("seed", self.seed.get())))
        self._update_generator_mode_ui()

        self.workers.set(str(check.get("workers", self.workers.get())))
        self.limit.set(str(check.get("limit", self.limit.get())))
        self.delay.set(str(check.get("delay", self.delay.get())))
        self.check_tme.set(bool(check.get("check_tme", self.check_tme.get())))
        self.check_fragment.set(bool(check.get("check_fragment", self.check_fragment.get())))
        self.check_instagram.set(bool(check.get("check_instagram", self.check_instagram.get())))
        self.check_x.set(bool(check.get("check_x", self.check_x.get())))
        self.check_tiktok.set(bool(check.get("check_tiktok", self.check_tiktok.get())))
        self.check_youtube.set(bool(check.get("check_youtube", self.check_youtube.get())))
        self.check_github.set(bool(check.get("check_github", self.check_github.get())))
        self.export_found.set(bool(check.get("export_found", self.export_found.get())))
        self.hide_busy.set(bool(check.get("hide_busy", self.hide_busy.get())))
        order_value = str(check.get("check_order", self.check_order_value()))
        self.set_check_order_from_value(order_value)

        lang = str(ui.get("language", self._serialize_ui_language())).strip().lower()
        self.ui_language.set(lang if lang in TRANSLATIONS else "ru")
        self.debug_mode.set(bool(ui.get("debug_mode", self.debug_mode.get())))
        self.autosave_latest.set(bool(ui.get("autosave_latest", self.autosave_latest.get())))

    def log_line(self, s: str):
        for part in s.splitlines(True):
            stripped = part.lstrip()
            self._track_check_progress(stripped)
            if stripped.startswith("[+]"):
                self._feed_visualizer("free")
                self.log.insert("end", part, "free")
            elif stripped.startswith("[-]"):
                self._feed_visualizer("busy")
                self.log.insert("end", part, "busy")
            elif stripped.startswith("[b]"):
                self._feed_visualizer("busy")
            elif stripped.startswith("[!]") or " limit - " in stripped:
                self.log.insert("end", part, "warn")
            else:
                self.log.insert("end", part)
        self.log.see("end")

    def _update_progress_label(self):
        total = self.progress_total if self.progress_total > 0 else 0
        self.progress_text.set(f"Checked: {self.progress_checked}/{total}   found: {self.progress_found}")

    def _reset_progress(self):
        self.progress_total = 0
        self.progress_checked = 0
        self.progress_found = 0
        self._update_progress_label()
        self._reset_visualizer()

    def _track_check_progress(self, stripped: str):
        loaded = re.match(r"Loaded (\d+) words\.", stripped)
        if loaded:
            self.progress_total = int(loaded.group(1))
            self.progress_checked = 0
            self.progress_found = 0
            self._update_progress_label()
            return
        if stripped.startswith(("[+]", "[-]", "[b]", "[?]")):
            self.progress_checked += 1
            if stripped.startswith("[+]"):
                self.progress_found += 1
            self._update_progress_label()
            return
        done = re.match(r"Done\. Checked: (\d+)\. Found: (\d+)\.", stripped)
        if done:
            self.progress_checked = int(done.group(1))
            self.progress_found = int(done.group(2))
            if self.progress_total < self.progress_checked:
                self.progress_total = self.progress_checked
            self._update_progress_label()

    def _drain_log(self):
        try:
            while True:
                self.log_line(self.q.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self._drain_log)

    def run_cmd(self, cmd: list[str], on_done=None):
        if self.proc and self.proc.poll() is None:
            messagebox.showwarning("Занято", "Уже что-то запущено")
            return False
        shown = " ".join(f'"{x}"' if " " in x else x for x in cmd)
        if self.debug_mode.get():
            self.q.put("\n$ " + shown + "\n")

        def worker():
            code = -1
            try:
                flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                self.proc = subprocess.Popen(cmd, cwd=str(BASE), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", creationflags=flags, env=env)
                assert self.proc.stdout is not None
                for line in self.proc.stdout:
                    self.q.put(line)
                code = self.proc.wait()
                if self.debug_mode.get():
                    self.q.put(f"\n[exit {code}]\n")
            except Exception as e:
                self.q.put(f"\n[error] {type(e).__name__}: {e}\n")
            finally:
                self.proc = None
                if on_done:
                    self.after(0, lambda: on_done(code))

        threading.Thread(target=worker, daemon=True).start()
        return True

    def deps_ready(self) -> bool:
        if os.name == "nt" and not VENV_PY.exists():
            return False
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            r = subprocess.run([real_python(), "-c", "import wordfreq"], cwd=str(BASE), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=flags, timeout=10)
            return r.returncode == 0
        except Exception:
            return False

    def ensure_deps_on_start(self):
        if self.deps_ready():
            self.q.put("wordfreq ok.\n")
            return
        self.q.put("wordfreq не найден, ставлю автоматически в локальную .venv...\n")
        self.install_deps(show_busy=False)

    def py_cmd(self, script: Path) -> list[str]:
        return [real_python(), "-u", str(script)]

    def generate_words(self):
        if not self.deps_ready():
            self.q.put("wordfreq не готов, сначала ставлю зависимости. Запусти генерацию еще раз после установки.\n")
            self.install_deps(show_busy=False)
            return
        cmd = self.py_cmd(GEN) + [
            "--out", self.out_file.get(),
            "--count", self.count.get(),
            "--scan", self.scan.get(),
            "--min-len", str(self.min_len.get()),
            "--max-len", str(self.max_len.get()),
            "--generator-mode", self.generator_mode.get(),
            "--prefix", self.prefix.get(),
            "--suffix", self.suffix.get(),
        ]
        if self.generator_mode.get() != "random_letters":
            cmd += [
                "--min-quality", str(self.min_quality.get()),
                "--max-quality", str(self.max_quality.get()),
                "--min-words", str(self.min_words.get()),
                "--max-words", str(self.max_words.get()),
            ]
        if self.add_articles.get():
            cmd += ["--add-articles"]
        if self.dedupe_letters.get():
            cmd += ["--dedupe-letters"]
        if self.seed.get().strip():
            cmd += ["--seed", self.seed.get().strip()]
        self.run_cmd(cmd)

    def delete_words_file(self):
        path = (BASE / self.out_file.get()).resolve() if not Path(self.out_file.get()).is_absolute() else Path(self.out_file.get())
        if not path.exists():
            self.q.put(f"Файл уже отсутствует: {path}\n")
            return
        if not messagebox.askyesno("Удалить file", f"Удалить {path.name}?"):
            return
        try:
            path.unlink()
            self.q.put(f"Удалено: {path}\n")
        except Exception as e:
            self.q.put(f"Не смог удалить {path}: {type(e).__name__}: {e}\n")

    def delete_found_file(self):
        path = (BASE / "found.txt").resolve()
        if not path.exists():
            self.q.put(f"Файл уже отсутствует: {path}\n")
            return
        if not messagebox.askyesno("Удалить found.txt", f"Удалить {path.name}?"):
            return
        try:
            path.unlink()
            self.q.put(f"Удалено: {path}\n")
        except Exception as e:
            self.q.put(f"Не смог удалить {path}: {type(e).__name__}: {e}\n")

    def start_or_continue_check(self):
        if self.paused:
            self.continue_check()
            return
        self.check_names()

    def pause_check(self):
        if not (self.proc and self.proc.poll() is None):
            self.q.put("Нечего ставить на паузу.\n")
            return
        try:
            PAUSE_FILE.write_text("paused", encoding="utf-8")
            self.paused = True
            self.update_action_bar()
        except Exception as e:
            self.q.put(f"Не смог включить паузу: {type(e).__name__}: {e}\n")

    def continue_check(self):
        try:
            PAUSE_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        self.paused = False
        self.q.put(f"{self.tr('log_continue_check')}\n")
        self.update_action_bar()

    def check_names(self):
        if not any((
            self.check_tme.get(),
            self.check_fragment.get(),
            self.check_instagram.get(),
            self.check_x.get(),
            self.check_tiktok.get(),
            self.check_youtube.get(),
            self.check_github.get(),
        )):
            messagebox.showwarning("Нечего проверять", "Включи хотя бы один сервис")
            return
        try:
            PAUSE_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            STOP_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        self.paused = False
        self._reset_progress()
        self.update_action_bar()
        cmd = self.py_cmd(CHECK) + [
            "--wordlist", self.wordlist.get(),
            "--workers", self.workers.get(),
            "--delay", self.delay.get(),
            "--max-len", "32",
            "--pause-file", str(PAUSE_FILE),
            "--stop-file", str(STOP_FILE),
            "--order", self.check_order_value(),
        ]
        if self.limit.get().strip() and self.limit.get().strip() != "0":
            cmd += ["--limit", self.limit.get().strip()]
        if self.check_tme.get():
            cmd += ["--check-telegram"]
        if self.check_fragment.get():
            cmd += ["--check-fragment"]
        if self.check_instagram.get():
            cmd += ["--check-instagram"]
        if self.check_x.get():
            cmd += ["--check-x"]
        if self.check_tiktok.get():
            cmd += ["--check-tiktok"]
        if self.check_youtube.get():
            cmd += ["--check-youtube"]
        if self.check_github.get():
            cmd += ["--check-github"]
        if self.export_found.get():
            cmd += ["--found-out", "found.txt"]
        if self.hide_busy.get():
            cmd += ["--hide-busy"]
        if self.run_cmd(cmd, on_done=lambda _code: self.check_done()):
            self.check_running = True
            self.update_action_bar()

    def check_done(self):
        try:
            PAUSE_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            STOP_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        self.paused = False
        self.check_running = False
        self.update_action_bar()

    def install_deps(self, show_busy: bool = True):
        if self.proc and self.proc.poll() is None:
            if show_busy:
                messagebox.showwarning("Занято", "Уже что-то запущено")
            return
        if os.name == "nt" and not VENV_PY.exists():
            self.q.put("Создаю локальную .venv...\n")
            self.run_cmd([launcher_python(), "-m", "venv", str(BASE / ".venv")], on_done=lambda code: self.install_deps(show_busy=False) if code == 0 else None)
            return
        self.q.put("Ставлю зависимости в локальный Python...\n")
        self.run_cmd([real_python(), "-m", "pip", "install", "-r", str(BASE / "requirements.txt")])

    def stop_proc(self):
        if self.proc and self.proc.poll() is None:
            if self.check_running:
                try:
                    STOP_FILE.write_text("stop", encoding="utf-8")
                    self.q.put(f"{self.tr('log_stopping_check')}\n")
                except Exception:
                    self.proc.terminate()
                    self.q.put("\n[terminated]\n")
            else:
                self.proc.terminate()
                self.q.put("\n[terminated]\n")
        try:
            PAUSE_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        self.paused = False
        if not self.check_running:
            self._reset_progress()
        self.update_action_bar()

    def open_folder(self):
        if os.name == "nt":
            os.startfile(BASE)
        else:
            self.run_cmd(["explorer.exe", str(BASE)])


if __name__ == "__main__":
    App().mainloop()
