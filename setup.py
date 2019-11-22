from setuptools import setup

project = "cdr"

setup(
    name=project,
    version='0.1',
    url='https://github.com/uwcirg/cdr',
    description='CDR (Clical Document Repository) is a Flask app providing API access to a PostgreSQL db holding significant data for CCDAs, stored on the filesystem.',
    author='CIRG',
    author_email='cirg@u.washington.edu',
    packages=["cdr"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'gunicorn',
        'psycopg2',
        'python-dateutil',
        'pytz',
        'tzlocal',
        'Flask',
        'Flask-Migrate',
        'Flask-SQLAlchemy',
        'Flask-Script',
        'Flask-Testing',
    ],
    test_suite='tests',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries'
    ]
)
