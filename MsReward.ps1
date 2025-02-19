# ----------------------------- Script description -----------------------------
# This script is a wrapper for the "MS Rewards Farmer" python script, which is
# a tool to automate the Microsoft Rewards daily tasks. The script will try to
# update the main script, detect the Python installation, run the main script
# and retry if it fails, while cleaning every error-prone elements (sessions,
# orphan chrome instances, etc.).

# Use the `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` command to allow
# script execution in PowerShell without confirmation each time.


# --------------------------- Script initialization ----------------------------
# Set the script directory as the working directory and define the script
# parameters

param (
    [switch]$help = $false,
    [switch]$update = $false,
    [switch]$noCacheDelete = $false,
    [int]$maxRetries = 5,
    [string]$arguments = "",
    [string]$pythonPath = "",
    [string]$scriptName = "main.py",
    [string]$cacheFolder = ".\sessions",
    [string]$logColor = "Yellow"
)

$name = "MS Rewards Farmer"
$startTime = Get-Date

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

if ($help) {
    Write-Host "Usage: .\MS_reward.ps1 [-help] [-update] [-maxRetries <int>] [-arguments <string>] [-pythonExecutablePath <string>] [-scriptName <string>] [-cacheFolder <string>] [-logColor <string>]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -help                 Display this help message."
    Write-Host "  -update               Update the script if a new version is available."
    Write-Host "  -noCacheDelete        Do not delete the cache folder if the script fails."
    Write-Host "  -maxRetries <int>     Maximum number of retries if the script fails (default: 5)."
    Write-Host "  -arguments <string>   Arguments to pass to the main script."
    Write-Host "  -pythonPath <string>  Path to the Python executable."
    Write-Host "  -scriptName <string>  Name of the main script."
    Write-Host "  -cacheFolder <string> Folder to store the sessions."
    Write-Host "  -logColor <string>    Color of the log messages (default: Yellow)."
    exit 0
}


# ------------------------------- Script update --------------------------------
# Try to update the script if git is available and the script is in a
# git repository

$updated = $false

if ($update -and (Test-Path .git) -and (Get-Command git -ErrorAction SilentlyContinue)) {
    $gitOutput = & git pull --ff-only
    if ($LastExitCode -eq 0) {
        if ($gitOutput -match "Already up to date.") {
            Write-Host "> $name is already up-to-date" -ForegroundColor $logColor
        } else {
            $updated = $true
            Write-Host "> $name updated successfully" -ForegroundColor $logColor
        }
    } else {
        Write-Host "> Cannot automatically update $name - please update it manually." -ForegroundColor $logColor
    }
}


# ----------------------- Python installation detection ------------------------
# Try to detect the Python installation or virtual environments

# If no virtual environment Python executable was provided, try to find a
# virtual environment Python executable
if (-not $pythonPath) {
    $pythonPath = (Get-ChildItem -Path .\ -Recurse -Filter python.exe | Where-Object { $_.FullName -match "Scripts\\python.exe" }).FullName | Select-Object -First 1
}

# If no virtual environment Python executable was found, try to find the py
# launcher
if (-not $pythonPath) {
    $pythonPath = (Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
}

# If no virtual environment Python executable or py launcher was found, try to
# find the system Python
if (-not $pythonPath) {
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
}

# If no Python executable was found, exit with an error
if (-not $pythonPath) {
    Write-Host "> Python executable not found. Please install Python." -ForegroundColor $logColor
    exit 1
}

Write-Host "> Python executable found at $pythonPath" -ForegroundColor $logColor

# ------------------------- Python dependencies update -------------------------
# Try to update the Python dependencies if the script was updated

if ($updated) {
    & $pythonPath -m pip install -r requirements.txt --upgrade
    if ($LastExitCode -eq 0) {
        Write-Host "> Python dependencies updated successfully" -ForegroundColor $logColor
    } else {
        Write-Host "> Cannot update Python dependencies - please update them manually." -ForegroundColor $logColor
    }
}


# --------------------------------- Script run ---------------------------------
# Try to run the script and retry if it fails, while cleaning every error-prone
# elements (sesions, orphan chrome instances, etc.)

function Invoke-Farmer {
    for ($i = 1; $i -le $maxRetries; $i++) {
        if ($arguments) {
            & $pythonPath $scriptName $arguments
        } else {
            & $pythonPath $scriptName
        }
        if ($LastExitCode -eq 0) {
            Write-Host "> $name completed (Attempt $i/$maxRetries)." -ForegroundColor $logColor
            exit 0
        }
        Write-Host "> $name failed (Attempt $i/$maxRetries) with exit code $LastExitCode." -ForegroundColor $logColor
        Stop-Process -Name "undetected_chromedriver" -ErrorAction SilentlyContinue
        Get-Process -Name "chrome" -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt $startTime } | Stop-Process -ErrorAction SilentlyContinue
    }
}

Invoke-Farmer

if (-not $noCacheDelete) {
    Write-Host "> All $name runs failed ($maxRetries/$maxRetries). Removing cache and re-trying..." -ForegroundColor $logColor

    if (Test-Path "$cacheFolder") {
        Remove-Item -Recurse -Force "$cacheFolder" -ErrorAction SilentlyContinue
    }

    Invoke-Farmer
}

Write-Host "> All $name runs failed ($maxRetries/$maxRetries). Exiting with error." -ForegroundColor $logColor

exit 1