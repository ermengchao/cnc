import requests
import yaml
import time
import sys
from login import login
from logout import logout
from test import test
from stay_alive import stay_alive_1, stay_alive_2

# 读取配置文件
with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

# 用户输入配置
userId = input("请输入校园网账号：")
config["payload"]["userId"] = userId

password = input("请输入校园网密码：")
config["payload"]["password"] = password

# 修改配置文件
with open("config.yaml", 'w', encoding = "utf-8") as file:
    yaml.dump(config, file)
print("用户配置已修改！")

result = test()
if result == 0:
    print("用户已离线！即将执行自动登录脚本...")
    time.sleep(2)
    login()

elif result == 1:
    print("用户在线！")

else:
    print("请您检查是否正处于学校范围，或者是否已经接入校园网...")
    print(result)
    sys.exit(0)

print("是否需要保持在线?(yes/no)")
while(True):
    choice = input()
    if choice == "yes" or choice == "y":
        print("请选择保持登入的模式...(1/2)")
        while True:
            method = int(input())
            if method == 1 or method == 2:
                break
            else:
                print("请输入 1 或 2...")
        if method == 1:
            stay_alive_1
        else:
            stay_alive_2

    elif choice == "no" or choice == "n":
        print("退出脚本...")
        break
    
    else:
        print("请输入 yes 或 no")