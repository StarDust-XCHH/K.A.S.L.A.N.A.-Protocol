[CmdletBinding()]
param(
    [string]$GsvRoot = "local_assets\GSVI-2.2.4-240318\GPT-SoVITS-Inference",
    [int]$Port = 5100
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
$pidPath = Join-Path $repoRoot "local_assets\logs\gsvi-server.pid"

if (-not (Test-Path -LiteralPath $pidPath)) {
    if (Test-LocalTcpPort -TargetPort $Port) {
        throw "Port $Port is reachable, but no project PID file exists. Refusing to stop it."
    }
    Write-Host "GSVI TTS server is not running."
    exit 0
}

$rawPid = (Get-Content -LiteralPath $pidPath -Raw).Trim()
$pidValue = 0
if (-not [int]::TryParse($rawPid, [ref]$pidValue)) {
    Remove-Item -LiteralPath $pidPath -Force
    throw "Removed invalid PID file, but did not stop any process."
}

$process = Get-CimInstance Win32_Process -Filter "ProcessId = $pidValue"
if ($null -eq $process) {
    Remove-Item -LiteralPath $pidPath -Force
    if (Test-LocalTcpPort -TargetPort $Port) {
        throw "PID $pidValue is stale, but port $Port is still reachable. Refusing to stop it."
    }
    Write-Host "Removed stale GSVI PID file."
    exit 0
}

$commandLine = [string]$process.CommandLine
$executable = [string]$process.ExecutablePath
if (-not ($commandLine.Contains($root) -or $executable.Contains($root))) {
    throw "PID $pidValue does not point to this project's GSVI process. Refusing to stop it."
}

Stop-Process -Id $pidValue -Force
Remove-Item -LiteralPath $pidPath -Force

$deadline = (Get-Date).AddSeconds(15)
while ((Get-Date) -lt $deadline) {
    if (-not (Test-LocalTcpPort -TargetPort $Port)) {
        Write-Host "GSVI TTS server stopped."
        exit 0
    }
    Start-Sleep -Milliseconds 500
}

throw "Stop was requested, but port $Port is still reachable."
