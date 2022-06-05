import binascii


def parse(data: bytes):
    """
    parse discovery packets
    """
    header = data[:4]
    payload = data[4:-4]
    packet_hash = int.from_bytes(data[-4:], 'little')

    print(data)
    payload_type = int.from_bytes(header[:2], 'big')
    length = int.from_bytes(header[2:4], 'big')

    print(length)
    print(len(payload))
    if not length == len(payload):
        raise ValueError('payload size invalid')

    if not binascii.crc32(header+payload) == packet_hash:
        raise ValueError('hash mismatch')

    match payload_type:
        case 2:
            packet = 'discover_request'
        case 3:
            packet = 'discover_reply'
        case 4:
            packet = 'getset_request'
        case 5:
            packet = 'getset_reply'
        case _:
            raise ValueError('invalid payload type')
    return packet, payload


def create(payload_type: str, payload: bytes):
    match payload_type:
        case 'discover_request':
            packet = 2
        case 'discover_reply':
            packet = 3
        case 'getset_request':
            packet = 4
        case 'getset_reply':
            packet = 5
        case _:
            raise ValueError('invalid payload type')

    packet = packet.to_bytes(2, 'big')
    packet += len(payload).to_bytes(2, 'big')
    packet += payload
    packet += binascii.crc32(packet).to_bytes(4, 'little')
    return packet


def discover_request():
    payload = 0x02.to_bytes(1, 'big') # HDHOMERUN_TAG_DEVICE_ID
    payload += 0x04.to_bytes(1, 'big')
    payload += b'\x5b\xc2\x44\xce'  # device id

    payload += 0x01.to_bytes(1, 'big') # HDHOMERUN_TAG_DEVICE_TYPE
    payload += 0x04.to_bytes(1, 'big')
    payload += 0x00000001.to_bytes(4, 'big') # HDHOMERUN_DEVICE_TYPE_TUNER


    payload += 0x10.to_bytes(1, 'big') # HDHOMERUN_TAG_TUNER_COUNT
    payload += 0x01.to_bytes(1, 'big')
    payload += 0x02.to_bytes(1, 'big') # 2 tuners

    return create('discover_reply', payload)