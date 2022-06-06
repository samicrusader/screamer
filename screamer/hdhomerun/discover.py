from .packets import create

def discover_request(payload: bytes):
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