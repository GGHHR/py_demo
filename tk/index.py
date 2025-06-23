import tkinter as tk

# 定义全局颜色列表
COLORS = ["#FF5733", "#33FF57", "#3357FF", "#F333FF", "#33FFF3"]

def button_click():
    """按钮点击事件处理函数"""
    try:
        # 从按钮文本中提取点击次数并加1
        click_count = int(button.cget("text").split()[-1]) + 1
    except (ValueError, IndexError):
        # 如果解析失败，重置为1
        click_count = 1
    # 更新按钮文本
    button.config(text=f"按钮被点击了 {click_count} 次")
    # 更新信息标签
    label.config(text=f"你点击了按钮 {click_count} 次！")
    # 改变按钮背景颜色
    button.config(bg=COLORS[click_count % len(COLORS)])
    # 根据点击次数奇偶性改变窗口背景
    window.config(bg="#F0F0F0" if click_count % 2 == 0 else "#E0E0E0")

def reset_clicks():
    """重置点击次数和界面状态"""
    button.config(text="按钮被点击了 0 次")
    label.config(text="点击下方按钮查看效果")
    button.config(bg="#4CAF50")
    window.config(bg="#F0F0F0")

# 创建主窗口并设置属性
window = tk.Tk()
window.title("Tkinter 按钮示例")
window.geometry("500x400")
window.configure(bg="#F0F0F0")

# 添加标题标签
title_label = tk.Label(
    window,
    text="Tkinter 按钮演示",
    font=("Arial", 20, "bold"),
    fg="#333333",
    bg="#F0F0F0"
)
title_label.pack(pady=20)

# 添加信息标签
label = tk.Label(
    window,
    text="点击下方按钮查看效果",
    font=("Arial", 14),
    fg="#555555",
    bg="#F0F0F0"
)
label.pack(pady=10)

# 创建并添加主按钮
button = tk.Button(
    window,
    text="按钮被点击了 0 次",
    font=("Arial", 14, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10,
    relief="raised",
    borderwidth=3,
    command=button_click
)
button.pack(pady=30)

# 添加重置按钮
reset_button = tk.Button(
    window,
    text="重置",
    font=("Arial", 12),
    bg="#FF5733",
    fg="white",
    command=reset_clicks
)
reset_button.pack(pady=10)

# 添加使用说明
instructions = tk.Label(
    window,
    text="提示：每次点击按钮会改变按钮文本、颜色和窗口背景",
    font=("Arial", 10),
    fg="#888888",
    bg="#F0F0F0"
)
instructions.pack(side="bottom", pady=10)

# 启动主事件循环
window.mainloop()