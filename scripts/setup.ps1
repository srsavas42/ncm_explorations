$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$pythonExe = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $pythonExe -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
    & uv pip install --python .venv/Scripts/python.exe -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Could not install dependencies.' }
    & uv pip install --python .venv/Scripts/python.exe --no-deps -e .
} else {
    & .venv/Scripts/python.exe -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Could not install dependencies.' }
    & .venv/Scripts/python.exe -m pip install --no-deps -e .
}
if ($LASTEXITCODE -ne 0) { throw 'Could not install ncm-probe.' }
& .venv/Scripts/python.exe -m ncm_probe verify-fixture
if ($LASTEXITCODE -ne 0) { throw 'Fixture verification failed.' }
Write-Host 'Ready. Use .venv\Scripts\python.exe -m ncm_probe --help'
