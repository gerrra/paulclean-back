"""Add pricing blocks tables

Revision ID: 003
Revises: 002_enhanced_auth
Create Date: 2025-08-25 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Create pricing_blocks table
    op.create_table('pricing_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('block_type', sa.String(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pricing_blocks_id'), 'pricing_blocks', ['id'], unique=False)
    
    # Create quantity_options table
    op.create_table('quantity_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pricing_block_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('min_quantity', sa.Integer(), nullable=True),
        sa.Column('max_quantity', sa.Integer(), nullable=True),
        sa.Column('unit_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pricing_block_id'], ['pricing_blocks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quantity_options_id'), 'quantity_options', ['id'], unique=False)
    
    # Create type_options table
    op.create_table('type_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pricing_block_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('options', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pricing_block_id'], ['pricing_blocks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_type_options_id'), 'type_options', ['id'], unique=False)
    
    # Create toggle_options table
    op.create_table('toggle_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pricing_block_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('short_description', sa.String(), nullable=False),
        sa.Column('full_description', sa.Text(), nullable=True),
        sa.Column('percentage_increase', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pricing_block_id'], ['pricing_blocks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_toggle_options_id'), 'toggle_options', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_toggle_options_id'), table_name='toggle_options')
    op.drop_table('toggle_options')
    op.drop_index(op.f('ix_type_options_id'), table_name='type_options')
    op.drop_table('type_options')
    op.drop_index(op.f('ix_quantity_options_id'), table_name='quantity_options')
    op.drop_table('quantity_options')
    op.drop_index(op.f('ix_pricing_blocks_id'), table_name='pricing_blocks')
    op.drop_table('pricing_blocks')
