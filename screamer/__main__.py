import argparse
from . import logger
from .hdhomerun import control as hdhrcontrol, discover as hdhrdiscover
from .hdhomerun.packets import parse as hdhrparse
from _thread import start_new_thread
import logging
import socket
import os
import threading
import toml
from flask import Flask

log = logger.setup_custom_logger('root')
config = dict()


def hdhr_create_http_mgmt_server():
    flask = Flask('screamer_hdhr_mgmt')
    flask.app_config = config

    if not os.path.exists(flask.instance_path):
        os.mkdir(flask.instance_path)

    from .hdhomerun import http_api
    flask.register_blueprint(http_api.bp)
    return flask


def hdhr_create_http_stream_server():
    flask = Flask('screamer_hdhr_http_stream')
    flask.app_config = config

    if not os.path.exists(flask.instance_path):
        os.mkdir(flask.instance_path)

    # from . import bla
    # app.register_blueprint(bla.bp)
    return flask


class HDHRCreateUDPBroadcastServer:
    log = logging.getLogger('hdhr_broadcast')
    log.setLevel(logging.INFO)
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

            x = hdhrparse(message)
            self.log.log(logging.DEBUG, f'Packet type: {x[0]}')
            self.log.log(logging.DEBUG, f'Packet payload: {x[1]}')
            match x[0]:
                case 'discover_request':
                    func = hdhrdiscover.discover_request
                case _:
                    self.log.log(logging.INFO, f'Client {address} sent invalid request.')
                    break

            data = func(payload=x[1], config=config)
            self.udp_socket.sendto(data, address)
            self.log.log(logging.DEBUG, f'Sent back {data}')

            # Sending a reply to client
            # udp_server_socket.sendto(bytesToSend, address)


class HDHRCreateLLMNRServer:
    log = logging.getLogger('hdhr_llmnr')
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


class HDHRCreateTCPControlServer:
    log = logging.getLogger('hdhr_tcpcontrol')
    log.setLevel(logging.INFO)
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
                x = hdhrparse(message)
                self.log.log(logging.DEBUG, f'Packet type: {x[0]}')
                self.log.log(logging.DEBUG, f'Packet payload: {x[1]}')
                match x[0]:
                    case 'getset_request':
                        func = hdhrcontrol.getset
                    case _:
                        self.log.log(logging.INFO, f'Client {address} sent invalid request.')
                        conn.close()
                data = func(payload=x[1], config=config, address=address)
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


class DVBLCreateTCPControlServer:
    log = logging.getLogger('dvbl_tcpcontrol')
    log.setLevel(logging.DEBUG)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    def handle(self, conn, address):
        while True:
            try:
                message = conn.recv(12)
                if not message:
                    self.log.log(logging.INFO, f'Client {address} dropped.')
                    break
                self.log.log(logging.DEBUG, f'Message from Client: {message}')
                if message == b'e\x00\x00\x00\x00\x00\x00\x00\x1f\x00\x00\x00':
                    self.log.log(logging.DEBUG, f'Client {address} sent header...')
                    conn.send(b'\x00')
                    message2 = conn.recv(31)
                    self.log.log(logging.DEBUG, f'Message from Client: {message2}')
                    if message2 == b'22 serialization::archive 8 0 0':
                        # ??
                        print('sending header of sorts...')
                        conn.send(b'\x65\x00\x00\x00\x00\x00\x00\x00\xa5\x02\x05\x00')
                        import time
                        time.sleep(1)
                        print('sending data...')
                        data = b'<?xml version="1.0"?>\n<channel_map><logical_channel><childlock>0</childlock><type>TV</type><number>1000</number><subnumber>0</subnumber><name>5 Star Max (East)</name><logo_id></logo_id><frequency>10640000</frequency><physical_channel><number>-1</number><subnumber>0</subnumber><type>TV</type><id>http://example.com:&lt;5 Star Max (East)&gt;</id><control_id>16255cfa-5e82-466d-98ab-124141a5870c</control_id><instance_id>54483477-533c-437f-937b-43dc3d1a8dc0</instance_id><instance_name>IPTV-1</instance_name><name>5 Star Max (East)</name><altid>http://example.com</altid><fta>1</fta><sync>0</sync></physical_channel></logical_channel><logical_channel><childlock>0</childlock><type>TV</type><number>1104</number><subnumber>0</subnumber><name>Heroes &amp; Icons Network</name><logo_id></logo_id><frequency>10170000</frequency><physical_channel><number>-1</number><subnumber>0</subnumber><type>TV</type><id>http://example.com:&lt;Heroes &amp; Icons Network&gt;</id><control_id>16255cfa-5e82-466d-98ab-124141a5870c</control_id><instance_id>54483477-533c-437f-937b-43dc3d1a8dc0</instance_id><instance_name>IPTV-1</instance_name><name>Heroes &amp; Icons Network</name><altid>http://example.com</altid><fta>1</fta><sync>0</sync></physical_channel></logical_channel></channel_map>\x0a'
                        conn.send(f'22 serialization::archive 8 0 0 0 0 {len(data)} '.encode() + data)
                        print('closing connection...')
                        conn.close()
                        break
                        print('nothing should go beyond this point')
                else:
                    self.log.log(logging.DEBUG, f'Don\'t understand packet from client {address}. Dropping...')
                    conn.close()
                    return
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
    parser.add_argument('--data', '-d', default=None,
                        help='Specify channel listing file.')
    parser.add_argument('--hwmodel', '-w', default=None,
                        help='Change hardware model.')
    parser.add_argument('--model', '-m', default=None,
                        help='Change device type.')
    parser.add_argument('--firmware', '-f', default=None,
                        help='Change emulated firmware version.')
    parser.add_argument('--device-id', '-i', default=None,
                        help='Change device ID.')
    parser.add_argument('--bind', '-b', default=None,
                        help='Change IP address of control servers. Leave blank for all interfaces.'
                             '(Broadcast/LLMNR excluded)')
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

    datafile = 'channels.toml'
    if args.data:
        datafile = args.data

    tomlconfig = dict()
    channeldata = dict()
    try:
        tomlconfig = toml.load(configfile)
    except FileNotFoundError:
        log.log(logging.ERROR, f'Config file {configfile} was not found, using command line parameters.')
    except toml.decoder.TomlDecodeError as e:
        log.log(logging.ERROR, f'Config file {configfile} has invalid syntax: {str(e)}. Bailing out.')
        exit(1)

    try:
        channeldata = toml.load(datafile)
    except FileNotFoundError:
        log.log(logging.ERROR, f'Config file {datafile} was not found, using command line parameters.')
    except toml.decoder.TomlDecodeError as e:
        log.log(logging.ERROR, f'Config file {datafile} has invalid syntax: {str(e)}. Bailing out.')
        exit(1)

    # Parse config variables
    try:
        toml_entry = tomlconfig['server']
    except KeyError:
        toml_entry = dict()

    for i in [
        ('server', ['bind', 'hdhr_webgui_port', 'enable_hdhr_webgui', 'enable_hdhr_httpstream', 'enable_hdhr_broadcast','enable_hdhr_control']),
        ('hdhomerun', ['hwmodel', 'model', 'firmware', 'device_id'])
    ]:
        cfg_entry = dict()
        for x in i[1]:
            if not getattr(args, x) == None:
                cfg_entry[x] = getattr(args, x)
            else:
                try:
                    tomlconfig[i[0]][x]
                except KeyError:
                    log.log(logging.ERROR, f'Config variable {i[0]}[{x}] is not set. Bailing out.')
                    exit(1)
                else:
                    cfg_entry[x] = tomlconfig[i[0]][x]
        config[i[0]] = cfg_entry

    config['channels'] = channeldata
    print(config)

    # Configure and start threads
    threads = list()
    if config['server']['enable_hdhr_webgui'] == True:
        hdhr_webgui_thread = threading.Thread(
            target=lambda: hdhr_create_http_mgmt_server().run(host=config['server']['bind'],
                                                              port=config['server']['hdhr_webgui_port'],
                                                              use_reloader=False, threaded=True), daemon=True)
        hdhr_webgui_thread.start()
        threads.append(hdhr_webgui_thread)
    if config['server']['enable_hdhr_httpstream'] == True:
        hdhr_http_stream_thread = threading.Thread(
            target=lambda: hdhr_create_http_stream_server().run(host=config['server']['bind'], port=5004,
                                                                use_reloader=False, threaded=True), daemon=True)
        hdhr_http_stream_thread.start()
        threads.append(hdhr_http_stream_thread)
    if config['server']['enable_hdhr_broadcast'] == True:
        hdhr_broadcast_thread = threading.Thread(
            target=lambda: HDHRCreateUDPBroadcastServer().run(ip='', port=65001), daemon=True)
        hdhr_broadcast_thread.start()
        threads.append(hdhr_broadcast_thread)
    if config['server']['enable_hdhr_control'] == True:
        hdhr_control_thread = threading.Thread(
            target=lambda: HDHRCreateTCPControlServer().run(ip=config['server']['bind'], port=65001), daemon=True)
        hdhr_control_thread.start()
        threads.append(hdhr_control_thread)
    if config['server']['enable_dvbl_control'] == True:
        dvbl_control_thread = threading.Thread(
            target=lambda: DVBLCreateTCPControlServer().run(ip=config['server']['bind'], port=39877), daemon=True)
        dvbl_control_thread.start()
        threads.append(dvbl_control_thread)
    # hdhr_llmnr_thread = threading.Thread(
    #    target=lambda: HDHRCreateLLMNRServer(config=config).run(ip='', port=5355),
    #    daemon=True)
    # hdhr_llmnr_thread.start() # not needed for now
    # threads.append(hdhr_llmnr_thread)

    for thread in threads:
        thread.join()
