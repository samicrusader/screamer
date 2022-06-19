import logging
import socket
from _thread import start_new_thread

class TCPControlServer:
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