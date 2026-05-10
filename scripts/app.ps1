param(
  [ValidateSet("setup", "start", "stop", "restart", "status", "logs")]
  [string]$Action = "start",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $RootDir ".run"
$LogDir = Join-Path $RunDir "logs"
$BackendPidFile = Join-Path $RunDir "backend.pid"
$FrontendPidFile = Join-Path $RunDir "frontend.pid"
$BackendOutLog = Join-Path $LogDir "backend.out.log"
$BackendErrLog = Join-Path $LogDir "backend.err.log"
$FrontendOutLog = Join-Path $LogDir "frontend.out.log"
$FrontendErrLog = Join-Path $LogDir "frontend.err.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Require-Command {
  param([string]$Name, [string]$Hint)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    Write-Host "Missing required command: $Name"
    Write-Host $Hint
    exit 1
  }
}

function Test-Running {
  param([string]$PidFile)
  if (-not (Test-Path $PidFile)) { return $false }
  $ProcessId = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if (-not $ProcessId) { return $false }
  return [bool](Get-Process -Id ([int]$ProcessId) -ErrorAction SilentlyContinue)
}

function Stop-FromPidFile {
  param([string]$Name, [string]$PidFile)
  if (-not (Test-Running $PidFile)) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "$Name is not running."
    return
  }

  $ProcessId = [int](Get-Content $PidFile | Select-Object -First 1)
  Write-Host "Stopping $Name (pid $ProcessId)..."
  Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
  Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
  Write-Host "$Name stopped."
}

function Ensure-EnvFile {
  $EnvFile = Join-Path $RootDir ".env"
  if (Test-Path $EnvFile) { return }

  Write-Host "No .env file found."
  Write-Host "Create one from .env.example and fill in LLM_* and EMBEDDING_* values before running analysis:"
  Write-Host "  copy .env.example .env"
  Write-Host ""
}

function Find-UvPython {
  $PythonRoot = Join-Path $RootDir ".uv-python"
  if (-not (Test-Path $PythonRoot)) { return $null }
  return Get-ChildItem -Path $PythonRoot -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
}

function Setup-Backend {
  Require-Command "uv" "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"

  $VenvDir = Join-Path $RootDir ".venv"
  if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating uv-managed Python environment..."
    Push-Location $RootDir
    try {
      & uv --cache-dir .uv-cache python install --install-dir .uv-python 3.11
      $LocalPython = Find-UvPython
      if (-not $LocalPython) {
        throw "Could not find uv-managed python.exe under .uv-python."
      }
      & uv --cache-dir .uv-cache venv --python $LocalPython .venv
    } finally {
      Pop-Location
    }
  }

  Write-Host "Syncing backend dependencies..."
  Push-Location $RootDir
  try {
    & uv --cache-dir .uv-cache sync
  } finally {
    Pop-Location
  }
}

function Setup-Frontend {
  Require-Command "npm" "Install Node.js 18+ first: https://nodejs.org/"

  $NodeModules = Join-Path $RootDir "frontend\node_modules"
  if (-not (Test-Path $NodeModules)) {
    Write-Host "Installing frontend dependencies..."
    Push-Location (Join-Path $RootDir "frontend")
    try {
      & npm install
    } finally {
      Pop-Location
    }
  }
}

function Setup-All {
  Ensure-EnvFile
  Setup-Backend
  Setup-Frontend
  Write-Host "Setup complete."
}

function Start-Backend {
  if (Test-Running $BackendPidFile) {
    Write-Host "Backend is already running (pid $(Get-Content $BackendPidFile))."
    return
  }

  Write-Host "Starting backend on http://127.0.0.1:$BackendPort ..."
  $Process = Start-Process -FilePath "uv" `
    -ArgumentList @("--cache-dir", ".uv-cache", "run", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "$BackendPort") `
    -WorkingDirectory $RootDir `
    -RedirectStandardOutput $BackendOutLog `
    -RedirectStandardError $BackendErrLog `
    -WindowStyle Hidden `
    -PassThru
  Set-Content -Path $BackendPidFile -Value $Process.Id
}

function Start-Frontend {
  if (Test-Running $FrontendPidFile) {
    Write-Host "Frontend is already running (pid $(Get-Content $FrontendPidFile))."
    return
  }

  Write-Host "Starting frontend on http://127.0.0.1:$FrontendPort ..."
  $Process = Start-Process -FilePath "npm" `
    -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "$FrontendPort") `
    -WorkingDirectory (Join-Path $RootDir "frontend") `
    -RedirectStandardOutput $FrontendOutLog `
    -RedirectStandardError $FrontendErrLog `
    -WindowStyle Hidden `
    -PassThru
  Set-Content -Path $FrontendPidFile -Value $Process.Id
}

function Start-All {
  Setup-All
  Start-Backend
  Start-Frontend
  Write-Host ""
  Write-Host "App is starting."
  Write-Host "Frontend: http://127.0.0.1:$FrontendPort/"
  Write-Host "Backend:  http://127.0.0.1:$BackendPort/"
  Write-Host "Logs:     $LogDir"
}

function Stop-All {
  Stop-FromPidFile "frontend" $FrontendPidFile
  Stop-FromPidFile "backend" $BackendPidFile
}

function Status-All {
  if (Test-Running $BackendPidFile) {
    Write-Host "Backend:  running (pid $(Get-Content $BackendPidFile))"
  } else {
    Write-Host "Backend:  stopped"
  }

  if (Test-Running $FrontendPidFile) {
    Write-Host "Frontend: running (pid $(Get-Content $FrontendPidFile))"
  } else {
    Write-Host "Frontend: stopped"
  }

  Write-Host "Logs:     $LogDir"
}

switch ($Action) {
  "setup" { Setup-All }
  "start" { Start-All }
  "stop" { Stop-All }
  "restart" {
    Stop-All
    Start-All
  }
  "status" { Status-All }
  "logs" {
    Write-Host "Backend stdout:  $BackendOutLog"
    Write-Host "Backend stderr:  $BackendErrLog"
    Write-Host "Frontend stdout: $FrontendOutLog"
    Write-Host "Frontend stderr: $FrontendErrLog"
  }
}
