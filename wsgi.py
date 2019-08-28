""" WSGI Entry Point

"""
from cdr import create_app

# WSGI object is named "application" by default
# https://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGICallableObject.html
application = create_app()
