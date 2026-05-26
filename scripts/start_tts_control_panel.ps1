[CmdletBinding()]
param(
    [string]$EnvName = "kaslana-protocol",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8765,
    [switch]$NoBrowser,
    [switch]$KeepExisting
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir "..")).Path
$panelScript = Join-Path $repoRoot "scripts\tts_control_panel.py"
$stopScript = Join-Path $repoRoot "scripts\stop_tts_control_panel.ps1"

if (-not (Test-Path -LiteralPath $panelScript)) {
    throw "Missing TTS control panel script: $panelScript"
}

function Get-PortListeners {
    param(
        [string]$HostAddress,
        [int]$Port
    )

    $connections = @(
        Get-NetTCPConnection -LocalAddress $HostAddress -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    )
    if (-not $connections) {
        $connections = @(
            Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        )
    }
    return $connections
}

function Test-PortBlockedByOtherProcess {
    param(
        [string]$HostAddress,
        [int]$Port
    )

    foreach ($conn in (Get-PortListeners -HostAddress $HostAddress -Port $Port)) {
        $processId = $conn.OwningProcess
        if (-not $processId) {
            continue
        }
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
        if ($proc -and $proc.CommandLine -notmatch "tts_control_panel\.py") {
            return $proc
        }
    }
    return $null
}

$url = "http://$HostAddress`:$Port"

if (-not $KeepExisting) {
    & $stopScript -HostAddress $HostAddress -Port $Port
}

$blocker = Test-PortBlockedByOtherProcess -HostAddress $HostAddress -Port $Port
if ($blocker) {
    $blockerPid = $blocker.ProcessId
    $blockerCmd = $blocker.CommandLine
    throw "Port $Port is already used by another process (PID $blockerPid): $blockerCmd"
}

$pythonArgs = @(
    $panelScript,
    "--host", $HostAddress,
    "--port", "$Port"
)
if (-not $NoBrowser) {
    $pythonArgs += "--open-browser"
}

Write-Host "Starting control panel on $url ..."
Write-Host "If the page looks outdated, run: .\scripts\stop_tts_control_panel.ps1"

Push-Location $repoRoot
try {
    conda run -n $EnvName python @pythonArgs
}
finally {
    Pop-Location
}
