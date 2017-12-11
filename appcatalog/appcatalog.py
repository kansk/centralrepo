import os
import sys
import json
import logging
import threading
import flask
import httplib
import requests
from flask import Flask, request, Response, jsonify

MEC_APP_CATALOG_IP = "0.0.0.0"
MEC_APP_CATALOG_PORT = 0xecb9

app_catalog = Flask(__name__)


class ApplicationCatalogDB:

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
                    "Loading application policy database %s" % self.file)
                self.db = json.load(app_file)
                logging.debug(json.dumps(self.db))
                
    def load_apps(self):
        self.lock.acquire()
        self.load_db()
        self.lock.release()
                
    def applications(self):
        self.load_apps()
        return self.db['applications']

    def add_in_db(self, metadata):
       # app_header = {}
       # with open("app-header.db") as app_file:
       #     logging.info(
       #         "Loading application header from app-header.db")
       #     app_header = json.load(app_file)
       # app_header['name'] = appname
       # app_header['metadata'] = metadata

        self.db['applications'].append(metadata)
        with open(self.file, 'w') as app_file:
            json.dump(self.db, app_file)
            
    def del_db(self, appname):
        self.db["applications"][:] = [a for a in self.db["applications"] if a.get('applicationName') != appname]
        
        with open(self.file, 'w') as app_file:
            json.dump(self.db, app_file)


    def find_app(self, app):
        app_data = None
        self.lock.acquire()
        self.load_db()
        for application in self.db["applications"]:
            if application['applicationName'] == app:
                app_data = application
        self.lock.release()
        return app_data


@app_catalog.route("/applicationcatalog/application/<appname>", methods=["GET"])
def details(appname):
    if (ac_db.find_app(appname) == None):
        resp = Response(
            response="APP NOT FOUND", status=httplib.NOT_FOUND)
        return resp    
    else:
        return json.dumps(ac_db.find_app(appname))
    
@app_catalog.route("/applicationcatalog/applications", methods=["GET"])
def apps():
    return json.dumps(ac_db.applications())

@app_catalog.route("/applicationcatalog/application", methods=["POST"])
def onboardapp():
    metadata = request.json
    if metadata == None:
        return Response(status=httplib.BAD_REQUEST)
    if (ac_db.find_app(metadata['applicationName']) != None):
        resp = Response(
            response="APP ONBOARD FAILED", status=httplib.CONFLICT)
    else:
        try:
            ac_db.add_in_db(metadata)
            resp = Response(
                response="APP ONBOARD SUCCESS", status=httplib.OK)
        except:
            resp = Response(
                response="UNABLE TO ONBOARD APP", status=httplib.INTERNAL_SERVER_ERROR)
    return resp

@app_catalog.route("/applicationcatalog/application/<appname>", methods=["DELETE"])
def del_app(appname):
    if (ac_db.find_app(appname) == None):
        resp = Response(
            response="APP NOT FOUND", status=httplib.NOT_FOUND)
    else:
        try:
            ac_db.del_db(appname)
            resp = Response(
                response="APP DELETION SUCCESS", status=httplib.OK)
        except:
            resp = Response(
                response="UNABLE TO DELETE APP", status=httplib.INTERNAL_SERVER_ERROR)
    return resp

if len(sys.argv) < 2:
    print("Usage: %s <app_catalog_db>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(filename='/opt/logs/appcatalog.log',level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

ac_db = ApplicationCatalogDB(sys.argv[1])

# Start the Flask web server (HTTP)
if __name__ == '__main__':
    app_catalog.run(
        host="0.0.0.0", port=MEC_APP_CATALOG_PORT, debug=True, threaded=True)
