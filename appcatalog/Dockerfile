FROM baseimage
COPY . /opt/appcatalog
WORKDIR /opt/appcatalog
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/opt/appcatalog/entrypoint.sh"]

