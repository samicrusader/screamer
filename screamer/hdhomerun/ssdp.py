import binascii

HDHOMERUN_MAX_PACKET_SIZE = 1460
HDHOMERUN_MAX_PAYLOAD_SIZE = 1452
HDHOMERUN_TYPE_DISCOVER_REQ = 0x0002
HDHOMERUN_TYPE_DISCOVER_RPY = 0x0003
HDHOMERUN_TYPE_GETSET_REQ = 0x0004
HDHOMERUN_TYPE_GETSET_RPY = 0x0005
HDHOMERUN_TAG_DEVICE_TYPE = 0x01
HDHOMERUN_TAG_DEVICE_ID = 0x02
HDHOMERUN_TAG_GETSET_NAME = 0x03
HDHOMERUN_TAG_GETSET_VALUE = 0x04
HDHOMERUN_TAG_GETSET_LOCKKEY = 0x15
HDHOMERUN_TAG_ERROR_MESSAGE = 0x05
HDHOMERUN_TAG_TUNER_COUNT = 0x10
HDHOMERUN_TAG_DEVICE_AUTH_BIN = 0x29
HDHOMERUN_TAG_BASE_URL = 0x2A
HDHOMERUN_TAG_DEVICE_AUTH_STR = 0x2B
HDHOMERUN_DEVICE_TYPE_WILDCARD = 0xFFFFFFFF
HDHOMERUN_DEVICE_TYPE_TUNER = 0x00000001
HDHOMERUN_DEVICE_ID_WILDCARD = 0xFFFFFFFF


def parse(data: bytes):
    """
    parse discovery packets
    """
    header = data[:4]
    payload = data[4:-4]
    packet_hash = int.from_bytes(data[-4:], 'little')

    print(data)
    payload_type = int.from_bytes(header[:2], 'little')
    length = int.from_bytes(header[2:4], 'little')

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

    packet = packet.to_bytes(2, 'little')
    packet += len(payload).to_bytes(2, 'little')
    packet += payload
    packet += binascii.crc32(packet).to_bytes(4, 'little')
    return packet
