<#
.SYNOPSIS
  Install, start, stop and inspect the desktop frame+pose service.
.DESCRIPTION
  Uses a Scheduled Task when Windows allows it. If registration is denied (common on
  locked-down or non-elevated sessions), falls back to a Startup-folder launcher that
  needs no administrator rights and restarts the service if it exits.
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
$stateDir = Join-Path $env:LOCALAPPDATA "HalloweenProjection"
$loopScript = Join-Path $stateDir "run-desktop.ps1"
$startupCmd = Join-Path ([Environment]::GetFolderPath("Startup")) "HalloweenProjectionDesktop.cmd"

function Get-ServiceProcesses {
    Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -match "desktop\.main" -or $_.CommandLine -match [regex]::Escape($loopScript) }
}

function Test-TaskInstalled {
    [bool](Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)
}

function Install-Launcher([string]$python, [string]$serviceArgs) {
    New-Item -ItemType Directory -Force $stateDir | Out-Null
    @"
Set-Location -LiteralPath '$repo'
while (`$true) {
    & '$python' -u -m desktop.main $serviceArgs
    Start-Sleep -Seconds 5
}
"@ | Set-Content -Path $loopScript -Encoding UTF8
    "@echo off`r`npowershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$loopScript`"" |
        Set-Content -Path $startupCmd -Encoding ASCII
}

function Start-Launcher {
    if (-not (Test-Path $loopScript)) { throw "Launcher not installed. Run: halloween.ps1 install" }
    if (Get-ServiceProcesses) { Write-Host "Already running."; return }
    Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $loopScript
}

function Stop-Launcher {
    # Stop the restart loop first so it cannot respawn the service.
    Get-ServiceProcesses | Sort-Object { $_.CommandLine -match "desktop\.main" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

switch ($Action) {
    "install" {
        $python = (Get-Command python).Source
        $serviceArgs = "--host $BindAddress --port 8765 --pose --model `"$Model`" --max-persons $MaxPersons"
        try {
            $act = New-ScheduledTaskAction -Execute $python -Argument "-u -m desktop.main $serviceArgs" -WorkingDirectory $repo
            $trigger = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
            $settings = New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) `
                -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
            Register-ScheduledTask -TaskName $TaskName -Action $act -Trigger $trigger -Settings $settings `
                -Description "Halloween frame ingest + pose service" -Force -ErrorAction Stop | Out-Null
            if (Test-Path $startupCmd) { Remove-Item $startupCmd -Force }
            Write-Host "Installed Scheduled Task '$TaskName' (starts at sign-in). Run: halloween.ps1 start"
        }
        catch {
            Write-Warning "Scheduled Task registration failed ($($_.Exception.Message)). Using Startup-folder launcher instead."
            Install-Launcher $python $serviceArgs
            Write-Host "Installed Startup launcher: $startupCmd (starts at sign-in). Run: halloween.ps1 start"
        }
    }
    "start" {
        if (Test-TaskInstalled) { Start-ScheduledTask -TaskName $TaskName } else { Start-Launcher }
        Write-Host "Started."
    }
    "stop" {
        if (Test-TaskInstalled) { Stop-ScheduledTask -TaskName $TaskName }
        Stop-Launcher
        Write-Host "Stopped."
    }
    "restart" {
        & $PSCommandPath stop -TaskName $TaskName
        Start-Sleep -Seconds 2
        & $PSCommandPath start -TaskName $TaskName
    }
    "status" {
        $mode = if (Test-TaskInstalled) { "ScheduledTask" } elseif (Test-Path $startupCmd) { "StartupLauncher" } else { "not installed" }
        $running = [bool](Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "desktop\.main" })
        $pose = Test-NetConnection -ComputerName 127.0.0.1 -Port 8766 -InformationLevel Quiet -WarningAction SilentlyContinue
        Write-Host "Mode: $mode | Process running: $running | Pose port 8766 listening: $pose"
    }
    "uninstall" {
        Stop-Launcher
        if (Test-TaskInstalled) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
        Remove-Item $startupCmd, $loopScript -Force -ErrorAction SilentlyContinue
        Write-Host "Removed."
    }
}
