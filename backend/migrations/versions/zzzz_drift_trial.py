"""drift trial — reverted after test"""
from alembic import op
revision = "zzzz_drift_trial"
down_revision = "246fdd13f6ee"   # current head — verify with `uv run alembic heads`
def upgrade():
    op.execute("ALTER TABLE table_that_does_not_exist ADD COLUMN x int")
def downgrade():
    pass
