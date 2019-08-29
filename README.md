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
python3 -m venv env
```

Activate virtual environment
```bash
source env/bin/activate
```

Install dependencies
```bash
pip install --requirement requirements.dev.txt
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

# NOTES
looks like there are exactly 3 unique values,
1 unique code and 1 unique status_code in the whole status collection

> db.status.find({'value': {$in: [ObjectId("56956a8786413c038a2d926e"), ObjectId("56956a8786413c038a2d929c"), ObjectId("56956a8786413c038a2d927e")]}}).count()
15080180
> db.status.find().count()
15080180

attempt update, using one value as example:
> db.status.find({'value': ObjectId("56956a8786413c038a2d927e")}).limit(1)
{ "_id" : ObjectId("56979a9286413cf3c5a4c4fa"), "status_code" : "completed", "code" : ObjectId("56956a8786413c038a2d926d"), "value" : ObjectId("56956a8786413c038a2d927e") }

