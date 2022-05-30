# import argparse
import logging
import socket
import os
import threading
from flask import Flask


def create_http_mgmt_server():
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


class CreateUDPBroadcastServer:
    log = logging.getLogger('udp_broadcast')
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def run(self, ip: str, port: int):
        self.udp_socket.bind((ip, port))
        self.log.log(logging.INFO, f'Listening on {ip if ip else "*"}:{port}')
        while True:
            recv = self.udp_socket.recvfrom(1024)

            message = recv[0]
            address = recv[1]
            self.log.log(logging.DEBUG, f'Message from Client: {message}')
            self.log.log(logging.DEBUG, f'Client IP Address: {address}')

            # Sending a reply to client
            # udp_server_socket.sendto(bytesToSend, address)


if __name__ == '__main__':
    management_thread = threading.Thread(
        target=lambda: create_http_mgmt_server().run(host='127.0.0.1', port=8080, use_reloader=False, threaded=True),
        daemon=True)
    management_thread.start()
    http_stream_thread = threading.Thread(
        target=lambda: create_http_stream_server().run(host='127.0.0.1', port=5004, use_reloader=False, threaded=True),
        daemon=True)
    http_stream_thread.start()
    broadcast_thread = threading.Thread(
        target=lambda: CreateUDPBroadcastServer().run(ip='', port=65001),
        daemon=True)
    broadcast_thread.start()
    for thread in [management_thread, http_stream_thread, broadcast_thread]:
        thread.join()
