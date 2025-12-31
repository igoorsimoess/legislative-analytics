#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi

  echo "The current project setup requires uv which is not installed."

  # If we're not in an interactive shell, don't block waiting for input.
  if [[ ! -t 0 ]]; then
    echo "Non-interactive shell detected. Please install uv and re-run."
    echo "Recommended install options:"
    echo "  - macOS (Homebrew): brew install uv"
    echo "  - Cross-platform:   curl -LsSf https://astral.sh/uv/install.sh | sh"
    return 1
  fi

  read -r -p "Install uv now? Yes or No: " answer
  case "$answer" in
    [Yy]|[Yy][Ee][Ss])
      echo "==> Installing uv"
      if command -v brew >/dev/null 2>&1; then
        brew install uv
      else
        if ! command -v curl >/dev/null 2>&1; then
          echo "curl not found. Please install uv manually and re-run."
          return 1
        fi
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # The installer typically places uv in ~/.local/bin
        export PATH="$HOME/.local/bin:$PATH"
      fi
      ;;
    *)
      echo "Aborting. Please install uv and re-run."
      return 1
      ;;
  esac

  if ! command -v uv >/dev/null 2>&1; then
    echo "uv install step completed but uv is still not on PATH."
    echo "Try restarting your shell or add ~/.local/bin to PATH, then re-run."
    return 1
  fi
}

ensure_uv

echo "==> Installing dependencies"
uv sync --dev

echo "==> Running main app (generate output CSVs)"
uv run python "$ROOT_DIR/src/main.py" --data-dir "$ROOT_DIR/data" --out-dir "$ROOT_DIR/output"

echo "==> Running test suite (excluding edge tests)"
uv run pytest -m "not edge" -v

echo "==> Running edge-case tests"
uv run pytest -m edge -v

echo "==> Done"


