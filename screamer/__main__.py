import argparse
import os
import threading
from flask import Flask


def create_mgmt_server():
    flask = Flask('screamer_mgmt')

    if not os.path.exists(flask.instance_path):
        os.mkdir(flask.instance_path)

    # from . import bla
    # app.register_blueprint(bla.bp)
    return flask


def create_http_stream_server():
    flask = Flask('screamer_http_stream')

    if not os.path.exists(flask.instance_path):
        os.mkdir(flask.instance_path)

    # from . import bla
    # app.register_blueprint(bla.bp)
    return flask


if __name__ == '__main__':
    mgmt = create_mgmt_server()
    stream = create_http_stream_server()
    management_thread = threading.Thread(
        target=lambda: mgmt.run(host='127.0.0.1', port=8080, use_reloader=False, threaded=True), daemon=True)
    management_thread.start()
    http_stream_thread = threading.Thread(
        target=lambda: stream.run(host='127.0.0.1', port=8081, use_reloader=False, threaded=True), daemon=True)
    http_stream_thread.start()
    for thread in [management_thread, http_stream_thread]:
        thread.join()
