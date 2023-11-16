FROM python:3

ENV PYTHONUNBUFFERED 1

RUN mkdir /dash-app
WORKDIR /dash-app

COPY app/requirements.txt /dash-app//
RUN python -m venv venv
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /dash-app//

ENV FLASK_APP app/dash-app.py

CMD [ "gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:80", "app:server"]