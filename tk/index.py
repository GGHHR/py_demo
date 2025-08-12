import tkinter as tk
from tkinter import messagebox

def center_window(win, width, height):
    # 获取屏幕宽高
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    # 计算左上角坐标
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

def show_input():
    user_input = entry.get()
    messagebox.showinfo("输入内容", f"你输入了: {user_input}")

root = tk.Tk()
root.title("居中窗口示例")

# 先居中窗口
center_window(root, 300, 150)

entry = tk.Entry(root, font=("Arial", 14))
entry.pack(pady=20)

btn = tk.Button(root, text="显示输入", command=show_input, font=("Arial", 12))
btn.pack()

root.mainloop()
