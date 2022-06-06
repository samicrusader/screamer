# import argparse
from . import logger
from .hdhomerun import control, discover
from .hdhomerun.packets import parse
from _thread import start_new_thread
import logging
import socket
import os
import time
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
            self.log.log(logging.INFO, f'Client {address} connected.')
            self.log.log(logging.DEBUG, f'Message from Client: {message}')

            x = parse(message)
            self.log.log(logging.DEBUG, f'Packet type: {x[0]}')
            self.log.log(logging.DEBUG, f'Packet payload: {x[1]}')
            match x[0]:
                case 'discover_request':
                    func = discover.discover_request
                case _:
                    self.log.log(logging.INFO, f'Client {address} sent invalid request.')
                    break

            self.udp_socket.sendto(func(payload=x[1]), address)
            break

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
            self.log.log(logging.INFO, f'Client {address} connected.')
            self.log.log(logging.DEBUG, f'Message from Client: {message}')


class CreateTCPControlServer:
    log = logging.getLogger('tcpcontrol')
    log.setLevel(logging.DEBUG)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    def handle(self, conn, address):
        while True:
            try:
                message = conn.recv(1460)
                if not message:
                    self.log.log(logging.INFO, f'Client {address} dropped.')
                    break

                self.log.log(logging.DEBUG, f'Message from Client: {message}')
                x = parse(message)
                self.log.log(logging.DEBUG, f'Packet type: {x[0]}')
                self.log.log(logging.DEBUG, f'Packet payload: {x[1]}')
                match x[0]:
                    case 'getset_request':
                        func = control.get_request
                    case _:
                        self.log.log(logging.INFO, f'Client {address} sent invalid request.')
                        conn.close()

                conn.send(func(payload=x[1]))
                conn.close()
            except OSError:
                self.log.log(logging.INFO, f'Client {address} dropped.')
                break

    def run(self, ip: str, port: int):
        self.tcp_socket.bind((ip, port))
        self.log.log(logging.INFO, f'Listening on {ip if ip else "*"}:{port}')
        self.tcp_socket.listen()
        while True:
            connection, address = self.tcp_socket.accept()
            self.log.log(logging.INFO, f'Client {address} connected.')
            start_new_thread(self.handle, (connection, address))


if __name__ == '__main__':
    webgui_thread = threading.Thread(
        target=lambda: create_http_mgmt_server().run(host='127.0.0.1', port=8080, use_reloader=False, threaded=True),
        daemon=True)
    webgui_thread.start()
    time.sleep(1)
    http_stream_thread = threading.Thread(
        target=lambda: create_http_stream_server().run(host='127.0.0.1', port=5004, use_reloader=False, threaded=True),
        daemon=True)
    http_stream_thread.start()
    time.sleep(1)
    broadcast_thread = threading.Thread(
        target=lambda: CreateUDPBroadcastServer().run(ip='', port=65001),
        daemon=True)
    broadcast_thread.start()
    time.sleep(1)
    control_thread = threading.Thread(
        target=lambda: CreateTCPControlServer().run(ip='', port=65001),
        daemon=True)
    control_thread.start()
    time.sleep(1)
    llmnr_thread = threading.Thread(
        target=lambda: CreateLLMNRServer().run(ip='', port=5355),
        daemon=True)
    #llmnr_thread.start() # not needed for now
    for thread in [webgui_thread, http_stream_thread, broadcast_thread, control_thread]:#, llmnr_thread]:
        thread.join()
