from .packets import create

# 03 0b [2f 73 79 73 2f 6d 6f 64 65 6c] 00 04 0f [68 64 68 6f 6d 65 72 75 6e 5f 64 76 62 74] 00

def get_request(payload):
    """
    Payload data:
    0x03 = HDHOMERUN_TAG_GETSET_NAME
    0x0b = Separator?
    <string> = Key
    0x00 = String terminator
    """
    key = payload.split(b'\x03\x0b')[1].split('\x00')[0].decode()
    match key:
        case '/sys/model':
            value = 'hdhomerun'
        case _:
            raise ValueError('invalid key')

    new_payload = 0x03.to_bytes(1, 'big') # HDHOMERUN_TAG_GETSET_NAME
    new_payload += 0x0b.to_bytes(1, 'big')
    new_payload += key.encode()
    new_payload += 0x00.to_bytes(1, 'big') # null terminator
    new_payload += 0x04.to_bytes(1, 'big') # HDHOMERUN_TAG_GETSET_VALUE
    new_payload += 0x0f.to_bytes(1, 'big')
    new_payload += value.encode()

    return create('getset_reply', new_payload)