#!/usr/bin/env bash
set -euo pipefail

# Minimal conda-first environment bootstrap skeleton for AI repo reproduction.
# This script intentionally avoids guessing too much. Adjust the environment
# name or package list to match the target repository README.

REPO_PATH="${1:-.}"
ENV_NAME="${2:-repro-env}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"

echo "Target repo: ${REPO_PATH}"
echo "Environment name: ${ENV_NAME}"

if command -v conda >/dev/null 2>&1; then
  if [ -f "${REPO_PATH}/environment.yml" ]; then
    echo "[1/3] Creating environment from environment.yml"
    conda env create -f "${REPO_PATH}/environment.yml"
    echo "[2/3] Activate the environment declared by environment.yml"
    echo "  conda activate <name-from-environment-yml>"
    echo "[3/3] Review README for any extra pip or asset steps"
  else
    echo "[1/3] Creating base environment"
    conda create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}"

    echo "[2/3] Activating environment"
    # shellcheck disable=SC1091
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "${ENV_NAME}"

    echo "[3/3] Installing common dependency files when present"
    if [ -f "${REPO_PATH}/requirements.txt" ]; then
      python -m pip install -r "${REPO_PATH}/requirements.txt"
    fi
  fi
else
  echo "conda was not found. Install Anaconda or Miniconda, or translate the setup manually."
  exit 1
fi
