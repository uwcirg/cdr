# CDR
Clinical Document Repository

Flask API used to store and present relative details for CCDA files
persisted to the filesystem.

# Install instructions

Clone git repository
```bash
git clone https://github.com/uwcirg/cdr.git
```

Create python 3 virtual environment
```bash
python3 -m venv env
```

Activate virtual environment
```bash
source env/bin/activate
```

Install dependencies
```bash
pip install wheel
pip install --requirement requirements.dev.txt
```

export varible needed to run development version
```bash
export FLASK_APP=manage.py
```

## run in develop mode
`flask run`

## run tests
from root of checkout:
`py.test`
