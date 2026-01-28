# CROAK Installer Script for Windows
# Computer Recognition Orchestration Agent Kit
# https://github.com/vfrog-ai/croak
#
# Usage:
#   .\install.ps1
#   .\install.ps1 -Dev
#   .\install.ps1 -NoVenv
#
# Run with: Set-ExecutionPolicy Bypass -Scope Process -Force; .\install.ps1

param(
    [switch]$Dev,
    [switch]$NoVenv,
    [switch]$Help
)

# Colors
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$Blue = "Blue"

function Write-Banner {
    Write-Host @"

   ____ ____   ___    _    _  __
  / ___|  _ \ / _ \  / \  | |/ /
 | |   | |_) | | | |/ _ \ | ' /
 | |___|  _ <| |_| / ___ \| . \
  \____|_| \_\\___/_/   \_\_|\_\

  Computer Recognition Orchestration Agent Kit
  by vfrog.ai

"@ -ForegroundColor $Green
}

function Write-Info($message) {
    Write-Host "[INFO] " -ForegroundColor $Blue -NoNewline
    Write-Host $message
}

function Write-Success($message) {
    Write-Host "[OK] " -ForegroundColor $Green -NoNewline
    Write-Host $message
}

function Write-Warning($message) {
    Write-Host "[WARN] " -ForegroundColor $Yellow -NoNewline
    Write-Host $message
}

function Write-Error($message) {
    Write-Host "[ERROR] " -ForegroundColor $Red -NoNewline
    Write-Host $message
}

function Show-Help {
    Write-Host "CROAK Installer for Windows"
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Dev      Install in development mode with dev dependencies"
    Write-Host "  -NoVenv   Skip virtual environment creation (use system Python)"
    Write-Host "  -Help     Show this help message"
    Write-Host ""
    Write-Host "Environment Variables:"
    Write-Host "  CROAK_INSTALL_DIR   Installation directory (default: ./)"
    Write-Host "  VFROG_API_KEY       vfrog.ai API key (optional, can be set later)"
    Write-Host ""
}

if ($Help) {
    Show-Help
    exit 0
}

# Print banner
Write-Banner

# Check system requirements
Write-Info "Checking system requirements..."

# Check Python version
function Test-Python {
    $pythonCmd = $null

    # Try python first, then python3
    foreach ($cmd in @("python", "python3")) {
        try {
            $version = & $cmd --version 2>&1
            if ($version -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -ge 3 -and $minor -ge 10) {
                    $script:PythonCmd = $cmd
                    Write-Success "Python $major.$minor found"
                    return $true
                }
            }
        } catch {
            continue
        }
    }

    Write-Error "Python 3.10 or higher required. Please install Python from https://python.org"
    return $false
}

# Check Git
function Test-Git {
    try {
        $version = git --version 2>&1
        if ($version -match "git version (.+)") {
            Write-Success "Git $($Matches[1]) found"
            return $true
        }
    } catch {
        Write-Warning "Git not found. Some features may not work."
        return $false
    }
    return $false
}

# Check NVIDIA GPU
function Test-CUDA {
    try {
        $nvidiaSmi = nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "NVIDIA GPU detected (driver: $nvidiaSmi)"
            $script:HasGPU = $true
            return $true
        }
    } catch {
        Write-Info "No NVIDIA GPU detected. Will use Modal.com for training."
        $script:HasGPU = $false
        return $false
    }
    $script:HasGPU = $false
    return $false
}

# Run checks
if (-not (Test-Python)) {
    exit 1
}
Test-Git | Out-Null
Test-CUDA | Out-Null

# Create virtual environment
if (-not $NoVenv) {
    Write-Info "Creating virtual environment..."

    $venvDir = if ($env:CROAK_INSTALL_DIR) {
        Join-Path $env:CROAK_INSTALL_DIR "venv"
    } else {
        ".\venv"
    }

    if (Test-Path $venvDir) {
        Write-Warning "Virtual environment already exists at $venvDir"
        $response = Read-Host "Overwrite? [y/N]"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Remove-Item -Recurse -Force $venvDir
        } else {
            Write-Info "Using existing virtual environment"
        }
    }

    if (-not (Test-Path $venvDir)) {
        & $PythonCmd -m venv $venvDir
        Write-Success "Virtual environment created at $venvDir"
    }

    # Activate virtual environment
    $activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Success "Virtual environment activated"
    } else {
        Write-Error "Could not find activation script at $activateScript"
        exit 1
    }

    # Upgrade pip
    pip install --upgrade pip --quiet
}

# Install CROAK
Write-Info "Installing CROAK..."

if ($Dev) {
    Write-Info "Installing in development mode with dev dependencies..."
    pip install -e ".[dev]" --quiet
    Write-Success "CROAK installed in development mode"
} else {
    pip install -e . --quiet
    Write-Success "CROAK installed"
}

# Verify installation
Write-Info "Verifying installation..."

try {
    $croakVersion = & $PythonCmd -c "import croak; print(croak.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "CROAK $croakVersion installed successfully"
    } else {
        throw "Import failed"
    }
} catch {
    Write-Error "CROAK installation verification failed"
    exit 1
}

# Check if croak CLI is available
try {
    $croakPath = Get-Command croak -ErrorAction Stop
    Write-Success "CROAK CLI is available"
} catch {
    Write-Warning "CROAK CLI not in PATH. You may need to activate the virtual environment."
}

# Setup configuration
Write-Info "Setting up configuration..."

# Create user config directory
$configDir = Join-Path $env:USERPROFILE ".croak"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
    Write-Success "Created config directory at $configDir"
}

# Check for vfrog API key
if ($env:VFROG_API_KEY) {
    Write-Success "VFROG_API_KEY environment variable detected"
} else {
    Write-Info "VFROG_API_KEY not set. You'll need this for annotation features."
    Write-Info "Get your API key at: https://vfrog.ai/settings/api"
}

# Print success message and next steps
Write-Host ""
Write-Host "============================================" -ForegroundColor $Green
Write-Host "  CROAK Installation Complete!" -ForegroundColor $Green
Write-Host "============================================" -ForegroundColor $Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor $Cyan
Write-Host ""

if (-not $NoVenv) {
    Write-Host "  1. Activate the virtual environment:"
    Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor $Yellow
    Write-Host ""
}

Write-Host "  2. Initialize a new CROAK project:"
Write-Host "     cd your-project-directory" -ForegroundColor $Yellow
Write-Host "     croak init" -ForegroundColor $Yellow
Write-Host ""
Write-Host "  3. Check pipeline status:"
Write-Host "     croak status" -ForegroundColor $Yellow
Write-Host ""
Write-Host "  4. Get help:"
Write-Host "     croak help" -ForegroundColor $Yellow
Write-Host ""

if (-not $env:VFROG_API_KEY) {
    Write-Host "Don't forget to set your vfrog API key:" -ForegroundColor $Yellow
    Write-Host '  $env:VFROG_API_KEY = "your_api_key_here"' -ForegroundColor $Yellow
    Write-Host ""
}

if (-not $HasGPU) {
    Write-Host "For GPU training, CROAK will use Modal.com:" -ForegroundColor $Cyan
    Write-Host "  1. Sign up at https://modal.com (free credits available)"
    Write-Host "  2. Run: modal setup"
    Write-Host ""
}

Write-Host "Happy detecting! " -ForegroundColor $Green -NoNewline
Write-Host "🐸"
Write-Host ""
