"""Enhanced authentication features

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('totp_secret', sa.String(), nullable=True))
    op.add_column('users', sa.Column('totp_enabled', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('email_verification_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), default=0))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    
    # Add new columns to clients table
    op.add_column('clients', sa.Column('hashed_password', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('totp_secret', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('totp_enabled', sa.Boolean(), default=False))
    op.add_column('clients', sa.Column('email_verified', sa.Boolean(), default=False))
    op.add_column('clients', sa.Column('email_verification_token', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True))
    op.add_column('clients', sa.Column('failed_login_attempts', sa.Integer(), default=0))
    op.add_column('clients', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    
    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_type', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'])
    
    # Create rate_limits table
    op.create_table('rate_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('requests_count', sa.Integer(), default=0),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_limits_key'), 'rate_limits', ['key'])
    op.create_index(op.f('ix_rate_limits_window_start'), 'rate_limits', ['window_start'])


def downgrade() -> None:
    # Drop rate_limits table
    op.drop_table('rate_limits')
    
    # Drop refresh_tokens table
    op.drop_table('refresh_tokens')
    
    # Remove columns from clients table
    op.drop_column('clients', 'locked_until')
    op.drop_column('clients', 'failed_login_attempts')
    op.drop_column('clients', 'email_verification_expires')
    op.drop_column('clients', 'email_verification_token')
    op.drop_column('clients', 'email_verified')
    op.drop_column('clients', 'totp_enabled')
    op.drop_column('clients', 'totp_secret')
    op.drop_column('clients', 'hashed_password')
    
    # Remove columns from users table
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'email_verification_expires')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret')
