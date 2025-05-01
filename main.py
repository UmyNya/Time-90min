import tkinter as tk
from tkinter import messagebox, font # Removed ttk import as we'll use customtkinter
import time
import random
import threading # Import threading
import json
from datetime import datetime, timedelta
import os
# import winsound # Remove winsound import
import sound_manager # Import the sound_manager module
import ctypes
import win32api
import win32con
import customtkinter

# --- Load Custom Font ---
FONT_NAME = "Alibaba PuHuiTi" # Name to refer to the font
FONT_FILENAME = "Alibaba-PuHuiTi-Regular.ttf"
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), FONT_FILENAME)

# Function to load font (consider error handling)
def load_custom_font():
    try:
        # This part might be tricky with CTk/Tkinter directly loading TTF
        # Often, the font needs to be installed system-wide or handled differently.
        # Let's try setting the default font for CTk widgets.
        # We'll define font tuples/objects later using this name if needed.
        # Note: Direct TTF loading in Tkinter/CTk without system install is complex.
        # A common approach is to assume the font is installed or use libraries
        # that handle font loading better if CTk doesn't do it automatically.
        # For now, we'll define the font name and try applying it.
        if not os.path.exists(FONT_PATH):
            print(f"Warning: Font file not found at {FONT_PATH}. Please copy it there.")
            return False
        # CustomTkinter might pick up fonts differently. Let's define the font object.
        # We will apply this font object to specific widgets.
        print(f"Font file found at {FONT_PATH}. Attempting to use '{FONT_NAME}'.")
        return True
    except Exception as e:
        print(f"Error loading custom font: {e}")
        return False

FONT_LOADED = load_custom_font()

# --- Constants ---
MAIN_TIMER_DURATION = 90 * 60  # 90 minutes in seconds
SHORT_BREAK_TIMER_DURATION = 10  # 10 seconds
LONG_BREAK_TIMER_DURATION = 20 * 60 # 20 minutes in seconds
SHORT_BREAK_MIN_INTERVAL = 3 * 60 # 3 minutes in seconds
SHORT_BREAK_MAX_INTERVAL = 5 * 60 # 5 minutes in seconds
DATA_FILE = "learning_data.json"

# --- DPI Awareness (Attempt to fix blurriness on Windows) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # For Windows 8.1+
except AttributeError:
    try:
        ctypes.windll.user32.SetProcessDPIAware() # For Windows Vista+
    except AttributeError:
        pass # Not supported on older Windows

# --- Sound Manager (Simplified) --- << REMOVED OLD WINSOUND CODE

# --- Remove internal sound functions --- << REMOVED DUPLICATE OLD WINSOUND CODE

# --- Media Control --- (Added Section)
def toggle_media_playback():
    """Simulates pressing the Play/Pause media key."""
    try:
        # VK_MEDIA_PLAY_PAUSE = 0xB3
        win32api.keybd_event(win32con.VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        time.sleep(0.1) # Small delay might be needed
        win32api.keybd_event(win32con.VK_MEDIA_PLAY_PAUSE, 0, win32con.KEYEVENTF_KEYUP, 0)
        print("Toggled media playback (Play/Pause key simulated).")
    except Exception as e:
        print(f"Error simulating media key: {e}")

# --- Settings Page using CustomTkinter ---
class SettingsPage(customtkinter.CTkToplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.title("设置")
        self.geometry("350x300") # Increased height further for new switch
        self.transient(parent)
        self.grab_set()
        self.app = app_instance

        # No need to set appearance mode here if set globally

        container = customtkinter.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=20, pady=20)

        # Apply custom font if loaded
        font_args = {"font": (FONT_NAME, 16, "bold")} if FONT_LOADED else {"font": customtkinter.CTkFont(size=16, weight="bold")}
        settings_label = customtkinter.CTkLabel(container, text="设置", **font_args)
        settings_label.pack(pady=(0, 15))

        # --- Auto-pause media setting ---
        pause_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        pause_frame.pack(fill="x", pady=5) # Reduced pady

        font_args_label = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        pause_label = customtkinter.CTkLabel(pause_frame, text="休息时自动暂停媒体:", **font_args_label)
        pause_label.pack(side="left", padx=(0, 10))

        # Use CTkSwitch
        self.auto_pause_switch = customtkinter.CTkSwitch(
            pause_frame,
            text="", # Keep text empty
            variable=self.app.auto_pause_media_var,
            onvalue=True,
            offvalue=False,
            command=self.app.save_data # Use save_data which now includes this var
        )
        # Ensure the switch reflects the loaded state
        if self.app.auto_pause_media_var.get():
            self.auto_pause_switch.select()
        else:
            self.auto_pause_switch.deselect()
        self.auto_pause_switch.pack(side="right")

        # --- Auto-resume media setting --- (Added)
        resume_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        resume_frame.pack(fill="x", pady=5) # Reduced pady

        resume_label = customtkinter.CTkLabel(resume_frame, text="休息后继续自动播放:", **font_args_label)
        resume_label.pack(side="left", padx=(0, 10))

        self.auto_resume_switch = customtkinter.CTkSwitch(
            resume_frame,
            text="",
            variable=self.app.auto_resume_media_var, # Link to new variable
            onvalue=True,
            offvalue=False,
            command=self.app.save_data # Save when changed
        )
        # Ensure the switch reflects the loaded state
        if self.app.auto_resume_media_var.get():
            self.auto_resume_switch.select()
        else:
            self.auto_resume_switch.deselect()
        self.auto_resume_switch.pack(side="right")

        # --- Clear Data Button ---
        font_args_button = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        clear_button = customtkinter.CTkButton(
            container,
            text="清空学习数据",
            command=self.confirm_clear_data,
            fg_color="#D32F2F", # Red color for destructive action
            hover_color="#B71C1C", # Darker red on hover
            **font_args_button
        )
        clear_button.pack(pady=(15, 5))

        # --- Close Button ---
        close_button = customtkinter.CTkButton(container, text="关闭", command=self.destroy, **font_args_button)
        close_button.pack(pady=(5, 0))

    def confirm_clear_data(self):
        confirmed = messagebox.askyesno(
            "确认操作",
            "您确定要清空所有学习记录吗？\n此操作无法撤销！",
            parent=self # Ensure dialog appears over the settings window
        )
        if confirmed:
            self.app.clear_learning_data()
            messagebox.showinfo("操作完成", "学习数据已清空。", parent=self)

# --- Main Application Class using CustomTkinter ---
class LearningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学习助手")
        # Change window size to 600x600
        self.root.geometry("500x400") # User requested size
        self.root.minsize(400, 300) # User requested min size

        # --- Set CustomTkinter Appearance ---
        customtkinter.set_appearance_mode("System") # Options: "System", "Dark", "Light"
        customtkinter.set_default_color_theme("blue") # Options: "blue", "green", "dark-blue"

        self.main_timer_seconds = MAIN_TIMER_DURATION
        self.long_break_seconds = LONG_BREAK_TIMER_DURATION
        self.current_timer_id = None
        self.short_break_timer_id = None
        self.start_time = None # Tracks start of the 90-min cycle
        self.session_start_time = None # Tracks start of the current learning segment (since last 'start')
        self.paused = False
        self.media_paused_by_app = False # Flag to track if media was paused by the app

        # Load data first
        self.load_data()
        # Initialize BooleanVars AFTER loading data, using the loaded values
        self.auto_pause_media_var = tk.BooleanVar(value=self.learning_data.get('auto_pause_media', True))
        self.auto_resume_media_var = tk.BooleanVar(value=self.learning_data.get('auto_resume_media', True)) # Added

        self.create_main_layout() # Create layout using CTk widgets
        self.show_start_button() # Show initial view

    def load_data(self):
        self.default_data = {
            "total_seconds": 0,
            "total_cycles": 0,
            "daily_log": {},
            "auto_pause_media": True, # Default value
            "auto_resume_media": True # Default value for new setting (Added)
        }
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    loaded_data = json.load(f)
                    # Ensure all default keys exist
                    self.learning_data = {**self.default_data, **loaded_data}
            except (json.JSONDecodeError, IOError):
                self.learning_data = self.default_data.copy()
        else:
            self.learning_data = self.default_data.copy()

    def save_data(self):
        # Update settings from BooleanVars before saving
        self.learning_data['auto_pause_media'] = self.auto_pause_media_var.get()
        self.learning_data['auto_resume_media'] = self.auto_resume_media_var.get() # Added
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.learning_data, f, indent=4)
        except IOError as e:
            messagebox.showerror("错误", f"无法保存学习数据: {e}")

    def clear_learning_data(self):
        """Resets learning data to defaults and saves."""
        print("Clearing learning data...")
        self.learning_data = self.default_data.copy() # Reset to default
        # Ensure the settings are preserved from the current UI state
        self.learning_data['auto_pause_media'] = self.auto_pause_media_var.get()
        self.learning_data['auto_resume_media'] = self.auto_resume_media_var.get() # Added
        self.save_data() # Save the cleared data
        self.update_overview_display() # Update the UI
        print("Learning data cleared and saved.")

    def create_main_layout(self):
        self.clear_window()
        # Main container frame using CTkFrame
        container = customtkinter.CTkFrame(self.root, fg_color="transparent") # Use root's bg
        container.pack(expand=True, fill='both')

        # Adjust column weights: Give sidebar more relative weight (e.g., 2:1 ratio)
        container.grid_columnconfigure(0, weight=2, uniform='group1') # Main content area weight reduced
        container.grid_columnconfigure(1, weight=1, uniform='group1') # Sidebar weight remains 1 (relative increase)
        container.grid_rowconfigure(0, weight=1)

        # --- Main Content Area (CTkFrame) ---
        self.main_frame = customtkinter.CTkFrame(container, corner_radius=10) # Add some rounding
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        # Configure main frame grid for content (title removed)
        self.main_frame.grid_rowconfigure(0, weight=1) # Row for the main content (start button/timer)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Add App Name Title to Main Frame --- << REMOVED

        # --- Sidebar Area (CTkFrame) ---
        self.sidebar_frame = customtkinter.CTkFrame(container, width=150, corner_radius=10) # Add matching corner radius
        self.sidebar_frame.grid(row=0, column=1, sticky='nsew', padx=(0, 10), pady=10) # Add padx for alignment
        self.sidebar_frame.grid_propagate(False) # Prevent resizing based on content
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        # Configure rows for sidebar content (Removed row 0 for App Name)
        self.sidebar_frame.grid_rowconfigure(0, weight=0) # Overview Title (was row 1)
        self.sidebar_frame.grid_rowconfigure(1, weight=0) # Overview Content Hours (was row 2)
        self.sidebar_frame.grid_rowconfigure(2, weight=0) # Overview Content Cycles (was row 3)
        self.sidebar_frame.grid_rowconfigure(3, weight=0, minsize=20) # Spacer (was row 4)
        self.sidebar_frame.grid_rowconfigure(4, weight=0) # Records Button (was row 5)
        self.sidebar_frame.grid_rowconfigure(5, weight=0) # Settings Button (was row 6)
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Bottom Spacer (was row 7)

        # Populate Sidebar with CTk Widgets (Removed App Name Label)
        font_args_overview_title = {"font": (FONT_NAME, 16, "bold")} if FONT_LOADED else {"font": customtkinter.CTkFont(size=16, weight="bold")} # Increased size from 14
        overview_title = customtkinter.CTkLabel(self.sidebar_frame, text="学习概览", **font_args_overview_title)
        overview_title.grid(row=0, column=0, pady=(10, 5), padx=20, sticky='ew') # Adjusted row index

        font_args_overview_text = {"font": (FONT_NAME, 14)} if FONT_LOADED else {"font": customtkinter.CTkFont(size=14)} # Increased size from 12
        self.overview_label_hours = customtkinter.CTkLabel(self.sidebar_frame, text="总时长: ...", anchor='w', **font_args_overview_text)
        self.overview_label_hours.grid(row=1, column=0, pady=2, padx=20, sticky='ew') # Adjusted row index
        self.overview_label_cycles = customtkinter.CTkLabel(self.sidebar_frame, text="总周期: ...", anchor='w', **font_args_overview_text)
        self.overview_label_cycles.grid(row=2, column=0, pady=(0, 0), padx=20, sticky='ew') # Adjusted row index

        font_args_sidebar_button = {"font": (FONT_NAME, 14)} if FONT_LOADED else {"font": customtkinter.CTkFont(size=14)} # Increased size from 12
        record_button = customtkinter.CTkButton(self.sidebar_frame, text="学习记录", command=self.show_learning_records, **font_args_sidebar_button)
        record_button.grid(row=4, column=0, pady=10, padx=30, sticky='ew') # Adjusted row index

        settings_button = customtkinter.CTkButton(self.sidebar_frame, text="设置", command=self.show_settings_view, **font_args_sidebar_button)
        settings_button.grid(row=5, column=0, pady=10, padx=30, sticky='ew') # Adjusted row index

        self.update_overview_display() # Initial update

    def show_start_button(self):
        self.clear_main_frame() # Use original clear_main_frame now
        # Center the button in the main frame
        content_frame = self.main_frame
        content_frame.grid_rowconfigure(0, weight=1) # Space above button
        content_frame.grid_rowconfigure(1, weight=0) # Button row
        content_frame.grid_rowconfigure(2, weight=1) # Space below button
        content_frame.grid_columnconfigure(0, weight=1)

        # Apply custom font if loaded
        font_args_start_button = {"font": (FONT_NAME, 24, 'bold')} if FONT_LOADED else {"font": customtkinter.CTkFont(size=24, weight='bold')}
        start_button = customtkinter.CTkButton(content_frame, text="开始 90 分钟学习",
                                             command=self.start_main_timer,
                                             width=300, height=80,
                                             **font_args_start_button)
        start_button.grid(row=1, column=0, sticky='') # Place button in the middle row (row 1)

    def update_overview_display(self):
        if hasattr(self, 'overview_label_hours'):
            total_seconds = self.learning_data.get("total_seconds", 0)
            total_cycles = self.learning_data.get("total_cycles", 0)
            total_hours = total_seconds / 3600
            self.overview_label_hours.configure(text=f"总时长: {total_hours:.2f} 小时")
            self.overview_label_cycles.configure(text=f"总周期: {total_cycles:.2f} 个")

    def create_countdown_view(self):
        self.clear_main_frame() # Use original clear_main_frame now
        content_frame = self.main_frame
        # Center content
        content_frame.grid_rowconfigure(0, weight=1) # Space above timer
        content_frame.grid_rowconfigure(1, weight=0) # Timer label row
        content_frame.grid_rowconfigure(2, weight=0) # Session duration label row (NEW)
        content_frame.grid_rowconfigure(3, weight=0) # Stop button row (Shifted down)
        content_frame.grid_rowconfigure(4, weight=1) # Space below button (Shifted down)
        content_frame.grid_columnconfigure(0, weight=1)

        self.timer_label = customtkinter.CTkLabel(content_frame, text="",
                                                font=customtkinter.CTkFont(size=80, weight='bold'))
        self.timer_label.grid(row=1, column=0, pady=(20, 5), sticky='') # Adjusted pady

        # --- Add Session Duration Label ---
        font_args_session = {"font": (FONT_NAME, 14)} if FONT_LOADED else {"font": customtkinter.CTkFont(size=14)}
        self.session_duration_label = customtkinter.CTkLabel(content_frame, text="你已学习 00:00 分钟", **font_args_session)
        self.session_duration_label.grid(row=2, column=0, pady=(0, 20), sticky='') # Place below timer

        stop_button = customtkinter.CTkButton(content_frame, text="停止并记录", command=self.stop_timer_and_return)
        stop_button.grid(row=3, column=0, pady=20, sticky='') # Place button in row 3

        self.update_timer_display() # Initial display update
        self.update_session_duration_display() # Initial session duration update

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_main_frame(self):
        if hasattr(self, 'main_frame'):
            for widget in self.main_frame.winfo_children():
                widget.destroy()

    def start_main_timer(self):
        self.start_time = datetime.now()
        self.session_start_time = datetime.now() # Initialize session start time here
        self.main_timer_seconds = MAIN_TIMER_DURATION
        self.paused = False
        self.create_countdown_view()
        self.run_main_timer()
        self.schedule_short_break()

    def run_main_timer(self):
        if self.paused:
            return
        if self.main_timer_seconds > 0:
            self.update_timer_display()
            self.update_session_duration_display()
            self.main_timer_seconds -= 1
            self.current_timer_id = self.root.after(1000, self.run_main_timer)
        else:
            # Use sound_manager for timer end sound
            # sound_manager.play_notification_sound('timer_end') # Assuming sound_manager handles different sounds
            sound_manager.play_notification_sound() # Use default if only one sound
            self.record_learning_session(completed_cycle=True)
            self.trigger_long_break()

    def update_timer_display(self):
        mins, secs = divmod(self.main_timer_seconds, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        if hasattr(self, 'timer_label'):
             self.timer_label.configure(text=time_str)

    def update_session_duration_display(self):
        """Updates the label showing the duration of the current learning segment."""
        if self.session_start_time and hasattr(self, 'session_duration_label'):
            elapsed_delta = datetime.now() - self.session_start_time
            elapsed_seconds = int(elapsed_delta.total_seconds())
            mins, secs = divmod(elapsed_seconds, 60)
            # Display as MM:SS minutes
            duration_str = f"你已学习 {mins:02d}:{secs:02d} "
            self.session_duration_label.configure(text=duration_str)

    def schedule_short_break(self):
        if self.paused or self.main_timer_seconds <= 0:
            return
        delay = random.randint(SHORT_BREAK_MIN_INTERVAL, SHORT_BREAK_MAX_INTERVAL)
        if self.main_timer_seconds > delay + SHORT_BREAK_TIMER_DURATION:
            self.short_break_timer_id = self.root.after(delay * 1000, self.trigger_short_break)

    def trigger_short_break(self):
        if self.paused or self.main_timer_seconds <= 0:
             return
        # Play sound using sound_manager BEFORE popup
        print("[Trigger Short Break] Playing sound first...")
        # sound_manager.play_notification_sound('short_break_start') # Assuming specific sound
        sound_manager.play_notification_sound() # Use default if only one sound
        print("[Trigger Short Break] Sound finished, showing popup.")
        self.pause_media_if_enabled()
        # Show the larger popup
        self.show_popup_countdown(SHORT_BREAK_TIMER_DURATION, self.end_short_break, "休息一下")

    def trigger_long_break(self):
        print("[Trigger Long Break] Playing sound first...")
        # sound_manager.play_notification_sound('long_break_start') # Assuming specific sound
        sound_manager.play_notification_sound() # Use default if only one sound
        print("[Trigger Long Break] Sound finished, showing popup.")
        self.pause_media_if_enabled()
        self.show_popup_countdown(LONG_BREAK_TIMER_DURATION, self.end_long_break, "长时间休息")

    def end_short_break(self):
        print("[End Short Break] Playing sound...")
        # sound_manager.play_notification_sound('short_break_end') # Assuming specific sound
        sound_manager.play_notification_sound() # Use default if only one sound
        print("[End Short Break] Sound finished.")
        # Resume media only if auto-resume is enabled AND media was paused by the app
        if self.auto_resume_media_var.get() and self.media_paused_by_app:
            print("[End Short Break] Resuming media playback...")
            toggle_media_playback()
        self.media_paused_by_app = False # Reset flag
        self.schedule_short_break() # Schedule the next one

    def end_long_break(self):
        print("[End Long Break] Playing sound...")
        # sound_manager.play_notification_sound('long_break_end') # Assuming specific sound
        sound_manager.play_notification_sound() # Use default if only one sound
        print("[End Long Break] Sound finished.")
        # Resume media only if auto-resume is enabled AND media was paused by the app
        if self.auto_resume_media_var.get() and self.media_paused_by_app:
            print("[End Long Break] Resuming media playback...")
            toggle_media_playback()
        self.media_paused_by_app = False # Reset flag
        self.show_start_button() # Return to start view after long break

    def show_popup_countdown(self, duration, callback, title="休息提醒"):
        popup = customtkinter.CTkToplevel(self.root)
        popup.title(title)
        popup.overrideredirect(True)  # 移除边框
        popup_width = 600 # Increased size
        popup_height = 300 # Increased size

        # --- Align Popup to Bottom-Right --- START
        
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        popup_width = int(screen_width*0.12) if popup.winfo_width() > 1 else 600
        popup_height = int(screen_height*0.12) if popup.winfo_height() > 1 else 300
        popup.update_idletasks() 
        x_coordinate = screen_width - popup_width
        y_coordinate = screen_height - popup_height - 40 # Adjust slightly for taskbar
        popup.geometry(f"{popup_width}x{popup_height}+{x_coordinate}+{y_coordinate}")
        # --- Align Popup to Bottom-Right --- END

        popup.transient(self.root)
        popup.grab_set()
        popup.attributes("-topmost", True) # Keep popup on top

        # Use a frame for centering content within the popup
        popup_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        popup_frame.pack(expand=True, fill="both")
        popup_frame.grid_rowconfigure(0, weight=1)
        popup_frame.grid_columnconfigure(0, weight=1)

        # Apply custom font if loaded, increase size for countdown
        font_args_popup = {"font": (FONT_NAME, 140, 'bold')} if FONT_LOADED else {"font": customtkinter.CTkFont(size=140, weight='bold')}
        label = customtkinter.CTkLabel(popup_frame, text="", **font_args_popup)
        label.grid(row=0, column=0, sticky="nsew") # Center using grid

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
            if hasattr(popup, 'after_id'):
                try:
                    popup.after_cancel(popup.after_id)
                except ValueError:
                    pass # Ignore if ID is invalid (already cancelled/finished)
            popup.destroy()
            # If popup closed manually during break, still call the end break logic
            # but don't reschedule short break if it was a short break popup
            if callback == self.end_short_break:
                self.end_short_break() # Run end logic (plays sound, potentially resumes)
                # Crucially, DO NOT reschedule the next short break here
            elif callback == self.end_long_break:
                self.end_long_break() # Run end logic

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

    def pause_media_if_enabled(self):
        """Pauses media playback if the setting is enabled."""
        if self.auto_pause_media_var.get():
            # --- Ideal Check (Difficult to Implement Reliably) ---
            # TODO: Implement a reliable check for active media playback state.
            # This is complex as it requires interacting with OS audio sessions
            # or specific application APIs. Libraries like pycaw might help but add complexity.
            # For now, we send the pause key regardless, assuming it's harmless if already paused.
            # is_playing = check_if_media_is_playing() # Placeholder for the check
            # if not is_playing:
            #     print("Media not detected as playing. Skipping pause.")
            #     return
            # --------------------------------------------------------

            print("Auto-pause enabled. Simulating pause key...")
            toggle_media_playback()
            self.media_paused_by_app = True # Set flag indicating app paused media
        else:
            print("Auto-pause disabled. Media playback not affected.")
            self.media_paused_by_app = False # Ensure flag is false if auto-pause is off

    def stop_timer_and_return(self):
        if self.current_timer_id:
            self.root.after_cancel(self.current_timer_id)
            self.current_timer_id = None
        if self.short_break_timer_id:
            try: # Add try-except for robustness
                self.root.after_cancel(self.short_break_timer_id)
                self.short_break_timer_id = None
            except ValueError:
                pass # Timer might have already fired or been cancelled
            except AttributeError: # Handle cases where after_id might not exist
                pass

        self.paused = True
        if self.start_time:
            self.record_learning_session(completed_cycle=False) # Call the correct (second) implementation
            self.start_time = None
        self.media_paused_by_app = False # Reset flag when stopping manually
        self.show_start_button()

    # --- REMOVED REDUNDANT record_learning_session METHOD ---

    def show_settings_view(self):
        """Opens the settings window."""
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.focus()
        else:
            self.settings_window = SettingsPage(self.root, self)
            self.settings_window.protocol("WM_DELETE_WINDOW", self.on_settings_close)

    def on_settings_close(self):
        if hasattr(self, 'settings_window'):
            self.settings_window.destroy()
            del self.settings_window # Ensure reference is removed

    def show_learning_records(self):
        # Check if a records window already exists
        if hasattr(self, 'records_window') and self.records_window.winfo_exists():
            self.records_window.lift()
            return

        self.records_window = customtkinter.CTkToplevel(self.root)
        self.records_window.title("学习记录")
        self.records_window.geometry("600x500") # Give it more space
        self.records_window.transient(self.root)
        self.records_window.grab_set()

        # --- View Selection --- 
        view_frame = customtkinter.CTkFrame(self.records_window, fg_color="transparent")
        view_frame.pack(pady=10, padx=20, fill='x')

        font_args_segmented = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        self.view_var = tk.StringVar(value="日") # Default view
        segmented_button = customtkinter.CTkSegmentedButton(
            view_frame,
            values=["日", "周", "月", "年"],
            variable=self.view_var,
            command=self.update_records_display, # Command to update text box
            **font_args_segmented
        )
        segmented_button.pack(expand=True)

        # --- Records Text Area --- 
        font_args_textbox = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        self.records_text = customtkinter.CTkTextbox(self.records_window, wrap='word', **font_args_textbox)
        self.records_text.pack(expand=True, fill='both', padx=20, pady=(0, 10))
        self.records_text.configure(state='disabled') # Make read-only initially

        # --- Close Button --- 
        font_args_button = {"font": (FONT_NAME, 12)} if FONT_LOADED else {}
        close_button = customtkinter.CTkButton(self.records_window, text="关闭", command=self.records_window.destroy, **font_args_button)
        close_button.pack(pady=10)

        # Load and display initial data (default view: Day)
        self.update_records_display(self.view_var.get())

    def update_records_display(self, selected_view):
        """Updates the records text box based on the selected view."""
        self.records_text.configure(state='normal') # Enable editing
        self.records_text.delete('1.0', tk.END)

        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            daily_log = data.get('daily_log', {})
        except (FileNotFoundError, json.JSONDecodeError):
            daily_log = {}

        if not daily_log:
            self.records_text.insert(tk.END, "暂无学习记录。")
            self.records_text.configure(state='disabled')
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

        self.records_text.configure(state='disabled') # Make read-only again

    def display_daily_records(self, daily_log, sorted_dates):
        """Formats and displays daily records."""
        for date_str in sorted_dates:
            sessions_data = daily_log[date_str]
            self.records_text.insert(tk.END, f"{date_str}:\n")

            if isinstance(sessions_data, list):
                # New format: List of session dictionaries
                for session in sessions_data:
                    if isinstance(session, dict):
                        start_time_str = session.get('start_time', 'N/A')
                        end_time_str = session.get('end_time', 'N/A')
                        duration_sec = session.get('duration_seconds', 0)
                        duration_min = duration_sec / 60
                        completed = session.get('completed', False)
                        status = "完成" if completed else f"中断 ({session.get('cycle_fraction', 0.0):.2f}周期)"
                        # Try to format time nicely
                        try:
                            start_dt = datetime.fromisoformat(start_time_str)
                            start_formatted = start_dt.strftime('%H:%M:%S')
                        except (ValueError, TypeError):
                            start_formatted = start_time_str
                        try:
                            end_dt = datetime.fromisoformat(end_time_str)
                            end_formatted = end_dt.strftime('%H:%M:%S')
                        except (ValueError, TypeError):
                            end_formatted = end_time_str

                        self.records_text.insert(tk.END, f"  - {start_formatted} -> {end_formatted} ({duration_min:.1f}分钟) - {status}\n")
                    else:
                        self.records_text.insert(tk.END, "  - [无效或格式错误的记录]\n")
            elif isinstance(sessions_data, dict):
                # Old format: Dictionary with daily totals
                total_sec = sessions_data.get('seconds', 0)
                total_cyc = sessions_data.get('cycles', 0.0)
                total_min = total_sec / 60
                # Remove the prefix '[旧格式数据]' 
                self.records_text.insert(tk.END, f"  - 总时长: {total_min:.1f} 分钟, 总周期: {total_cyc:.2f}\n")
            else:
                # Unknown format
                self.records_text.insert(tk.END, "  - [未知格式数据]\n")
            self.records_text.insert(tk.END, "\n") # Add space between days

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
                    weekly_data[week_key] = {'total_seconds': 0, 'total_cycles': 0.0, 'start_date': date_obj, 'end_date': date_obj}
                else:
                    # Update start/end dates for the week range
                    weekly_data[week_key]['start_date'] = min(weekly_data[week_key]['start_date'], date_obj)
                    weekly_data[week_key]['end_date'] = max(weekly_data[week_key]['end_date'], date_obj)

                # Aggregate data based on format
                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if isinstance(session, dict):
                            weekly_data[week_key]['total_seconds'] += session.get('duration_seconds', 0)
                            weekly_data[week_key]['total_cycles'] += session.get('cycle_fraction', 1.0 if session.get('completed', False) else 0.0)
                elif isinstance(sessions_data, dict):
                    weekly_data[week_key]['total_seconds'] += sessions_data.get('seconds', 0)
                    weekly_data[week_key]['total_cycles'] += sessions_data.get('cycles', 0.0)

            except ValueError:
                continue # Skip invalid date strings

        if not weekly_data:
            self.records_text.insert(tk.END, "暂无周记录数据。\n")
            return

        # Sort weeks chronologically (descending)
        sorted_weeks = sorted(weekly_data.keys(), reverse=True)

        for week_key in sorted_weeks:
            data = weekly_data[week_key]
            total_min = data['total_seconds'] / 60
            start_date_str = data['start_date'].strftime('%Y-%m-%d')
            end_date_str = data['end_date'].strftime('%Y-%m-%d')
            self.records_text.insert(tk.END, f"{week_key} ({start_date_str} 至 {end_date_str}):\n")
            self.records_text.insert(tk.END, f"  - 总时长: {total_min:.1f} 分钟, 总周期: {data['total_cycles']:.2f}\n\n")

    def display_monthly_records(self, daily_log):
        """Aggregates and displays records by month."""
        monthly_data = {}
        for date_str, sessions_data in daily_log.items():
            try:
                date_obj = datetime.fromisoformat(date_str)
                month_key = date_obj.strftime('%Y-%m') # Format as YYYY-MM

                if month_key not in monthly_data:
                    monthly_data[month_key] = {'total_seconds': 0, 'total_cycles': 0.0}

                # Aggregate data based on format
                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if isinstance(session, dict):
                            monthly_data[month_key]['total_seconds'] += session.get('duration_seconds', 0)
                            monthly_data[month_key]['total_cycles'] += session.get('cycle_fraction', 1.0 if session.get('completed', False) else 0.0)
                elif isinstance(sessions_data, dict):
                    monthly_data[month_key]['total_seconds'] += sessions_data.get('seconds', 0)
                    monthly_data[month_key]['total_cycles'] += sessions_data.get('cycles', 0.0)

            except ValueError:
                continue # Skip invalid date strings

        if not monthly_data:
            self.records_text.insert(tk.END, "暂无月记录数据。\n")
            return

        # Sort months chronologically (descending)
        sorted_months = sorted(monthly_data.keys(), reverse=True)

        for month_key in sorted_months:
            data = monthly_data[month_key]
            total_min = data['total_seconds'] / 60
            self.records_text.insert(tk.END, f"{month_key}:\n")
            self.records_text.insert(tk.END, f"  - 总时长: {total_min:.1f} 分钟, 总周期: {data['total_cycles']:.2f}\n\n")

    def display_yearly_records(self, daily_log):
        """Aggregates and displays records by year."""
        yearly_data = {}
        for date_str, sessions_data in daily_log.items():
            try:
                date_obj = datetime.fromisoformat(date_str)
                year_key = str(date_obj.year) # Format as YYYY

                if year_key not in yearly_data:
                    yearly_data[year_key] = {'total_seconds': 0, 'total_cycles': 0.0}

                # Aggregate data based on format
                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if isinstance(session, dict):
                            yearly_data[year_key]['total_seconds'] += session.get('duration_seconds', 0)
                            yearly_data[year_key]['total_cycles'] += session.get('cycle_fraction', 1.0 if session.get('completed', False) else 0.0)
                elif isinstance(sessions_data, dict):
                    yearly_data[year_key]['total_seconds'] += sessions_data.get('seconds', 0)
                    yearly_data[year_key]['total_cycles'] += sessions_data.get('cycles', 0.0)

            except ValueError:
                continue # Skip invalid date strings

        if not yearly_data:
            self.records_text.insert(tk.END, "暂无年记录数据。\n")
            return

        # Sort years chronologically (descending)
        sorted_years = sorted(yearly_data.keys(), reverse=True)

        for year_key in sorted_years:
            data = yearly_data[year_key]
            total_min = data['total_seconds'] / 60
            self.records_text.insert(tk.END, f"{year_key}年:\n")
            self.records_text.insert(tk.END, f"  - 总时长: {total_min:.1f} 分钟, 总周期: {data['total_cycles']:.2f}\n\n")

    def record_learning_session(self, completed_cycle=False):
        if self.start_time:
            end_time = datetime.now()
            duration_seconds = (end_time - self.start_time).total_seconds()
            today_str = end_time.strftime("%Y-%m-%d")

            # Calculate cycle fraction
            if completed_cycle:
                cycle_fraction = 1.0
            else:
                elapsed_time = MAIN_TIMER_DURATION - self.main_timer_seconds
                cycle_fraction = elapsed_time / MAIN_TIMER_DURATION
                cycle_fraction = max(0.0, min(1.0, cycle_fraction)) # Clamp between 0 and 1

            session_data = {
                "start_time": self.start_time.strftime("%H:%M:%S"),
                "end_time": end_time.strftime("%H:%M:%S"),
                "duration_seconds": int(duration_seconds),
                "completed_cycle": completed_cycle,
                "cycle_fraction": cycle_fraction
            }

            if today_str not in self.learning_data["daily_log"]:
                self.learning_data["daily_log"][today_str] = []
            self.learning_data["daily_log"][today_str].append(session_data)

            # Update totals only if the cycle was completed or partially completed
            self.learning_data["total_seconds"] = self.learning_data.get("total_seconds", 0) + int(duration_seconds * cycle_fraction)
            self.learning_data["total_cycles"] = self.learning_data.get("total_cycles", 0) + cycle_fraction

            self.save_data()
            self.update_overview_display()
            self.start_time = None # Reset start time

# --- Main Execution ---
if __name__ == "__main__":
    # Initialize pygame mixer before creating the Tkinter root
    # sound_manager.init_mixer() # REMOVED - Initialization happens on import

    root = customtkinter.CTk()
    app = LearningApp(root)
    root.mainloop()

    # Quit pygame mixer when the application closes
    sound_manager.quit_mixer()