$RedirectUrl = curl -s -L -w "%{url_effective}`n" -o /dev/null --max-time 1 http://10.254.241.19

if ($LASTEXITCODE -ne 0) {
    Write-Host "🥹 curl 执行出错..."
    exit 1
}

switch -Wildcard ($RedirectUrl) {
    "http://10.254.241.19/eportal/success.jsp*" {
        Write-Host "🥰 在线中..."
        exit 0
    }
    "http://123.123.123.123/" {
        Write-Host "😶 离线中..."
        exit 0
    }
    "http://10.254.241.19/" {
        Write-Host "🤡 未接入校园网..."
        exit 0
    }
    Default {
        Write-Host "🥹 未知错误..."
        exit 1
    }
}
