FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
ENV STATIC_URL /static
ENV STATIC_PATH /app/app/static
COPY ./requirements.txt /app/requirements.txt
RUN apk --update add bash nano python3 python3-dev gcc \
    gfortran musl-dev && pip install -r requirements.txt
COPY ./app /app/
EXPOSE 80
