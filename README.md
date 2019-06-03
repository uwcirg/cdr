# CDR
Clinical Document Repository

Convenient hole to throw CCDAs in, with simple APIs for getting back
what you need.

---

~/puppet-5-control/data/nodes/fermium.cirg.washington.edu.yaml

# mkdir -p /srv/www/fenway-cdr.cirg.washington.edu/htdocs

# cd /srv/www/fenway-cdr.cirg.washington.edu
# chmod 2775 htdocs
# chown -R cpro:cpro htdocs

# su - cpro

$ git clone --branch feature_cnics_pro_fenway_parity git@github.com:uwcirg/cdr.git /srv/www/fenway-cdr.cirg.washington.edu/htdocs

$ cd /srv/www/fenway-cdr.cirg.washington.edu/htdocs

$ virtualenv env
$ /srv/www/fenway-cdr.cirg.washington.edu/htdocs/env/bin/python setup.py install

---

Testing:

GET https://fenway-cdr.cirg.washington.edu/patients/644135/problem_list?filter=%7B%22filter%22%3A%7B%22icd9%22%3A+%7B%22code%22%3A+%5B%22296.2%2A%22%2C%22296.3%2A%22%2C%22300.4%22%2C%22311.%2A%22%5D%7D%2C%22icd10%22%3A+%7B%22code%22%3A+%5B%22F32.%2A%22%2C%22F33.%2A%22%5D%7D%7D%2C%22status%22%3A+%7B%22value%22%3A+%7B%22code%22%3A+%2255561003%22%2C+%22code_system%22%3A+%222.16.840.1.113883.6.96%22%7D%7D%7D

https://fenway-cdr.cirg.washington.edu/patients/41815/problem_list?filter=%7B%22filter%22%3A%7B%22icd9%22%3A+%7B%22code%22%3A+%5B%22296.2%2A%22%2C%22296.3%2A%22%2C%22300.4%22%2C%22311.%2A%22%5D%7D%2C%22icd10%22%3A+%7B%22code%22%3A+%5B%22F32.%2A%22%2C%22F33.%2A%22%5D%7D%7D%2C%22status%22%3A+%7B%22value%22%3A+%7B%22code%22%3A+%2255561003%22%2C+%22code_system%22%3A+%222.16.840.1.113883.6.96%22%7D%7D%7D

PUT /cdr/patients/4824/ccda?
