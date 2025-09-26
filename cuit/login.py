#!/usr/bin/env python3
import os
import sys
import requests
import re

def login():
    # 读取环境变量或交互式输入
    CUIT_USERID = os.getenv('CUIT_USERID')
    if not CUIT_USERID:
        CUIT_USERID = input("请输入账号: ")
        with open(os.path.expanduser('~/.zshrc'), 'a') as f:
            f.write(f'\nexport CUIT_USERID="{CUIT_USERID}"\n')

    CUIT_PASSWORD = os.getenv('CUIT_PASSWORD')
    if not CUIT_PASSWORD:
        CUIT_PASSWORD = input("请输入密码: ")
        with open(os.path.expanduser('~/.zshrc'), 'a') as f:
            f.write(f'\nexport CUIT_PASSWORD="{CUIT_PASSWORD}"\n')

    CUIT_SERVICE = os.getenv('CUIT_SERVICE')
    if not CUIT_SERVICE:
        CUIT_SERVICE = input("请选择服务(移动输入 1, 电信输入 2): ")
        if CUIT_SERVICE == "1":
            CUIT_SERVICE = "移动"
        elif CUIT_SERVICE == "2":
            CUIT_SERVICE = "电信"
        else:
            print("😡无效输入！请输入 1 (移动) 或 2 (电信)")
            sys.exit(1)
        with open(os.path.expanduser('~/.zshrc'), 'a') as f:
            f.write(f'\nexport CUIT_SERVICE="{CUIT_SERVICE}"\n')

    # 获取 wlanuserip
    try:
        res = requests.get('http://123.123.123.123', timeout=1)
        wlanuserip_match = re.search(r"wlanuserip=([^&']+)", res.text)
        if wlanuserip_match:
            wlanuserip = wlanuserip_match.group(1)
        else:
            print("😔未能提取 wlanuserip！")
            sys.exit(1)
    except Exception as e:
        print(f"😔获取 wlanuserip 失败: {e}")
        sys.exit(1)

    # 组装 queryString
    queryString = (
        f"wlanuserip={wlanuserip}%26wlanacname%3D97a2ecf6f720c9b94344e81caa687812"
        f"%26ssid%3D%26nasip%3D9146c4376ca4d4ab9a67a9844f8bc16d"
        f"%26snmpagentip%3D%26mac%3Dbd8f5f309cc69769d66831f103fe88ca"
        f"%26t%3Dwireless-v2%26url%3Dce94fa5d1476f4035bdffb297b90e6a80e35ca1c5603dac6"
        f"%26apmac%3D%26nasid%3D97a2ecf6f720c9b94344e81caa687812"
        f"%26vid%3D925d31c78b7e2db7%26port%3Df614e30cdb9a8059"
        f"%26nasportid%3D42f79eb53725d6ee652dfa421b44ee78e44b6411390f557927632a20f09105dcc3eca938f5c79281"
    )

    # 发起登录请求
    payload = {
        "userId": CUIT_USERID,
        "password": CUIT_PASSWORD,
        "service": CUIT_SERVICE,
        "queryString": queryString,
        "operatorPwd": "",
        "operatorUserId": "",
        "validcode": "",
        "passwordEncrypt": "false"
    }

    try:
        response = requests.post(
            'http://10.254.241.19/eportal/InterFace.do?method=login',
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            data=payload,
            timeout=5
        )
        resp_json = response.json()
    except Exception as e:
        print(f"😔登录请求失败: {e}")
        sys.exit(1)

    # 处理返回结果
    result = resp_json.get('result')
    message = resp_json.get('message', '')

    if result == "success":
        if not message:
            print("🥰登录成功！")
        else:
            print(f"😋{message}")
    elif result == "fail":
        print(f"😫登录失败！错误信息: {message}")
    else:
        print(f"😔未知错误！输出信息: {resp_json}")

if __name__ == "__main__":
    login()