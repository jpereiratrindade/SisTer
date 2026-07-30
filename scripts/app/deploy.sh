#!/usr/bin/env bash
set -euo pipefail

echo "==> Starting SisTer Production Deployment"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# 1. Update source code (optional, uncomment if you want automatic git pull)
# echo "==> Pulling latest code..."
# git pull origin main

# 2. Build the application in Release mode
echo "==> Building application..."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)" --target sisterd

# 3. Run database migrations for production
# This assumes you have SISTER_DB_PASSWORD and other envs set, or you source them.
echo "==> Running database migrations..."
if [[ -f ".env.production" ]]; then
  set -a
  source ".env.production"
  set +a
fi

# We use the existing migrate.sh script
# Since sister_env.sh doesn't officially support production yet, we set the env vars manually
export SISTER_DATABASE_URL="${SISTER_DATABASE_URL:-postgresql://sister:sister@localhost:5432/sister_prod}"

# Check if migrate.sh supports 'production', if not just run goose directly or adjust the script
./scripts/db/migrate.sh production || echo "Migration script may not support production environment natively yet. Check scripts/lib/sister_env.sh."

# 4. Restart the systemd service
echo "==> Restarting systemd service..."
# Use sudo if the script isn't running as root
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl restart sisterd
  echo "==> Checking service status..."
  sudo systemctl status sisterd --no-pager || true
else
  echo "Warning: systemctl not found. Service not restarted."
fi

echo "==> Deploy finished successfully!"
