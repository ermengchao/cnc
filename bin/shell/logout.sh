#!/bin/bash

readonly STATUS_ONLINE=0
readonly STATUS_OFFLINE=1
readonly STATUS_UNCONNECTED=2
readonly STATUS_ERROR=3

get_campus_network_status() {
  local redirect_url
  redirect_url=$(curl -s -L -w "%{url_effective}\n" -o /dev/null --max-time 1 http://10.254.241.19)
  local curl_exit_code=$?

  if [[ $curl_exit_code -ne 0 ]]; then
    if [[ $curl_exit_code -eq 28 ]]; then
      return $STATUS_OFFLINE
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

campus_network_logout() {
  curl -s -X POST -o /dev/null 'http://10.254.241.19/eportal/InterFace.do?method=logout'
}

get_campus_network_status
s=$?
case "$s" in
  $STATUS_ONLINE)
    echo "😶在线中，执行注销脚本..."

    campus_network_logout

    get_campus_network_status
    s=$?
    case "$s" in
      $STATUS_ONLINE)
        echo "😫注销失败！"
        exit 1
        ;;
      $STATUS_OFFLINE)
        echo "🥰注销成功！"
        exit 0
        ;;
      *)
        echo "🥹未知错误！"
        exit 1
        ;;
    esac
    ;;

  $STATUS_OFFLINE)
    echo "🥰你已离线！"
    exit 0
    ;;

  $STATUS_UNCONNECTED)
    echo "🤡注销失败！未接入校园网！"
    exit 1
    ;;

  *)
    echo $s
    echo "🥹未知错误..."
    exit 1
    ;;
esac
