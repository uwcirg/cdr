from setuptools import setup

project = "cdr"

setup(
    name=project,
    version='0.1',
    url='https://github.com/uwcirg/cdr',
    description='CDR (Clical Document Repository) is a Flask (Python microframework) providing API access to a MongoDB instance housing CCDAs.',
    author='CIRG',
    author_email='cirg@u.washington.edu',
    packages=["cdr"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'python-dateutil',
        'pytz',
        'tzlocal',
        'Flask',
        'Flask-MongoEngine',
        'Flask-Script',
        'Flask-Testing',
        'nose',
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
