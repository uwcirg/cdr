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
        'python-dateutil==2.4.2',
        'pytz==2015.7',
        'tzlocal==1.2',
        'Flask==0.10.1',
        'Flask-MongoEngine==0.7.4',
        'Flask-WTF==0.12',
        'Jinja2==2.8',
        'WTForms==2.1',
        'Werkzeug==0.11.3',
        'itsdangerous==0.24',
        'MarkupSafe==0.23',
        'mongoengine==0.10.5',
        'pymongo==3.2',
        'Flask-Script==2.0.5',
        'Flask-Testing==0.4.2',
        'nose==1.3.7'
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
