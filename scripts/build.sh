#!/usr/bin/env bash
# Build a single-file binary for the current OS/arch into dist/blktop.
set -euo pipefail
cd "$(dirname "$0")/.."

uv run pyinstaller --noconfirm --clean --onefile \
    --name blktop \
    --paths src \
    --collect-data textual \
    --collect-submodules rich._unicode_data \
    --distpath dist --workpath build/pyinstaller --specpath build \
    scripts/entry.py

echo "Built: $(du -h dist/blktop | cut -f1)  dist/blktop"
