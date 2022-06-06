from .packets import create
import math

# 03 0b [...] 00 04 0f [68 64 68 6f 6d 65 72 75 6e 5f 64 76 62 74]
# 03 05 [...] 00 04 ec 03 [stupidly long string]
# 03 05 [...] 00 04 ec 03 [74 65 73 74 21]
# 03 0b [...] 00 04 c3 ac 03 [74 65 73 74 21]


def getset(payload: bytes):
    key_length = (int.from_bytes(payload[1:2], 'little'))
    print(f'key length: {key_length}')
    key = payload[2:(key_length+1)].decode()
    print(f'key: {key}')
    newvalue = None
    if payload.split(key.encode())[1]:
        newvalue_length = int.from_bytes(payload[(key_length+3):(key_length+4)], 'little')
        print(f'value length: {newvalue_length}')
        newvalue = payload[(key_length+4):(key_length+3+newvalue_length)].decode()
        print(f'value: {newvalue}')
    match key:
        case '/sys/model':
            value = 'hdhomerun_atsc'  # https://www.silicondust.com/support/linux/
        case 'help':
            value = 'Supported configuration options:\n/ir/target <protocol>://<ip>:<port>\n/lineup/location <countrycode> : <postcode>\n/sys/copyright\n/sys/dvbc_modulation\n/sys/debug\n/sys/features\n/sys/hwmodel\n/sys/model\n/sys/restart <resource>\n/sys/version\n/tuner<n>/channel <modulation>:<freq | ch>\n/tuner<n>/channelmap <channelmap>\n/tuner<n>/debug\n/tuner<n>/filter "0x<nnnn>-0x<nnnn> [...]"\n/tuner<n>/lockkey\n/tuner<n>/program <program number>\n/tuner<n>/streaminfo\n/tuner<n>/status\n/tuner<n>/target <ip>:<port>\n'
        case _:
            raise ValueError('invalid key')

    if newvalue:
        print(f'client wants {key} set to {newvalue}')
        value = newvalue

    new_payload = 0x03.to_bytes(1, 'big')  # HDHOMERUN_TAG_GETSET_NAME
    new_payload += key_length.to_bytes(1, 'little')
    new_payload += key.encode()
    new_payload += 0x00.to_bytes(1, 'big')  # null terminator
    new_payload += 0x04.to_bytes(1, 'big')  # HDHOMERUN_TAG_GETSET_VALUE
    value_length = (len(value)+1)  # we have to account for the null terminator
    if math.ceil((value_length / 236)) > 1:  # if our length is over 236 bytes
        value_length_bytes = 0xec.to_bytes(1, 'little')  # we have to split it by 236 and indicate it
        value_length_bytes += math.ceil((value_length / 236)).to_bytes(1, 'little')  # by (length / 236) rounded up
    else: # otherwise
        value_length_bytes = value_length.to_bytes(1, 'little') # just send the length
    new_payload += value_length_bytes
    new_payload += value.encode()
    new_payload += 0x00.to_bytes(1, 'big')  # null terminator
    return create('getset_reply', new_payload)

