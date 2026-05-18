#!/usr/bin/env bash
# Backup the LingvoPal PostgreSQL database.
#
# Usage:
#   ./scripts/backup_db.sh                 # uses .env from project root
#   ./scripts/backup_db.sh --dry-run       # print pg_dump command, don't run
#
# Output: backups/lingvopal_YYYYMMDD_HHMMSS.sql.gz in the project root.
# Keeps the last 14 daily backups; older files are pruned automatically.
#
# Requirements: pg_dump on PATH (or inside the postgres container via docker exec).
# Schedule with cron:
#   0 3 * * * /path/to/LingvoPal/scripts/backup_db.sh >> /var/log/lingvopal_backup.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
BACKUP_DIR="$PROJECT_ROOT/backups"
KEEP_DAYS=14

# ── Load .env (if present) ────────────────────────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_USER="${DATABASE_USER:-lingvopal_user}"
DB_PASS="${DATABASE_PASSWORD:-}"
DB_NAME="${DATABASE_NAME:-lingvopal}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
FILENAME="lingvopal_${TIMESTAMP}.sql.gz"
OUTPUT="$BACKUP_DIR/$FILENAME"

# ── Dry-run mode ─────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--dry-run" ]]; then
  echo "DRY RUN — would execute:"
  echo "  PGPASSWORD=*** pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME | gzip > $OUTPUT"
  exit 0
fi

mkdir -p "$BACKUP_DIR"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting backup → $OUTPUT"

PGPASSWORD="$DB_PASS" pg_dump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --format=plain \
  --no-owner \
  --no-acl \
  "$DB_NAME" \
  | gzip -9 > "$OUTPUT"

SIZE="$(du -sh "$OUTPUT" | cut -f1)"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup complete — $SIZE → $FILENAME"

# ── Prune old backups ─────────────────────────────────────────────────────────
find "$BACKUP_DIR" -name "lingvopal_*.sql.gz" -mtime "+$KEEP_DAYS" -delete
REMAINING=$(find "$BACKUP_DIR" -name "lingvopal_*.sql.gz" | wc -l)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Pruned backups older than ${KEEP_DAYS} days — ${REMAINING} files kept"
