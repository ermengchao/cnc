#!/bin/bash

redirect_url=$(curl -s -L -w "%{url_effective}\n" -o /dev/null --max-time 1 http://10.254.241.19)

if [[ $curl_exit_code -ne 0 ]]; then
    echo "🥹 curl 执行出错..."
fi

case "$redirect_url" in
    http://10.254.241.19/eportal/success.jsp*)
        echo "🥰 在线中..."
    ;;

    http://123.123.123.123/)
        echo "😶 离线中..."
    ;;

    http://10.254.241.19/)
        echo "🤡 未接入校园网..."
    ;;

    *)
        echo "🥹 未知错误..."
    ;;
esac