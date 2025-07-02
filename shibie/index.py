import os
import cv2
import numpy as np
import pyautogui
import time
import keyboard

def find_and_click(img_name):
    image_paths = []
    if os.path.isdir(img_name):
        for file in os.listdir(img_name):
            full_path = os.path.join(img_name, file)
            if os.path.isdir(full_path):
                image_paths.extend(find_and_click(full_path))
            elif file.endswith('.png'):
                image_paths.append(full_path)
    elif img_name.endswith('.png'):
        image_paths.append(img_name)
    return image_paths


def move_mouse_to_image(file_path):

    # 使用 pyautogui 查找图片位置
    print(file_path)

    image_to_find = cv2.imread(file_path)
    # 获取屏幕截图
    screenshot = pyautogui.screenshot()

    # 将截图转换为OpenCV格式
    screenshot_cv = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_RGB2BGR)

    # 在屏幕截图上查找图像
    result = cv2.matchTemplate(screenshot_cv, image_to_find, cv2.TM_CCOEFF_NORMED)

    # 设定阈值
    threshold = 0.8
    loc = np.where(result >= threshold)

    # 画矩形
    for pt in zip(*loc[::-1]):
        cv2.rectangle(screenshot_cv, pt, (pt[0] + image_to_find.shape[1], pt[1] + image_to_find.shape[0]), (0, 255, 0),
                      2)
        x, y = pt
        w, h = image_to_find.shape[:-1]
        x += h // 2
        y += w // 2

        pyautogui.click(x, y)

def run():
    #退出程序
    keyboard.add_hotkey('esc', lambda: os._exit(0))
    # 查找图片路径
    paths = find_and_click(os.path.dirname(os.path.abspath(__file__)))
    while True:
        time.sleep(0.5)
        for file in paths:
            # 识别图片
            move_mouse_to_image(file)

run()