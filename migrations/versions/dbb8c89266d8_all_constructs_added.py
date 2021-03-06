"""all constructs added

Revision ID: dbb8c89266d8
Revises: 0884800e0264
Create Date: 2020-03-19 09:27:19.172582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbb8c89266d8'
down_revision = '0884800e0264'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('SurveyData', sa.Column('construct10neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct10pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct11neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct11pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct12neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct12pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct13neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct13pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct14neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct14pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct15neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct15pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct2neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct2pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct3neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct3pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct4neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct4pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct5neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct5pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct6neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct6pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct7neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct7pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct8neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct8pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct9neg', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('construct9pos', sa.Text(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose02', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose03', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose04', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose05', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose06', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose07', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose08', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose09', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose10', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose11', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose12', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose13', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose14', sa.Integer(), nullable=True))
    op.add_column('SurveyData', sa.Column('oddgoose15', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('SurveyData', 'oddgoose15')
    op.drop_column('SurveyData', 'oddgoose14')
    op.drop_column('SurveyData', 'oddgoose13')
    op.drop_column('SurveyData', 'oddgoose12')
    op.drop_column('SurveyData', 'oddgoose11')
    op.drop_column('SurveyData', 'oddgoose10')
    op.drop_column('SurveyData', 'oddgoose09')
    op.drop_column('SurveyData', 'oddgoose08')
    op.drop_column('SurveyData', 'oddgoose07')
    op.drop_column('SurveyData', 'oddgoose06')
    op.drop_column('SurveyData', 'oddgoose05')
    op.drop_column('SurveyData', 'oddgoose04')
    op.drop_column('SurveyData', 'oddgoose03')
    op.drop_column('SurveyData', 'oddgoose02')
    op.drop_column('SurveyData', 'construct9pos')
    op.drop_column('SurveyData', 'construct9neg')
    op.drop_column('SurveyData', 'construct8pos')
    op.drop_column('SurveyData', 'construct8neg')
    op.drop_column('SurveyData', 'construct7pos')
    op.drop_column('SurveyData', 'construct7neg')
    op.drop_column('SurveyData', 'construct6pos')
    op.drop_column('SurveyData', 'construct6neg')
    op.drop_column('SurveyData', 'construct5pos')
    op.drop_column('SurveyData', 'construct5neg')
    op.drop_column('SurveyData', 'construct4pos')
    op.drop_column('SurveyData', 'construct4neg')
    op.drop_column('SurveyData', 'construct3pos')
    op.drop_column('SurveyData', 'construct3neg')
    op.drop_column('SurveyData', 'construct2pos')
    op.drop_column('SurveyData', 'construct2neg')
    op.drop_column('SurveyData', 'construct15pos')
    op.drop_column('SurveyData', 'construct15neg')
    op.drop_column('SurveyData', 'construct14pos')
    op.drop_column('SurveyData', 'construct14neg')
    op.drop_column('SurveyData', 'construct13pos')
    op.drop_column('SurveyData', 'construct13neg')
    op.drop_column('SurveyData', 'construct12pos')
    op.drop_column('SurveyData', 'construct12neg')
    op.drop_column('SurveyData', 'construct11pos')
    op.drop_column('SurveyData', 'construct11neg')
    op.drop_column('SurveyData', 'construct10pos')
    op.drop_column('SurveyData', 'construct10neg')
    # ### end Alembic commands ###
