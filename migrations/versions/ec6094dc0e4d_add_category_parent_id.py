
"""Add category parent_id

Revision ID: ec6094dc0e4d
Revises:
Create Date: 2026-11-03 00:13:35.895695
"""
from alembic import op
import sqlalchemy as sa


revision = 'ec6094dc0e4d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('parent_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_category_parent_id_category',
            'category',
            ['parent_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_category_parent_id_category',
            type_='foreignkey'
        )
        batch_op.drop_column('parent_id')
