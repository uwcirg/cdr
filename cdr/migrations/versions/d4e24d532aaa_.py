"""Migrate latest mongo content into postgres

NB - Mongo has since been removed from the project.  To prevent
build errors, this migration has been stripped of its content, see
repository history for details.

Revision ID: d4e24d532aaa
Revises: 
Create Date: 2019-11-20 09:53:58.970000

"""


def upgrade():
    pass


def downgrade():
    # no downgrade path - create fresh postgres database if necessary
    pass
