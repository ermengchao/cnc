import requests
import yaml

# 读取配置文件
with open("config.yaml", 'r', encoding = "utf-8") as file:
    config = yaml.safe_load(file)

def logout():
    try:
        post_response = requests.post(config["urls"]["logout"], data = config["payload"]["logout"], headers = config["headers"])
        if post_response.status_code == 200:
            print("登出成功！")
            return 1
        else:
            print("登出失败！")
            return 0

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    logout()