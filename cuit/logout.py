import requests

try:
    response = requests.post('http://10.254.241.19/eportal/InterFace.do?method=logout')
    if response.status_code == 200:
        print("🥳 已成功发送注销请求！")
    else:
        print(f"😟 注销请求返回了非200状态码: {response.status_code}")
except Exception as e:
    print(f"😔 注销请求失败: {e}")