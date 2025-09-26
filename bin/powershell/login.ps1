$STATUS_ONLINE = 0
$STATUS_OFFLINE = 1
$STATUS_UNCONNECTED = 2
$STATUS_ERROR = 3

function Write-UserConfig {
    $config = Join-Path $PSScriptRoot 'env.ps1'
    $config_modified = $false

    if ([string]::IsNullOrEmpty($env:CUIT_USERID) -and (Test-Path $config)) {
        . $config
        if ([string]::IsNullOrEmpty($env:CUIT_USERID)) {
            Remove-Item $config -ErrorAction SilentlyContinue
        }
    }

    if ([string]::IsNullOrEmpty($env:CUIT_USERID)) {
        $env:CUIT_USERID = Read-Host '请输入账号'
        Add-Content -Path $config -Value ('$env:CUIT_USERID = "{0}"' -f $env:CUIT_USERID)
        $config_modified = $true
    }

    if ([string]::IsNullOrEmpty($env:CUIT_PASSWORD)) {
        # PowerShell 7+ 可用 -MaskInput 隐藏输入；如果是 Windows PowerShell 可换成 -AsSecureString 再转换
        $env:CUIT_PASSWORD = Read-Host '请输入密码' -MaskInput
        Add-Content -Path $config -Value ('$env:CUIT_PASSWORD = "{0}"' -f $env:CUIT_PASSWORD)
        $config_modified = $true
    }

    if ([string]::IsNullOrEmpty($env:CUIT_SERVICE)) {
        $input = Read-Host '请选择服务(移动输入 1, 电信输入 2)'
        switch ($input) {
            '1' { $env:CUIT_SERVICE = '移动' }
            '2' { $env:CUIT_SERVICE = '电信' }
            default { Write-Host '🤡 无效输入'; exit 1 }
        }
        Add-Content -Path $config -Value ('$env:CUIT_SERVICE = "{0}"' -f $env:CUIT_SERVICE)
        $config_modified = $true
    }

    if ($config_modified) {
        Write-Host "✅已写入配置文件：$config"
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

$status = Get-CampusNetwork-Status
switch ($status) {
    $STATUS_ONLINE {
        Write-Host '🥰 你已在线！'
        exit 0
    }
    $STATUS_OFFLINE {
        Write-Host '😶 离线中，执行登录脚本...'

        Write-UserConfig
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