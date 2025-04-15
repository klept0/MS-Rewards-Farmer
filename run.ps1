# ----------------------------- Script description -----------------------------
# This script is a wrapper for the "MS Rewards Farmer" python script, which is
# a tool to automate the Microsoft Rewards daily tasks. The script will try to
# update the main script, detect the Python installation, stop orphan chrome
# instances, run the main script and retry if it fails (optionally cleaning
# every error-prone sessions).

# Use the `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` command to allow
# script execution in PowerShell without confirmation each time.


# --------------------------- Script initialization ----------------------------
# Set the script directory as the working directory and define the script
# parameters

param (
    [Alias('h')][switch]$help = $false,
    [Alias('u')][switch]$update = $false,
    [Alias('d')][switch]$deleteSessionsOnFail = $false,
    [Alias('r', 'retries')][int]$maxAttempts = 1,
    [Alias('a', 'args')][string]$arguments = "",
    [Alias('p', 'python')][string]$pythonPath = "",
    [Alias('sc', 'script')][string]$scriptDir = "",
    [Alias('se')][string]$sessions = ".\sessions"
)

$name = "MS Rewards Farmer"
$startTime = Get-Date

if ($scriptDir) {
    if (-not (Test-Path $scriptDir)) {
        Write-Host "> Script directory not found at $scriptDir. Please provide a valid path." -ForegroundColor "Green"
        exit 1
    }
} else {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
}

Write-Host "> Entering $scriptDir" -ForegroundColor "Green"
Set-Location $scriptDir

if ($help) {
    Write-Host "Usage: .\run.ps1 [-h] [-u] [-d] [-r <int>] [-a <string>] [-p <string>] [-s <string>] [-c <string>]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -h, -help"
    Write-Host "      Display this help message."
    Write-Host "  -u, -update"
    Write-Host "      Update the script if a new version is available."
    Write-Host "  -d, -deleteSessionsOnFail"
    Write-Host "      Delete the cache folder if the script fails."
    Write-Host "  -r <int>, -retries <int>, -maxRetries <int>"
    Write-Host "      Maximum number of retries if the script fails (default: 3)."
    Write-Host "  -a <string>, -args <string>, -arguments <string>"
    Write-Host "      Arguments to pass to the main script (default: none)."
    Write-Host "  -p <string>, -python <string>, -pythonPath <string>"
    Write-Host "      Path to the Python executable (default: detected)."
    Write-Host "  -sc <string>, -script <string>, -scriptDir <string>"
    Write-Host "      Path to the main script directory (default: current directory)."
    Write-Host "  -se <string>, -sessions <string>"
    Write-Host "      Folder to store the sessions (default: .\sessions)."
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
            Write-Host "> $name is already up-to-date" -ForegroundColor "Green"
        } else {
            $updated = $true
            Write-Host "> $name updated successfully" -ForegroundColor "Green"
        }
    } else {
        Write-Host "> Cannot automatically update $name - please update it manually." -ForegroundColor "Green"
    }
}


# ----------------------- Python installation detection ------------------------
# Try to detect the Python installation or virtual environments

# If the python path is provided, check if it is a valid Python executable
if ($pythonPath -and -not (Test-Path $pythonPath)) {
    Write-Host "> Python executable not found at $pythonPath. Please provide a valid path." -ForegroundColor "Green"
    exit 1
}

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
    Write-Host "> Python executable not found. Please install Python." -ForegroundColor "Green"
    exit 1
}

Write-Host "> Using Python executable at $pythonPath" -ForegroundColor "Green"

# ------------------------- Python dependencies update -------------------------
# Try to update the Python dependencies if the script was updated

if ($updated) {
    & $pythonPath -m pip install -r requirements.txt --upgrade
    if ($LastExitCode -eq 0) {
        Write-Host "> Python dependencies updated successfully" -ForegroundColor "Green"
    } else {
        Write-Host "> Cannot update Python dependencies - please update them manually." -ForegroundColor "Green"
    }
}


# --------------------------------- Script run ---------------------------------
# Try to run the script and retry if it fails, while cleaning every error-prone
# elements (sesions, orphan chrome instances, etc.)

function Invoke-Farmer {
    for ($i = 1; $i -le $maxAttempts; $i++) {
        Stop-Process -Name "undetected_chromedriver" -ErrorAction SilentlyContinue
        Get-Process -Name "chrome" -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt $startTime } | Stop-Process -ErrorAction SilentlyContinue
        if ($arguments) {
            & $pythonPath "main.py" $arguments
        } else {
            & $pythonPath "main.py"
        }
        if ($LastExitCode -eq 0) {
            Write-Host "> $name completed (Attempt $i/$maxAttempts)." -ForegroundColor "Green"
            exit 0
        }
        Write-Host "> $name failed (Attempt $i/$maxAttempts) with exit code $LastExitCode." -ForegroundColor "Green"
    }
}

Invoke-Farmer

if ($deleteSessionsOnFail) {
    Write-Host "> All $name runs failed ($maxAttempts/$maxAttempts). Removing cache and re-trying..." -ForegroundColor "Green"

    if (Test-Path "$sessions") {
        Remove-Item -Recurse -Force "$sessions" -ErrorAction SilentlyContinue
    }

    Invoke-Farmer
}

Write-Host "> All $name runs failed ($maxAttempts/$maxAttempts). Exiting with error." -ForegroundColor "Green"

exit 1