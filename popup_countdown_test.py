import customtkinter
import tkinter as tk
import os
from datetime import datetime

FONT_NAME = "Alibaba PuHuiTi"
FONT_FILENAME = "Alibaba-PuHuiTi-Regular.ttf"
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), FONT_FILENAME)
FONT_LOADED = os.path.exists(FONT_PATH)

def show_popup_countdown(root, duration, callback, title="休息提醒"):
        popup = customtkinter.CTkToplevel(root)
        popup.title(title)
        popup.overrideredirect(True)  # 移除边框
        popup_width = 600 # Increased size
        popup_height = 300 # Increased size

        # --- Align Popup to Bottom-Right --- START
        popup.update_idletasks()  # 确保窗口尺寸已更新
        # screen_width = root.winfo_screenwidth()
        # screen_height = root.winfo_screenheight() 
        import ctypes
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        print(screen_width, screen_height)
        popup_width = int(screen_width*0.12) if popup.winfo_width() > 1 else 600
        popup_height = int(screen_height*0.12) if popup.winfo_height() > 1 else 300
        popup.update_idletasks() 
        print(popup_width, popup_height)
        x_coordinate = screen_width - popup_width*2-50
        y_coordinate = screen_height - popup_height*2 -50 # Adjust slightly for taskbar
        print(x_coordinate, y_coordinate)
        popup.geometry(f"{popup_width}x{popup_height}+{x_coordinate}+{y_coordinate}")
    
        # --- Align Popup to Bottom-Right --- END

        popup.transient(root)
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
                    pass
            popup.destroy()
            if callback:
                callback()
        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

# 测试入口
if __name__ == "__main__":
    root = customtkinter.CTk()
    root.withdraw()  # 隐藏主窗口
    def on_countdown_end():
        print("倒计时结束！")
        root.destroy()
    show_popup_countdown(root, 10, on_countdown_end, title="测试弹窗倒计时")
    root.mainloop()