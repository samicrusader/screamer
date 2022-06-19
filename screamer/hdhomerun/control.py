from .packets import create, parse
from _thread import start_new_thread
from screamer.tv_freq import atsc_freq
from time import sleep
import logging
import math
import numpy
import socket
import threading


class TCPControlServer:
    """
    TCP control server for HDHomeRun emulation.
    """
    # configure logging
    log = logging.getLogger('hdhr_tcpcontrol')
    log.setLevel(logging.INFO)

    # configure socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    def __init__(self, config: dict):
        """
        initialize class
        """
        self.config = config
        self.session = {'lineup': {'scan': 'complete', 'progress': 100, 'found': len(self.config['channels'].keys())},
                        'tuners': {}}
        for i in range(self.config['hdhomerun']['tuners']):
            self.session['tuners'][i] = {'ch': 'none', 'channelmap': 'us-bcast', 'filter': '', 'lock': 'none', 'ss': 0,
                                     'snq': 0, 'seq': 0, 'dbg': '0', 'bps': 0, 'pps': 0, 'program': 0,
                                     'lockkey': 'none', 'target': 'none', 'streaminfo': 'none', 'vchannel': 'none'}
        print(self.session)

    def clear_tuner(self, tuner: int):
        self.session['tuners'][tuner]['ch'] = 'none'
        self.session['tuners'][tuner]['filter'] = ''
        self.session['tuners'][tuner]['lock'] = 'none'
        self.session['tuners'][tuner]['program'] = 0
        # session['tuners'][i]['target'] = 'none'  # TODO: implement when streaming is implemented
        self.session['tuners'][tuner]['vchannel'] = 'none'
        self.session['tuners'][tuner]['ss'] = 0
        self.session['tuners'][tuner]['snq'] = 0
        self.session['tuners'][tuner]['seq'] = 0
        self.session['tuners'][tuner]['dbg'] = '0'
        self.session['tuners'][tuner]['bps'] = 0
        self.session['tuners'][tuner]['pps'] = 0

    def set_tuner(self, freq: str, tuner: int):
        print(f'wants freq {freq}')
        if freq == 'none':
            self.clear_tuner(tuner)
            return
        if int(freq.split(':')[1]) < 1000000:
            print(f'channel number {freq.split(":")[1]} detected')
            if 'ch_' + freq.split(':')[1] in self.config['channels'].keys():
                freq_int = self.config['channels']['ch_' + freq.split(':')[1]]['freq_low'] + 1
                print(f'found channel {freq.split(":")[1]} on frequency {freq_int}')
            else:
                print(f'falling back to atsc')
                try:
                    freq_int = atsc_freq[int(freq.split(':')[1])]['low']
                except KeyError:
                    self.set_tuner(self.config, f'auto:2', tuner)
                    return
        else:
            freq_int = int(int(freq.split(':')[1]) / 1000000)
        band_raw = freq.split(':')[0]
        if band_raw in ['8vsb', 'auto6t']:
            band = 'terrestial'
            band_type = '8vsb'
        elif band_raw in ['qam256', 'qam64', 'qam', 'auto6c']:
            band = 'cable'
            if band_raw in ['auto6c', 'qam']:
                band_type = 'qam256'
            else:
                band_type = band_raw
        elif band_raw == 'auto':
            if self.session['tuners'][tuner]['channelmap'] == 'us-bcast':
                band = 'terrestial'
                band_type = '8vsb'
        print(f'adjusting to {freq_int} mhz on {band} with {band_type} (detected from {band_raw})')
        channels = list()
        for cid, channel in self.config['channels'].items():
            if freq_int in range(channel['freq_low'], channel['freq_high'] + 1):
                print(f'freq: {type(freq)}')
                print(f'{freq_int} is within {channel["freq_low"]} and {channel["freq_high"]}, used by channel {cid}')
                channels.append(cid)
        self.session['tuners'][tuner]['ch'] = freq
        self.session['tuners'][tuner]['filter'] = '0x0000-0x1fff'
        self.session['tuners'][tuner]['program'] = 1
        self.session['tuners'][tuner]['vchannel'] = 'none'
        self.session['tuners'][tuner]['dbg'] = '0'  # TODO: figure whatever the hell this is out
        if not channels == list():
            self.session['tuners'][tuner]['lock'] = band_type
            self.session['tuners'][tuner]['ss'] = self.config['channels'][channels[0]]['signal_strength']
            self.session['tuners'][tuner]['snq'] = self.config['channels'][channels[0]]['signal_quality']
            self.session['tuners'][tuner]['seq'] = self.config['channels'][channels[0]]['symbol_quality']
            self.session['tuners'][tuner]['bps'] = 19251200  # TODO: implement when streaming is a thing
            self.session['tuners'][tuner]['pps'] = 0  # TODO: implement when streaming is a thing
            self.session['tuners'][tuner]['streaminfo'] = str()
            _i = 1
            for i in channels:
                channel = self.config['channels'][i]
                self.session['tuners'][tuner]['streaminfo'] += \
                    f'{_i}: {channel["master_channel"]}.{channel["virtual_channel"]} {channel["name"]}\x0a'
            self.session['tuners'][tuner]['streaminfo'] += 'tsid=0x0100\n'
            return True
        else:
            self.session['tuners'][tuner]['lock'] = 'none'
            self.session['tuners'][tuner]['ss'] = 0
            self.session['tuners'][tuner]['snq'] = 0
            self.session['tuners'][tuner]['seq'] = 0
            self.session['tuners'][tuner]['bps'] = 0
            self.session['tuners'][tuner]['pps'] = 0
            self.session['tuners'][tuner]['streaminfo'] = 'none\n\n'
            return False

    def scan(self):
        self.session['lineup']['scan'] = 'running'
        self.session['lineup']['progress'] = 0
        self.session['lineup']['found'] = 0
        arrays = list()
        tuners = self.config['hdhomerun']['tuners']
        for array in numpy.array_split(range(2, 70), tuners):
            arrays.append(list(array))
        print(arrays)
        checked = 0
        found = 0
        while True:
            for i in range(tuners):
                if not len(arrays[i]) == 0:
                    channel = (arrays[i][0])
                    print(f'checking channel {channel}...')
                    print(channel)
                    print(atsc_freq[channel]["low"])
                    if self.session['tuners'][i]['channelmap'] == 'us-bcast':
                        tunermap = '8vsb'
                    elif self.session['tuners'][i]['channelmap'] == 'us-cable':
                        tunermap = 'qam256'
                    tuned = self.set_tuner(f'{tunermap}:{atsc_freq[channel]["low"] * 1000000}', i)
                    if tuned:
                        found += 1
                        print(f'added {channel} to found')
                    arrays[i].pop(0)
                    checked += 1
                    self.session['lineup']['progress'] = int((checked / 68) * 100)
                    self.session['lineup']['found'] = found
                    sleep(0.25)
                else:
                    print(f'tuner {i} exhausted of channels')
                    self.clear_tuner(i)
            x = 0
            for i in range(tuners):
                x += len(arrays[i])
            sleep(2)
            if x == 0:
                break
        self.session['lineup']['scan'] = 'complete'

    def getset_request(self, payload: bytes, address: tuple):
        tuners = self.config['hdhomerun']['tuners']
        key_length = (int.from_bytes(payload[1:2], 'little'))
        key = payload[2:(key_length + 2)].decode().strip('\x00')
        print(key)
        new_value = None
        if payload.split(key.encode())[1]:
            newvalue_length = int.from_bytes(payload[(key_length + 3):(key_length + 4)], 'little')
            try:
                new_value = payload[(key_length + 4):(key_length + 3 + newvalue_length)].decode()
            except Exception:
                print('new_value is raw bytes, have fun...')
                new_value = payload[(key_length + 4):(key_length + 3 + newvalue_length)]
        print(f'client requested {key}{":" + str(new_value) if new_value else ""}')
        match key:
            case '/lineup/scan':
                if new_value:
                    if not self.session['lineup']['scan'] == 'running':
                        scan_thread = threading.Thread(target=lambda: self.scan(), daemon=True)
                        scan_thread.start()
                        sleep(0.25)
                value = f'state={self.session["lineup"]["scan"]} progress={self.session["lineup"]["progress"]}% found={self.session["lineup"]["found"]}'
            case '/sys/copyright':
                value = 'HDHomerun is copyright of SiliconDust.\nThis program was created using clean-room reverse engineering of both libhdhomerun and actual HDHomerun units.\nhttps://github.com/samicrusader/screamer\n'
            case '/sys/debug':
                value = 'mem: ddr=128 nbk=1 dmk=341 fet=0\nloop: pkt=2\nt0: pt=12 cal=-5465\nt1: pt=12 cal=-5465\nt2: pt=12 cal=-5465\nt3: pt=12 cal=-5490\neth: link=100f\n'
            case '/sys/features':
                value = 'channelmap: us-bcast us-cable us-hrc us-irc kr-bcast kr-cable\nmodulation: 8vsb qam256 qam64\nauto-modulation: auto auto6t auto6c qam\n'
            case '/sys/hwmodel':
                value = self.config['hdhomerun']['hwmodel']
            case '/sys/model':
                value = self.config['hdhomerun']['model']
            case '/sys/version':
                value = self.config['hdhomerun']['firmware']
            case 'help':
                value = 'Supported configuration options:\n/lineup/scan\n/sys/copyright\n/sys/debug\n/sys/features\n/sys/hwmodel\n/sys/model\n/sys/restart <resource>\n/sys/version\n/tuner<n>/channel <modulation>:<freq|ch>\n/tuner<n>/channelmap <channelmap>\n/tuner<n>/debug\n/tuner<n>/filter "0x<nnnn>-0x<nnnn> [...]"\n/tuner<n>/lockkey\n/tuner<n>/program <program number>\n/tuner<n>/status\n/tuner<n>/plpinfo\n/tuner<n>/streaminfo\n/tuner<n>/target <ip>:<port>\n/tuner<n>/vchannel <vchannel>\n'
            case _:
                if key.startswith('/tuner'):
                    current_tuner = int(key.split('/tuner')[1].split('/')[0])
                    if current_tuner > tuners:
                        raise ValueError('tuner called not within allowed tuners for model')
                    tinfo = self.session['tuners'][current_tuner]
                    if not new_value and not address[0] == self.session['tuners'][current_tuner]['lockkey'] and not \
                            self.session['tuners'][current_tuner]['lockkey'] == 'none':
                        raise ValueError('You can\'t set a locked tuner dumbass')
                    match key.split('/tuner')[1].split('/')[1]:
                        case 'channel':
                            if new_value:
                                self.set_tuner(new_value, current_tuner)
                            value = self.session['tuners'][current_tuner]['ch']
                        case 'channelmap':
                            if new_value:
                                if new_value in ['us-bcast', 'us-cable', 'us-hrc', 'us-irc', 'kr-bcast', 'kr-cable']:
                                    self.session['tuners'][current_tuner]['channelmap'] = new_value
                            value = self.session['tuners'][current_tuner]['channelmap']
                        case 'debug':
                            value = f'tun: ch={tinfo["ch"]} lock={tinfo["lock"]} ss={tinfo["ss"]} snq={tinfo["snq"]} seq={tinfo["seq"]} dbg={tinfo["dbg"]}\ndev: bps={tinfo["bps"]} resync=0 overflow=0\nts: bps=0 te=0 crc=0\nnet: bps=0 pps={tinfo["pps"]} err=0 stop=0\n '
                        case 'filter':
                            if new_value:
                                if type(new_value) == str:
                                    self.session['tuners'][current_tuner]['filter'] = new_value
                                elif type(new_value) == bytes:
                                    # https://stackoverflow.com/a/59152577
                                    # https://stackoverflow.com/a/339024
                                    self.session['tuners'][current_tuner]['filter'] = '-'.join(
                                        [f'0x{val.rjust(4, "0")}' for val in new_value.hex(' ').split()])
                            value = self.session['tuners'][current_tuner]['filter']
                        case 'lockkey':
                            if new_value:
                                if new_value == 'none':
                                    self.session['tuners'][current_tuner]['lockkey'] = 'none'
                                else:
                                    self.session['tuners'][current_tuner]['lockkey'] = address[0]
                            value = self.session['tuners'][current_tuner]['lockkey']
                        case 'program':
                            if new_value:
                                self.session['tuners'][current_tuner]['program'] = int(new_value)
                            value = str(self.session['tuners'][current_tuner]['program'])
                        case 'status':
                            value = f'ch={tinfo["ch"]} lock={tinfo["lock"]} ss={tinfo["ss"]} snq={tinfo["snq"]} seq={tinfo["seq"]} bps={tinfo["bps"]} pps={tinfo["pps"]}'
                        case 'plpinfo':
                            value = ''  # ??
                        case 'streaminfo':
                            value = tinfo['streaminfo']
                        case 'target':  # This bit is what actually does stuff.
                            if new_value:
                                self.session['tuners'][current_tuner]['target'] = new_value
                            value = self.session['tuners'][current_tuner]['target']
                        case 'vchannel':
                            if new_value:
                                self.session['tuners'][current_tuner]['vchannel'] = new_value
                            value = self.session['tuners'][current_tuner]['vchannel']
                else:
                    raise ValueError('invalid key')

        new_payload = 0x03.to_bytes(1, 'big')  # HDHOMERUN_TAG_GETSET_NAME
        new_payload += key_length.to_bytes(1, 'little')
        new_payload += key.encode()
        new_payload += 0x00.to_bytes(1, 'big')  # null terminator
        new_payload += 0x04.to_bytes(1, 'big')  # HDHOMERUN_TAG_GETSET_VALUE
        value_length = (len(value) + 1)  # we have to account for the null terminator
        if math.ceil((value_length / 236)) > 1:  # if our length is over 236 bytes
            value_length_bytes = 0xec.to_bytes(1, 'little')  # we have to split it by 236 and indicate it
            value_length_bytes += math.ceil((value_length / 236)).to_bytes(1, 'little')  # by (length / 236) rounded up
        else:  # otherwise
            value_length_bytes = value_length.to_bytes(1, 'little')  # just send the length
            # value_length_bytes += 0x01.to_bytes(1, 'little') # with 1
        new_payload += value_length_bytes
        new_payload += value.encode()
        new_payload += 0x00.to_bytes(1, 'big')  # null terminator
        return create('getset_reply', new_payload)

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
                        func = self.getset_request
                    case _:
                        self.log.log(logging.INFO, f'Client {address} sent invalid request.')
                        conn.close()
                data = func(payload=x[1], address=address)
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
