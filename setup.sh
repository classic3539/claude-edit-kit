#!/usr/bin/env bash
# One-time setup: tools, local transcriber, Claude plugins. Safe to run again.
set -uo pipefail
cd "$(dirname "$0")"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is missing. Install it from https://brew.sh, then run ./setup.sh again."
  exit 1
fi

echo "== tools (ffmpeg, yt-dlp, node, python)"
brew install ffmpeg yt-dlp node python@3.12 || { echo "brew install failed, see above"; exit 1; }

echo "== transcriber"
if [ "$(uname -m)" = "arm64" ]; then
  PY="$(brew --prefix)/opt/python@3.12/bin/python3.12"
  [ -x .venv/bin/python ] || "$PY" -m venv .venv
  .venv/bin/pip install -q --upgrade pip parakeet-mlx || { echo "parakeet-mlx install failed, see above"; exit 1; }
  echo "parakeet-mlx ready (the model downloads on the first transcribe)"
else
  echo "Not an Apple Silicon Mac: parakeet-mlx won't run here. Open Claude Code and say: set up whisper.cpp for scripts/transcribe.py"
fi

echo "== Claude plugins"
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add heygen-com/hyperframes   || echo "  (hyperframes marketplace: see message above)"
  claude plugin install hyperframes@hyperframes          || echo "  (hyperframes plugin: see message above)"
  claude plugin marketplace add bradautomates/claude-video || echo "  (watch marketplace: see message above)"
  claude plugin install watch@claude-video               || echo "  (watch plugin: see message above)"
else
  echo "Claude Code isn't installed. Install it, then run ./setup.sh again (or run these 4 lines):"
  echo "  claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes"
  echo "  claude plugin marketplace add bradautomates/claude-video && claude plugin install watch@claude-video"
fi

mkdir -p footage references renders
echo
echo "Done. Start Claude Code in this folder with: claude"
