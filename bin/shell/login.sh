#!/bin/bash

readonly STATUS_ONLINE=0
readonly STATUS_OFFLINE=1
readonly STATUS_UNCONNECTED=2
readonly STATUS_ERROR=3

write_user_config() {
  CUIT_USERID="${CUIT_USERID:-}"
  CUIT_PASSWORD="${CUIT_PASSWORD:-}"
  CUIT_SERVICE="${CUIT_SERVICE:-}"
  config="./env.sh"
  config_modify="${config_modify:0}"

  if [[ -z "$CUIT_USERID" && -e $config ]]; then
    source $config
    if [[ -z "$CUIT_USERID" ]]; then
      rm $config
    fi
  fi

  if [[ -z "$CUIT_USERID" ]]; then
    read -r -p "请输入账号: " CUIT_USERID
    echo "export CUIT_USERID=\"$CUIT_USERID\"" >> "$config"
    config_modify=1
  fi

  if [[ -z "$CUIT_PASSWORD" ]]; then
    read -r -p "请输入密码: " CUIT_PASSWORD
    echo "export CUIT_PASSWORD=\"$CUIT_PASSWORD\"" >> "$config"
    config_modify=1
  fi

  if [[ -z "$CUIT_SERVICE" ]]; then
    read -r -p "请选择服务(移动输入 1, 电信输入 2): " input
    case "$input" in
      1) CUIT_SERVICE="移动" ;;
      2) CUIT_SERVICE="电信" ;;
      *) echo "🤡 无效输入"; exit 1 ;;
    esac
    echo "export CUIT_SERVICE=\"$CUIT_SERVICE\"" >> "$shell_config"
    config_modify=1
  fi

  if [[ $config_modify -eq 1 ]]; then
    echo "✅已写入配置文件：$config"
  fi
}

get_campus_network_status() {
  local redirect_url
  redirect_url=$(curl -s -L -w "%{url_effective}\n" -o /dev/null --max-time 1 http://10.254.241.19)
  local curl_exit_code=$?

  if [[ $curl_exit_code -ne 0 ]]; then
    if [[ $curl_exit_code -eq 28 ]]; then
      return $STATUS_ONLINE
    else
      printf 'curl_exit_code=%s\n' "$curl_exit_code" >&2
      return $STATUS_ERROR
    fi
  fi

  case "$redirect_url" in
  http://10.254.241.19/eportal/success.jsp*)
    return $STATUS_ONLINE
    ;;
  http://123.123.123.123/)
    return $STATUS_OFFLINE
    ;;
  http://10.254.241.19/)
    return $STATUS_UNCONNECTED
    ;;
  *)
    return $STATUS_ERROR
    ;;
esac
}

get_queryString() {
  curl -s 123.123.123.123 --max-time 1 | grep -o "wlanuserip=[^']*"
}

campus_network_login() {
  local userId="$1"
  local password="$2"
  local service="$3"
  local queryString="$4"

  curl -s -X POST -o /dev/null 'http://10.254.241.19/eportal/InterFace.do?method=login' \
    -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
    --data-urlencode "userId=$userId" \
    --data-urlencode "password=$password" \
    --data-urlencode "service=$service" \
    --data-urlencode "queryString=$queryString" \
    --data-urlencode 'operatorPwd=' \
    --data-urlencode 'operatorUserId=' \
    --data-urlencode 'validcode=' \
    --data-urlencode 'passwordEncrypt=false'
}

# 只有在 TTY 时才交互写入
if [[ -t 0 ]]; then
  write_user_config
fi

get_campus_network_status
s=$?
case $s in
  $STATUS_ONLINE)
    echo "🥰你已在线！"
    exit 0
    ;;

  $STATUS_OFFLINE)
    echo "😶离线中，执行登录脚本..."

    queryString=$(get_queryString)
    campus_network_login "$CUIT_USERID" "$CUIT_PASSWORD" "$CUIT_SERVICE" "$queryString"

    get_campus_network_status
    s=$?

    case $s in
      $STATUS_ONLINE)
        echo "🥰登录成功！"
        exit 0
        ;;
      $STATUS_OFFLINE)
        echo "😫登录失败！"
        exit 1
        ;;
      *)
        echo "🥹未知错误！"
        exit 1
        ;;
    esac
    ;;

  $STATUS_UNCONNECTED)
    echo "🤡登录失败！未接入校园网！"
    exit 1
    ;;

  *)
    echo "🥹未知错误..."
    exit 1
    ;;
esac