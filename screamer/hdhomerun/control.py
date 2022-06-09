from .packets import create
from screamer.tv_freq import atsc_freq
from time import sleep
import math
import numpy
import re
import threading

session = {'lineup': {'scan': 'incomplete', 'progress': 0, 'found': 0}, 'tuners': {
    0: {'ch': 'none', 'channelmap': 'us-bcast', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
    1: {'ch': 'none', 'channelmap': 'us-bcast', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
    2: {'ch': 'none', 'channelmap': 'us-bcast', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
    3: {'ch': 'none', 'channelmap': 'us-bcast', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
}}


def clear_tuner(tuner: int):
    session['tuners'][tuner]['ch'] = 'none'
    session['tuners'][tuner]['filter'] = ''
    session['tuners'][tuner]['lock'] = 'none'
    session['tuners'][tuner]['program'] = 0
    # session['tuners'][i]['target'] = 'none'  # TODO: implement when streaming is implemented
    session['tuners'][tuner]['vchannel'] = 'none'
    session['tuners'][tuner]['ss'] = 0
    session['tuners'][tuner]['snq'] = 0
    session['tuners'][tuner]['seq'] = 0
    session['tuners'][tuner]['dbg'] = '0'
    session['tuners'][tuner]['bps'] = 0
    session['tuners'][tuner]['pps'] = 0


def set_tuner(config: dict, freq: int, tuner: int):
    channels = list()
    print(freq)
    for cid, channel in config['channels'].items():
        if freq in range(channel['freq_low'], channel['freq_high']+1):
            print(f'{freq} is definitely within {channel["freq_low"]} and {channel["freq_high"]}')
            channels.append(cid)
    print('current channels:', channels)
    session['tuners'][tuner]['ch'] = f'8vsb:{(freq * 1000000)}'
    session['tuners'][tuner]['filter'] = '0x0000-0x1fff'
    session['tuners'][tuner]['program'] = 0
    session['tuners'][tuner]['vchannel'] = 'none'
    session['tuners'][tuner]['dbg'] = '0'  # TODO: figure whatever the hell this is out
    if not channels == list():
        session['tuners'][tuner]['lock'] = f'8vsb:{(freq * 1000000)}'
        session['tuners'][tuner]['ss'] = config['channels'][channels[0]]['signal_strength']
        session['tuners'][tuner]['snq'] = config['channels'][channels[0]]['signal_quality']
        session['tuners'][tuner]['seq'] = config['channels'][channels[0]]['symbol_quality']
        # session['tuners'][tuner]['bps']  # TODO: implement when streaming is a thing
        # session['tuners'][tuner]['pps']  # TODO: implement when streaming is a thing
        session['tuners'][tuner]['streaminfo'] = str()
        _i = 1
        for i in channels:
            channel = config['channels'][i]
            session['tuners'][tuner]['streaminfo'] += \
                f'{_i}: {channel["master_channel"]}.{channel["virtual_channel"]} {channel["name"]}\n'
        session['tuners'][tuner]['streaminfo'] += 'tsid=0x0100\n\n'
        return True
    else:
        session['tuners'][tuner]['lock'] = 'none'
        session['tuners'][tuner]['ss'] = 0
        session['tuners'][tuner]['snq'] = 0
        session['tuners'][tuner]['seq'] = 0
        session['tuners'][tuner]['bps'] = 0
        session['tuners'][tuner]['pps'] = 0
        session['tuners'][tuner]['streaminfo'] = 'none\n\n'
        return False


def scan(config: dict):
    session['lineup']['scan'] = 'running'
    session['lineup']['progress'] = 0
    session['lineup']['found'] = 0
    try:
        tuners = int(re.findall(r'\d+', config['device']['hwmodel'].split('-')[-1])[0])
    except IndexError:
        tuners = 1
    arrays = list()
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
                tuned = set_tuner(config, atsc_freq[channel]["low"], i)  # FIXME: frequency is too exact
                if tuned:
                    found += 1
                    print(f'added {channel} to found')
                arrays[i].pop(0)
                checked += 1
                session['lineup']['progress'] = int((checked / 68) * 100)
                session['lineup']['found'] = found
                sleep(0.25)
            else:
                print(f'tuner {i} exhausted of channels')
                clear_tuner(i)
        x = 0
        for i in range(tuners):
            x += len(arrays[i])
        sleep(2)
        if x == 0:
            break
    session['lineup']['scan'] = 'complete'


def getset(payload: bytes, config: dict, address: tuple):
    if session['lineup']['scan'] == 'incomplete':
        session['lineup']['scan'] = 'complete'
        session['lineup']['progress'] = 100
        session['lineup']['found'] = len(config['channels'].keys())
    try:
        tuners = int(re.findall(r'\d+', config['device']['hwmodel'].split('-')[-1])[0])
    except IndexError:
        tuners = 1
    key_length = (int.from_bytes(payload[1:2], 'little'))
    key = payload[2:(key_length + 1)].decode()
    new_value = None
    if payload.split(key.encode())[1]:
        newvalue_length = int.from_bytes(payload[(key_length + 3):(key_length + 4)], 'little')
        try:
            new_value = payload[(key_length + 4):(key_length + 3 + newvalue_length)].decode()
        except Exception:
            print('new_value is raw bytes, have fun...')
            new_value = payload[(key_length + 4):(key_length + 3 + newvalue_length)]
    match key:
        case '/lineup/scan':
            if new_value:
                if not session['lineup']['scan'] == 'running':
                    scan_thread = threading.Thread(target=lambda: scan(config), daemon=True)
                    scan_thread.start()
                    sleep(0.25)
            value = f'state={session["lineup"]["scan"]} progress={session["lineup"]["progress"]}% found={session["lineup"]["found"]}'
        case '/sys/copyright':
            value = 'HDHomerun is copyright of SiliconDust.\nThis program was created using clean-room reverse engineering of both libhdhomerun and actual HDHomerun units.\nhttps://github.com/samicrusader/screamer\n'
        case '/sys/debug':
            value = 'mem: ddr=128 nbk=1 dmk=341 fet=0\nloop: pkt=2\nt0: pt=12 cal=-5465\nt1: pt=12 cal=-5465\nt2: pt=12 cal=-5465\nt3: pt=12 cal=-5490\neth: link=100f\n'
        case '/sys/features':
            value = 'channelmap: us-bcast us-cable us-hrc us-irc kr-bcast kr-cable\nmodulation: 8vsb qam256 qam64\nauto-modulation: auto auto6t auto6c qam\n'
        case '/sys/hwmodel':
            value = config['device']['hwmodel']
        case '/sys/model':
            value = config['device']['model']
        case '/sys/version':
            value = config['device']['firmware']
        case 'help':
            value = 'Supported configuration options:\n/lineup/scan\n/sys/copyright\n/sys/debug\n/sys/features\n/sys/hwmodel\n/sys/model\n/sys/restart <resource>\n/sys/version\n/tuner<n>/channel <modulation>:<freq|ch>\n/tuner<n>/channelmap <channelmap>\n/tuner<n>/debug\n/tuner<n>/filter "0x<nnnn>-0x<nnnn> [...]"\n/tuner<n>/lockkey\n/tuner<n>/program <program number>\n/tuner<n>/status\n/tuner<n>/plpinfo\n/tuner<n>/streaminfo\n/tuner<n>/target <ip>:<port>\n/tuner<n>/vchannel <vchannel>\n'
        case _:
            if key.startswith('/tuner'):
                current_tuner = int(key.split('/tuner')[1].split('/')[0])
                if current_tuner > tuners:
                    raise ValueError('tuner called not within allowed tuners for model')
                tinfo = session['tuners'][current_tuner]
                if not new_value and not address[0] == session['tuners'][current_tuner]['lockkey'] and not session['tuners'][current_tuner]['lockkey'] == 'none':
                    raise ValueError('You can\'t set a locked tuner dumbass')
                match key.split('/tuner')[1].split('/')[1]:
                    case 'channel':
                        if new_value:
                            if new_value == 'none':
                                clear_tuner(current_tuner)
                            else:
                                freq = int(int(new_value.split(':')[1]) / 1000000)
                                set_tuner(config, freq, current_tuner)
                                session['tuners'][current_tuner]['ch'] = new_value
                        value = session['tuners'][current_tuner]['ch']
                    case 'channelmap':
                        if new_value:
                            if new_value in ['us-bcast', 'us-cable', 'us-hrc', 'us-irc', 'kr-bcast', 'kr-cable']:
                                session['tuners'][current_tuner]['channelmap'] = new_value
                        value = session['tuners'][current_tuner]['channelmap']
                    case 'debug':
                        value = f'tun: ch={tinfo["ch"]} lock={tinfo["lock"]} ss={tinfo["ss"]} snq={tinfo["snq"]} seq={tinfo["seq"]} dbg={tinfo["dbg"]}\ndev: bps={tinfo["bps"]} resync=0 overflow=0\nts: bps=0 te=0 crc=0\nnet: bps=0 pps={tinfo["pps"]} err=0 stop=0\n'
                    case 'filter':
                        if new_value:
                            if type(new_value) == str:
                                session['tuners'][current_tuner]['filter'] = new_value
                            elif type(new_value) == bytes:
                                # https://stackoverflow.com/a/59152577
                                # https://stackoverflow.com/a/339024
                                session['tuners'][current_tuner]['filter'] = '-'.join([f'0x{val.rjust(4, "0")}' for val in new_value.hex(' ').split()])
                        value = session['tuners'][current_tuner]['filter']
                    case 'lockkey':
                        if new_value:
                            if new_value == 'none':
                                session['tuners'][current_tuner]['lockkey'] = 'none'
                            else:
                                session['tuners'][current_tuner]['lockkey'] = address[0]
                        value = session['tuners'][current_tuner]['lockkey']
                    case 'program':
                        if new_value:
                            session['tuners'][current_tuner]['program'] = new_value
                        value = session['tuners'][current_tuner]['program']
                    case 'status':
                        value = f'ch={tinfo["ch"]} lock={tinfo["lock"]} ss={tinfo["ss"]} snq={tinfo["snq"]} seq={tinfo["seq"]} bps={tinfo["bps"]} pps={tinfo["pps"]}'
                    case 'plpinfo':
                        value = ''  # ??
                    case 'streaminfo':
                        value = tinfo['streaminfo']
                    case 'target':  # This bit is what actually does stuff.
                        if new_value:
                            session['tuners'][current_tuner]['target'] = new_value
                        value = session['tuners'][current_tuner]['target']
                    case 'vchannel':
                        if new_value:
                            session['tuners'][current_tuner]['vchannel'] = new_value
                        value = session['tuners'][current_tuner]['vchannel']
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
        value_length_bytes += 0x01.to_bytes(1, 'little') # with 1
    new_payload += value_length_bytes
    new_payload += value.encode()
    new_payload += 0x00.to_bytes(1, 'big')  # null terminator
    return create('getset_reply', new_payload)
