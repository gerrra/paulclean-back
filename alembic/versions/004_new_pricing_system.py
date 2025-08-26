"""New pricing system

Revision ID: 004
Revises: 003
Create Date: 2025-08-26 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Создаем новую таблицу services
    op.create_table('services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_services_id'), 'services', ['id'], unique=False)
    
    # Создаем новые таблицы для системы ценообразования
    
    # Таблица опций ценообразования
    op.create_table('pricing_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('option_type', sa.String(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_hidden', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pricing_options_id'), 'pricing_options', ['id'], unique=False)
    
    # Таблица для опций "цена за штуку"
    op.create_table('per_unit_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pricing_option_id', sa.Integer(), nullable=False),
        sa.Column('price_per_unit', sa.Float(), nullable=False),
        sa.Column('short_description', sa.String(), nullable=True),
        sa.Column('full_description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['pricing_option_id'], ['pricing_options.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_per_unit_options_id'), 'per_unit_options', ['id'], unique=False)
    
    # Таблица для селекторных опций
    op.create_table('selector_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pricing_option_id', sa.Integer(), nullable=False),
        sa.Column('short_description', sa.String(), nullable=True),
        sa.Column('full_description', sa.Text(), nullable=True),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['pricing_option_id'], ['pricing_options.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_selector_options_id'), 'selector_options', ['id'], unique=False)
    
    # Таблица для процентных опций
    op.create_table('percentage_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pricing_option_id', sa.Integer(), nullable=False),
        sa.Column('short_description', sa.String(), nullable=True),
        sa.Column('full_description', sa.Text(), nullable=True),
        sa.Column('percentage_value', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['pricing_option_id'], ['pricing_options.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_percentage_options_id'), 'percentage_options', ['id'], unique=False)
    
    # Обновляем таблицу order_items - заменяем старые поля на JSON
    op.drop_column('order_items', 'removable_cushion_count')
    op.drop_column('order_items', 'unremovable_cushion_count')
    op.drop_column('order_items', 'pillow_count')
    op.drop_column('order_items', 'window_count')
    op.drop_column('order_items', 'rug_width')
    op.drop_column('order_items', 'rug_length')
    op.drop_column('order_items', 'rug_count')
    op.drop_column('order_items', 'base_cleaning')
    op.drop_column('order_items', 'pet_hair')
    op.drop_column('order_items', 'urine_stains')
    op.drop_column('order_items', 'accelerated_drying')
    
    # Добавляем новое поле для выбранных опций
    op.add_column('order_items', sa.Column('selected_options', sa.JSON(), nullable=False))


def downgrade():
    # Восстанавливаем старые поля в order_items
    op.add_column('order_items', sa.Column('removable_cushion_count', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('unremovable_cushion_count', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('pillow_count', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('window_count', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('rug_width', sa.Float(), nullable=True))
    op.add_column('order_items', sa.Column('rug_length', sa.Float(), nullable=True))
    op.add_column('order_items', sa.Column('rug_count', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('base_cleaning', sa.Boolean(), nullable=True))
    op.add_column('order_items', sa.Column('pet_hair', sa.Boolean(), nullable=True))
    op.add_column('order_items', sa.Column('urine_stains', sa.Boolean(), nullable=True))
    op.add_column('order_items', sa.Column('accelerated_drying', sa.Boolean(), nullable=True))
    
    # Убираем новое поле
    op.drop_column('order_items', 'selected_options')
    
    # Удаляем новые таблицы
    op.drop_index(op.f('ix_percentage_options_id'), table_name='percentage_options')
    op.drop_table('percentage_options')
    op.drop_index(op.f('ix_selector_options_id'), table_name='selector_options')
    op.drop_table('selector_options')
    op.drop_index(op.f('ix_per_unit_options_id'), table_name='per_unit_options')
    op.drop_table('per_unit_options')
    op.drop_index(op.f('ix_pricing_options_id'), table_name='pricing_options')
    op.drop_table('pricing_options')
    op.drop_index(op.f('ix_services_id'), table_name='services')
    op.drop_table('services')
