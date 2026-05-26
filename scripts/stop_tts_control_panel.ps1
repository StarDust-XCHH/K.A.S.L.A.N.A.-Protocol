[CmdletBinding()]
param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8765,
    [switch]$All
)

$ErrorActionPreference = "Stop"

function Get-ControlPanelProcesses {
    param(
        [string]$HostAddress,
        [int]$Port,
        [switch]$All
    )

    $byPort = @{}
    if (-not $All) {
        $connections = @(
            Get-NetTCPConnection -LocalAddress $HostAddress -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        )
        if (-not $connections) {
            $connections = @(
                Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
            )
        }
        foreach ($conn in $connections) {
            if ($conn.OwningProcess) {
                $byPort[$conn.OwningProcess] = $true
            }
        }
    }

    $result = @()
    foreach ($proc in Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue) {
        if ($proc.CommandLine -notmatch "tts_control_panel\.py") {
            continue
        }
        if ($All -or $byPort.ContainsKey($proc.ProcessId)) {
            $result += $proc
        }
    }
    return $result
}

$processes = @(Get-ControlPanelProcesses -HostAddress $HostAddress -Port $Port -All:$All)
if (-not $processes) {
    Write-Host "No control panel process is listening on http://${HostAddress}:${Port}."
    exit 0
}

foreach ($proc in $processes) {
    Write-Host "Stopping control panel PID $($proc.ProcessId): $($proc.CommandLine)"
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Milliseconds 600

$remaining = @(Get-ControlPanelProcesses -HostAddress $HostAddress -Port $Port -All:$All)
if ($remaining) {
    foreach ($proc in $remaining) {
        Write-Host "Retry stopping PID $($proc.ProcessId)..."
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 600
    $remaining = @(Get-ControlPanelProcesses -HostAddress $HostAddress -Port $Port -All:$All)
}

if ($remaining) {
    $ids = ($remaining | ForEach-Object { $_.ProcessId }) -join ", "
    throw "Failed to stop control panel process(es): $ids"
}

Write-Host "Control panel stopped."
