[CmdletBinding()]
param(
    [string]$GsvRoot = "local_assets\GSVI-2.2.4-240318\GPT-SoVITS-Inference",
    [int]$Port = 5100,
    [int]$WaitSeconds = 180
)

$ErrorActionPreference = "Stop"

function Test-LocalTcpPort {
    param([int]$TargetPort)

    $client = $null
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $async = $client.BeginConnect("127.0.0.1", $TargetPort, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne(500)) {
            return $false
        }
        $client.EndConnect($async)
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($client -ne $null) {
            $client.Dispose()
        }
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir "..")).Path

if ([System.IO.Path]::IsPathRooted($GsvRoot)) {
    $rootPath = $GsvRoot
}
else {
    $rootPath = Join-Path $repoRoot $GsvRoot
}

$root = (Resolve-Path -LiteralPath $rootPath).Path
$runtime = Join-Path $root "runtime\python.exe"
$backend = Join-Path $root "Inference\src\tts_backend.py"

if (-not (Test-Path -LiteralPath $runtime)) {
    throw "Missing GSVI runtime Python: $runtime"
}
if (-not (Test-Path -LiteralPath $backend)) {
    throw "Missing GSVI backend: $backend"
}

if (Test-LocalTcpPort -TargetPort $Port) {
    Write-Host "GSVI TTS server is already reachable at http://127.0.0.1:$Port"
    exit 0
}

$wrapper = Join-Path $root ".kaslana_start_backend.py"
$wrapperContent = @"
from __future__ import annotations

from pathlib import Path
import os
import sys

root = Path(__file__).resolve().parent
os.chdir(root)
sys.path.insert(0, str(root / "Inference" / "src"))

import tts_backend  # noqa: E402

if __name__ == "__main__":
    port = $Port
    tts_backend.app.run(host="127.0.0.1", port=port)
"@
Set-Content -LiteralPath $wrapper -Value $wrapperContent -Encoding UTF8

$logsDir = Join-Path $repoRoot "local_assets\logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stdout = Join-Path $logsDir "gsvi-$stamp.stdout.log"
$stderr = Join-Path $logsDir "gsvi-$stamp.stderr.log"
$pidPath = Join-Path $logsDir "gsvi-server.pid"
$quotedWrapper = '"' + $wrapper + '"'

$process = Start-Process `
    -FilePath $runtime `
    -ArgumentList $quotedWrapper `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

Set-Content -LiteralPath $pidPath -Value $process.Id -Encoding ASCII

Write-Host "Started GSVI TTS backend process $($process.Id)."
Write-Host "stdout: $stdout"
Write-Host "stderr: $stderr"

$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    if ($process.HasExited) {
        throw "GSVI TTS backend exited before port $Port became reachable. Check $stdout and $stderr"
    }
    if (Test-LocalTcpPort -TargetPort $Port) {
        Write-Host "GSVI TTS server is reachable at http://127.0.0.1:$Port"
        exit 0
    }
}

throw "GSVI TTS backend is still starting or blocked after $WaitSeconds seconds. Check $stdout and $stderr"
