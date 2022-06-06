import binascii


def parse(data: bytes):
    """
    parse discovery packets
    """
    header = data[:4]
    payload = data[4:-4]
    packet_hash = int.from_bytes(data[-4:], 'little')

    payload_type = int.from_bytes(header[:2], 'big')
    length = int.from_bytes(header[2:4], 'big')

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
