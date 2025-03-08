# cuit-campus-network

成都信息工程大学 校园网自动登录&保持登录脚本（Python 实现）  

后续会推出更多客户端的登录和自动连接脚本

## 自动认证原理

通过抓包发现，校园网认证的过程中，客户端会向服务器发送一个 POST 请求。因此，我们可以通过 Python 中的 requests 库来模拟浏览器行为，向服务器发送这两个数据包，从而实现自动登录

### 自动认证操作

1. 退出登录
2. 在输入校园网账号密码后在键盘上点击f12（或右键网页 -> 检查），找到网络选项
3. 点击认证
4. 找到 ***sucess.jsp*** 开头的文件以及 ***InterFace.do*** 开头的文件。根据前者的 Payload 内容修改 ***payload_config.py*** 文件，根据后者的“标头”内容修改 ***headers_config*** 文件
5. 根据你的客户端配置环境，需要安装 requests 库。如果执行 login.py 文件后输出“认证成功”，则表示成功配置

## 保持登录原理

1.通过一个死循环，不断检测校园网是否连接。如果未连接，则执行登录脚本。

- 优点：稳定
- 缺点：后台需始终运行该程序，占用些微系统资源；用于执行程序的主机不能关机

2.由于校园网登录有时效性（约为 48 小时不到），可以通过在固定时间执行登出脚本后马上执行登录脚本，从而刷新已登录时间。

- 优点：不需要保持开机，只需要在特定时间运行即可
- 缺点：不如方法一稳定

### MacOS 实现保持登录

- 通过 plist 文件实现

1.plist 文件路径

`~/Library/LaunchAgents/com.campusnetwork.auto.plist`

2.编辑 plist 文件

用你喜爱的文本编辑器打开上述文件，输入：

```shell
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- 唯一标识符 -->
    <key>Label</key>
    <string>com.campusnetwork.auto</string>

    <!-- 任务运行的命令和参数 -->
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>
        /Users/chao/Documents/Scripts/Campus_Network/.venv/bin/python /Users/chao/Documents/Scripts/Campus_Network/logout.py &&
        /Users/chao/Documents/Scripts/Campus_Network/.venv/bin/python /Users/chao/Documents/Scripts/Campus_Network/login.py
        </string>
    </array>

    <!-- 定时触发时间 -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>5</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <!-- 任务运行环境 -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <!-- 日志路径 -->
    <key>StandardOutPath</key>
    <string>/Users/chao/Documents/Scripts/Campus_Network/campusnetwork.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/chao/Documents/Scripts/Campus_Network/campusnetwork_error.log</string>
</dict>
</plist>
```

记得改成你自己的文件路径

3.加载任务

在终端输入：
`launchctl load ~/Library/LaunchAgents/com.campusnetwork.auto.plist`

4.(可选)卸载任务

在终端输入：
`launchctl unload ~/Library/LaunchAgents/com.campusnetwork.auto.plist`
