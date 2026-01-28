#!/usr/bin/env bash
# CROAK Installer Script
# Computer Recognition Orchestration Agent Kit
# https://github.com/vfrog-ai/croak
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/vfrog-ai/croak/main/install.sh | bash
#   or
#   ./install.sh
#
# Options:
#   --dev       Install in development mode with dev dependencies
#   --no-venv   Skip virtual environment creation (use system Python)
#   --help      Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# CROAK ASCII Art
print_banner() {
    echo -e "${GREEN}"
    cat << 'EOF'
   ____ ____   ___    _    _  __
  / ___|  _ \ / _ \  / \  | |/ /
 | |   | |_) | | | |/ _ \ | ' /
 | |___|  _ <| |_| / ___ \| . \
  \____|_| \_\\___/_/   \_\_|\_\

  Computer Recognition Orchestration Agent Kit
  by vfrog.ai
EOF
    echo -e "${NC}"
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help message
show_help() {
    echo "CROAK Installer"
    echo ""
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dev       Install in development mode with dev dependencies"
    echo "  --no-venv   Skip virtual environment creation (use system Python)"
    echo "  --help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  CROAK_INSTALL_DIR   Installation directory (default: ./)"
    echo "  VFROG_API_KEY       vfrog.ai API key (optional, can be set later)"
    echo ""
}

# Parse arguments
DEV_MODE=false
USE_VENV=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Print banner
print_banner

# Check system requirements
log_info "Checking system requirements..."

# Check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python not found. Please install Python 3.10 or higher."
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
        log_error "Python 3.10 or higher required. Found: $PYTHON_VERSION"
        exit 1
    fi

    log_success "Python $PYTHON_VERSION found"
}

# Check Git
check_git() {
    if ! command -v git &> /dev/null; then
        log_warning "Git not found. Some features may not work."
    else
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        log_success "Git $GIT_VERSION found"
    fi
}

# Check CUDA (optional)
check_cuda() {
    if command -v nvidia-smi &> /dev/null; then
        CUDA_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n1)
        log_success "NVIDIA GPU detected (driver: $CUDA_VERSION)"
        HAS_GPU=true
    else
        log_info "No NVIDIA GPU detected. Will use Modal.com for training."
        HAS_GPU=false
    fi
}

check_python
check_git
check_cuda

# Create virtual environment
if [ "$USE_VENV" = true ]; then
    log_info "Creating virtual environment..."

    VENV_DIR="${CROAK_INSTALL_DIR:-.}/venv"

    if [ -d "$VENV_DIR" ]; then
        log_warning "Virtual environment already exists at $VENV_DIR"
        read -p "Overwrite? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            log_info "Using existing virtual environment"
        fi
    fi

    if [ ! -d "$VENV_DIR" ]; then
        $PYTHON_CMD -m venv "$VENV_DIR"
        log_success "Virtual environment created at $VENV_DIR"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"

    # Upgrade pip
    pip install --upgrade pip --quiet
fi

# Install CROAK
log_info "Installing CROAK..."

if [ "$DEV_MODE" = true ]; then
    log_info "Installing in development mode with dev dependencies..."
    pip install -e ".[dev]" --quiet
    log_success "CROAK installed in development mode"
else
    pip install -e . --quiet
    log_success "CROAK installed"
fi

# Verify installation
log_info "Verifying installation..."

if $PYTHON_CMD -c "import croak" 2>/dev/null; then
    CROAK_VERSION=$($PYTHON_CMD -c "import croak; print(croak.__version__)")
    log_success "CROAK $CROAK_VERSION installed successfully"
else
    log_error "CROAK installation verification failed"
    exit 1
fi

# Check if croak CLI is available
if command -v croak &> /dev/null; then
    log_success "CROAK CLI is available"
else
    log_warning "CROAK CLI not in PATH. You may need to activate the virtual environment."
fi

# Setup configuration
log_info "Setting up configuration..."

# Create user config directory
CONFIG_DIR="$HOME/.croak"
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
    log_success "Created config directory at $CONFIG_DIR"
fi

# Check for vfrog API key
if [ -n "$VFROG_API_KEY" ]; then
    log_success "VFROG_API_KEY environment variable detected"
else
    log_info "VFROG_API_KEY not set. You'll need this for annotation features."
    log_info "Get your API key at: https://vfrog.ai/settings/api"
fi

# Print success message and next steps
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  CROAK Installation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo ""

if [ "$USE_VENV" = true ]; then
    echo "  1. Activate the virtual environment:"
    echo -e "     ${YELLOW}source venv/bin/activate${NC}"
    echo ""
fi

echo "  2. Initialize a new CROAK project:"
echo -e "     ${YELLOW}cd your-project-directory${NC}"
echo -e "     ${YELLOW}croak init${NC}"
echo ""
echo "  3. Check pipeline status:"
echo -e "     ${YELLOW}croak status${NC}"
echo ""
echo "  4. Get help:"
echo -e "     ${YELLOW}croak help${NC}"
echo ""

if [ -z "$VFROG_API_KEY" ]; then
    echo -e "${YELLOW}Don't forget to set your vfrog API key:${NC}"
    echo -e "  ${YELLOW}export VFROG_API_KEY=your_api_key_here${NC}"
    echo ""
fi

if [ "$HAS_GPU" = false ]; then
    echo -e "${CYAN}For GPU training, CROAK will use Modal.com:${NC}"
    echo "  1. Sign up at https://modal.com (free credits available)"
    echo "  2. Run: modal setup"
    echo ""
fi

echo -e "${GREEN}Happy detecting! 🐸${NC}"
echo ""
