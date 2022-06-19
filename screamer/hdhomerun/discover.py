from .packets import create, parse
import logging
import socket


class UDPBroadcastServer:
    """
    Broadcast server for HDHomeRun emulation.

    The hdhomerun_config tool, Windows utility, and the official apps use this to query for devices.
    """
    # configure logging
    log = logging.getLogger('hdhr_broadcast')
    log.setLevel(logging.INFO)

    # configure socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def __init__(self, config: dict):
        """
        initialize class
        """
        self.config = config

    def discover_request(self):
        payload = 0x02.to_bytes(1, 'big')  # HDHOMERUN_TAG_DEVICE_ID
        payload += 0x04.to_bytes(1, 'big')  # 4 bytes
        payload += bytes.fromhex(self.config['hdhomerun']['device_id'])

        payload += 0x01.to_bytes(1, 'big')  # HDHOMERUN_TAG_DEVICE_TYPE
        payload += 0x04.to_bytes(1, 'big')  # 4 bytes
        payload += 0x00000001.to_bytes(4, 'big')  # HDHOMERUN_DEVICE_TYPE_TUNER

        payload += 0x10.to_bytes(1, 'big')  # HDHOMERUN_TAG_TUNER_COUNT
        payload += 0x01.to_bytes(1, 'big')  # 1 byte
        payload += self.config['hdhomerun']['tuners'].to_bytes(1, 'big')

        return create('discover_reply', payload)

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
                    func = self.discover_request
                case _:
                    self.log.log(logging.INFO, f'Client {address} sent invalid request.')
                    break

            data = func()
            self.udp_socket.sendto(data, address)
            self.log.log(logging.DEBUG, f'Sent back {data}')

            # Sending a reply to client
            # udp_server_socket.sendto(bytesToSend, address)
