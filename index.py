import os
import cv2
import numpy as np
import pyautogui
import time

def find_and_click(img_name):
    # 读取要查找的图像
    image_to_find = cv2.imread(img_name)

    # 如果图像未加载，输出一条消息并返回
    if image_to_find is None:
        print(f"Image {img_name} not found.")
        return

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

    # 如果未找到匹配，跳过当前循环
    if loc[0].size == 0:
        return

    # 画矩形
    for pt in zip(*loc[::-1]):
        cv2.rectangle(screenshot_cv, pt, (pt[0] + image_to_find.shape[1], pt[1] + image_to_find.shape[0]), (0, 255, 0),2)
        x, y = pt
        w, h = image_to_find.shape[:-1]
        x += h // 2
        y += w // 2

        pyautogui.click(x, y)

    # 显示结果
    # cv2.imshow("Result", screenshot_cv)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

def run():
    while True:
        # 每秒运行一次的代码
        print("This code will run every second.")

        # 暂停一秒
        # time.sleep(3)

        # 获取当前目录中的所有文件名
        files = os.listdir(".")

        # 检查每个文件名是否以 .png 结尾
        for file in files:
            if file.endswith(".png"):
                # 调用图像识别和点击方法
                find_and_click(file)

run()
