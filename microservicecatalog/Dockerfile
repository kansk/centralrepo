FROM tiangolo/uwsgi-nginx-flask:flask
COPY . /opt/mscatalog
WORKDIR /opt/mscatalog
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/opt/mscatalog/entrypoint.sh"]

