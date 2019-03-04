FROM python:3.6
ADD . /cdr
WORKDIR /cdr
RUN pip install -r requirements.txt
