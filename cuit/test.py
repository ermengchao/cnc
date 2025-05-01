'''
    此脚本用于确认校园网连接状态。若成功连接，向 {schoolWebLoginURL} 发送 POST 请求时，会返回登录成功的 HTML 代码，反之则会返回登录界面的 HTML 代码。判断依据是 yaml 配置文件中的 target-code，包含一段 Javascript 代码用于重定向。
    虽然校园网提供接口 {getOnlineUserInfo} (curl "http://10.254.241.19/eportal/InterFace.do?method=getOnlineUserInfo")，但是还需要结合 {AuthInterface.js} 获取用户信息，略微复杂，故未采用。
'''

import requests
import yaml
import gzip

with open("config.yaml", 'r', encoding = "utf-8") as file:
    config = yaml.safe_load(file)

def test():
    post_response = requests.post(config["urls"]["schoolWebLoginURL"])

    if config["target_code"]["fail"] in post_response.text:
        return 0
    
    content = gzip.decompress(post_response.content).decode('gbk')
    if config["target_code"]["success"] in content:
        return 1
    
    return 2
    print(post_response.text)
    print(config["target-code"]["fail"] in post_response.text)

if __name__ == "__main__":
    print("测试结束，", end = '')
    if (result:=test()) == 1:
        print("登入成功！")
    elif result == 0:
        print("登入失败！")
    else:
        print("发生错误！")