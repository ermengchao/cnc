$STATUS_ONLINE = 0
$STATUS_OFFLINE = 1
$STATUS_UNCONNECTED = 2
$STATUS_ERROR = 3

function Write-UserConfig {
    . $PROFILE.CurrentUserAllHosts
    if (-not $env:CUIT_USERID) {
        $env:CUIT_USERID = Read-Host '请输入账号 (CUIT_USERID):'
        '$env:CUIT_USERID = "' + $env:CUIT_USERID + '"' | Add-Content -Path $PROFILE.CurrentUserAllHosts
    }

    if (-not $env:CUIT_PASSWORD) {
        $env:CUIT_PASSWORD = Read-Host '请输入密码 (CUIT_PASSWORD):'
        '$env:CUIT_PASSWORD = "' + $env:CUIT_PASSWORD + '"' | Add-Content -Path $PROFILE.CurrentUserAllHosts
    }

    if (-not $env:CUIT_SERVICE) {
        $choice = Read-Host '请选择服务 (输入 1 = 移动, 2 = 电信):'
        switch ($choice) {
            '1' { $env:CUIT_SERVICE = '移动' }
            '2' { $env:CUIT_SERVICE = '电信' }
            default {
                Write-Host '🤡 无效输入！请输入 1 (移动) 或 2 (电信)' -ForegroundColor Red
                exit 1
            }
        }
        '$env:CUIT_SERVICE = "' + $env:CUIT_SERVICE + '"' | Add-Content -Path $PROFILE.CurrentUserAllHosts
    }
}

function Get-QueryString {
    $response = curl -s 123.123.123.123 --max-time 1
    if ($response -match 'wlanuserip=[^'']*') {
        Write-Output $matches[0]
    }
}

function Get-CampusNetwork-Status {
    try {
        $RedirectUrl = $(curl -s -L -w "%{url_effective}\n" -o /dev/null --max-time 1 http://10.254.241.19)
    }
    catch {
        return $STATUS_ERROR
    }

    switch -Wildcard ($RedirectUrl) {
        "http://10.254.241.19/eportal/success.jsp*" {
            return $STATUS_ONLINE
        }
        "http://123.123.123.123/" {
            return $STATUS_OFFLINE
        }
        "http://10.254.241.19/" {
            return $STATUS_UNCONNECTED
        }
        Default {
            return $STATUS_ERROR
        }
    }
}

function Invoke-CampusNetwork-Login {
    param (
        [Parameter(Mandatory = $true)]
        [string]$UserID,

        [Parameter(Mandatory = $true)]
        [string]$Password,

        [Parameter(Mandatory = $true)]
        [string]$Service,

        [Parameter(Mandatory = $true)]
        [string]$QueryString
    )

    curl -s -X POST -o /dev/null 'http://10.254.241.19/eportal/InterFace.do?method=login' `
        -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' `
        --data-urlencode "userId=$userId" `
        --data-urlencode "password=$password" `
        --data-urlencode "service=$service" `
        --data-urlencode "queryString=$queryString" `
        --data-urlencode 'operatorPwd=' `
        --data-urlencode 'operatorUserId=' `
        --data-urlencode 'validcode=' `
        --data-urlencode 'passwordEncrypt=false'
}

Write-UserConfig

$status = Get-CampusNetwork-Status
switch ($status) {
    $STATUS_ONLINE {
        Write-Host '🥰 你已在线！'
        exit 0
    }
    $STATUS_OFFLINE {
        Write-Host '😶 离线中，执行登录脚本...'
        
        $queryString = Get-QueryString
        Invoke-CampusNetwork-Login `
            -UserID $env:CUIT_USERID `
            -Password $env:CUIT_PASSWORD `
            -Service $env:CUIT_SERVICE `
            -QueryString $queryString

        $status = Get-CampusNetwork-Status
        if ($status -eq 0) {
            Write-Host '🥰 登录成功！'
            exit 0
        }
        elseif ($status -eq 1) {
            Write-Host "😫 登录失败！输出信息:`n$responseContent"
            exit 1
        }
        else {
            Write-Host "🥹 未知错误！输出信息:`n$responseContent"
            exit 1
        }
    }
    $STATUS_UNCONNECTED {
        Write-Host '🤡 登录失败！未接入校园网！' -ForegroundColor Red
        exit 1
    }
    Default {
        Write-Host '🥹 未知错误...' -ForegroundColor Yellow
        exit 1
    }
}