from .packets import create

def discover_request(payload: bytes):
    payload = 0x02.to_bytes(1, 'big')  # HDHOMERUN_TAG_DEVICE_ID
    payload += 0x04.to_bytes(1, 'big')
    payload += b'\x10\x7c\x21\xc8'  # device id, https://github.com/Silicondust/libhdhomerun/blob/032728af66da1eff490e5b22d0427a314c93fa31/hdhomerun_discover.c ??

    payload += 0x01.to_bytes(1, 'big')  # HDHOMERUN_TAG_DEVICE_TYPE
    payload += 0x04.to_bytes(1, 'big')
    payload += 0x00000001.to_bytes(4, 'big')  # HDHOMERUN_DEVICE_TYPE_TUNER

    payload += 0x10.to_bytes(1, 'big')  # HDHOMERUN_TAG_TUNER_COUNT
    payload += 0x01.to_bytes(1, 'big')
    payload += 0x02.to_bytes(1, 'big')  # 2 tuners

    return create('discover_reply', payload)
