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
