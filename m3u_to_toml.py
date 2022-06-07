#!/usr/bin/env python3

import argparse
import requests
import toml

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

atsc_freq = {2: {'high': 54, 'low': 60}, 3: {'high': 60, 'low': 66}, 4: {'high': 66, 'low': 72},
             5: {'high': 76, 'low': 82}, 6: {'high': 82, 'low': 88}, 7: {'high': 174, 'low': 180},
             8: {'high': 180, 'low': 186}, 9: {'high': 186, 'low': 192}, 10: {'high': 192, 'low': 198},
             11: {'high': 198, 'low': 204}, 12: {'high': 204, 'low': 210}, 13: {'high': 210, 'low': 216},
             14: {'high': 470, 'low': 476}, 15: {'high': 476, 'low': 482}, 16: {'high': 482, 'low': 488},
             17: {'high': 488, 'low': 494}, 18: {'high': 494, 'low': 500}, 19: {'high': 500, 'low': 506},
             20: {'high': 506, 'low': 512}, 21: {'high': 512, 'low': 518}, 22: {'high': 518, 'low': 524},
             23: {'high': 524, 'low': 530}, 24: {'high': 530, 'low': 536}, 25: {'high': 536, 'low': 542},
             26: {'high': 542, 'low': 548}, 27: {'high': 548, 'low': 554}, 28: {'high': 554, 'low': 560},
             29: {'high': 560, 'low': 566}, 30: {'high': 566, 'low': 572}, 31: {'high': 572, 'low': 578},
             32: {'high': 578, 'low': 584}, 33: {'high': 584, 'low': 590}, 34: {'high': 590, 'low': 596},
             35: {'high': 596, 'low': 602}, 36: {'high': 602, 'low': 608}, 37: {'high': 608, 'low': 614},
             38: {'high': 614, 'low': 620}, 39: {'high': 620, 'low': 626}, 40: {'high': 626, 'low': 632},
             41: {'high': 632, 'low': 638}, 42: {'high': 638, 'low': 644}, 43: {'high': 644, 'low': 650},
             44: {'high': 650, 'low': 656}, 45: {'high': 656, 'low': 662}, 46: {'high': 662, 'low': 668},
             47: {'high': 668, 'low': 674}, 48: {'high': 674, 'low': 680}, 49: {'high': 680, 'low': 686},
             50: {'high': 686, 'low': 692}, 51: {'high': 692, 'low': 698}, 52: {'high': 698, 'low': 704},
             53: {'high': 704, 'low': 710}, 54: {'high': 710, 'low': 716}, 55: {'high': 716, 'low': 722},
             56: {'high': 722, 'low': 728}, 57: {'high': 728, 'low': 734}, 58: {'high': 734, 'low': 740},
             59: {'high': 740, 'low': 746}, 60: {'high': 746, 'low': 752}, 61: {'high': 752, 'low': 758},
             62: {'high': 758, 'low': 764}, 63: {'high': 764, 'low': 770}, 64: {'high': 770, 'low': 776},
             65: {'high': 776, 'low': 782}, 66: {'high': 782, 'low': 788}, 67: {'high': 788, 'low': 794},
             68: {'high': 794, 'low': 800}, 69: {'high': 800, 'low': 806}}

tomlchannels = dict()

for i, channel in enumerate(channels):
    tomlchannel = dict()
    tomlchannel['name'] = channel[0]
    tomlchannel['source'] = channel[1]
    tomlchannel['master_channel'] = i+2
    tomlchannel['virtual_channel'] = 1
    tomlchannel['freq_low'] = atsc_freq[i + 2]['high']   # accidentally switched them
    tomlchannel['freq_high'] = atsc_freq[i + 2]['low']
    tomlchannel['freq_type'] = freq_type
    tomlchannel['signal_strength'] = 100
    tomlchannel['signal_quality'] = 100
    tomlchannel['symbol_quality'] = 100
    tomlchannel['bitrate'] = 'will figure out later'
    tomlchannels.update({f'ch_{i}': tomlchannel})

fh = open('channels.toml', 'w')
toml.dump(tomlchannels, fh)
fh.close()