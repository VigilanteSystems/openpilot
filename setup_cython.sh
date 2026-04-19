#!/bin/bash
# Setup script for building openpilot Cython modules
# Run from openpilot root directory
#
# Usage: ./setup_cython.sh
#
# This builds all native modules needed for pytest collection

set -e

cd "$(dirname "$0")"
REPO_ROOT=$(pwd)

echo "=== openpilot Cython build setup ==="

# Git safe directories
echo "Configuring git..."
for dir in panda opendbc_repo rednose_repo tinygrad_repo teleoprtc_repo msgq_repo; do
    git config --global --add safe.directory "$REPO_ROOT/$dir" 2>/dev/null || true
done

# Sync dependencies
echo "[1/4] Syncing dependencies..."
uv sync --extra tools

# Install test dependencies
echo "[2/4] Installing test dependencies..."
uv pip install -q \
    pytest pytest-xdist pytest-randomly pytest-timeout pytest-asyncio \
    hypothesis pytest-benchmark flaky pytest-mock pytest-repeat nbmake pycapnp

# Build all native modules
echo "[3/4] Building native modules..."
uv run scons -j$(nproc)

# Verify
echo "[4/4] Verifying..."
uv run python -c "
from openpilot.common.params_pyx import Params
from msgq.ipc_pyx import Context
print('Build verification: OK')
"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Run pytest collection:"
echo "  time uv run pytest --collect-only"
echo ""
echo "Expected output format (from issue #32611):"
echo "  real    0mX.XXXs"
echo "  user   0mX.XXXs"
echo "  sys    0mX.XXXs"
echo "  === 4011 tests collected in X.XXs ==="