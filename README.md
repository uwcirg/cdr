# CDR
Clinical Document Repository

Convenient hole to throw CCDAs in, with simple APIs for getting back
what you need.

# Install instructions

Clone git repository
```bash
git clone https://github.com/uwcirg/cdr.git
```

Create python 3 virtual environment
```bash
virtualenv --python=/usr/bin/python3 env
```

Activate virtual environment
```bash
source env/bin/activate
```

Install dependencies
```bash
pip install -r requirements.dev.txt
```

export varible needed to run development version
```bash
export FLASK_APP=manage.py
```

## run in develop mode
```flask run```

## run tests
from root of checkout:
```py.test```

# Example mongo query to view saved CCDA info
db.observation.find({'icd10': ObjectId("56956a8786413c038a2d926b")})
