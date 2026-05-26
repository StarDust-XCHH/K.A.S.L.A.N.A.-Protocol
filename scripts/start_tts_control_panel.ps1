[CmdletBinding()]
param(
    [string]$EnvName = "kaslana-protocol",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir "..")).Path
$panelScript = Join-Path $repoRoot "scripts\tts_control_panel.py"

if (-not (Test-Path -LiteralPath $panelScript)) {
    throw "Missing TTS control panel script: $panelScript"
}

$url = "http://$HostAddress`:$Port"
if (-not $NoBrowser) {
    Start-Process $url
}

Push-Location $repoRoot
try {
    conda run -n $EnvName python $panelScript --host $HostAddress --port $Port
}
finally {
    Pop-Location
}
