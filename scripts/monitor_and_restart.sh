#!/bin/bash

# Скрипт мониторинга и автоматического восстановления
# Автор: AI Assistant
# Дата: 2025-08-25

set -e

# Конфигурация
SERVICE_NAME="cleaning_service_api_stable"
REDIS_NAME="cleaning_service_redis_stable"
COMPOSE_FILE="docker-compose.stable.yml"
WORK_DIR="/opt/fastapi-backend"
LOG_FILE="/var/log/cleaning_service_monitor.log"
MAX_RESTARTS=3
CHECK_INTERVAL=60

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Функция проверки здоровья API
check_api_health() {
    local response
    response=$(curl -s -f --max-time 10 "http://localhost:8000/health" 2>/dev/null || echo "FAILED")
    
    if [[ "$response" == *"healthy"* ]]; then
        echo "HEALTHY"
    else
        echo "UNHEALTHY"
    fi
}

# Функция проверки статуса контейнера
check_container_status() {
    local container_name=$1
    local status
    
    status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "NOT_FOUND")
    echo "$status"
}

# Функция перезапуска сервиса
restart_service() {
    local service=$1
    local reason=$2
    
    log "🔄 Перезапускаем $service. Причина: $reason"
    
    cd "$WORK_DIR" || exit 1
    
    # Останавливаем сервис
    docker-compose -f "$COMPOSE_FILE" stop "$service" 2>/dev/null || true
    
    # Ждем остановки
    sleep 5
    
    # Запускаем сервис
    docker-compose -f "$COMPOSE_FILE" up -d "$service"
    
    # Ждем запуска
    sleep 10
    
    log "✅ $service перезапущен"
}

# Функция полного перезапуска
full_restart() {
    local reason=$1
    
    log "🚨 Выполняем полный перезапуск. Причина: $reason"
    
    cd "$WORK_DIR" || exit 1
    
    # Останавливаем все
    docker-compose -f "$COMPOSE_FILE" down
    
    # Очищаем Docker
    docker system prune -f
    
    # Запускаем заново
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Ждем запуска
    sleep 30
    
    log "✅ Полный перезапуск завершен"
}

# Функция проверки дискового пространства
check_disk_space() {
    local usage
    usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $usage -gt 90 ]]; then
        log "⚠️  Внимание! Диск заполнен на ${usage}%"
        return 1
    fi
    
    return 0
}

# Функция проверки памяти
check_memory() {
    local mem_usage
    mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if [[ $mem_usage -gt 90 ]]; then
        log "⚠️  Внимание! Память используется на ${mem_usage}%"
        return 1
    fi
    
    return 0
}

# Основной цикл мониторинга
main() {
    log "🚀 Запуск мониторинга сервиса $SERVICE_NAME"
    
    local restart_count=0
    
    while true; do
        log "🔍 Проверка состояния сервисов..."
        
        # Проверяем дисковое пространство и память
        check_disk_space
        check_memory
        
        # Проверяем статус API контейнера
        local api_status
        api_status=$(check_container_status "$SERVICE_NAME")
        
        if [[ "$api_status" == "NOT_FOUND" ]]; then
            log "❌ Контейнер $SERVICE_NAME не найден"
            restart_service "api" "container_not_found"
            ((restart_count++))
        elif [[ "$api_status" != "running" ]]; then
            log "❌ Контейнер $SERVICE_NAME не запущен (статус: $api_status)"
            restart_service "api" "container_not_running"
            ((restart_count++))
        else
            # Проверяем здоровье API
            local health_status
            health_status=$(check_api_health)
            
            if [[ "$health_status" == "UNHEALTHY" ]]; then
                log "❌ API нездоров"
                restart_service "api" "api_unhealthy"
                ((restart_count++))
            else
                log "✅ API работает нормально"
                restart_count=0  # Сбрасываем счетчик при успехе
            fi
        fi
        
        # Проверяем Redis
        local redis_status
        redis_status=$(check_container_status "$REDIS_NAME")
        
        if [[ "$redis_status" != "running" ]]; then
            log "❌ Redis не запущен (статус: $redis_status)"
            restart_service "redis" "redis_not_running"
        fi
        
        # Если слишком много перезапусков, делаем полный перезапуск
        if [[ $restart_count -ge $MAX_RESTARTS ]]; then
            log "🚨 Слишком много перезапусков ($restart_count). Выполняем полный перезапуск"
            full_restart "too_many_restarts"
            restart_count=0
        fi
        
        log "⏳ Следующая проверка через $CHECK_INTERVAL секунд"
        sleep $CHECK_INTERVAL
    done
}

# Обработка сигналов
trap 'log "🛑 Получен сигнал завершения. Останавливаем мониторинг"; exit 0' SIGTERM SIGINT

# Запуск
main "$@"
