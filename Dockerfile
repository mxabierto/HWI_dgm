FROM python:2-alpine
MAINTAINER Francisco Vaquero <akura11.tt@gmail.com>

RUN apk add git bash --update-cache && rm -rf /var/cache/apk/*

RUN mkdir /project && touch /var/log/buda.log && touch /var/log/test.log && touch /var/log/budacron.log
COPY . project/
RUN pip install -r /project/requirements.txt

EXPOSE 8001

CMD ["python", "project/Buda/manage.py", "runserver", "0.0.0.0:8001"]
