#!/bin/sh
# Keep the production HTTPS override active during routine Compose operations.
set -eu
release_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec docker compose --env-file "$release_root/release.env" \
  -f "$release_root/deploy/compose.yaml" \
  -f "$release_root/deploy/compose.public.yaml" "$@"
