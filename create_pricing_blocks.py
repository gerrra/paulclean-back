#!/usr/bin/env python3
"""
Скрипт для создания примеров блоков ценообразования
"""
import sqlite3
import json
import sys
import os
from datetime import datetime

# Добавляем путь к модулям приложения
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_pricing_blocks():
    """Создаем примеры блоков ценообразования для услуг"""
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('cleaning_service.db')
    cursor = conn.cursor()
    
    # Получаем первую услугу (или создаем тестовую)
    cursor.execute("SELECT id FROM services LIMIT 1")
    service_result = cursor.fetchone()
    
    if not service_result:
        print("❌ Нет услуг в базе данных. Сначала создайте услугу через админку.")
        return
    
    service_id = service_result[0]
    print(f"✅ Используем услугу с ID: {service_id}")
    
    # Создаем блоки ценообразования
    pricing_blocks = [
        {
            "name": "Количество подушек дивана",
            "block_type": "quantity",
            "order_index": 1,
            "is_required": True,
            "quantity_options": {
                "name": "Подушки дивана",
                "unit_price": 30.0,
                "min_quantity": 1,
                "max_quantity": 10,
                "unit_name": "штука"
            }
        },
        {
            "name": "Количество окон",
            "block_type": "quantity", 
            "order_index": 2,
            "is_required": False,
            "quantity_options": {
                "name": "Окна",
                "unit_price": 25.0,
                "min_quantity": 1,
                "max_quantity": 20,
                "unit_name": "штука"
            }
        },
        {
            "name": "Базовая чистка",
            "block_type": "toggle",
            "order_index": 3,
            "is_required": False,
            "toggle_option": {
                "name": "Базовая чистка",
                "short_description": "Глубокая чистка",
                "full_description": "Использование специальных средств для глубокой чистки",
                "percentage_increase": 38.0
            }
        },
        {
            "name": "Шерсть животных",
            "block_type": "toggle",
            "order_index": 4,
            "is_required": False,
            "toggle_option": {
                "name": "Шерсть животных",
                "short_description": "Удаление шерсти",
                "full_description": "Специальная обработка для удаления шерсти животных",
                "percentage_increase": 15.0
            }
        },
        {
            "name": "Ускоренная сушка",
            "block_type": "toggle",
            "order_index": 5,
            "is_required": False,
            "toggle_option": {
                "name": "Ускоренная сушка",
                "short_description": "Быстрая сушка",
                "full_description": "Использование специального оборудования для ускоренной сушки",
                "percentage_increase": 0.0  # Фиксированная надбавка $45
            }
        }
    ]
    
    for block_data in pricing_blocks:
        # Создаем блок ценообразования
        cursor.execute("""
            INSERT INTO pricing_blocks (service_id, name, block_type, order_index, is_required, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            service_id,
            block_data["name"],
            block_data["block_type"],
            block_data["order_index"],
            block_data["is_required"],
            True,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        block_id = cursor.lastrowid
        print(f"✅ Создан блок: {block_data['name']} (ID: {block_id})")
        
        # Создаем опции в зависимости от типа блока
        if block_data["block_type"] == "quantity" and "quantity_options" in block_data:
            qo = block_data["quantity_options"]
            cursor.execute("""
                INSERT INTO quantity_options (pricing_block_id, name, unit_price, min_quantity, max_quantity, unit_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                block_id,
                qo["name"],
                qo["unit_price"],
                qo["min_quantity"],
                qo["max_quantity"],
                qo["unit_name"],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            print(f"  ✅ Создана опция количества: {qo['name']} - ${qo['unit_price']} за {qo['unit_name']}")
        
        elif block_data["block_type"] == "toggle" and "toggle_option" in block_data:
            to = block_data["toggle_option"]
            cursor.execute("""
                INSERT INTO toggle_options (pricing_block_id, name, short_description, full_description, percentage_increase, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                block_id,
                to["name"],
                to["short_description"],
                to["full_description"],
                to["percentage_increase"],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            print(f"  ✅ Создана опция переключения: {to['name']} - {to['percentage_increase']}%")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Блоки ценообразования созданы успешно!")
    print(f"📋 Создано блоков: {len(pricing_blocks)}")
    print(f"🔗 Связаны с услугой ID: {service_id}")
    print("\n💡 Теперь можно тестировать API:")
    print(f"   GET /api/services/{service_id}/pricing-structure")
    print(f"   POST /api/services/{service_id}/calculate-price")

if __name__ == "__main__":
    create_pricing_blocks()
