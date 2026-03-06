"""Initial migration — all tables

Revision ID: 0001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

Covers every table used by the PPC Affiliate Platform:
  users, affiliates, clients, campaigns, clicks,
  leads, conversions, payouts, analytics

Run with:
  flask db upgrade          # apply
  flask db downgrade base   # revert everything
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id',            sa.Integer(),     primary_key=True),
        sa.Column('email',         sa.String(120),   nullable=False),
        sa.Column('username',      sa.String(80),    nullable=False),
        sa.Column('password_hash', sa.String(255),   nullable=False),
        sa.Column('first_name',    sa.String(50)),
        sa.Column('last_name',     sa.String(50)),
        sa.Column('role',          sa.String(20),    server_default='user'),
        sa.Column('is_active',     sa.Boolean(),     server_default=sa.true()),
        sa.Column('created_at',    sa.DateTime(),    server_default=sa.func.now()),
        sa.Column('updated_at',    sa.DateTime(),    server_default=sa.func.now(),
                  onupdate=sa.func.now()),
        sa.UniqueConstraint('email',    name='uq_users_email'),
        sa.UniqueConstraint('username', name='uq_users_username'),
    )
    op.create_index('ix_users_email',    'users', ['email'],    unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # ── affiliates ────────────────────────────────────────────────────────────
    op.create_table(
        'affiliates',
        sa.Column('id',              sa.Integer(), primary_key=True),
        sa.Column('user_id',         sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('referral_code',   sa.String(20), nullable=False),
        sa.Column('commission_rate', sa.Float(),   server_default='0.2'),
        sa.Column('payment_email',   sa.String(120)),
        sa.Column('total_earnings',  sa.Float(),   server_default='0'),
        sa.Column('pending_payout',  sa.Float(),   server_default='0'),
        sa.Column('status',          sa.String(20), server_default='active'),
        sa.Column('created_at',      sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('referral_code', name='uq_affiliates_referral_code'),
    )
    op.create_index('ix_affiliates_referral_code', 'affiliates', ['referral_code'], unique=True)

    # ── clients ───────────────────────────────────────────────────────────────
    op.create_table(
        'clients',
        sa.Column('id',           sa.Integer(),  primary_key=True),
        sa.Column('user_id',      sa.Integer(),  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_name', sa.String(100), nullable=False),
        sa.Column('website',      sa.String(200)),
        sa.Column('industry',     sa.String(50)),
        sa.Column('status',       sa.String(20), server_default='active'),
        sa.Column('created_at',   sa.DateTime(), server_default=sa.func.now()),
    )

    # ── campaigns ─────────────────────────────────────────────────────────────
    op.create_table(
        'campaigns',
        sa.Column('id',             sa.Integer(),  primary_key=True),
        sa.Column('client_id',      sa.Integer(),  sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('affiliate_id',   sa.Integer(),  sa.ForeignKey('affiliates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name',           sa.String(100), nullable=False),
        sa.Column('description',    sa.Text()),
        sa.Column('offer_url',      sa.String(500), nullable=False),
        sa.Column('status',         sa.String(20),  server_default='draft'),
        sa.Column('budget',         sa.Float(),    server_default='0'),
        sa.Column('cost_per_click', sa.Float(),    server_default='0'),
        sa.Column('affiliate_cpc',  sa.Float(),    server_default='0'),
        sa.Column('total_clicks',   sa.Integer(),  server_default='0'),
        sa.Column('total_spend',    sa.Float(),    server_default='0'),
        sa.Column('start_date',     sa.DateTime()),
        sa.Column('end_date',       sa.DateTime()),
        sa.Column('created_at',     sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at',     sa.DateTime(), server_default=sa.func.now()),
    )

    # ── clicks ────────────────────────────────────────────────────────────────
    op.create_table(
        'clicks',
        sa.Column('id',               sa.Integer(),  primary_key=True),
        sa.Column('campaign_id',      sa.Integer(),  sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('affiliate_id',     sa.Integer(),  sa.ForeignKey('affiliates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ip_address',       sa.String(45), nullable=False),
        sa.Column('user_agent',       sa.String(500)),
        sa.Column('fingerprint_hash', sa.String(64)),
        sa.Column('is_valid',         sa.Boolean(),  server_default=sa.true()),
        sa.Column('payout_amount',    sa.Float(),    server_default='0'),
        sa.Column('created_at',       sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_clicks_campaign_id',      'clicks', ['campaign_id'])
    op.create_index('ix_clicks_affiliate_id',     'clicks', ['affiliate_id'])
    op.create_index('ix_clicks_ip_address',       'clicks', ['ip_address'])
    op.create_index('ix_clicks_fingerprint_hash', 'clicks', ['fingerprint_hash'])
    op.create_index('ix_clicks_created_at',       'clicks', ['created_at'])

    # ── leads ─────────────────────────────────────────────────────────────────
    op.create_table(
        'leads',
        sa.Column('id',           sa.Integer(),  primary_key=True),
        sa.Column('campaign_id',  sa.Integer(),  sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('affiliate_id', sa.Integer(),  sa.ForeignKey('affiliates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('email',        sa.String(120), nullable=False),
        sa.Column('name',         sa.String(100)),
        sa.Column('phone',        sa.String(20)),
        sa.Column('metadata',     sa.JSON()),
        sa.Column('ip_address',   sa.String(45)),
        sa.Column('user_agent',   sa.String(500)),
        sa.Column('status',       sa.String(20), server_default='pending'),
        sa.Column('fraud_score',  sa.Float(),    server_default='0'),
        sa.Column('created_at',   sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at',   sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_leads_email',       'leads', ['email'])
    op.create_index('ix_leads_campaign_id', 'leads', ['campaign_id'])

    # ── conversions ───────────────────────────────────────────────────────────
    op.create_table(
        'conversions',
        sa.Column('id',           sa.Integer(), primary_key=True),
        sa.Column('lead_id',      sa.Integer(), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('campaign_id',  sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('affiliate_id', sa.Integer(), sa.ForeignKey('affiliates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('revenue',      sa.Float(),   server_default='0'),
        sa.Column('commission',   sa.Float(),   server_default='0'),
        sa.Column('status',       sa.String(20), server_default='pending'),
        sa.Column('created_at',   sa.DateTime(), server_default=sa.func.now()),
    )

    # ── payouts ───────────────────────────────────────────────────────────────
    op.create_table(
        'payouts',
        sa.Column('id',                sa.Integer(), primary_key=True),
        sa.Column('affiliate_id',      sa.Integer(), sa.ForeignKey('affiliates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount',            sa.Float(),   nullable=False),
        sa.Column('currency',          sa.String(3), server_default='USD'),
        sa.Column('status',            sa.String(20), server_default='pending'),
        sa.Column('payment_method',    sa.String(50)),
        sa.Column('payment_reference', sa.String(100)),
        sa.Column('processed_at',      sa.DateTime()),
        sa.Column('created_at',        sa.DateTime(), server_default=sa.func.now()),
    )

    # ── analytics ─────────────────────────────────────────────────────────────
    op.create_table(
        'analytics',
        sa.Column('id',           sa.Integer(), primary_key=True),
        sa.Column('event_type',   sa.String(50), nullable=False),
        sa.Column('campaign_id',  sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True),
        sa.Column('affiliate_id', sa.Integer(), sa.ForeignKey('affiliates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('lead_id',      sa.Integer(), sa.ForeignKey('leads.id',      ondelete='SET NULL'), nullable=True),
        sa.Column('metadata',     sa.JSON()),
        sa.Column('ip_address',   sa.String(45)),
        sa.Column('user_agent',   sa.String(500)),
        sa.Column('created_at',   sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_analytics_event_type', 'analytics', ['event_type'])
    op.create_index('ix_analytics_created_at', 'analytics', ['created_at'])


def downgrade():
    op.drop_table('analytics')
    op.drop_table('payouts')
    op.drop_table('conversions')
    op.drop_table('leads')
    op.drop_table('clicks')
    op.drop_table('campaigns')
    op.drop_table('clients')
    op.drop_table('affiliates')
    op.drop_table('users')
