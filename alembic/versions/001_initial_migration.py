"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create clients table
    op.create_table('clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clients_email'), 'clients', ['email'], unique=True)

    # Create services table
    op.create_table('services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('price_per_removable_cushion', sa.Float(), nullable=True),
        sa.Column('price_per_unremovable_cushion', sa.Float(), nullable=True),
        sa.Column('price_per_pillow', sa.Float(), nullable=True),
        sa.Column('price_per_window', sa.Float(), nullable=True),
        sa.Column('base_surcharge_pct', sa.Float(), nullable=True),
        sa.Column('pet_hair_surcharge_pct', sa.Float(), nullable=True),
        sa.Column('urine_stain_surcharge_pct', sa.Float(), nullable=True),
        sa.Column('accelerated_drying_surcharge', sa.Float(), nullable=True),
        sa.Column('before_image', sa.String(), nullable=True),
        sa.Column('after_image', sa.String(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create cleaners table
    op.create_table('cleaners',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('calendar_email', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cleaners_email'), 'cleaners', ['email'], unique=True)

    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.String(), nullable=False),
        sa.Column('scheduled_time', sa.String(), nullable=False),
        sa.Column('total_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('cleaner_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('google_calendar_event_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cleaner_id'], ['cleaners.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create order_items table
    op.create_table('order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('removable_cushion_count', sa.Integer(), nullable=True),
        sa.Column('unremovable_cushion_count', sa.Integer(), nullable=True),
        sa.Column('pillow_count', sa.Integer(), nullable=True),
        sa.Column('window_count', sa.Integer(), nullable=True),
        sa.Column('rug_width', sa.Float(), nullable=True),
        sa.Column('rug_length', sa.Float(), nullable=True),
        sa.Column('rug_count', sa.Integer(), nullable=True),
        sa.Column('base_cleaning', sa.Boolean(), nullable=True),
        sa.Column('pet_hair', sa.Boolean(), nullable=True),
        sa.Column('urine_stains', sa.Boolean(), nullable=True),
        sa.Column('accelerated_drying', sa.Boolean(), nullable=True),
        sa.Column('calculated_cost', sa.Float(), nullable=False),
        sa.Column('calculated_time_minutes', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create cleaner_service association table
    op.create_table('cleaner_service',
        sa.Column('cleaner_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['cleaner_id'], ['cleaners.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], )
    )


def downgrade() -> None:
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cleaner_service')
    op.drop_table('cleaners')
    op.drop_table('services')
    op.drop_table('clients')
    op.drop_table('users')
