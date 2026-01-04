#!/bin/bash
# Backup script for Dora data volumes
set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Compose project name
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dora}"

echo "Starting backup at $(date)"
echo "Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to backup a volume
backup_volume() {
    local volume_name=$1
    local backup_file="$BACKUP_DIR/${volume_name}_${TIMESTAMP}.tar.gz"

    echo "Backing up volume: $volume_name"

    docker run --rm \
        -v "${PROJECT_NAME}_${volume_name}:/data:ro" \
        -v "$BACKUP_DIR:/backup" \
        alpine \
        tar czf "/backup/$(basename "$backup_file")" -C /data .

    if [ $? -eq 0 ]; then
        echo "Successfully backed up $volume_name to $backup_file"
        ls -lh "$backup_file"
    else
        echo "ERROR: Failed to backup $volume_name"
        return 1
    fi
}

# Function to backup PostgreSQL database
backup_postgres() {
    local backup_file="$BACKUP_DIR/postgres_${TIMESTAMP}.sql.gz"

    echo "Backing up PostgreSQL database..."

    docker exec "${PROJECT_NAME}_postgres_1" \
        pg_dumpall -U dora | gzip > "$backup_file"

    if [ $? -eq 0 ]; then
        echo "Successfully backed up PostgreSQL to $backup_file"
        ls -lh "$backup_file"
    else
        echo "ERROR: Failed to backup PostgreSQL"
        return 1
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    echo "Cleaning up backups older than $RETENTION_DAYS days..."

    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

    echo "Cleanup completed"
}

# Backup volumes
backup_volume "qdrant_data"
backup_volume "neo4j_data"
backup_volume "redis_data"

# Backup PostgreSQL if running
if docker ps --format '{{.Names}}' | grep -q "${PROJECT_NAME}_postgres"; then
    backup_postgres
fi

# Backup user data directory
if [ -d "/app/data" ]; then
    echo "Backing up user data directory..."
    tar czf "$BACKUP_DIR/user_data_${TIMESTAMP}.tar.gz" -C /app data
    echo "User data backed up"
fi

# Cleanup old backups
cleanup_old_backups

# Summary
echo "======================================"
echo "Backup completed successfully at $(date)"
echo "Backup location: $BACKUP_DIR"
echo "======================================"
du -sh "$BACKUP_DIR"
echo "======================================"

exit 0
