#!/bin/bash

# Скрипт установки стабильной версии с мониторингом
# Автор: AI Assistant
# Дата: 2025-08-25

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка root прав
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен быть запущен от root"
        exit 1
    fi
}

# Проверка Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    
    log_success "Docker и Docker Compose доступны"
}

# Создание необходимых директорий
create_directories() {
    log "Создание необходимых директорий..."
    
    mkdir -p /opt/fastapi-backend/{data,logs}
    mkdir -p /var/log
    
    log_success "Директории созданы"
}

# Остановка старых сервисов
stop_old_services() {
    log "Остановка старых сервисов..."
    
    cd /opt/fastapi-backend
    
    # Останавливаем все docker-compose
    for compose_file in docker-compose*.yml; do
        if [[ -f "$compose_file" ]]; then
            log "Останавливаем $compose_file..."
            docker-compose -f "$compose_file" down 2>/dev/null || true
        fi
    done
    
    log_success "Старые сервисы остановлены"
}

# Запуск стабильной версии
start_stable_version() {
    log "Запуск стабильной версии..."
    
    cd /opt/fastapi-backend
    
    # Запускаем стабильную версию
    docker-compose -f docker-compose.stable.yml up -d
    
    # Ждем запуска
    log "Ожидание запуска сервисов..."
    sleep 30
    
    # Проверяем статус
    if docker-compose -f docker-compose.stable.yml ps | grep -q "Up"; then
        log_success "Стабильная версия запущена"
    else
        log_error "Ошибка запуска стабильной версии"
        exit 1
    fi
}

# Настройка мониторинга
setup_monitoring() {
    log "Настройка мониторинга..."
    
    # Делаем скрипт исполняемым
    chmod +x /opt/fastapi-backend/scripts/monitor_and_restart.sh
    
    # Копируем systemd сервис
    cp /opt/fastapi-backend/scripts/cleaning-service-monitor.service /etc/systemd/system/
    
    # Перезагружаем systemd
    systemctl daemon-reload
    
    # Включаем автозапуск
    systemctl enable cleaning-service-monitor.service
    
    # Запускаем мониторинг
    systemctl start cleaning-service-monitor.service
    
    log_success "Мониторинг настроен и запущен"
}

# Проверка работоспособности
test_functionality() {
    log "Тестирование функциональности..."
    
    # Ждем еще немного для полного запуска
    sleep 10
    
    # Проверяем health endpoint
    if curl -s -f --max-time 10 "http://localhost:8000/health" | grep -q "healthy"; then
        log_success "Health endpoint работает"
    else
        log_error "Health endpoint не работает"
        return 1
    fi
    
    # Тестируем регистрацию
    local test_response
    test_response=$(curl -s -X POST 'http://localhost:8000/api/register' \
        -H 'Content-Type: application/json' \
        -d '{"full_name":"Test User Stable","email":"teststable@example.com","phone":"+1234567897","address":"Test Address Stable","password":"testpass123"}' \
        --max-time 10)
    
    if echo "$test_response" | grep -q "access_token"; then
        log_success "Регистрация работает"
    else
        log_warning "Регистрация может не работать: $test_response"
    fi
    
    return 0
}

# Настройка логирования
setup_logging() {
    log "Настройка логирования..."
    
    # Создаем logrotate конфигурацию
    cat > /etc/logrotate.d/cleaning-service << EOF
/var/log/cleaning_service_monitor.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
    
    log_success "Логирование настроено"
}

# Основная функция
main() {
    log "🚀 Начало установки стабильной версии с мониторингом"
    
    check_root
    check_docker
    create_directories
    stop_old_services
    start_stable_version
    setup_monitoring
    setup_logging
    
    if test_functionality; then
        log_success "🎉 Установка завершена успешно!"
        log "📊 Статус сервисов:"
        docker-compose -f /opt/fastapi-backend/docker-compose.stable.yml ps
        log "📊 Статус мониторинга:"
        systemctl status cleaning-service-monitor.service --no-pager -l
    else
        log_warning "⚠️  Установка завершена с предупреждениями"
    fi
    
    log "📚 Полезные команды:"
    log "  - Просмотр логов: journalctl -u cleaning-service-monitor.service -f"
    log "  - Статус сервисов: docker-compose -f /opt/fastapi-backend/docker-compose.stable.yml ps"
    log "  - Перезапуск: systemctl restart cleaning-service-monitor.service"
}

# Запуск
main "$@"
