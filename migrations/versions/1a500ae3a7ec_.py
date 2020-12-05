"""empty message

Revision ID: 1a500ae3a7ec
Revises: 
Create Date: 2020-11-29 00:11:44.212947

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1a500ae3a7ec'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('is_approved', sa.String(length=10), nullable=False))
    op.add_column('user', sa.Column('user_type', sa.String(length=10), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column(' is_approved', mysql.TEXT(), nullable=True))
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_constraint(None, 'user', type_='unique')
    op.alter_column('user', 'image_file',
               existing_type=mysql.TEXT(),
               nullable=True)
    op.alter_column('user', 'email',
               existing_type=mysql.VARCHAR(length=32),
               nullable=True)
    op.drop_column('user', 'user_type')
    op.drop_column('user', 'is_approved')
    op.create_table('OAuth_user',
    sa.Column('id', mysql.TEXT(), nullable=False),
    sa.Column('username', mysql.TEXT(), nullable=False),
    sa.Column('email', mysql.TEXT(), nullable=False),
    sa.Column('image_file', mysql.TEXT(), nullable=False),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('strategies',
    sa.Column('user_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('strategy_location', mysql.VARCHAR(length=1024), nullable=False),
    sa.Column('strategy_id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('last_modified_date', mysql.DATETIME(), nullable=False),
    sa.Column('last_modified_user', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('strategy_name', mysql.VARCHAR(length=64), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='userid_fk', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('strategy_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('backtests',
    sa.Column('strategy_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('backtest_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('pnl_location', mysql.VARCHAR(length=1024), nullable=False),
    sa.Column('last_modified_date', mysql.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['strategy_id'], ['strategies.strategy_id'], name='backtests_ibfk_1'),
    sa.PrimaryKeyConstraint('strategy_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###