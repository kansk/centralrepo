import os
import sys
import json
import logging
import threading
import flask
import httplib
import requests
from flask import Flask, request, Response, jsonify

MEC_MS_CATALOG_IP = "0.0.0.0"
MEC_MS_CATALOG_PORT = 0xecc9

ms_catalog = Flask(__name__)


class MicroserviceCatalogDB:

    def __init__(self, file):
        self.lock = threading.Lock()
        self.file = file
        self.mtime = 0
        self.load_db()

    def load_db(self):
        mtime = os.stat(self.file).st_mtime
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.file) as app_file:
                logging.info(
                    "Loading microservice database %s" % self.file)
                self.db = json.load(app_file)
                logging.debug(json.dumps(self.db))
                
    def load_ms(self):
        self.lock.acquire()
        self.load_db()
        self.lock.release()
                
    def ms(self):
        self.load_ms()
        return self.db['microservices']

    def add_in_db(self, metadata):
       # app_header = {}
       # with open("microservice-header.db") as app_file:
       #     logging.info(
       #         "Loading microservice header from microservice-header.db")
       #     app_header = json.load(app_file)
       # app_header['microServiceName'] = msname
       # app_header['metadata'] = metadata

        self.db['microservices'].append(metadata)
        with open(self.file, 'w') as app_file:
            json.dump(self.db, app_file)
            
    def del_db(self, msname):
        self.db["microservices"][:] = [m for m in self.db["microservices"] if m.get('microServiceName') != msname]
        
        with open(self.file, 'w') as app_file:
            json.dump(self.db, app_file)


    def find_microservice(self, ms):
        app_data = None
        self.lock.acquire()
        self.load_db()
        for microservice in self.db["microservices"]:
            if microservice['microServiceName'] == ms:
                app_data = microservice
        self.lock.release()
        return app_data


@ms_catalog.route("/microservicecatalog/microservice/<msname>", methods=["GET"])
def details(msname):
    if (mc_db.find_microservice(msname) == None):
        resp = Response(
            response="MS NOT FOUND", status=httplib.NOT_FOUND)
        return resp
    else:
        return json.dumps(mc_db.find_microservice(msname))

@ms_catalog.route("/microservicecatalog/microservices", methods=["GET"])
def getAll_ms():
    return json.dumps(mc_db.ms())

@ms_catalog.route("/microservicecatalog/microservice", methods=["POST"])
def onboardms():
    metadata = request.json
    if metadata == None:
        return Response(status=httplib.BAD_REQUEST)
    if (mc_db.find_microservice(metadata['microServiceName']) != None):
        resp = Response(
            response="MS ONBOARD FAILED", status=httplib.CONFLICT)
    else:
        try:
            mc_db.add_in_db(metadata)
            resp = Response(
                response="MS ONBOARD SUCCESS", status=httplib.OK)
        except:
            resp = Response(
                response="UNABLE TO ONBOARD MS", status=httplib.INTERNAL_SERVER_ERROR)
    return resp

@ms_catalog.route("/microservicecatalog/microservice/<msname>", methods=["DELETE"])
def del_ms(msname):
    if (mc_db.find_microservice(msname) == None):
        resp = Response(
            response="MS NOT FOUND", status=httplib.NOT_FOUND)
    else:
        try:
            mc_db.del_db(msname)
            resp = Response(
                response="MS DELETION SUCCESS", status=httplib.OK)
        except:
            resp = Response(
                response="UNABLE TO DELETE MS", status=httplib.INTERNAL_SERVER_ERROR)
    return resp
    

if len(sys.argv) < 2:
    print("Usage: %s <ms_catalog_db>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(filename='/opt/logs/microservicecatalog.log',level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

mc_db = MicroserviceCatalogDB(sys.argv[1])

# Start the Flask web server (HTTP)
if __name__ == '__main__':
    ms_catalog.run(
        host="0.0.0.0", port=MEC_MS_CATALOG_PORT, debug=True, threaded=True)
