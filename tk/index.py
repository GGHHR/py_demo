import tkinter as tk
from tkinter import messagebox
from playwright.sync_api import sync_playwright
import os
import re
import json


def url_to_filename(url):
    """
    【正向转换】将完整的URL转换为一个对操作系统安全的文件名。
    例如: 'https://example.com/user' -> 'example.com_user.json'
    """
    # 移除协议头 (http://, https://)
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]

    # 移除结尾的斜杠，避免文件名以_结尾
    if url.endswith("/"):
        url = url[:-1]

    # 替换所有对文件名无效的字符为下划线
    return re.sub(r'[\\/*?:"<>|]', "_", url) + ".json"


def filename_to_display_text(filename):
    """
    【反向转换】将安全文件名转换为用于在列表框中显示的可读文本。
    例如: 'example.com_user.json' -> 'example.com/user'
    """
    # 移除 .json 后缀
    text = filename[:-5]
    # 将下划线替换回斜杠
    return text.replace("_", "/")


def add_item():
    """
    处理添加网址、保存信息，并在列表中显示“美化后”的名称。
    """
    url_input = entry.get().strip()
    if url_input:
        if not os.path.exists("data"):
            os.makedirs("data")

        # 1. 将输入的URL转换为安全文件名
        file_name = url_to_filename(url_input)
        file_path = os.path.join("data", file_name)

        try:
            with sync_playwright() as p:
                executable = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
                browser = p.chromium.launch(headless=False, executable_path=executable)
                context = browser.new_context()
                page = context.new_page()
                page.goto(url_input)

                page.wait_for_event("close")

                storage_state = context.storage_state()
                # 注意：我们不再需要将原始URL存入JSON文件，因为文件名本身就是来源
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(storage_state, f, indent=4)

                browser.close()

            # 2. 将安全文件名转换为美化的显示文本
            display_text = filename_to_display_text(file_name)

            # 3. 将美化后的文本添加到列表框
            listbox.insert(tk.END, display_text)
            entry.delete(0, tk.END)
            messagebox.showinfo("成功", f"登录信息已保存至 {file_path}")

        except Exception as e:
            messagebox.showerror("错误", f"发生错误: {e}")

    else:
        messagebox.showwarning("提示", "请输入内容")


def load_items():
    """
    启动时加载data文件夹中的文件名，并将其转换为“美化版”显示在列表中。
    """
    data_dir = "data"
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                # 将读到的每个文件名都转换为美化的显示文本
                display_text = filename_to_display_text(filename)
                # 添加到列表框
                listbox.insert(tk.END, display_text)


# --- GUI 界面设置 ---
root = tk.Tk()
root.title("简单列表应用")
root.geometry("300x400")

entry = tk.Entry(root, width=30)
entry.pack(pady=10)

add_button = tk.Button(root, text="添加", command=add_item)
add_button.pack(pady=5)

listbox = tk.Listbox(root, width=35, height=15)
listbox.pack(pady=10)

# 程序启动时，加载并转换数据显示
load_items()

root.mainloop()