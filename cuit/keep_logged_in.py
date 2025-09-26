import requests
import yaml
import time
import schedule
from login import login
from logout import logout
from test import test

# 读取配置文件
with open("config.yaml", 'r', encoding = "utf-8") as file:
    config = yaml.safe_load(file)

# 通过死循环不断运行登入脚本
def keep_logged_in_v1():
    while True:
        result = test()
        if result == 1:
            time.sleep(300)
        else:
            print("保持登录脚本运行失败。请检查配置或者是否处于校园网范围内...")

# 定期登出再登入
def keep_logged_in_v2():
    while True:
        login()
        if not login():
            print("保持登入脚本退出...")
            break
        schedule.every().day.at("5:00").do(logout)
        schedule.every().day.at("5:00").do(login)