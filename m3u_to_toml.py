#!/usr/bin/env python3

import argparse
import requests
import toml
from screamer.tv_freq import atsc_freq

parser = argparse.ArgumentParser(prog='python3 m3u_to_toml.py')
parser.add_argument('--playlist', '-p', help='Specify playlist file.')
args = parser.parse_args()

if args.playlist.startswith('http'):
    m3u = requests.get(args.playlist).text
else:
    m3u = open(args.playlist, 'r').read()

channels = list()
m3u = m3u.splitlines()  # split by lines
for i, line in enumerate(m3u):  # i = line number
    if line.startswith('#EXTINF:'):
        name = line.split('tvg-name="')[1].split('"')[0]
        source = m3u[i + 1]
        channels.append((name, source))

freq_type = '8vsb'  # antenna
if len(channels) > 68:
    freq_type = 'qam256'  # cable

tomlchannels = dict()

for i, channel in enumerate(channels):
    tomlchannel = dict()
    tomlchannel['name'] = channel[0]
    tomlchannel['source'] = channel[1]
    tomlchannel['master_channel'] = i+2
    tomlchannel['virtual_channel'] = 1
    tomlchannel['freq_type'] = freq_type
    tomlchannel['signal_strength'] = 100
    tomlchannel['signal_quality'] = 100
    tomlchannel['symbol_quality'] = 100
    tomlchannel['bitrate'] = 'will figure out later'
    tomlchannels.update({f'ch_{i}': tomlchannel})

fh = open('channels.toml', 'w')
toml.dump(tomlchannels, fh)
fh.close()