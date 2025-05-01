$STATUS_ONLINE = 0
$STATUS_OFFLINE = 1
$STATUS_UNCONNECTED = 2
$STATUS_ERROR = 3

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

function Invoke-CampusNetwork-Logout {
    curl -s -X POST -o /dev/null 'http://10.254.241.19/eportal/InterFace.do?method=logout'
}

$s = Get-CampusNetwork-Status
switch ($s) {
    $STATUS_ONLINE {
        Write-Host "😶在线中，执行注销脚本..."

        Invoke-CampusNetwork-Logout

        $s = Get-CampusNetwork-Status
        switch ($s) {
            $STATUS_ONLINE {
                Write-Host "😫注销失败！"
                exit 1
            }
            $STATUS_OFFLINE {
                Write-Host "🥰注销成功！"
                exit 0
            }
            Default {
                Write-Host "🥹未知错误！"
                exit 1
            }
        }
    }
    $STATUS_OFFLINE {
        Write-Host "🥰你已离线！"
        exit 0
    }
    $STATUS_UNCONNECTED {
        Write-Host "🤡注销失败！未接入校园网！"
        exit 1
    }
    Default {
        Write-Host "🥹未知错误！"
        exit 1
    }
}