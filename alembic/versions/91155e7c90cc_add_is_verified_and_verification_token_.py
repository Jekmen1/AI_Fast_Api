from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '33a5f2f097e7'
down_revision = '975b5502ed3c'
branch_labels = None
depends_on = None

def upgrade():


    # Add the new columns to the 'user' table
    op.add_column('user', sa.Column('is_verified', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('verification_token', sa.String(length=255), nullable=True))

    # Create a unique constraint on the 'verification_token' column
    op.create_unique_constraint(None, 'user', ['verification_token'])

def downgrade():
    # Drop the new columns in case of downgrade
    op.drop_table('user', if_exists=True)

    op.drop_constraint(None, 'user', type_='unique')
    op.drop_column('user', 'verification_token')
    op.drop_column('user', 'is_verified')



