from .packets import create
from screamer.tv_freq import atsc_freq
from time import sleep
import math
import numpy
import re
import threading

session = {'lineup': {'scan': 'incomplete', 'progress': 0, 'found': 0}, 'tuners': {
    0: {'ch': 'none', 'channelmap': 'none', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
    1: {'ch': 'none', 'channelmap': 'none', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
    2: {'ch': 'none', 'channelmap': 'none', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
    3: {'ch': 'none', 'channelmap': 'none', 'filter': '', 'lock': 'none', 'ss': 0, 'snq': 0, 'seq': 0, 'dbg': '0',
        'bps': 0, 'pps': 0, 'program': 0, 'lockkey': 'none', 'target': 'none', 'streaminfo': 'none',
        'vchannel': 'none'},
}}


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
                print(channel)
                print(atsc_freq[channel]["low"])
                session['tuners'][i]['ch'] = f'8vsb:{(atsc_freq[channel]["low"] * 1000000)}'
                # TODO: session['tuners'][i]['filter']
                session['tuners'][i]['lock'] = f'8vsb:{(atsc_freq[channel]["low"] * 1000000)}'
                # TODO: session['tuners'][i]['lockkey']
                session['tuners'][i]['program'] = 1
                # TODO: session['tuners'][i]['target']
                session['tuners'][i]['vchannel'] = f'{channel}.1'
                print(f'checking channel {checked + 1}...')
                if f'ch_{channel}' in config['channels'].keys():
                    session['tuners'][i]['ss'] = config['channels'][f'ch_{channel}']['signal_strength']
                    session['tuners'][i]['snq'] = config['channels'][f'ch_{channel}']['signal_quality']
                    session['tuners'][i]['seq'] = config['channels'][f'ch_{channel}']['symbol_quality']
                    # TODO: session['tuners'][i]['dbg'] # ??
                    # TODO: session['tuners'][i]['bps']
                    # TODO: session['tuners'][i]['pps']
                    found += 1
                    print(f'added {checked + 2} to found')
                else:
                    session['tuners'][i]['ss'] = 0
                    session['tuners'][i]['snq'] = 0
                    session['tuners'][i]['seq'] = 0
                    # TODO: session['tuners'][i]['dbg']
                    # TODO: session['tuners'][i]['bps']
                    # TODO: session['tuners'][i]['pps']
                arrays[i].pop(0)
                checked += 1
                session['lineup']['progress'] = int((checked / 68) * 100)
                session['lineup']['found'] = found
                sleep(0.25)
            else:
                print(f'tuner {i} exhausted of channels')
                session['tuners'][i]['ch'] = 'none'
                session['tuners'][i]['filter'] = ''
                session['tuners'][i]['lock'] = 'none'
                session['tuners'][i]['lockkey'] = 'none'
                session['tuners'][i]['program'] = 0
                session['tuners'][i]['target'] = 'none'
                session['tuners'][i]['vchannel'] = 'none'
                session['tuners'][i]['ss'] = 0
                session['tuners'][i]['snq'] = 0
                session['tuners'][i]['seq'] = 0
                session['tuners'][i]['dbg'] = '0'
                session['tuners'][i]['bps'] = 0
                session['tuners'][i]['pps'] = 0
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
    newvalue = None
    if payload.split(key.encode())[1]:
        newvalue_length = int.from_bytes(payload[(key_length + 3):(key_length + 4)], 'little')
        newvalue = payload[(key_length + 4):(key_length + 3 + newvalue_length)].decode()
    match key:
        case '/lineup/scan':
            if newvalue:
                if not session['lineup']['scan'] == 'running':
                    scanthread = threading.Thread(target=lambda: scan(config), daemon=True)
                    scanthread.start()
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
                currenttuner = int(key.split('/tuner')[1].split('/')[0])
                if currenttuner > tuners:
                    raise ValueError('tuner called not within allowed tuners for model')
                tinfo = session['tuners'][currenttuner]
                match key.split('/tuner')[1].split('/')[1]:
                    case 'channel':
                        if newvalue:
                            session['tuners'][currenttuner]['ch'] = newvalue
                        value = session['tuners'][currenttuner]['ch']
                    case 'channelmap':
                        if newvalue:
                            session['tuners'][currenttuner]['channelmap'] = newvalue
                        value = session['tuners'][currenttuner]['channelmap']
                    case 'debug':
                        value = f'tun: ch={tinfo["ch"]} lock={tinfo["lock"]} ss={tinfo["ss"]} snq={tinfo["snq"]} seq={tinfo["seq"]} dbg={tinfo["dbg"]}\ndev: bps={tinfo["bps"]} resync=0 overflow=0\nts: bps=0 te=0 crc=0\nnet: bps=0 pps={tinfo["pps"]} err=0 stop=0\n'
                    case 'filter':
                        if newvalue:
                            session['tuners'][currenttuner]['filter'] = newvalue
                        value = session['tuners'][currenttuner]['filter']
                    case 'lockkey':
                        if newvalue:
                            if newvalue == 'none':
                                session['tuners'][currenttuner]['lockkey'] = 'none'
                            else:
                                session['tuners'][currenttuner]['lockkey'] = address[0]
                        value = session['tuners'][currenttuner]['lockkey']
                    case 'program':
                        if newvalue:
                            session['tuners'][currenttuner]['program'] = newvalue
                        value = session['tuners'][currenttuner]['program']
                    case 'status':
                        value = f'ch={tinfo["ch"]} lock={tinfo["lock"]} ss={tinfo["ss"]} snq={tinfo["snq"]} seq={tinfo["seq"]} bps={tinfo["bps"]} pps={tinfo["pps"]}'
                    case 'plpinfo':
                        value = ''  # ??
                    case 'streaminfo':
                        value = tinfo['streaminfo']
                    case 'target':  # This bit is what actually does stuff.
                        if newvalue:
                            session['tuners'][currenttuner]['target'] = newvalue
                        value = session['tuners'][currenttuner]['target']
                    case 'vchannel':
                        if newvalue:
                            session['tuners'][currenttuner]['vchannel'] = newvalue
                        value = session['tuners'][currenttuner]['vchannel']
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
