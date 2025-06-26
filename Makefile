.PHONY: help up down logs psql backup restore clean

help:
	@echo "Available commands:"
	@echo "  make up       - Start the database"
	@echo "  make down     - Stop the database"
	@echo "  make logs     - View database logs"
	@echo "  make psql     - Connect to database"
	@echo "  make backup   - Create a backup"
	@echo "  make restore  - Restore from backup"
	@echo "  make clean    - Remove all data (careful!)"

up:
	docker compose up -d
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "Database is running!"

down:
	docker compose down

logs:
	docker compose logs -f postgis

psql:
	docker exec -it mariupol_postgis psql -U mariupol_researcher -d mariupol_toponyms

backup:
	@mkdir -p data/backups
	@DATE=$$(date +%Y%m%d_%H%M%S); \
	docker exec mariupol_postgis pg_dump -U mariupol_researcher mariupol_toponyms > data/backups/backup_$$DATE.sql
	@echo "Backup created!"

restore:
	@echo "Available backups:"
	@ls -la data/backups/*.sql
	@echo "To restore, run: docker exec -i mariupol_postgis psql -U mariupol_researcher mariupol_toponyms < data/backups/[backup_file]"

clean:
	@echo "WARNING: This will delete all data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue"
	@read confirm
	docker compose down -v