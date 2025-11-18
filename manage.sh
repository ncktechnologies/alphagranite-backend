#!/bin/bash

# Quick commands for common tasks

case "$1" in
    start)
        echo "Starting application..."
        docker-compose up -d
        ;;
    stop)
        echo "Stopping application..."
        docker-compose down
        ;;
    restart)
        echo "Restarting application..."
        docker-compose restart
        ;;
    logs)
        echo "Showing logs (press Ctrl+C to exit)..."
        docker-compose logs -f web
        ;;
    build)
        echo "Rebuilding application..."
        docker-compose up -d --build
        ;;
    migrate)
        echo "Running migrations..."
        docker-compose exec web python scripts/auto_migrate.py
        ;;
    shell)
        echo "Opening shell in web container..."
        docker-compose exec web /bin/bash
        ;;
    db)
        echo "Opening PostgreSQL shell..."
        docker-compose exec db psql -U admin -d alpha_granite
        ;;
    backup)
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        echo "Creating backup: $BACKUP_FILE"
        docker-compose exec -T db pg_dump -U admin alpha_granite > "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        ;;
    status)
        echo "Container status:"
        docker-compose ps
        ;;
    clean)
        echo "Cleaning up containers and images..."
        docker-compose down
        docker system prune -f
        ;;
    *)
        echo "Alpha Granite Backend - Management Commands"
        echo ""
        echo "Usage: ./manage.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show application logs"
        echo "  build    - Rebuild and start services"
        echo "  migrate  - Run database migrations"
        echo "  shell    - Open shell in web container"
        echo "  db       - Open PostgreSQL shell"
        echo "  backup   - Create database backup"
        echo "  status   - Show container status"
        echo "  clean    - Clean up containers and images"
        echo ""
        ;;
esac
