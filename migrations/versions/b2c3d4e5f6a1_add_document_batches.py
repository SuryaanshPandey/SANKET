"""add_document_batches

Revision ID: b2c3d4e5f6a1
Revises: f393e89d69b3
Create Date: 2026-09-19 06:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, Sequence[str], None] = 'f393e89d69b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONType = JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create document_batches table if not already existing
    if 'document_batches' not in tables:
        op.create_table(
            'document_batches',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('case_id', sa.String(length=64), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_by', sa.String(length=128), nullable=False),
            sa.Column('total_documents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('processed_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
            sa.Column('cross_document_analysis', JSONType, nullable=False),
        )
        op.create_index('ix_document_batches_case_id', 'document_batches', ['case_id'])
        op.create_index('ix_document_batches_status', 'document_batches', ['status'])

    # 2. Add batch_id to documents if not already existing
    doc_columns = [col['name'] for col in inspector.get_columns('documents')]
    if 'batch_id' not in doc_columns:
        with op.batch_alter_table('documents') as batch_op:
            batch_op.add_column(sa.Column('batch_id', sa.String(length=36), nullable=True))
            batch_op.create_index('ix_documents_batch_id', ['batch_id'])
            batch_op.create_foreign_key(
                'fk_documents_batch_id',
                'document_batches',
                ['batch_id'],
                ['id'],
                ondelete='SET NULL',
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    doc_columns = [col['name'] for col in inspector.get_columns('documents')]

    if 'batch_id' in doc_columns:
        with op.batch_alter_table('documents') as batch_op:
            batch_op.drop_constraint('fk_documents_batch_id', type_='foreignkey')
            batch_op.drop_index('ix_documents_batch_id')
            batch_op.drop_column('batch_id')

    tables = inspector.get_table_names()
    if 'document_batches' in tables:
        op.drop_index('ix_document_batches_status', table_name='document_batches')
        op.drop_index('ix_document_batches_case_id', table_name='document_batches')
        op.drop_table('document_batches')
