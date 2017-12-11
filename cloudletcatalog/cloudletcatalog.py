import os
import sys
import json
import logging
import threading
import flask
import httplib
import requests
from flask import Flask, request, Response, jsonify

MEC_CLOUDLET_CATALOG_IP = "0.0.0.0"
MEC_CLOUDLET_CATALOG_PORT = 0xecba

cloudlet_catalog = Flask(__name__)


class CloudletCatalogDB:

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

    def load_cloudlets(self):
        self.lock.acquire()
        self.load_db()
        self.lock.release()

    def cloudlets(self):
        self.load_cloudlets()
        return self.db['cloudlets']

    def update_status(self, cloudlet_id, status):
        for cloudlet in self.db["cloudlets"]:
            if cloudlet['cloudletName'] == cloudlet_id:
                cloudlet['onBoardStatus'] = status

        with open(self.file, 'w') as app_file:
            json.dump(self.db, app_file)
            
    def update_cloudlet(self, cl, metadata):
        self.db["cloudlets"][:] = [c for c in self.db["cloudlets"] if c.get('cloudletName') != cl]
        self.db['cloudlets'].append(metadata)
        with open(self.file, 'w') as app_file:
            json.dump(self.db, app_file)
            
    def add_in_db(self, cl):
        cl_header = {}
        with open("cloudlet-header.db") as cl_file:
            logging.info(
                "Loading cloudlet header from cloudlet-header.db")
            cl_header = json.load(cl_file)
        cl_header['cloudletName'] = cl

        self.db['cloudlets'].append(cl_header)
        with open(self.file, 'w') as cl_db_file:
            json.dump(self.db, cl_db_file)
            
    def find_cloudlet(self, cl):
        cl_data = None
        self.lock.acquire()
        self.load_db()
        for cloudlet in self.db["cloudlets"]:
            if cloudlet['cloudletName'] == cl:
                cl_data = cloudlet
        self.lock.release()
        return cl_data


@cloudlet_catalog.route("/cloudletcatalog/cloudlets", methods=["GET"])
def cloudlets():
    return json.dumps(cc_db.cloudlets())


@cloudlet_catalog.route("/cloudletcatalog/cloudlet/<cloudlet>", methods=["POST"])
def onboardcloudlet(cloudlet):
    
    if (cc_db.find_cloudlet(cloudlet) != None):
        resp = Response(
            response="CLOUDLET ONBOARD FAILED", status=httplib.CONFLICT)
    else:
        try:
            cc_db.add_in_db(cloudlet)
            resp = Response(
                response="CLOUDLET ONBOARD SUCCESS", status=httplib.OK)
        except:
            resp = Response(
                response="UNABLE TO ONBOARD CLOUDLET", status=httplib.INTERNAL_SERVER_ERROR)
    return resp
    
#@cloudlet_catalog.route("/cloudletcatalog/cloudlet/<cloudlet>", methods=["PUT"])
#def update_cl(cloudlet):
#    metadata = request.json
#    if metadata == None:
#        return Response(status=httplib.BAD_REQUEST)
#    if (cc_db.find_cloudlet(cloudlet) == None):
#        resp = Response(
#            response="CLOUDLET UPDATE FAILED", status=httplib.NOT_FOUND)
#    else:
#        try:
#            cc_db.update_cloudlet(str(cloudlet), metadata)
#            resp = Response(
#                response="CLOUDLET UPDATION SUCCESS", status=httplib.OK)
#        except:
#            resp = Response(
#                response="CLOUDLET UPDATION FAILED", status=httplib.INTERNAL_SERVER_ERROR)
#    return resp

@cloudlet_catalog.route("/cloudletcatalog/cloudlet/<cloudlet_id>", methods=["GET"])
def details(cloudlet_id):
    for cloudlet in cc_db.cloudlets():
        if cloudlet['cloudletName'] == cloudlet_id:
            return json.dumps(cloudlet)
    return Response(response="CLOUDLET NOT FOUND", status=httplib.NOT_FOUND)


@cloudlet_catalog.route("/cloudletcatalog/cloudlet/<cloudlet>", methods=["PUT"])
def update(cloudlet):
    try:
        status = request.args.get('status')
        cc_db.update_status(cloudlet, status)
        resp = Response(
            response="CLOUDLET UPDATION SUCCESS", status=httplib.OK)
    except:
        resp = Response(
            response="CLOUDLET UPDATION FAILED", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@cloudlet_catalog.route("/api/v1.0/centralrepo/cloudletcatalog/capacity", methods=['GET'])
def capacity():

    try:
        cloudlet_ids = request.args.get('cloudlet_ids')
        cloudlet_ids = eval(cloudlet_ids)
        data = {}
        for cloudlet_id in cloudlet_ids:
            data[cloudlet_id] = cc_db.cloudlets()['cloudlets'][
                cloudlet_id]['resource']

        resp = json.dumps(data)
    except:
        resp = Response(
            response="UNABLE TO FETCH CAPACITY OF CLOUDLETS", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@cloudlet_catalog.route("/api/v1.0/centralrepo/cloudletcatalog/usage", methods=['GET'])
def usage():

    try:
        cloudlet_ids = request.args.get('cloudlet_ids')
        cloudlet_ids = eval(cloudlet_ids)
        data = {}
        for cloudlet_id in cloudlet_ids:
            data[cloudlet_id] = cc_db.cloudlets()['cloudlets'][
                cloudlet_id]['usage']
        resp = json.dumps(data)

    except:
        resp = Response(
            response="UNABLE TO FETCH USAGE OF CLOUDLETS", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


if len(sys.argv) < 2:
    print("Usage: %s <cloudlet_catalog_db>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

cc_db = CloudletCatalogDB(sys.argv[1])

# Start the Flask web server (HTTP)
if __name__ == '__main__':
    cloudlet_catalog.run(
        host="0.0.0.0", port=MEC_CLOUDLET_CATALOG_PORT, debug=True, threaded=True)
