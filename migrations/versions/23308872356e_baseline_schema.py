"""baseline schema

Revision ID: 23308872356e
Revises: 
Create Date: 2026-07-18 22:41:40.114995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '23308872356e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'userdb',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('google_sub', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_userdb_google_sub'), 'userdb', ['google_sub'], unique=True)

    op.create_table(
        'urldb',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('fullurl', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('shorturl', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['userdb.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_urldb_shorturl'), 'urldb', ['shorturl'], unique=False)
    op.create_index(op.f('ix_urldb_user_id'), 'urldb', ['user_id'], unique=False)



def downgrade() -> None:
    op.drop_table('urldb')
    op.drop_table('userdb')
