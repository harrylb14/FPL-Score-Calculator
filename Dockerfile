FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
RUN apk --update add bash nano
ENV STATIC_URL /static
ENV STATIC_PATH /Documents/fpl_scores/FPL-Score-Calculator/app/static
COPY ./requirements.txt /Documents/fpl_scores/FPL-Score-Calculator/requirements.txt
RUN pip install -r /Documents/fpl_scores/FPL-Score-Calculator/requirements.txt