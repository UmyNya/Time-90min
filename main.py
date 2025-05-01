import tkinter as tk
from tkinter import messagebox, font, ttk # Import ttk and font
import time
import random
import threading
import json
from datetime import datetime, timedelta
import os
import winsound # For sound on Windows
import sound_manager # Import the new sound module
import ctypes # Import ctypes for DPI awareness

# Constants
MAIN_TIMER_DURATION = 90 * 60  # 90 minutes in seconds
SHORT_BREAK_TIMER_DURATION = 10  # 10 seconds
LONG_BREAK_TIMER_DURATION = 20 * 60 # 20 minutes in seconds
SHORT_BREAK_MIN_INTERVAL = 3 * 60 # 3 minutes in seconds
SHORT_BREAK_MAX_INTERVAL = 5 * 60 # 5 minutes in seconds
DATA_FILE = "learning_data.json"

# UI Style Constants (Inspired by Target Image)
BG_COLOR = "#2c2c2c" # Dark background
FG_COLOR = "#ffffff" # White text
ACCENT_COLOR = "#4a4a4a" # Slightly lighter gray for accents/sidebar
BUTTON_BG = "#007aff" # Blue for primary buttons
BUTTON_FG = "white"
SECONDARY_BUTTON_BG = "#555555" # Gray for secondary buttons
SECONDARY_BUTTON_FG = "white"
FONT_FAMILY = "Segoe UI"
FONT_SIZE_SMALL = 9
FONT_SIZE_NORMAL = 12 # Increased for clarity
FONT_SIZE_LARGE = 20 # Increased for clarity
FONT_SIZE_TIMER = 80 # Increased timer font size further

# --- DPI Awareness (Attempt to fix blurriness on Windows) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # For Windows 8.1+
except AttributeError:
    try:
        ctypes.windll.user32.SetProcessDPIAware() # For Windows Vista+
    except AttributeError:
        pass # Not supported on older Windows

class LearningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学习助手")
        # Double the initial size
        self.root.geometry("1600x1000") 
        self.root.configure(bg=BG_COLOR)
        # Double the minsize accordingly
        self.root.minsize(1400, 900)

        # --- Style Configuration --- 
        self.style = ttk.Style()
        self.style.theme_use('clam') # Use a theme that allows more customization

        # General Frame Style
        self.style.configure('TFrame', background=BG_COLOR)
        self.style.configure('Sidebar.TFrame', background=ACCENT_COLOR)
        self.style.configure('Main.TFrame', background=BG_COLOR)

        # General Label Style
        self.style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        self.style.configure('Sidebar.TLabel', background=ACCENT_COLOR, foreground=FG_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        self.style.configure('Header.TLabel', background=BG_COLOR, foreground=FG_COLOR, font=(FONT_FAMILY, FONT_SIZE_LARGE, 'bold'))
        self.style.configure('SidebarHeader.TLabel', background=ACCENT_COLOR, foreground=FG_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL, 'bold'))
        # Explicitly re-configure Timer.TLabel to ensure the font size is applied
        self.style.configure('Timer.TLabel', background=BG_COLOR, foreground=FG_COLOR, font=(FONT_FAMILY, FONT_SIZE_TIMER, 'bold'))

        # Button Styles
        self.style.configure('TButton', 
                             font=(FONT_FAMILY, FONT_SIZE_LARGE, 'bold'), # Increased font size
                             padding=(40, 20), # Increased padding significantly
                             relief='flat', 
                             borderwidth=0,
                             focuscolor=self.style.lookup('TButton','background')) # Remove focus ring
        self.style.map('TButton', 
                       background=[('!active', BUTTON_BG), ('active', '#005ecb')],
                       foreground=[('!active', BUTTON_FG), ('active', BUTTON_FG)])

        self.style.configure('Secondary.TButton', 
                             font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                             padding=(15, 8),
                             relief='flat',
                             borderwidth=0,
                             focuscolor=self.style.lookup('Secondary.TButton','background'))
        self.style.map('Secondary.TButton', 
                       background=[('!active', SECONDARY_BUTTON_BG), ('active', '#777777')],
                       foreground=[('!active', SECONDARY_BUTTON_FG), ('active', SECONDARY_BUTTON_FG)])

        # Treeview Style (for records)
        self.style.configure('Treeview', 
                             background=ACCENT_COLOR, # Match sidebar
                             foreground=FG_COLOR, 
                             fieldbackground=ACCENT_COLOR,
                             font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                             borderwidth=0,
                             rowheight=50, # Increase row height
                             relief='flat')
        self.style.configure('Treeview.Heading', 
                             font=(FONT_FAMILY, FONT_SIZE_NORMAL, 'bold'),
                             background=SECONDARY_BUTTON_BG, # Use secondary button color for heading
                             foreground=SECONDARY_BUTTON_FG,
                             padding=5,
                             relief='flat')
        self.style.map('Treeview.Heading', background=[('active', SECONDARY_BUTTON_BG)]) # Keep heading color
        # Remove treeview borders
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        # Default font for tk widgets if needed
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        self.root.option_add("*Font", default_font)

        self.main_timer_seconds = MAIN_TIMER_DURATION
        self.long_break_seconds = LONG_BREAK_TIMER_DURATION
        self.current_timer_id = None
        self.short_break_timer_id = None
        self.start_time = None
        self.paused = False

        self.load_data()
        self.create_main_layout() # First create the layout with main_frame
        self.show_start_button() # Then show the start button view

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.learning_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.learning_data = {"total_seconds": 0, "total_cycles": 0, "daily_log": {}}
        else:
            self.learning_data = {"total_seconds": 0, "total_cycles": 0, "daily_log": {}}

    def save_data(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.learning_data, f, indent=4)
        except IOError as e:
            messagebox.showerror("错误", f"无法保存学习数据: {e}")

    def create_main_layout(self):
        """Creates the main layout with a central area and a sidebar."""
        self.clear_window()
        # Main container frame
        container = ttk.Frame(self.root, style='TFrame')
        container.pack(expand=True, fill='both')

        # Add uniform option to maintain strict column proportions
        container.grid_columnconfigure(0, weight=3, uniform='group1') # Main area takes more space
        container.grid_columnconfigure(1, weight=1, uniform='group1') # Sidebar
        container.grid_rowconfigure(0, weight=1)

        # --- Main Content Area --- 
        self.main_frame = ttk.Frame(container, padding=20, style='Main.TFrame')
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        self.main_frame.grid_rowconfigure(0, weight=1) # Allow content to expand vertically
        self.main_frame.grid_columnconfigure(0, weight=1) # Allow content to expand horizontally

        # --- Sidebar Area --- 
        self.sidebar_frame = ttk.Frame(container, padding="15 15 15 15", style='Sidebar.TFrame')
        self.sidebar_frame.grid(row=0, column=1, sticky='nsew')
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        # Configure rows for sidebar content
        self.sidebar_frame.grid_rowconfigure(0, weight=0) # Overview Title
        self.sidebar_frame.grid_rowconfigure(1, weight=0) # Overview Content
        self.sidebar_frame.grid_rowconfigure(2, weight=0) # Spacer
        self.sidebar_frame.grid_rowconfigure(3, weight=0) # Records Button
        self.sidebar_frame.grid_rowconfigure(4, weight=1) # Bottom Spacer

        # Populate Sidebar
        ttk.Label(self.sidebar_frame, text="学习概览", style='SidebarHeader.TLabel').grid(row=0, column=0, pady=(0, 5), sticky='ew')
        # Placeholder for overview data - you'll need to update this
        self.overview_label_hours = ttk.Label(self.sidebar_frame, text="总时长: ...", style='Sidebar.TLabel')
        self.overview_label_hours.grid(row=1, column=0, pady=2, sticky='ew')
        self.overview_label_cycles = ttk.Label(self.sidebar_frame, text="总周期: ...", style='Sidebar.TLabel')
        self.overview_label_cycles.grid(row=2, column=0, pady=(0, 20), sticky='ew')

        record_button = ttk.Button(self.sidebar_frame, text="学习记录", command=self.show_learning_records, style='Secondary.TButton')
        record_button.grid(row=3, column=0, pady=10, sticky='ew')

        self.update_overview_display() # Initial update

    def show_start_button(self):
        """Displays the start button in the main frame."""
        self.clear_main_frame()
        # Reset grid configurations explicitly before applying new ones
        # Reset rows potentially used by countdown view
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_rowconfigure(3, weight=0)
        # Reset column used by both views
        self.main_frame.grid_columnconfigure(0, weight=0)

        # Configure grid to center the button using spacer rows
        self.main_frame.grid_rowconfigure(0, weight=1) # Space above button
        self.main_frame.grid_rowconfigure(1, weight=0) # Button row
        self.main_frame.grid_rowconfigure(2, weight=1) # Space below button
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Button uses the 'TButton' style configured in __init__
        start_button = ttk.Button(self.main_frame, text="开始 90 分钟学习", command=self.start_main_timer, style='TButton')
        # Place button in the middle row (row 1)
        start_button.grid(row=1, column=0, sticky='')

    def update_overview_display(self):
        """Updates the learning overview labels in the sidebar."""
        if hasattr(self, 'overview_label_hours'): # Check if sidebar exists
            total_seconds = self.learning_data.get("total_seconds", 0)
            total_cycles = self.learning_data.get("total_cycles", 0)
            total_hours = total_seconds / 3600
            self.overview_label_hours.config(text=f"总时长: {total_hours:.2f} 小时")
            self.overview_label_cycles.config(text=f"总周期: {total_cycles:.2f} 个")

    def create_countdown_view(self):
        """Displays the countdown timer in the main frame."""
        self.clear_main_frame()

        # Reset grid configurations explicitly before applying new ones
        # Reset row potentially used by start button view
        self.main_frame.grid_rowconfigure(0, weight=0)
        # Reset column used by both views
        self.main_frame.grid_columnconfigure(0, weight=0)
        # Reset other rows just in case (although start button only uses row 0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_rowconfigure(3, weight=0)

        # Configure main frame for countdown display - add weights for centering
        self.main_frame.grid_rowconfigure(0, weight=1) # Space above timer
        self.main_frame.grid_rowconfigure(1, weight=0) # Timer label row (no extra weight)
        self.main_frame.grid_rowconfigure(2, weight=0) # Button row
        self.main_frame.grid_rowconfigure(3, weight=1) # Space below button
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Switch to tk.Label and set font directly as ttk.Style might not apply correctly
        self.timer_label = tk.Label(self.main_frame, text="", 
                                  font=(FONT_FAMILY, FONT_SIZE_TIMER, 'bold'), 
                                  fg=FG_COLOR, 
                                  bg=BG_COLOR) # Need to set colors manually for tk.Label
        # Place timer in row 1, remove sticky to allow centering
        self.timer_label.grid(row=1, column=0, pady=20, sticky='') 

        stop_button = ttk.Button(self.main_frame, text="停止并记录", command=self.stop_timer_and_return, style='Secondary.TButton')
        # Place button in row 2
        stop_button.grid(row=2, column=0, pady=20, sticky='') # Center button

        self.update_timer_display()

    def clear_window(self):
        """Clears all widgets from the root window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_main_frame(self):
        """Clears all widgets from the main content frame."""
        if hasattr(self, 'main_frame'):
            for widget in self.main_frame.winfo_children():
                widget.destroy()

    def start_main_timer(self):
        self.start_time = datetime.now()
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
            self.main_timer_seconds -= 1
            self.current_timer_id = self.root.after(1000, self.run_main_timer)
        else:
            # Play sound when main timer finishes using the sound manager
            sound_manager.play_notification_sound('Timer End')

            self.record_learning_session(completed_cycle=True)
            self.trigger_long_break()

    def update_timer_display(self):
        mins, secs = divmod(self.main_timer_seconds, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        if hasattr(self, 'timer_label'): # Check if label exists
             self.timer_label.config(text=time_str)

    def schedule_short_break(self):
        if self.paused or self.main_timer_seconds <= 0:
            return
        delay = random.randint(SHORT_BREAK_MIN_INTERVAL, SHORT_BREAK_MAX_INTERVAL)
        # Ensure break doesn't start too close to the end
        if self.main_timer_seconds > delay + SHORT_BREAK_TIMER_DURATION:
            self.short_break_timer_id = self.root.after(delay * 1000, self.trigger_short_break)

    def trigger_short_break(self):
        if self.paused or self.main_timer_seconds <= 0:
             return # Don't trigger if main timer stopped

        # Play sound BEFORE showing the popup
        sound_manager.play_notification_sound('Short Break Start')

        # Now show the popup countdown
        self.show_popup_countdown(SHORT_BREAK_TIMER_DURATION, self.schedule_short_break)

    def trigger_long_break(self):
        # Play sound BEFORE showing the popup
        sound_manager.play_notification_sound('Long Break Start')

        # Now show the popup countdown
        self.show_popup_countdown(LONG_BREAK_TIMER_DURATION, self.root.quit, width=300, height=300, font_size=100)

    # Renamed from show_fullscreen_countdown
    def show_popup_countdown(self, duration, callback_on_finish, width=600, height=600, font_size=150): # Increased default size and font size
        # Pause main timer during breaks
        was_paused = self.paused
        self.paused = True
        if self.current_timer_id:
            self.root.after_cancel(self.current_timer_id)
            self.current_timer_id = None
        if self.short_break_timer_id:
            self.root.after_cancel(self.short_break_timer_id)
            self.short_break_timer_id = None

        popup = tk.Toplevel(self.root)
        popup.title("休息一下")
        popup.attributes('-topmost', True) # Keep on top
        popup.configure(bg='black') # Simple black background for popup
        popup.overrideredirect(True) # Remove window decorations for a cleaner popup

        # Calculate position for bottom-right corner
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = screen_width - width - 20  # 20px offset from edge
        y = screen_height - height - 50 # 50px offset from bottom (taskbar)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        popup_label = tk.Label(popup, text="", font=(FONT_FAMILY, font_size), fg="white", bg="black")
        popup_label.pack(expand=True, fill='both')

        # Sound is now played *before* this popup is shown (in trigger_short_break/trigger_long_break)

        remaining_time = duration

        def update_popup():
            nonlocal remaining_time
            if remaining_time >= 0:
                mins, secs = divmod(remaining_time, 60)
                # Display seconds only for short break, MM:SS for long break
                if duration == SHORT_BREAK_TIMER_DURATION:
                    time_str = f"{secs}"
                else:
                    time_str = f"{mins:02d}:{secs:02d}"
                popup_label.config(text=time_str)
                remaining_time -= 1
                # Use popup's after method
                popup.after_id = popup.after(1000, update_popup)
            else:
                # Play sound when countdown finishes
                if duration == SHORT_BREAK_TIMER_DURATION:
                    sound_manager.play_notification_sound('Short Break End')
                # Consider adding a sound for long break end if needed
                # elif duration == LONG_BREAK_TIMER_DURATION:
                #     sound_manager.play_notification_sound('Long Break End')
                popup.destroy()
                # Resume main timer only if it wasn't already paused externally
                if not was_paused:
                    self.paused = False
                    self.run_main_timer() # Resume main timer
                if callback_on_finish:
                    callback_on_finish() # Schedule next break or quit

        update_popup()

    def stop_timer_and_return(self):
        if self.current_timer_id:
            self.root.after_cancel(self.current_timer_id)
            self.current_timer_id = None
        if self.short_break_timer_id:
            self.root.after_cancel(self.short_break_timer_id)
            self.short_break_timer_id = None
        
        # Also cancel any active popup timer
        # Find the popup window if it exists and cancel its timer
        for win in self.root.winfo_children():
            if isinstance(win, tk.Toplevel) and hasattr(win, 'after_id'):
                try:
                    win.after_cancel(win.after_id)
                    win.destroy()
                except tk.TclError:
                    pass # Ignore if already cancelled/destroyed

        self.paused = True # Ensure timers don't restart unexpectedly

        if self.start_time:
            self.record_learning_session(completed_cycle=False)
            self.start_time = None # Reset start time

        self.show_start_button() # Go back to the start button view

    def record_learning_session(self, completed_cycle):
        if not self.start_time:
            return # Avoid recording if timer wasn't started

        end_time = datetime.now()
        duration_seconds = (end_time - self.start_time).total_seconds()
        # Cap duration at the intended cycle length if completed
        if completed_cycle:
             duration_seconds = min(duration_seconds, MAIN_TIMER_DURATION)

        cycle_fraction = duration_seconds / MAIN_TIMER_DURATION
        today = end_time.strftime("%Y-%m-%d")

        self.learning_data["total_seconds"] = self.learning_data.get("total_seconds", 0) + duration_seconds
        self.learning_data["total_cycles"] = self.learning_data.get("total_cycles", 0) + cycle_fraction

        if today not in self.learning_data["daily_log"]:
            self.learning_data["daily_log"][today] = {"seconds": 0, "cycles": 0}

        self.learning_data["daily_log"][today]["seconds"] += duration_seconds
        self.learning_data["daily_log"][today]["cycles"] += cycle_fraction

        self.save_data()
        self.start_time = None # Reset after recording
        self.update_overview_display() # Update sidebar after recording

    def show_learning_records(self):
        """Displays the learning records in the main frame."""
        self.clear_main_frame()

        # Configure main frame for records display
        self.main_frame.grid_rowconfigure(0, weight=0) # Title
        self.main_frame.grid_rowconfigure(1, weight=0) # View buttons
        self.main_frame.grid_rowconfigure(2, weight=1) # Log display (takes most space)
        self.main_frame.grid_rowconfigure(3, weight=0) # Back button
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Title --- 
        ttk.Label(self.main_frame, text="学习记录", style='Header.TLabel').grid(row=0, column=0, pady=(0, 15), sticky='n')

        # --- View Selection Buttons --- 
        view_button_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        view_button_frame.grid(row=1, column=0, pady=10, sticky='ew')
        view_button_frame.grid_columnconfigure((0,1,2,3), weight=1) # Distribute buttons evenly

        ttk.Button(view_button_frame, text="日视图", command=lambda: self.display_records_in_tree('day'), style='Secondary.TButton').grid(row=0, column=0, padx=5, sticky='ew')
        ttk.Button(view_button_frame, text="周视图", command=lambda: self.display_records_in_tree('week'), style='Secondary.TButton').grid(row=0, column=1, padx=5, sticky='ew')
        ttk.Button(view_button_frame, text="月视图", command=lambda: self.display_records_in_tree('month'), style='Secondary.TButton').grid(row=0, column=2, padx=5, sticky='ew')
        ttk.Button(view_button_frame, text="年视图", command=lambda: self.display_records_in_tree('year'), style='Secondary.TButton').grid(row=0, column=3, padx=5, sticky='ew')

        # --- Log Display Area (Using Treeview) --- 
        # Frame to hold treeview and scrollbar
        self.log_display_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        self.log_display_frame.grid(row=2, column=0, sticky='nsew', pady=5)
        self.log_display_frame.grid_columnconfigure(0, weight=1)
        self.log_display_frame.grid_rowconfigure(0, weight=1)

        # Initial display (e.g., daily)
        self.display_records_in_tree('day')

        # --- Back Button --- 
        back_button = ttk.Button(self.main_frame, text="返回", command=self.show_start_button, style='Secondary.TButton')
        back_button.grid(row=3, column=0, pady=(10, 0), sticky='') # Center button

    def display_records_in_tree(self, view_type):
        """Displays aggregated records in the Treeview within the log_display_frame."""
        # Clear previous log display in the specific frame
        for widget in self.log_display_frame.winfo_children():
            widget.destroy()

        # Use Treeview for a structured look
        columns = ('period', 'hours', 'cycles')
        tree = ttk.Treeview(self.log_display_frame, columns=columns, show='headings', style='Treeview')

        # Define headings
        tree.heading('period', text='时间段')
        tree.heading('hours', text='时长 (小时)')
        tree.heading('cycles', text='周期数')

        # Configure column widths (adjust as needed)
        tree.column('period', anchor=tk.W, width=200, stretch=tk.YES)
        tree.column('hours', anchor=tk.CENTER, width=100, stretch=tk.NO)
        tree.column('cycles', anchor=tk.CENTER, width=100, stretch=tk.NO)

        aggregated_data = self.aggregate_data(view_type)

        # Sort keys (dates, weeks, months, years) reverse chronologically
        sorted_keys = sorted(aggregated_data.keys(), reverse=True)

        for key in sorted_keys:
            data = aggregated_data[key]
            hours = data.get("seconds", 0) / 3600
            cycles = data.get("cycles", 0)
            tree.insert('', tk.END, values=(key, f"{hours:.2f}", f"{cycles:.2f}"))

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.log_display_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        # Use grid for tree and scrollbar
        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

    def aggregate_data(self, view_type):
        daily_log = self.learning_data.get("daily_log", {})
        aggregated = {}

        for date_str, data in daily_log.items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                seconds = data.get("seconds", 0)
                cycles = data.get("cycles", 0)

                if view_type == 'day':
                    key = date_str
                elif view_type == 'week':
                    # ISO week date: year, week number, weekday
                    year, week_num, _ = date_obj.isocalendar()
                    # Find the start date of the week (Monday)
                    start_of_week = date_obj - timedelta(days=date_obj.weekday())
                    key = f"{start_of_week.strftime('%Y-%m-%d')} (W{week_num:02d})"
                elif view_type == 'month':
                    key = date_obj.strftime("%Y-%m")
                elif view_type == 'year':
                    key = date_obj.strftime("%Y")
                else:
                    continue # Should not happen

                if key not in aggregated:
                    aggregated[key] = {"seconds": 0, "cycles": 0}

                aggregated[key]["seconds"] += seconds
                aggregated[key]["cycles"] += cycles
            except ValueError:
                print(f"Skipping invalid date format: {date_str}") # Log error
                continue

        return aggregated

if __name__ == "__main__":
    root = tk.Tk()
    app = LearningApp(root)
    root.mainloop()