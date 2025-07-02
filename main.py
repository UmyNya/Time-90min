import ctypes
import tkinter as tk
from tkinter import messagebox, font
import time
import random
import json
from datetime import datetime, timedelta
import os
import sound_manager
import win32api
import win32con
import customtkinter
from PIL import Image, ImageTk  # 导入 Pillow 库的 Image 和 ImageTk 模块

# --- CustomTkinter 缩放设置 ---
# 将 customtkinter 的内部缩放设置回 1 (100%)，让 Tkinter/OS 处理 DPI
customtkinter.set_widget_scaling(1) # 控件缩放
customtkinter.set_window_scaling(1) # 窗口缩放

# --- Load Custom Font ---
FONT_NAME = "Alibaba PuHuiTi"
FONT_FILENAME = "Alibaba-PuHuiTi-Regular.ttf"
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), FONT_FILENAME)


def load_custom_font():
    try:
        if not os.path.exists(FONT_PATH):
            print(f"Warning: Font file not found at {FONT_PATH}. Please copy it there.")
            return False
        print(f"Font file found at {FONT_PATH}. Attempting to use '{FONT_NAME}'.")
        return True
    except Exception as e:
        print(f"Error loading custom font: {e}")
        return False


FONT_LOADED = load_custom_font()

# --- Constants ---
DEFAULT_MAIN_TIMER_DURATION = 90 * 60  # 默认90分钟（秒）
SHORT_BREAK_TIMER_DURATION = 10  # 10 seconds
LONG_BREAK_TIMER_DURATION = 20 * 60  # 20 minutes in seconds

# 短休息间隔选项（秒）
BREAK_INTERVAL_OPTIONS = {
    "5-10s": (5, 10),
    "2-4分钟": (2 * 60, 4 * 60),
    "3-5分钟": (3 * 60, 5 * 60),
    "4-6分钟": (4 * 60, 6 * 60),
    "5-7分钟": (5 * 60, 7 * 60),
    "5-10min": (5 * 60, 10 * 60),
    "10-15min": (10 * 60, 15 * 60),
    "15-25min": (15 * 60, 25 * 60),
    "25-45min": (25 * 60, 45 * 60),
}

# 默认短休息间隔
DEFAULT_BREAK_INTERVAL = "3-5分钟"

DATA_FILE = "learning_data.json"

# 要修改音频文件请到 sound_manager.py 中修改 SOUND_FILE_NAME 参数
# 源代码是 SOUND_FILE_NAME = "twinkling_sound.mp3"

# 如果要修改倒计时弹窗的相关配置，去本脚本的 show_popup_countdown 这个函数中修改
# 测试弹出可以用 popup_countdown_test.py 来测试
# 这里是部分配置，我提到上面来了
POPUP_WIDTH = 200  # 默认为 600 或屏幕大小的 0.12 倍
POPUP_HEIGHT = 200  # 默认为 300 或屏幕大小的 0.12 倍
POPUP_FONT_SIZE = 20  # 默认为 140
POPUP_IMAGE_DIR = "./background/"
POPUP_IMAGE_FONT_COLOR = "black"
POPUP_IS_KEEP_ASPECT_RATIO = (
    True  # True 则固定POPUP_HEIGHT，根据图片长宽比例调整POPUP_WIDTH。否则固定窗口大小
)


# --- DPI Awareness (修复Windows上的模糊问题) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Windows 8.1+
except AttributeError:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Windows Vista+
    except AttributeError:
        pass  # 不支持的旧版Windows

# --- 媒体控制 ---
import asyncio
from media_status_fetcher import (
    get_media_status,
    toggle_media_playback as async_toggle_media_playback,
)


def get_current_media_status():
    """获取当前媒体播放状态"""
    try:
        status = asyncio.run(get_media_status())
        print(f"当前媒体状态: {status}")
        return status
    except Exception as e:
        print(f"获取媒体状态时出错: {e}")
        return "未知状态"


def toggle_media_playback():
    """切换媒体播放/暂停状态"""
    try:
        result = asyncio.run(async_toggle_media_playback())
        print(result)
        return result
    except Exception as e:
        print(f"切换媒体播放状态时出错: {e}")
        try:
            win32api.keybd_event(win32con.VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(
                win32con.VK_MEDIA_PLAY_PAUSE, 0, win32con.KEYEVENTF_KEYUP, 0
            )
            print("回退到模拟按键方式切换媒体播放状态")
        except Exception as e2:
            print(f"模拟媒体键时出错: {e2}")
        return "未知结果"


# --- Settings Page using CustomTkinter ---
class SettingsPage(customtkinter.CTkToplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.title("设置")
        self.geometry("400x500")  # 增加高度以容纳新选项
        self.transient(parent)
        self.grab_set()
        self.app = app_instance

        # No need to set appearance mode here if set globally

        container = customtkinter.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=20, pady=20)

        # Apply custom font if loaded
        font_args = (
            {"font": (FONT_NAME, 16, "bold")}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=16, weight="bold")}
        )
        settings_label = customtkinter.CTkLabel(container, text="设置", **font_args)
        settings_label.pack(pady=(0, 15))

        # --- Auto-pause media setting ---
        pause_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        pause_frame.pack(fill="x", pady=5)  # Reduced pady

        font_args_label = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        pause_label = customtkinter.CTkLabel(
            pause_frame, text="休息时自动暂停媒体:", **font_args_label
        )
        pause_label.pack(side="left", padx=(0, 10))

        # Use CTkSwitch
        self.auto_pause_switch = customtkinter.CTkSwitch(
            pause_frame,
            text="",  # Keep text empty
            variable=self.app.auto_pause_media_var,
            onvalue=True,
            offvalue=False,
            command=self.app.save_data,  # Use save_data which now includes this var
        )
        # Ensure the switch reflects the loaded state
        if self.app.auto_pause_media_var.get():
            self.auto_pause_switch.select()
        else:
            self.auto_pause_switch.deselect()
        self.auto_pause_switch.pack(side="right")

        # --- Auto-resume media setting --- (Added)
        resume_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        resume_frame.pack(fill="x", pady=5)  # Reduced pady

        resume_label = customtkinter.CTkLabel(
            resume_frame, text="休息后继续自动播放:", **font_args_label
        )
        resume_label.pack(side="left", padx=(0, 10))

        self.auto_resume_switch = customtkinter.CTkSwitch(
            resume_frame,
            text="",
            variable=self.app.auto_resume_media_var,  # Link to new variable
            onvalue=True,
            offvalue=False,
            command=self.app.save_data,  # Save when changed
        )
        # Ensure the switch reflects the loaded state
        if self.app.auto_resume_media_var.get():
            self.auto_resume_switch.select()
        else:
            self.auto_resume_switch.deselect()
        self.auto_resume_switch.pack(side="right")

        # --- 周期时间设置 ---
        cycle_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        cycle_frame.pack(fill="x", pady=10)

        cycle_label = customtkinter.CTkLabel(
            cycle_frame, text="学习周期时间:", **font_args_label
        )
        cycle_label.pack(side="left", padx=(0, 10))

        # 创建滑块和数值显示
        cycle_slider_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        cycle_slider_frame.pack(fill="x", pady=5)

        self.cycle_slider = customtkinter.CTkSlider(
            cycle_slider_frame,
            from_=1,
            to=180,
            number_of_steps=179,
            command=self.update_cycle_value,
            variable=self.app.cycle_duration_var,
        )
        self.cycle_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.cycle_value_label = customtkinter.CTkLabel(
            cycle_slider_frame,
            text=f"{self.app.cycle_duration_var.get()}分钟",
            width=60,
            **font_args_label,
        )
        self.cycle_value_label.pack(side="right")

        # --- 短休息间隔设置 ---
        break_interval_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        break_interval_frame.pack(fill="x", pady=10)

        break_interval_label = customtkinter.CTkLabel(
            break_interval_frame, text="短休息间隔:", **font_args_label
        )
        break_interval_label.pack(side="left", padx=(0, 10))

        # 创建下拉菜单
        self.break_interval_menu = customtkinter.CTkOptionMenu(
            break_interval_frame,
            values=list(BREAK_INTERVAL_OPTIONS.keys()),
            variable=self.app.break_interval_var,
            command=self.app.save_data,
            **font_args_label,
        )
        self.break_interval_menu.pack(side="right")

        # --- Clear Data Button --- (移动到短休息间隔下方)
        font_args_button = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        clear_button = customtkinter.CTkButton(
            container,
            text="清空学习数据",
            command=self.confirm_clear_data,
            fg_color="#D32F2F",  # Red color for destructive action
            hover_color="#B71C1C",  # Darker red on hover
            **font_args_button,
        )
        clear_button.pack(pady=(15, 5))

        # --- Close Button ---
        close_button = customtkinter.CTkButton(
            container, text="关闭", command=self.close_settings, **font_args_button
        )
        close_button.pack(pady=(15, 0))

    def close_settings(self):
        # 关闭设置页面前刷新主界面按钮
        self.app.show_start_button()
        self.destroy()

    def confirm_clear_data(self):
        confirmed = messagebox.askyesno(
            "确认操作",
            "您确定要清空所有学习记录吗？\n此操作无法撤销！",
            parent=self,  # Ensure dialog appears over the settings window
        )
        if confirmed:
            self.app.clear_learning_data()
            messagebox.showinfo("操作完成", "学习数据已清空。", parent=self)

    def update_cycle_value(self, value=None):
        # 更新周期时间显示
        current_value = self.app.cycle_duration_var.get()
        self.cycle_value_label.configure(text=f"{current_value}分钟")
        self.app.save_data()


# --- Main Application Class using CustomTkinter ---
class LearningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学习助手")
        # Change window size to 600x600
        self.root.geometry("500x400")  # User requested size
        self.root.minsize(400, 300)  # User requested min size

        # --- Set CustomTkinter Appearance ---
        customtkinter.set_appearance_mode(
            "System"
        )  # Options: "System", "Dark", "Light"
        customtkinter.set_default_color_theme(
            "blue"
        )  # Options: "blue", "green", "dark-blue"

        self.main_timer_seconds = DEFAULT_MAIN_TIMER_DURATION
        self.long_break_seconds = LONG_BREAK_TIMER_DURATION
        self.current_timer_id = None
        self.short_break_timer_id = None
        self.start_time = None  # Tracks start of the 90-min cycle
        self.session_start_time = (
            None  # Tracks start of the current learning segment (since last 'start')
        )
        self.paused = False
        self.media_paused_by_app = False  # Flag to track if media was paused by the app
        self.is_paused_for_5min = False  # 是否处于5分钟暂停状态
        self.pause_end_time = None  # 暂停结束时间
        self.pause_timer_id = None  # 暂停计时器ID

        # Load data first
        self.load_data()
        # Initialize BooleanVars AFTER loading data, using the loaded values
        self.auto_pause_media_var = tk.BooleanVar(
            value=self.learning_data.get("auto_pause_media", True)
        )
        self.auto_resume_media_var = tk.BooleanVar(
            value=self.learning_data.get("auto_resume_media", True)
        )

        # 初始化周期时间（分钟）
        self.cycle_duration_var = tk.IntVar(
            value=self.learning_data.get("cycle_duration", 90)
        )

        # 初始化短休息间隔选项
        self.break_interval_var = tk.StringVar(
            value=self.learning_data.get("break_interval", DEFAULT_BREAK_INTERVAL)
        )

        self.create_main_layout()  # Create layout using CTk widgets
        self.show_start_button()  # Show initial view

    def load_data(self):
        self.default_data = {
            "total_seconds": 0,
            "total_cycles": 0,
            "daily_log": {},
            "auto_pause_media": True,  # Default value
            "auto_resume_media": True,  # Default value for new setting
            "cycle_duration": 90,  # 默认周期时间（分钟）
            "break_interval": DEFAULT_BREAK_INTERVAL,  # 默认短休息间隔
        }
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    loaded_data = json.load(f)
                    # Ensure all default keys exist
                    self.learning_data = {**self.default_data, **loaded_data}
            except (json.JSONDecodeError, IOError):
                self.learning_data = self.default_data.copy()
        else:
            self.learning_data = self.default_data.copy()

    def save_data(self, value=None):
        # Update settings from BooleanVars before saving
        self.learning_data["auto_pause_media"] = self.auto_pause_media_var.get()
        self.learning_data["auto_resume_media"] = self.auto_resume_media_var.get()
        self.learning_data["cycle_duration"] = self.cycle_duration_var.get()
        self.learning_data["break_interval"] = self.break_interval_var.get()
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.learning_data, f, indent=4)
        except IOError as e:
            messagebox.showerror("错误", f"无法保存学习数据: {e}")

    def clear_learning_data(self):
        """Resets learning data to defaults and saves."""
        print("Clearing learning data...")
        self.learning_data = self.default_data.copy()  # Reset to default
        # Ensure the settings are preserved from the current UI state
        self.learning_data["auto_pause_media"] = self.auto_pause_media_var.get()
        self.learning_data["auto_resume_media"] = self.auto_resume_media_var.get()
        self.learning_data["cycle_duration"] = self.cycle_duration_var.get()
        self.learning_data["break_interval"] = self.break_interval_var.get()
        self.save_data()  # Save the cleared data
        self.update_overview_display()  # Update the UI
        print("Learning data cleared and saved.")

    def create_main_layout(self):
        self.clear_window()
        # Main container frame using CTkFrame
        container = customtkinter.CTkFrame(
            self.root, fg_color="transparent"
        )  # Use root's bg
        container.pack(expand=True, fill="both")

        # Adjust column weights: Give sidebar more relative weight (e.g., 2:1 ratio)
        container.grid_columnconfigure(
            0, weight=2, uniform="group1"
        )  # Main content area weight reduced
        container.grid_columnconfigure(
            1, weight=1, uniform="group1"
        )  # Sidebar weight remains 1 (relative increase)
        container.grid_rowconfigure(0, weight=1)

        # --- Main Content Area (CTkFrame) ---
        self.main_frame = customtkinter.CTkFrame(
            container, corner_radius=10
        )  # Add some rounding
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        # Configure main frame grid for content (title removed)
        self.main_frame.grid_rowconfigure(
            0, weight=1
        )  # Row for the main content (start button/timer)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Add App Name Title to Main Frame --- << REMOVED

        # --- Sidebar Area (CTkFrame) ---
        self.sidebar_frame = customtkinter.CTkFrame(
            container, width=150, corner_radius=10
        )  # Add matching corner radius
        self.sidebar_frame.grid(
            row=0, column=1, sticky="nsew", padx=(0, 10), pady=10
        )  # Add padx for alignment
        self.sidebar_frame.grid_propagate(False)  # Prevent resizing based on content
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        # Configure rows for sidebar content (Removed row 0 for App Name)
        self.sidebar_frame.grid_rowconfigure(0, weight=0)  # Overview Title (was row 1)
        self.sidebar_frame.grid_rowconfigure(
            1, weight=0
        )  # Overview Content Hours (was row 2)
        self.sidebar_frame.grid_rowconfigure(
            2, weight=0
        )  # Overview Content Cycles (was row 3)
        self.sidebar_frame.grid_rowconfigure(
            3, weight=0, minsize=20
        )  # Spacer (was row 4)
        self.sidebar_frame.grid_rowconfigure(4, weight=0)  # Records Button (was row 5)
        self.sidebar_frame.grid_rowconfigure(5, weight=0)  # Settings Button (was row 6)
        self.sidebar_frame.grid_rowconfigure(6, weight=1)  # Bottom Spacer (was row 7)

        # Populate Sidebar with CTk Widgets (Removed App Name Label)
        font_args_overview_title = (
            {"font": (FONT_NAME, 16, "bold")}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=16, weight="bold")}
        )  # Increased size from 14
        overview_title = customtkinter.CTkLabel(
            self.sidebar_frame, text="学习概览", **font_args_overview_title
        )
        overview_title.grid(
            row=0, column=0, pady=(10, 5), padx=20, sticky="ew"
        )  # Adjusted row index

        font_args_overview_text = (
            {"font": (FONT_NAME, 14)}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=14)}
        )  # Increased size from 12
        self.overview_label_hours = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="总时长: ...",
            anchor="w",
            **font_args_overview_text,
        )
        self.overview_label_hours.grid(
            row=1, column=0, pady=2, padx=20, sticky="ew"
        )  # Adjusted row index
        self.overview_label_cycles = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="总周期: ...",
            anchor="w",
            **font_args_overview_text,
        )
        self.overview_label_cycles.grid(
            row=2, column=0, pady=(0, 0), padx=20, sticky="ew"
        )  # Adjusted row index

        font_args_sidebar_button = (
            {"font": (FONT_NAME, 14)}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=14)}
        )  # Increased size from 12
        record_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="学习记录",
            command=self.show_learning_records,
            **font_args_sidebar_button,
        )
        record_button.grid(
            row=4, column=0, pady=10, padx=30, sticky="ew"
        )  # Adjusted row index

        settings_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="设置",
            command=self.show_settings_view,
            **font_args_sidebar_button,
        )
        settings_button.grid(
            row=5, column=0, pady=10, padx=30, sticky="ew"
        )  # Adjusted row index

        self.update_overview_display()  # Initial update

    def show_start_button(self):
        self.clear_main_frame()  # Use original clear_main_frame now
        # 创建一个容器框架，用于居中放置按钮
        content_frame = self.main_frame

        # 配置行权重，确保按钮垂直居中
        for i in range(5):
            content_frame.grid_rowconfigure(i, weight=1)
        content_frame.grid_rowconfigure(2, weight=2)  # 中间行权重更大，确保按钮居中
        content_frame.grid_columnconfigure(0, weight=1)
        # 创建一个内部容器来放置按钮和标签，确保它们作为一个整体居中
        center_container = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        center_container.grid(row=2, column=0, sticky="nsew")
        center_container.grid_rowconfigure(0, weight=1)  # 按钮行
        center_container.grid_rowconfigure(1, weight=0)  # 休息时间标签行
        center_container.grid_columnconfigure(0, weight=1)

        # Apply custom font if loaded
        font_args_start_button = (
            {"font": (FONT_NAME, 24, "bold")}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=24, weight="bold")}
        )

        # 使用当前设置的周期时间
        cycle_minutes = self.cycle_duration_var.get()
        start_button = customtkinter.CTkButton(
            center_container,
            text=f"开始 {cycle_minutes} 分钟学习",
            command=self.start_main_timer,
            width=300,
            height=80,
            **font_args_start_button,
        )
        start_button.grid(
            row=0, column=0, pady=(0, 10), sticky=""
        )  # 放在中间容器的第一行

        # 添加休息时间标签
        font_args_break = (
            {"font": (FONT_NAME, 14)}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=14)}
        )
        self.break_time_label = customtkinter.CTkLabel(
            center_container, text="", **font_args_break
        )
        self.break_time_label.grid(row=1, column=0, pady=(0, 0), sticky="")

        # 如果有休息开始时间，显示已休息时间
        if hasattr(self, "break_start_time"):
            self.update_break_time_display()
            # 每秒更新休息时间显示
            self.break_timer_id = self.root.after(1000, self.update_break_time_display)

    def update_overview_display(self):
        if hasattr(self, "overview_label_hours"):
            total_seconds = self.learning_data.get("total_seconds", 0)
            total_cycles = self.learning_data.get("total_cycles", 0)
            total_hours = total_seconds / 3600
            self.overview_label_hours.configure(text=f"总时长: {total_hours:.2f} 小时")
            self.overview_label_cycles.configure(text=f"总周期: {total_cycles:.2f} 个")

    def create_countdown_view(self):
        self.clear_main_frame()  # Use original clear_main_frame now
        content_frame = self.main_frame
        # Center content
        content_frame.grid_rowconfigure(0, weight=1)  # Space above timer
        content_frame.grid_rowconfigure(1, weight=0)  # Timer label row
        content_frame.grid_rowconfigure(2, weight=0)  # Session duration label row (NEW)
        content_frame.grid_rowconfigure(3, weight=0)  # Buttons row (Shifted down)
        content_frame.grid_rowconfigure(
            4, weight=1
        )  # Space below button (Shifted down)
        content_frame.grid_columnconfigure(0, weight=1)

        # 创建一个固定高度的容器来放置计时器标签，确保暂停状态不会影响布局
        timer_container = customtkinter.CTkFrame(
            content_frame, fg_color="transparent", height=100
        )
        timer_container.grid(row=1, column=0, pady=(20, 5), sticky="")
        timer_container.grid_propagate(False)  # 防止内容影响容器大小

        self.timer_label = customtkinter.CTkLabel(
            timer_container, text="", font=customtkinter.CTkFont(size=80, weight="bold")
        )
        self.timer_label.place(relx=0.5, rely=0.5, anchor="center")  # 在容器中居中放置

        # --- Add Session Duration Label ---
        font_args_session = (
            {"font": (FONT_NAME, 14)}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=14)}
        )
        self.session_duration_label = customtkinter.CTkLabel(
            content_frame, text="你已学习 00:00 分钟", **font_args_session
        )
        self.session_duration_label.grid(
            row=2, column=0, pady=(0, 20), sticky=""
        )  # Place below timer

        # 创建按钮容器框架 - 使用垂直布局
        buttons_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=20, sticky="")

        # 添加停止按钮
        font_args_button = (
            {"font": (FONT_NAME, 14)}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=14)}
        )
        stop_button = customtkinter.CTkButton(
            buttons_frame,
            text="停止并记录",
            command=self.stop_timer_and_return,
            width=200,
            **font_args_button,
        )
        stop_button.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="")

        # 添加暂停5分钟按钮 - 放在停止按钮下方
        self.pause_button = customtkinter.CTkButton(
            buttons_frame,
            text="暂停5分钟",
            command=self.pause_timer_for_5min,
            width=200,
            **font_args_button,
        )
        self.pause_button.grid(row=1, column=0, padx=10, pady=(0, 0), sticky="")

        self.update_timer_display()  # Initial display update
        self.update_session_duration_display()  # Initial session duration update

        # 初始化暂停相关变量
        self.is_paused_for_5min = False
        self.pause_end_time = None
        self.pause_timer_id = None

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_main_frame(self):
        if hasattr(self, "main_frame"):
            for widget in self.main_frame.winfo_children():
                widget.destroy()

    def start_main_timer(self):
        self.start_time = datetime.now()
        self.session_start_time = datetime.now()  # Initialize session start time here
        self.timer_start_time = (
            datetime.now()
        )  # 记录计时器开始时间，用于基于实际时间的计时

        # 使用用户设置的周期时间
        cycle_minutes = self.cycle_duration_var.get()
        self.total_timer_seconds = cycle_minutes * 60  # 总计时时间（不变）
        self.main_timer_seconds = self.total_timer_seconds  # 初始剩余时间

        self.paused = False
        self.paused_elapsed_time = 0  # 初始化暂停时已经过的时间

        # 取消休息时间显示的定时器（如果存在）
        if hasattr(self, "break_timer_id") and self.break_timer_id:
            self.root.after_cancel(self.break_timer_id)
            self.break_timer_id = None

        self.create_countdown_view()
        self.run_main_timer()
        self.schedule_short_break()

    def run_main_timer(self):
        if self.paused:
            return

        if self.main_timer_seconds > 0:
            # 基于实际时间计算剩余时间
            if hasattr(self, "timer_start_time"):
                elapsed_seconds = int(
                    (datetime.now() - self.timer_start_time).total_seconds()
                )
                # 使用暂停时已经过的时间作为基准，避免暂停期间的时间被计入
                adjusted_elapsed = self.paused_elapsed_time + elapsed_seconds
                self.main_timer_seconds = max(
                    0, self.total_timer_seconds - adjusted_elapsed
                )

            self.update_timer_display()
            self.update_session_duration_display()

            # 使用较短的间隔更新，提高精度
            self.current_timer_id = self.root.after(100, self.run_main_timer)
        else:
            # 取消当前计时器，防止重复触发
            if self.current_timer_id:
                self.root.after_cancel(self.current_timer_id)
                self.current_timer_id = None
            # 计时器结束时不播放声音，因为trigger_long_break中会播放
            # 直接记录学习会话并触发长休息
            self.record_learning_session(completed_cycle=True)
            self.trigger_long_break()

    def update_timer_display(self):
        mins, secs = divmod(self.main_timer_seconds, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        if hasattr(self, "timer_label"):
            self.timer_label.configure(text=time_str)

    def update_session_duration_display(self):
        """Updates the label showing the duration of the current learning segment."""
        if hasattr(self, "session_duration_label"):
            # 使用总周期时间减去剩余时间来计算已学习时间
            # 这种方法更准确，不受暂停次数影响
            cycle_minutes = self.cycle_duration_var.get()
            total_seconds = cycle_minutes * 60
            elapsed_seconds = total_seconds - self.main_timer_seconds
            mins, secs = divmod(elapsed_seconds, 60)
            # Display as MM:SS minutes
            duration_str = f"你已学习 {mins:02d}:{secs:02d} "
            self.session_duration_label.configure(text=duration_str)

    def pause_timer_for_5min(self):
        """暂停计时器5分钟"""
        if self.is_paused_for_5min:
            # 如果已经处于暂停状态，则恢复计时
            self.resume_timer()
            return

        # 设置暂停状态
        self.paused = True
        self.is_paused_for_5min = True

        # 计算暂停结束时间（当前时间 + 5分钟）
        self.pause_end_time = datetime.now() + timedelta(minutes=5)

        # 记录暂停时的已经过时间
        if hasattr(self, "timer_start_time"):
            elapsed_seconds = int(
                (datetime.now() - self.timer_start_time).total_seconds()
            )
            self.paused_elapsed_time += elapsed_seconds
            # 重置计时器开始时间，为恢复做准备
            self.timer_start_time = datetime.now()

        # 更新按钮文本
        self.pause_button.configure(text="继续")

        # 设置暂停样式
        font_args_pause = (
            {"font": (FONT_NAME, 50, "bold")}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=50, weight="bold")}
        )
        self.timer_label.configure(text="暂停中", justify="center", **font_args_pause)

        # 开始显示暂停倒计时
        self.update_pause_timer()

    def resume_timer(self):
        """恢复计时器"""
        # 取消暂停状态
        self.paused = False
        self.is_paused_for_5min = False
        # 取消暂停计时器
        if self.pause_timer_id:
            self.root.after_cancel(self.pause_timer_id)
            self.pause_timer_id = None

        # 重置计时器开始时间，以便正确计算剩余时间
        self.timer_start_time = datetime.now()

        # 更新按钮文本
        self.pause_button.configure(text="暂停5分钟")

        # 恢复原来的大字体
        font_args_normal = {"font": customtkinter.CTkFont(size=80, weight="bold")}
        self.timer_label.configure(**font_args_normal)

        # 恢复计时器显示
        self.update_timer_display()

        # 继续主计时器
        self.run_main_timer()

    def update_pause_timer(self):
        """更新暂停倒计时显示"""
        if not self.is_paused_for_5min or not self.pause_end_time:
            return

        # 计算剩余暂停时间
        remaining_delta = self.pause_end_time - datetime.now()
        remaining_seconds = max(0, int(remaining_delta.total_seconds()))

        mins, secs = divmod(remaining_seconds, 60)

        # 更新标签文本 - 使用较小的字体显示"暂停中"
        self.timer_label.configure(
            text=f"暂停中\n{mins:02d}:{secs:02d}", justify="center"
        )

        if remaining_seconds <= 0:
            # 暂停时间结束，恢复计时
            self.resume_timer()
        else:
            # 每秒更新一次
            self.pause_timer_id = self.root.after(1000, self.update_pause_timer)

    def schedule_short_break(self):
        if self.paused or self.main_timer_seconds <= 0:
            return

        # 获取当前选择的短休息间隔范围
        interval_key = self.break_interval_var.get()
        min_interval, max_interval = BREAK_INTERVAL_OPTIONS[interval_key]

        delay = random.randint(min_interval, max_interval)
        if self.main_timer_seconds > delay + SHORT_BREAK_TIMER_DURATION:
            self.short_break_timer_id = self.root.after(
                delay * 1000, self.trigger_short_break
            )

    def trigger_short_break(self):
        if self.paused or self.main_timer_seconds <= 0:
            return
        # Play sound using sound_manager BEFORE popup
        print("[Trigger Short Break] Playing sound first...")
        # 短休息时激活蓝牙耳机（这不是周期完成的弹窗，所以保持原有行为）
        sound_manager.play_notification_sound(activate_bluetooth=True)  # 激活蓝牙耳机
        print("[Trigger Short Break] Sound finished, showing popup.")

        # Pause media if setting is enabled and media is playing
        if self.auto_pause_media_var.get():
            print(
                "[Trigger Short Break] Auto-pause media enabled, checking media status..."
            )
            media_status = get_current_media_status()
            if media_status == "播放":
                print("[Trigger Short Break] Media is playing, pausing...")
                toggle_media_playback()  # Call the media control function
                self.media_paused_by_app = True  # Set flag to remember we paused it
                print("[Trigger Short Break] Media paused.")
            else:
                print(
                    f"[Trigger Short Break] Media is not playing (status: {media_status}), not pausing."
                )
                self.media_paused_by_app = False  # Make sure flag is not set

        # Show the larger popup
        self.show_popup_countdown(
            SHORT_BREAK_TIMER_DURATION, self.end_short_break, "休息一下"
        )

    def trigger_long_break(self):
        print("[Trigger Long Break] Playing sound first...")
        # 只在这里播放一次提示音，不激活蓝牙耳机（避免播放两次声音）
        sound_manager.play_notification_sound(
            activate_bluetooth=False
        )  # 不激活蓝牙耳机
        print("[Trigger Long Break] Sound finished, showing popup.")

        # 暂停媒体播放（如果设置启用且媒体正在播放）
        if self.auto_pause_media_var.get():
            print(
                "[Trigger Long Break] Auto-pause media enabled, checking media status..."
            )
            media_status = get_current_media_status()
            if media_status == "播放":
                print("[Trigger Long Break] Media is playing, pausing...")
                toggle_media_playback()  # 调用媒体控制函数
                self.media_paused_by_app = True  # 设置标志记住是应用暂停的
                print("[Trigger Long Break] Media paused.")
            else:
                print(
                    f"[Trigger Long Break] Media is not playing (status: {media_status}), not pausing."
                )
                self.media_paused_by_app = False  # 确保标志未设置

        # 记录休息开始时间
        self.break_start_time = datetime.now()

        # 显示恭喜完成周期的弹窗，而不是倒计时
        self.show_completion_popup()

    def end_short_break(self):
        print("[End Short Break] Playing sound...")
        # 短休息结束时激活蓝牙耳机（这不是周期完成的弹窗，所以保持原有行为）
        sound_manager.play_notification_sound(activate_bluetooth=False)  # 激活蓝牙耳机
        print("[End Short Break] Sound finished.")
        # Resume media only if auto-resume is enabled AND media was paused by the app
        if self.auto_resume_media_var.get() and self.media_paused_by_app:
            print(
                "[End Short Break] Auto-resume media enabled and we paused it, checking media status..."
            )
            media_status = get_current_media_status()
            if media_status == "暂停":
                print("[End Short Break] Media is paused, resuming...")
                toggle_media_playback()  # Call the media control function
                print("[End Short Break] Media resumed.")
            else:
                print(
                    f"[End Short Break] Media is not paused (status: {media_status}), not resuming."
                )
        self.media_paused_by_app = False  # Reset flag
        self.schedule_short_break()  # Schedule the next one

    def end_long_break(self):
        print("[End Long Break] No sound played at end of long break.")
        # 不再播放提示音
        # 不再自动恢复媒体播放
        self.media_paused_by_app = False  # 重置标志
        self.show_start_button()  # 长休息后返回开始视图

    def show_completion_popup(self):
        """显示恭喜完成周期的弹窗"""
        popup = customtkinter.CTkToplevel(self.root)
        popup.title("周期完成")
        popup.overrideredirect(True)  # 移除边框
        popup_width = 400
        popup_height = 200

        # 对齐弹窗到屏幕右下角
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)

        popup.update_idletasks()
        x_coordinate = screen_width - popup_width * 2 - 50
        y_coordinate = screen_height - popup_height * 2 - 50  # 调整以适应任务栏
        popup.geometry(f"{popup_width}x{popup_height}+{x_coordinate}+{y_coordinate}")

        popup.transient(self.root)
        popup.grab_set()
        popup.attributes("-topmost", True)  # 保持弹窗在顶层

        # 使用框架在弹窗内居中内容
        popup_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        popup_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # 恭喜文本
        font_args_popup = (
            {"font": (FONT_NAME, 18, "bold")}
            if FONT_LOADED
            else {"font": customtkinter.CTkFont(size=18, weight="bold")}
        )
        label = customtkinter.CTkLabel(
            popup_frame, text="恭喜你，完成了一个周期！", **font_args_popup
        )
        label.pack(pady=(20, 30))

        # 关闭按钮
        close_button = customtkinter.CTkButton(
            popup_frame, text="关闭", command=lambda: self.close_completion_popup(popup)
        )
        close_button.pack(pady=10)

        # 处理手动关闭弹窗
        popup.protocol("WM_DELETE_WINDOW", lambda: self.close_completion_popup(popup))

    def close_completion_popup(self, popup):
        """关闭完成周期弹窗并返回到开始界面"""
        popup.destroy()
        self.end_long_break()

    def update_break_time_display(self):
        """更新显示休息时间的标签"""
        if hasattr(self, "break_start_time") and hasattr(self, "break_time_label"):
            current_time = datetime.now()
            elapsed_delta = current_time - self.break_start_time
            elapsed_minutes = int(elapsed_delta.total_seconds() / 60)

            self.break_time_label.configure(text=f"你已经休息 {elapsed_minutes} 分钟")

            # 每秒更新一次
            self.break_timer_id = self.root.after(1000, self.update_break_time_display)

    def show_popup_countdown(
        self,
        duration,
        callback,
        title="休息提醒",
        image_dir=POPUP_IMAGE_DIR,
        image_font_color=POPUP_IMAGE_FONT_COLOR,
        is_keep_aspect_ratio=POPUP_IS_KEEP_ASPECT_RATIO,
    ):
        popup = customtkinter.CTkToplevel(self.root)
        popup.title(title)
        popup.overrideredirect(True)  # 移除边框
        popup_width = 600  # Increased size
        popup_height = 300  # Increased size
        # 如果有相关的全局配置，则优先使用全局配置
        if POPUP_WIDTH:
            popup_width = POPUP_WIDTH
        if POPUP_HEIGHT:
            popup_height = POPUP_HEIGHT

        # --- Align Popup to Bottom-Right --- START

        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)

        # 默认初始化窗口 popup.winfo_width() 会等于 1 。
        # 这里是判断如果窗口大小初始化不正常，就动态设置为屏幕的 0.12 倍，解决分辨率问题
        popup_width = (
            int(screen_width * 0.12) if popup.winfo_width() <= 1 else popup_width
        )
        popup_height = (
            int(screen_height * 0.12) if popup.winfo_height() <= 1 else popup_height
        )
        
        # 尝试在图片文件夹下随机加载图片
        image_path = ""
        if os.path.isdir(image_dir):
            # List all files in the directory
            all_files = os.listdir(image_dir)
            # Define common image file extensions
            # You can expand this list if you have other formats
            image_extensions = ('.png', '.jpg', '.jpeg')
            # Filter out non-image files
            image_files = [f for f in all_files if f.lower().endswith(image_extensions)]
            if image_files:
                # 如果存在图片文件
                print(image_files)
                image_path = image_dir + random.choice(image_files)
                print(image_path)
            
        
        # 根据图片的长宽和配置来综合确定窗口大小
        background_image_tk = None
        if image_path and os.path.exists(image_path):
            try:
                pil_image = Image.open(image_path)
                # 确定图片的原始大小和长宽比
                original_image_width = 0
                original_image_height = 0
                if pil_image:
                    original_image_width, original_image_height = pil_image.size
                image_aspect_ratio = original_image_width / original_image_height
                # 确定图片的大小，
                # is_keep_aspect_ratio==True是固定高度，根据图片长宽比来动态调整高度.
                # 否则固定窗口大小
                if is_keep_aspect_ratio:
                    calculated_width = int(popup_height * image_aspect_ratio)
                    popup_width = calculated_width
                popup_height = popup_height
                background_image_tk = True
            except Exception as e:
                print(f"加载或处理背景图片失败: {e}")
                background_image_tk = None  # 如果加载失败，则不使用图片

        popup.update_idletasks()
        x_coordinate = screen_width - int(popup_width * 1.05) - 100
        y_coordinate = screen_height - int(popup_height * 1.05) - 100  # Adjust slightly for taskbar
        popup.geometry(f"{popup_width}x{popup_height}+{x_coordinate}+{y_coordinate}")
        # --- Align Popup to Bottom-Right --- END

        popup.transient(self.root)
        popup.grab_set()
        popup.attributes("-topmost", True)  # Keep popup on top
        

        # --- 背景图片处理部分 ---
        # 根据是否有背景图片选择使用 CTkCanvas 或 CTkFrame 作为容器
        if background_image_tk and pil_image:
            # 调整图片大小以适应弹窗
            # 使用 Image.LANCZOS 算法进行高质量缩放
            pil_image = pil_image.resize((popup.winfo_width(), popup.winfo_height()), Image.LANCZOS)
            background_image_tk = ImageTk.PhotoImage(pil_image)
            # 使用 CTkCanvas 来显示背景图片
            canvas = customtkinter.CTkCanvas(
                popup,
                width=popup.winfo_width(), # 使用当前窗口（经过DPI调整）的大小，从而覆盖整个窗口
                height=popup.winfo_height(),
                highlightthickness=0,  # highlightthickness=0 移除 Canvas 边框
                bd=0,  # bd=0 移除 borderwidth
                relief="flat",
            )
            canvas.pack(expand=True, padx=0, pady=0, ipadx=0, ipady=0)
            canvas.create_image(
                popup.winfo_width() / 2,
                popup.winfo_height() / 2,
                image=background_image_tk,
                anchor="center",
            )  # 将图片放置在 Canvas 的居中位置
            canvas.background_image = (
                background_image_tk  # 将图片引用保存到 Canvas，防止被垃圾回收
            )

            # 倒计时标签现在放置在 Canvas 上
            font_size = POPUP_FONT_SIZE if POPUP_FONT_SIZE else 140
            font_args_popup = (
                {"font": (FONT_NAME, font_size, "bold")}
                if FONT_LOADED
                else {"font": customtkinter.CTkFont(size=font_size, weight="bold")}
            )
            # 标签背景设置为透明 (fg_color="transparent")，确保图片能显示出来
            # 文本颜色建议设为白色或与背景对比鲜明的颜色
            label = customtkinter.CTkLabel(
                canvas,
                text="",
                fg_color="transparent",
                text_color=image_font_color,
                **font_args_popup,
            )
            # 使用 create_window 将标签放置在 Canvas 中央
            canvas.create_window(
                popup.winfo_width() / 2,
                popup.winfo_height() / 2,
                window=label,
                anchor="center",
            )
        else:
            # 如果没有背景图片，则回退到使用 CTkFrame
            # Use a frame for centering content within the popup
            popup_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
            popup_frame.pack(expand=True, fill="both")
            popup_frame.grid_rowconfigure(0, weight=1)
            popup_frame.grid_columnconfigure(0, weight=1)

            # Apply custom font if loaded, increase size for countdown
            font_size = POPUP_FONT_SIZE if POPUP_FONT_SIZE else 140
            font_args_popup = (
                {"font": (FONT_NAME, font_size, "bold")}
                if FONT_LOADED
                else {"font": customtkinter.CTkFont(size=font_size, weight="bold")}
            )
            label = customtkinter.CTkLabel(popup_frame, text="", **font_args_popup)
            label.grid(row=0, column=0, sticky="nsew")  # Center using grid

        def update_popup_timer(secs):
            if secs >= 0:
                label.configure(text=f"{secs}")
                popup.after_id = popup.after(1000, update_popup_timer, secs - 1)
            else:
                popup.destroy()
                if callback:
                    callback()

        update_popup_timer(duration)

        # Handle closing the popup manually
        def on_popup_close():
            if hasattr(popup, "after_id"):
                try:
                    popup.after_cancel(popup.after_id)
                except ValueError:
                    pass  # Ignore if ID is invalid (already cancelled/finished)
            popup.destroy()
            # If popup closed manually during break, still call the end break logic
            # but don't reschedule short break if it was a short break popup
            if callback == self.end_short_break:
                self.end_short_break()  # Run end logic (plays sound, potentially resumes)
                # Crucially, DO NOT reschedule the next short break here
            elif callback == self.end_long_break:
                self.end_long_break()  # Run end logic

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

    # pause_media_if_enabled函数已被移除，使用更精确的媒体状态检测逻辑替代

    def stop_timer_and_return(self):
        if self.current_timer_id:
            self.root.after_cancel(self.current_timer_id)
            self.current_timer_id = None
        if self.short_break_timer_id:
            try:  # Add try-except for robustness
                self.root.after_cancel(self.short_break_timer_id)
                self.short_break_timer_id = None
            except ValueError:
                pass  # Timer might have already fired or been cancelled
            except AttributeError:  # Handle cases where after_id might not exist
                pass

        # 取消休息时间显示的定时器（如果存在）
        if hasattr(self, "break_timer_id") and self.break_timer_id:
            try:
                self.root.after_cancel(self.break_timer_id)
                self.break_timer_id = None
            except ValueError:
                pass
            except AttributeError:
                pass

        # 取消暂停计时器（如果存在）
        if hasattr(self, "pause_timer_id") and self.pause_timer_id:
            try:
                self.root.after_cancel(self.pause_timer_id)
                self.pause_timer_id = None
            except ValueError:
                pass
            except AttributeError:
                pass

        self.paused = True
        self.is_paused_for_5min = False
        if self.start_time:
            self.record_learning_session(
                completed_cycle=False
            )  # Call the correct (second) implementation
            self.start_time = None
        self.media_paused_by_app = False  # Reset flag when stopping manually
        self.show_start_button()

    # --- REMOVED REDUNDANT record_learning_session METHOD ---

    def show_settings_view(self):
        """Opens the settings window."""
        if hasattr(self, "settings_window") and self.settings_window.winfo_exists():
            self.settings_window.focus()
        else:
            self.settings_window = SettingsPage(self.root, self)
            self.settings_window.protocol("WM_DELETE_WINDOW", self.on_settings_close)

    def on_settings_close(self):
        if hasattr(self, "settings_window"):
            self.settings_window.destroy()
            del self.settings_window  # Ensure reference is removed

    def show_learning_records(self):
        # Check if a records window already exists
        if hasattr(self, "records_window") and self.records_window.winfo_exists():
            self.records_window.lift()
            return

        self.records_window = customtkinter.CTkToplevel(self.root)
        self.records_window.title("学习记录")
        self.records_window.geometry("600x500")  # Give it more space
        self.records_window.transient(self.root)
        self.records_window.grab_set()

        # --- View Selection ---
        view_frame = customtkinter.CTkFrame(self.records_window, fg_color="transparent")
        view_frame.pack(pady=10, padx=20, fill="x")

        font_args_segmented = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        self.view_var = tk.StringVar(value="日")  # Default view
        segmented_button = customtkinter.CTkSegmentedButton(
            view_frame,
            values=["日", "周", "月", "年"],
            variable=self.view_var,
            command=self.update_records_display,  # Command to update text box
            **font_args_segmented,
        )
        segmented_button.pack(expand=True)

        # --- Records Text Area ---
        font_args_textbox = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        self.records_text = customtkinter.CTkTextbox(
            self.records_window, wrap="word", **font_args_textbox
        )
        self.records_text.pack(expand=True, fill="both", padx=20, pady=(0, 10))
        self.records_text.configure(state="disabled")  # Make read-only initially

        # --- Close Button ---
        font_args_button = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        close_button = customtkinter.CTkButton(
            self.records_window,
            text="关闭",
            command=self.records_window.destroy,
            **font_args_button,
        )
        close_button.pack(pady=10)

        # Load and display initial data (default view: Day)
        self.update_records_display(self.view_var.get())

    def update_records_display(self, selected_view):
        """Updates the records text box based on the selected view."""
        self.records_text.configure(state="normal")  # Enable editing
        self.records_text.delete("1.0", tk.END)

        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            daily_log = data.get("daily_log", {})
        except (FileNotFoundError, json.JSONDecodeError):
            daily_log = {}

        if not daily_log:
            self.records_text.insert(tk.END, "暂无学习记录。")
            self.records_text.configure(state="disabled")
            return

        # Sort dates for consistent display
        sorted_dates = sorted(daily_log.keys(), reverse=True)

        if selected_view == "日":
            self.display_daily_records(daily_log, sorted_dates)
        elif selected_view == "周":
            self.display_weekly_records(daily_log)
        elif selected_view == "月":
            self.display_monthly_records(daily_log)
        elif selected_view == "年":
            self.display_yearly_records(daily_log)

        self.records_text.configure(state="disabled")  # Make read-only again

    def display_daily_records(self, daily_log, sorted_dates):
        """Formats and displays daily records."""
        for date_str in sorted_dates:
            sessions_data = daily_log[date_str]
            self.records_text.insert(tk.END, f"{date_str}:\n")

            if isinstance(sessions_data, list):
                # New format: List of session dictionaries
                for session in sessions_data:
                    if isinstance(session, dict):
                        start_time_str = session.get("start_time", "N/A")
                        end_time_str = session.get("end_time", "N/A")
                        duration_sec = session.get("duration_seconds", 0)
                        duration_min = duration_sec / 60
                        completed = session.get("completed", False)
                        status = (
                            "完成"
                            if completed
                            else f"中断 ({session.get('cycle_fraction', 0.0):.2f}周期)"
                        )
                        # Try to format time nicely
                        try:
                            start_dt = datetime.fromisoformat(start_time_str)
                            start_formatted = start_dt.strftime("%H:%M:%S")
                        except (ValueError, TypeError):
                            start_formatted = start_time_str
                        try:
                            end_dt = datetime.fromisoformat(end_time_str)
                            end_formatted = end_dt.strftime("%H:%M:%S")
                        except (ValueError, TypeError):
                            end_formatted = end_time_str

                        self.records_text.insert(
                            tk.END,
                            f"  - {start_formatted} -> {end_formatted} ({duration_min:.1f}分钟) - {status}\n",
                        )
                    else:
                        self.records_text.insert(tk.END, "  - [无效或格式错误的记录]\n")
            elif isinstance(sessions_data, dict):
                # Old format: Dictionary with daily totals
                total_sec = sessions_data.get("seconds", 0)
                total_cyc = sessions_data.get("cycles", 0.0)
                total_min = total_sec / 60
                # Remove the prefix '[旧格式数据]'
                self.records_text.insert(
                    tk.END,
                    f"  - 总时长: {total_min:.1f} 分钟, 总周期: {total_cyc:.2f}\n",
                )
            else:
                # Unknown format
                self.records_text.insert(tk.END, "  - [未知格式数据]\n")
            self.records_text.insert(tk.END, "\n")  # Add space between days

    # --- Placeholder functions for other views ---
    def display_weekly_records(self, daily_log):
        """Aggregates and displays records by week."""
        weekly_data = {}
        for date_str, sessions_data in daily_log.items():
            try:
                date_obj = datetime.fromisoformat(date_str)
                # Get ISO week number and year
                year, week, _ = date_obj.isocalendar()
                week_key = f"{year}-W{week:02d}"

                if week_key not in weekly_data:
                    weekly_data[week_key] = {
                        "total_seconds": 0,
                        "total_cycles": 0.0,
                        "start_date": date_obj,
                        "end_date": date_obj,
                    }
                else:
                    # Update start/end dates for the week range
                    weekly_data[week_key]["start_date"] = min(
                        weekly_data[week_key]["start_date"], date_obj
                    )
                    weekly_data[week_key]["end_date"] = max(
                        weekly_data[week_key]["end_date"], date_obj
                    )

                # Aggregate data based on format
                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if isinstance(session, dict):
                            weekly_data[week_key]["total_seconds"] += session.get(
                                "duration_seconds", 0
                            )
                            weekly_data[week_key]["total_cycles"] += session.get(
                                "cycle_fraction",
                                1.0 if session.get("completed", False) else 0.0,
                            )
                elif isinstance(sessions_data, dict):
                    weekly_data[week_key]["total_seconds"] += sessions_data.get(
                        "seconds", 0
                    )
                    weekly_data[week_key]["total_cycles"] += sessions_data.get(
                        "cycles", 0.0
                    )

            except ValueError:
                continue  # Skip invalid date strings

        if not weekly_data:
            self.records_text.insert(tk.END, "暂无周记录数据。\n")
            return

        # Sort weeks chronologically (descending)
        sorted_weeks = sorted(weekly_data.keys(), reverse=True)

        for week_key in sorted_weeks:
            data = weekly_data[week_key]
            total_min = data["total_seconds"] / 60
            start_date_str = data["start_date"].strftime("%Y-%m-%d")
            end_date_str = data["end_date"].strftime("%Y-%m-%d")
            self.records_text.insert(
                tk.END, f"{week_key} ({start_date_str} 至 {end_date_str}):\n"
            )
            self.records_text.insert(
                tk.END,
                f"  - 总时长: {total_min:.1f} 分钟, 总周期: {data['total_cycles']:.2f}\n\n",
            )

    def display_monthly_records(self, daily_log):
        """Aggregates and displays records by month."""
        monthly_data = {}
        for date_str, sessions_data in daily_log.items():
            try:
                date_obj = datetime.fromisoformat(date_str)
                month_key = date_obj.strftime("%Y-%m")  # Format as YYYY-MM

                if month_key not in monthly_data:
                    monthly_data[month_key] = {"total_seconds": 0, "total_cycles": 0.0}

                # Aggregate data based on format
                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if isinstance(session, dict):
                            monthly_data[month_key]["total_seconds"] += session.get(
                                "duration_seconds", 0
                            )
                            monthly_data[month_key]["total_cycles"] += session.get(
                                "cycle_fraction",
                                1.0 if session.get("completed", False) else 0.0,
                            )
                elif isinstance(sessions_data, dict):
                    monthly_data[month_key]["total_seconds"] += sessions_data.get(
                        "seconds", 0
                    )
                    monthly_data[month_key]["total_cycles"] += sessions_data.get(
                        "cycles", 0.0
                    )

            except ValueError:
                continue  # Skip invalid date strings

        if not monthly_data:
            self.records_text.insert(tk.END, "暂无月记录数据。\n")
            return

        # Sort months chronologically (descending)
        sorted_months = sorted(monthly_data.keys(), reverse=True)

        for month_key in sorted_months:
            data = monthly_data[month_key]
            total_min = data["total_seconds"] / 60
            self.records_text.insert(tk.END, f"{month_key}:\n")
            self.records_text.insert(
                tk.END,
                f"  - 总时长: {total_min:.1f} 分钟, 总周期: {data['total_cycles']:.2f}\n\n",
            )

    def display_yearly_records(self, daily_log):
        """Aggregates and displays records by year."""
        yearly_data = {}
        for date_str, sessions_data in daily_log.items():
            try:
                date_obj = datetime.fromisoformat(date_str)
                year_key = str(date_obj.year)  # Format as YYYY

                if year_key not in yearly_data:
                    yearly_data[year_key] = {"total_seconds": 0, "total_cycles": 0.0}

                # Aggregate data based on format
                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if isinstance(session, dict):
                            yearly_data[year_key]["total_seconds"] += session.get(
                                "duration_seconds", 0
                            )
                            yearly_data[year_key]["total_cycles"] += session.get(
                                "cycle_fraction",
                                1.0 if session.get("completed", False) else 0.0,
                            )
                elif isinstance(sessions_data, dict):
                    yearly_data[year_key]["total_seconds"] += sessions_data.get(
                        "seconds", 0
                    )
                    yearly_data[year_key]["total_cycles"] += sessions_data.get(
                        "cycles", 0.0
                    )

            except ValueError:
                continue  # Skip invalid date strings

        if not yearly_data:
            self.records_text.insert(tk.END, "暂无年记录数据。\n")
            return

        # Sort years chronologically (descending)
        sorted_years = sorted(yearly_data.keys(), reverse=True)

        for year_key in sorted_years:
            data = yearly_data[year_key]
            total_min = data["total_seconds"] / 60
            self.records_text.insert(tk.END, f"{year_key}年:\n")
            self.records_text.insert(
                tk.END,
                f"  - 总时长: {total_min:.1f} 分钟, 总周期: {data['total_cycles']:.2f}\n\n",
            )

    def record_learning_session(self, completed_cycle=False):
        if self.start_time:
            end_time = datetime.now()
            # 使用总周期时间减去剩余时间来计算已学习时间
            # 这种方法更准确，不受暂停次数影响
            cycle_minutes = self.cycle_duration_var.get()
            total_seconds = cycle_minutes * 60
            duration_seconds = total_seconds - self.main_timer_seconds
            today_str = end_time.strftime("%Y-%m-%d")

            # Calculate cycle fraction
            if completed_cycle:
                cycle_fraction = 1.0
            else:
                # 使用总周期时间计算周期分数
                cycle_fraction = duration_seconds / total_seconds
                cycle_fraction = max(
                    0.0, min(1.0, cycle_fraction)
                )  # Clamp between 0 and 1

            session_data = {
                "start_time": self.start_time.strftime("%H:%M:%S"),
                "end_time": end_time.strftime("%H:%M:%S"),
                "duration_seconds": int(duration_seconds),
                "completed_cycle": completed_cycle,
                "cycle_fraction": cycle_fraction,
            }

            if today_str not in self.learning_data["daily_log"]:
                self.learning_data["daily_log"][today_str] = []
            self.learning_data["daily_log"][today_str].append(session_data)

            # Update totals only if the cycle was completed or partially completed
            self.learning_data["total_seconds"] = self.learning_data.get(
                "total_seconds", 0
            ) + int(duration_seconds * cycle_fraction)
            self.learning_data["total_cycles"] = (
                self.learning_data.get("total_cycles", 0) + cycle_fraction
            )

            self.save_data()
            self.update_overview_display()
            self.start_time = None  # Reset start time


# --- Main Execution ---
if __name__ == "__main__":
    # Initialize pygame mixer before creating the Tkinter root
    # sound_manager.init_mixer() # REMOVED - Initialization happens on import

    root = customtkinter.CTk()
    app = LearningApp(root)
    root.mainloop()

    # Quit pygame mixer when the application closes
    sound_manager.quit_mixer()
