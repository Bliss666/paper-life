# 定时出稿 · Windows 任务计划安装脚本
# 用法（PowerShell）:
#   cd d:\bliss\图文
#   powershell -ExecutionPolicy Bypass -File .\install_schedule.ps1
#
# 说明：任务以当前用户身份运行，工作目录固定为项目根目录。

param(
    [string]$Time = "08:30",
    [string]$TaskName = "ThinkNote_图文定时出稿"
)

$ErrorActionPreference = "Stop"
$ProjectDir = "d:\bliss\图文"
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) { $Python = "python" }

$LogDir = Join-Path $ProjectDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd"
$OutLog = Join-Path $LogDir "scheduler-$Stamp.log"
$ErrLog = Join-Path $LogDir "scheduler-$Stamp.err.log"

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c cd /d `"$ProjectDir`" && `"$Python`" pipeline\scheduler.py >> `"$OutLog`" 2>> `"$ErrLog`""

$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "OK: scheduled task installed -> $TaskName (daily at $Time)"
Write-Host "   logs: $LogDir"
Write-Host "   trigger now: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "   uninstall: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"