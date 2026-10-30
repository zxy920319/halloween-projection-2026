param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [Parameter(Mandatory = $true)]
    [string]$PythonPath,
    [Parameter(Mandatory = $true)]
    [string]$PoseModelPath,
    [string]$TaskName = "HalloweenProjectionDesktop",
    [string]$BindAddress = "127.0.0.1",
    [int]$FramePort = 8765,
    [int]$PosePort = 8766
)

$ErrorActionPreference = "Stop"
$project = (Resolve-Path -LiteralPath $ProjectPath).Path
$python = (Resolve-Path -LiteralPath $PythonPath).Path
$model = (Resolve-Path -LiteralPath $PoseModelPath).Path
$modelRelative = [System.IO.Path]::GetRelativePath($project, $model)

$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "-u -m desktop.main --host $BindAddress --port $FramePort --pose --model `"$modelRelative`" --pose-port $PosePort" `
    -WorkingDirectory $project
$trigger = New-ScheduledTaskTrigger -AtLogOn
$restart = New-ScheduledTaskSettingsSet `
    -RestartCount 10 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $restart `
    -Principal $principal `
    -Description "Starts the local Halloween Projection frame and pose services at sign-in." `
    -Force | Out-Null

Write-Host "Registered '$TaskName'. Start it with: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Frame ingest binds to $BindAddress`:$FramePort; pose publishing remains on loopback port $PosePort."
