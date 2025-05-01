readonly STATUS_ONLINE=0
readonly STATUS_OFFLINE=1
readonly STATUS_UNCONNECTED=2
readonly STATUS_ERROR=3

write_user_config() {
  local current_shell shell_config

  # 检测 shell 类型
  current_shell=$(ps -p $$ -o comm= | awk -F/ '{print $NF}')
  case "$current_shell" in
    zsh) shell_config="$HOME/.zshenv" ;;
    bash)
      if [[ -f "$HOME/.bash_profile" ]]; then
        shell_config="$HOME/.bash_profile"
      else
        shell_config="$HOME/.bashrc"
      fi
      ;;
    *) 
      echo "⚠️ 不支持的 shell: $current_shell, 默认写入 ~/.profile"
      shell_config="$HOME/.profile"
      ;;
  esac

  CUIT_USERID="${CUIT_USERID:-}"
  CUIT_PASSWORD="${CUIT_PASSWORD:-}"
  CUIT_SERVICE="${CUIT_SERVICE:-}"

  if [[ -z "$CUIT_USERID" ]]; then
    read -r -p "请输入账号: " CUIT_USERID
    [[ -n "$CUIT_USERID" ]] && ! grep -q "^export CUIT_USERID=" "$shell_config" && \
      echo "export CUIT_USERID=\"$CUIT_USERID\"" >> "$shell_config"
  fi

  if [[ -z "$CUIT_PASSWORD" ]]; then
    read -r -p "请输入密码: " CUIT_PASSWORD
    [[ -n "$CUIT_PASSWORD" ]] && ! grep -q "^export CUIT_PASSWORD=" "$shell_config" && \
      echo "export CUIT_PASSWORD=\"$CUIT_PASSWORD\"" >> "$shell_config"
  fi

  if [[ -z "$CUIT_SERVICE" ]]; then
    read -r -p "请选择服务(移动输入 1, 电信输入 2): " input
    case "$input" in
      1) CUIT_SERVICE="移动" ;;
      2) CUIT_SERVICE="电信" ;;
      *) echo "🤡 无效输入"; exit 1 ;;
    esac
    [[ -n "$CUIT_SERVICE" ]] && ! grep -q "^export CUIT_SERVICE=" "$shell_config" && \
      echo "export CUIT_SERVICE=\"$CUIT_SERVICE\"" >> "$shell_config"
  fi

  echo "✅已写入配置文件：$shell_config"
}

get_campus_network_status() {
  local redirect_url
  redirect_url=$(curl -s -L -w "%{url_effective}\n" -o /dev/null --max-time 1 http://10.254.241.19)

  if [[ $curl_exit_code -ne 0 ]]; then
    return $STATUS_ERROR
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

write_user_config
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