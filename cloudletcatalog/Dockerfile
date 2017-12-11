FROM baseimage
COPY . /opt/cloudletcatalog
WORKDIR /opt/cloudletcatalog
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/opt/cloudletcatalog/entrypoint.sh"]
