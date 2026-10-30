<#
.SYNOPSIS
  Install, start, stop and inspect the desktop frame+pose service (Windows Scheduled Task).
.EXAMPLE
  .\deploy\windows\halloween.ps1 install -BindAddress 100.83.94.65 -MaxPersons 3
  .\deploy\windows\halloween.ps1 start | stop | restart | status | uninstall
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("install", "start", "stop", "restart", "status", "uninstall")]
    [string]$Action,
    [string]$BindAddress = "127.0.0.1",
    [string]$Model = "models\pose_landmarker_lite.task",
    [ValidateRange(1, 3)][int]$MaxPersons = 1,
    [string]$TaskName = "HalloweenProjectionDesktop"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

switch ($Action) {
    "install" {
        $python = (Get-Command python).Source
        $taskArgs = "-u -m desktop.main --host $BindAddress --port 8765 --pose --model `"$Model`" --max-persons $MaxPersons"
        $act = New-ScheduledTaskAction -Execute $python -Argument $taskArgs -WorkingDirectory $repo
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $settings = New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) `
            -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
        $me = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        $principal = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $act -Trigger $trigger -Settings $settings `
            -Principal $principal -Description "Halloween frame ingest + pose service" -Force | Out-Null
        Write-Host "Installed '$TaskName' (starts at sign-in). Run: halloween.ps1 start"
    }
    "start" { Start-ScheduledTask -TaskName $TaskName; Write-Host "Started." }
    "stop" {
        Stop-ScheduledTask -TaskName $TaskName
        Write-Host "Stopped."
    }
    "restart" {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "Restarted."
    }
    "status" {
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        $state = (Get-ScheduledTask -TaskName $TaskName).State
        Write-Host "State: $state | LastRun: $($info.LastRunTime) | LastResult: $($info.LastTaskResult)"
        Test-NetConnection -ComputerName 127.0.0.1 -Port 8766 -InformationLevel Quiet |
            ForEach-Object { Write-Host "Pose port 8766 listening: $_" }
    }
    "uninstall" { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false; Write-Host "Removed." }
}
