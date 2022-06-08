from .packets import create
import re


def discover_request(payload: bytes, config: dict):
    payload = 0x02.to_bytes(1, 'big')  # HDHOMERUN_TAG_DEVICE_ID
    payload += 0x04.to_bytes(1, 'big')
    payload += bytes.fromhex(config['device']['device_id']) # https://github.com/Silicondust/libhdhomerun/blob/master/hdhomerun_discover.c ??

    payload += 0x01.to_bytes(1, 'big')  # HDHOMERUN_TAG_DEVICE_TYPE
    payload += 0x04.to_bytes(1, 'big')
    payload += 0x00000001.to_bytes(4, 'big')  # HDHOMERUN_DEVICE_TYPE_TUNER

    try:
        tuners = int(re.findall(r'\d+', config['device']['hwmodel'].split('-')[-1])[0])
    except IndexError:
        tuners = 1

    payload += 0x10.to_bytes(1, 'big')  # HDHOMERUN_TAG_TUNER_COUNT
    payload += 0x01.to_bytes(1, 'big')
    payload += tuners.to_bytes(1, 'big')  # 2 tuners

    return create('discover_reply', payload)
