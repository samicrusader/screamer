from .packets import create
import math


def getset(payload: bytes, config: dict):
    key_length = (int.from_bytes(payload[1:2], 'little'))
    key = payload[2:(key_length+1)].decode()
    newvalue = None
    if payload.split(key.encode())[1]:
        newvalue_length = int.from_bytes(payload[(key_length+3):(key_length+4)], 'little')
        newvalue = payload[(key_length+4):(key_length+3+newvalue_length)].decode()
    match key:
        case '/lineup/scan':
            value = 'state=complete progress=100% found=71'
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
        case '/tuner0/channel':
            value = 'none'
            value = '8vsb:183000000'
        case '/tuner0/channelmap':
            value = 'us-bcast'
        case '/tuner0/debug':
            value = 'tun: ch=none lock=none ss=0 snq=0 seq=0 dbg=0\ndev: bps=0 resync=0 overflow=0\nts:  bps=0 te=0 crc=0\nnet: bps=0 pps=0 err=0 stop=4\n'
            value = 'tun: ch=8vsb:183000000 lock=8vsb:183000000 ss=96 snq=63 seq=100 dbg=-3800/1660\ndev: bps=19251200 resync=0 overflow=0\nts:  bps=16544 te=0 crc=0\nnet: bps=16544 pps=11 err=0 stop=0\n'
        case '/tuner0/filter':
            value = ''
            value = '0x0000 0x0040'
        case '/tuner0/lockkey':
            value = 'none'
            value = '1.1.1.1'
        case '/tuner0/program':
            value = '0'
            value = '2'
        case '/tuner0/status':
            value = 'ch=none lock=none ss=0 snq=0 seq=0 bps=0 pps=0'
            value = 'ch=8vsb:183000000 lock=8vsb ss=96 snq=60 seq=100 bps=16544 pps=10'
        case '/tuner0/plpinfo':
            value = ''
        case '/tuner0/streaminfo':
            value = 'none\n'
            value = '1: 14.1 XHSPR\n2: 22.1 XHSPR (no data)\n3: 20.1 XHSPR (no data)\n4: 14.1 XHSPR (no data)\n5: 14.1 XHSPR (no data)\n'
        case '/tuner0/target':
            value = 'none'
            value = 'http://1.1.1.1:6969'
        case '/tuner0/vchannel':
            value = 'none'
            value = '22.1'
        case 'help':
            value = 'Supported configuration options:\n/lineup/scan\n/sys/copyright\n/sys/debug\n/sys/features\n/sys/hwmodel\n/sys/model\n/sys/restart <resource>\n/sys/version\n/tuner<n>/channel <modulation>:<freq|ch>\n/tuner<n>/channelmap <channelmap>\n/tuner<n>/debug\n/tuner<n>/filter "0x<nnnn>-0x<nnnn> [...]"\n/tuner<n>/lockkey\n/tuner<n>/program <program number>\n/tuner<n>/status\n/tuner<n>/plpinfo\n/tuner<n>/streaminfo\n/tuner<n>/target <ip>:<port>\n/tuner<n>/vchannel <vchannel>\n'
        case _:
            raise ValueError('invalid key')

    if newvalue:
        print(f'client wants {key} set to {newvalue}')
        #value = newvalue

    new_payload = 0x03.to_bytes(1, 'big')  # HDHOMERUN_TAG_GETSET_NAME
    new_payload += key_length.to_bytes(1, 'little')
    new_payload += key.encode()
    new_payload += 0x00.to_bytes(1, 'big')  # null terminator
    new_payload += 0x04.to_bytes(1, 'big')  # HDHOMERUN_TAG_GETSET_VALUE
    value_length = (len(value)+1)  # we have to account for the null terminator
    if math.ceil((value_length / 236)) > 1:  # if our length is over 236 bytes
        value_length_bytes = 0xec.to_bytes(1, 'little')  # we have to split it by 236 and indicate it
        value_length_bytes += math.ceil((value_length / 236)).to_bytes(1, 'little')  # by (length / 236) rounded up
    else:  # otherwise
        value_length_bytes = value_length.to_bytes(1, 'little')  # just send the length
    new_payload += value_length_bytes
    new_payload += value.encode()
    new_payload += 0x00.to_bytes(1, 'big')  # null terminator
    return create('getset_reply', new_payload)
