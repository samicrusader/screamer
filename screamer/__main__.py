# import argparse
from . import logger
from .hdhomerun import discover
import logging
import socket
import os
import threading
from flask import Flask

log = logger.setup_custom_logger('root')


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
    log = logging.getLogger('broadcast')
    log.setLevel(logging.DEBUG)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def run(self, ip: str, port: int):
        self.log.log(logging.INFO, f'Listening on {ip if ip else "*"}:{port}')
        self.udp_socket.bind((ip, port))
        while True:
            message, address = self.udp_socket.recvfrom(1460)

            self.log.log(logging.INFO, f'Message from Client: {message}')
            self.log.log(logging.INFO, f'Client IP Address: {address}')
            
            x = discover.parse(message)
            print(x)
            print(discover.discover_request())
            if x[0] == 'discover_request':
                self.udp_socket.sendto(discover.discover_request(), address)
            else:
                print('no workey')

            # Sending a reply to client
            # udp_server_socket.sendto(bytesToSend, address)


class CreateLLMNRServer:
    log = logging.getLogger('llmnr')
    log.setLevel(logging.DEBUG)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def run(self, ip: str, port: int):
        self.log.log(logging.INFO, f'Listening on {ip if ip else "*"}:{port}')
        self.udp_socket.bind((ip, port))
        while True:
            message, address = self.udp_socket.recvfrom(1460)

            self.log.log(logging.INFO, f'Message from Client: {message}')
            self.log.log(logging.INFO, f'Client IP Address: {address}')

class CreateTCPControlServer:
    log = logging.getLogger('tcpcontrol')
    log.setLevel(logging.DEBUG)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    def run(self, ip: str, port: int):
        self.log.log(logging.INFO, f'Listening on {ip if ip else "*"}:{port}')
        self.tcp_socket.bind((ip, port))
        while True:
            message, address = self.tcp_socket.recvfrom(1460)

            self.log.log(logging.INFO, f'Message from Client: {message}')
            self.log.log(logging.INFO, f'Client IP Address: {address}')

if __name__ == '__main__':
    webgui_thread = threading.Thread(
        target=lambda: create_http_mgmt_server().run(host='127.0.0.1', port=8080, use_reloader=False, threaded=True),
        daemon=True)
    webgui_thread.start()
    http_stream_thread = threading.Thread(
        target=lambda: create_http_stream_server().run(host='127.0.0.1', port=5004, use_reloader=False, threaded=True),
        daemon=True)
    http_stream_thread.start()
    broadcast_thread = threading.Thread(
        target=lambda: CreateUDPBroadcastServer().run(ip='', port=65001),
        daemon=True)
    broadcast_thread.start()
    control_thread = threading.Thread(
        target=lambda: CreateTCPControlServer().run(ip='', port=65001),
        daemon=True)
    control_thread.start()
    llmnr_thread = threading.Thread(
        target=lambda: CreateLLMNRServer().run(ip='224.0.0.252', port=5355),
        daemon=True)
    llmnr_thread.start()
    for thread in [webgui_thread, http_stream_thread, broadcast_thread]:
        thread.join()
