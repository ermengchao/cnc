import requests
import yaml
from test import test

# 读取配置文件
with open("config.yaml", 'r', encoding="utf-8") as file:
    config = yaml.safe_load(file)

def login():
    try:
        post_response = requests.post(config["urls"]["login"], data = config["payload"]["login"], headers = config["headers"])
        if result:=test() == 1:
            print("登入成功！")
            return 1
        else:
            print("登入失败！")
            return 0

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    login()