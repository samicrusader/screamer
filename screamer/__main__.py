import argparse
from . import logger
from .hdhomerun import control, discover
from .hdhomerun.packets import parse
from _thread import start_new_thread
import logging
import socket
import os
import threading
import toml
from flask import Flask

log = logger.setup_custom_logger('root')
config = dict()


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

            data = func(payload=x[1])
            self.udp_socket.sendto(data, address)
            self.log.log(logging.DEBUG, f'Sent back {data}')

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
                        func = control.getset
                    case _:
                        self.log.log(logging.INFO, f'Client {address} sent invalid request.')
                        conn.close()
                data = func(payload=x[1])
                conn.send(data)
                self.log.log(logging.DEBUG, f'Sent back {data}')
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
    # ArgumentParser setup
    parser = argparse.ArgumentParser(
        description='''HDHomerun Emulator.
    Model information is available at https://www.silicondust.com/support/linux/.
    Firmware information is available at https://www.silicondust.com/support/downloads/firmware-changelog/.
    Device ID format is available in docs.txt (more reverse engineering needed, just use 107C21C8.)

    Command line arguments take priority over config settings.''',
        prog='python3 -m screamer'
    )
    parser.add_argument('--config', '-c', default=None,
                        help='Specify configuration file.')
    parser.add_argument('--hwmodel', '-w', default=None,
                        help='Change hardware model.')
    parser.add_argument('--model', '-m', default=None,
                        help='Change device type.')
    parser.add_argument('--firmware', '-f', default=None,
                        help='Change emulated firmware version.')
    parser.add_argument('--device-id', '-i', default=None,
                        help='Change device ID.')
    parser.add_argument('--bind', '-b', default=None,
                        help='Change IP address of control servers. (Broadcast/LLMNR excluded)')
    parser.add_argument('--webgui-port', '--wp', default=None,
                        help='Specify WebGUI port.')
    parser.add_argument('--enable-webgui', default=None,
                        help='Enable/Disable Web GUI.')
    parser.add_argument('--enable-httpstream', default=None,
                        help='Enable/Disable HTTPStream server.')
    parser.add_argument('--enable-broadcast', default=None,
                        help='Enable/Disable UDP Broadcast client.')
    parser.add_argument('--enable-control', default=None,
                        help='Enable/Disable TCP Control server.')

    args = parser.parse_args()

    # Load .toml settings
    configfile = 'config.toml'
    if args.config:
        configfile = args.config

    tomlconfig = dict()
    try:
        tomlconfig = toml.load(configfile)
    except FileNotFoundError:
        log.log(logging.ERROR, f'Config file {configfile} was not found, using command line parameters.')
    except toml.decoder.TomlDecodeError as e:
        log.log(logging.ERROR, f'Config file {configfile} has invalid syntax: {str(e)}. Bailing out.')
        exit(1)

    # Parse config variables
    try: toml_entry = tomlconfig['server']
    except KeyError: toml_entry = dict()

    for i in [
        ('server', ['bind', 'webgui_port', 'enable_webgui', 'enable_httpstream', 'enable_broadcast', 'enable_control']),
        ('device', ['hwmodel', 'model', 'firmware', 'device_id'])
    ]:
        cfg_entry = dict()
        for x in i[1]:
            if getattr(args, x):
                cfg_entry[x] = getattr(args, x)
            else:
                try: tomlconfig[i[0]][x]
                except KeyError:
                    log.log(logging.ERROR, f'Config variable {i[0]}[{x}] is not set. Bailing out.')
                    exit(1)
                else: cfg_entry[x] = tomlconfig[i[0]][x]
        config[i[0]] = cfg_entry

    print(config)

    # Setup threads
    webgui_thread = threading.Thread(
        target=lambda: create_http_mgmt_server().run(host='127.0.0.1', port=8080, use_reloader=False, threaded=True),
        daemon=True)
    http_stream_thread = threading.Thread(
        target=lambda: create_http_stream_server().run(host='127.0.0.1', port=5004, use_reloader=False, threaded=True),
        daemon=True)
    broadcast_thread = threading.Thread(
        target=lambda: CreateUDPBroadcastServer().run(ip='', port=65001),
        daemon=True)
    control_thread = threading.Thread(
        target=lambda: CreateTCPControlServer().run(ip='', port=65001),
        daemon=True)
    llmnr_thread = threading.Thread(
        target=lambda: CreateLLMNRServer().run(ip='', port=5355),
        daemon=True)

    # Start server threads
    webgui_thread.start()
    http_stream_thread.start()
    broadcast_thread.start()
    control_thread.start()

    #llmnr_thread.start() # not needed for now
    for thread in [webgui_thread, http_stream_thread, broadcast_thread, control_thread]:#, llmnr_thread]:
        thread.join()
