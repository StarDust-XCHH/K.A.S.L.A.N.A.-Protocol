param(
    [string]$EnvName = $(if ($env:KASLANA_CONDA_ENV) { $env:KASLANA_CONDA_ENV } else { "kaslana-protocol" }),
    [switch]$SkipTorch
)

$ErrorActionPreference = "Stop"

function Set-EnvDefault {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType File -Path $Path -Force | Out-Null
    }

    $lines = @(Get-Content -LiteralPath $Path)
    $escapedKey = [regex]::Escape($Key)
    $index = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "^\s*$escapedKey\s*=") {
            $index = $i
            break
        }
    }

    if ($index -lt 0) {
        Add-Content -LiteralPath $Path -Value "$Key=$Value"
        return
    }

    $existingValue = ($lines[$index] -split "=", 2)[1].Trim()
    if ([string]::IsNullOrWhiteSpace($existingValue) -or $existingValue -eq "replace-me") {
        $lines[$index] = "$Key=$Value"
        Set-Content -LiteralPath $Path -Value $lines -Encoding utf8
    }
}

function Invoke-Conda {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    Write-Host "conda $($Arguments -join ' ')"
    & conda @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "conda command failed: conda $($Arguments -join ' ')"
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        throw "conda was not found on PATH."
    }

    $envList = conda env list --json | ConvertFrom-Json
    $envExists = $false
    foreach ($envPath in $envList.envs) {
        if ((Split-Path -Leaf $envPath) -eq $EnvName) {
            $envExists = $true
            break
        }
    }

    if ($envExists) {
        Invoke-Conda env update -n $EnvName -f environment.yml
    } else {
        Invoke-Conda env create -f environment.yml
    }

    Invoke-Conda run -n $EnvName python -m pip install --upgrade pip

    if (-not $SkipTorch) {
        Invoke-Conda run -n $EnvName python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    } else {
        Write-Host "Skipping PyTorch CUDA wheel installation because -SkipTorch was provided."
    }

    Write-Host "conda run -n $EnvName python -m pip install -e `".[dev]`""
    & conda run -n $EnvName python -m pip install "-e" ".[dev]"
    if ($LASTEXITCODE -ne 0) {
        throw "conda command failed: conda run -n $EnvName python -m pip install -e `".[dev]`""
    }

    if (-not (Test-Path -LiteralPath ".env")) {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
        Write-Host "Created .env from .env.example."
    }

    if (-not (Test-Path -LiteralPath "config\config.yaml")) {
        Copy-Item -LiteralPath "config\config.example.yaml" -Destination "config\config.yaml"
        Write-Host "Created config\config.yaml from config\config.example.yaml."
    }

    Set-EnvDefault -Path ".env" -Key "KASLANA_CONDA_ENV" -Value $EnvName
    $kianaInferConfig = "assets\琪亚娜E7\琪亚娜E7\infer_config.json"
    if (Test-Path -LiteralPath $kianaInferConfig) {
        Set-EnvDefault -Path ".env" -Key "KASLANA_TTS_INFER_CONFIG" -Value $kianaInferConfig
        Set-EnvDefault -Path ".env" -Key "KASLANA_TTS_API_STYLE" -Value "gsvi"
        Set-EnvDefault -Path ".env" -Key "KASLANA_TTS_ENDPOINT" -Value "http://127.0.0.1:5100"
    }

    Write-Host ""
    Write-Host "K.A.S.L.A.N.A. conda environment is ready: $EnvName"
    Write-Host "Next checks:"
    Write-Host "  conda run -n $EnvName python scripts\check_gpu.py"
    Write-Host "  conda run -n $EnvName python -m pytest"
    Write-Host "  conda run -n $EnvName python scripts\try_gpt_sovits_tts.py --list-emotions"
}
finally {
    Pop-Location
}
