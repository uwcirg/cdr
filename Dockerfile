FROM python:3.7
ADD . /cdr
WORKDIR /cdr
RUN apt-get update && apt-get install --assume-yes wait-for-it && apt-get clean
RUN pip install --upgrade pip
RUN pip install --requirement requirements.txt

ENV \
    BASH_ENV=/etc/profile.d/remap_envvars.sh \
    FLASK_APP=/cdr/manage.py \
    GUNICORN_CMD_ARGS='--timeout 90' \
    RUN_USER=www-data \
    PORT=5000

USER "${RUN_USER}"

EXPOSE "${PORT}"

CMD \
    wait-for-it \
        --host="${PGHOST}" \
        --port="${PGPORT:-5432}" \
        --strict \
    -- \
        flask initdb && \
        gunicorn \
            --bind "0.0.0.0:${PORT}" \
        wsgi:application
