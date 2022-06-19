from . import logger
from .hdhomerun.control import TCPControlServer as HDHRTCPControlServer
from .hdhomerun.discover import UDPBroadcastServer as HDHRUDPBroadcastServer
from .hdhomerun.llmnr import LLMNRServer as HDHRLLMNRServer
from .dvblink.control import TCPControlServer as DVBLTCPControlServer
import argparse
import logging
import os
import threading
import toml
from flask import Flask

log = logger.setup_custom_logger('root')
config = dict()


def hdhr_create_http_mgmt_server():
    flask = Flask('screamer_hdhr_mgmt')
    flask.app_config = config

    if not os.path.exists(flask.instance_path):
        os.mkdir(flask.instance_path)

    from .hdhomerun import http_api
    flask.register_blueprint(http_api.bp)
    return flask


def hdhr_create_http_stream_server():
    flask = Flask('screamer_hdhr_http_stream')
    flask.app_config = config

    if not os.path.exists(flask.instance_path):
        os.mkdir(flask.instance_path)

    # from . import bla
    # app.register_blueprint(bla.bp)
    return flask


if __name__ == '__main__':
    # ArgumentParser setup
    parser = argparse.ArgumentParser(
        description='''HDHomerun Emulator.
    Model information is available at https://www.silicondust.com/support/linux/.
    Firmware information is available at https://www.silicondust.com/support/downloads/firmware-changelog/.
    Device ID format is available in docs.txt (more reverse engineering needed, just use 107C21C8.)

    Command line arguments take priority over config settings.''',
        prog='python3 -m screamer'
    )
    parser.add_argument('--config', '-c', default=None,
                        help='Specify configuration file.')
    parser.add_argument('--data', '-d', default=None,
                        help='Specify channel listing file.')
    parser.add_argument('--hwmodel', '-w', default=None,
                        help='Change hardware model.')
    parser.add_argument('--model', '-m', default=None,
                        help='Change device type.')
    parser.add_argument('--firmware', '-f', default=None,
                        help='Change emulated firmware version.')
    parser.add_argument('--device-id', '-i', default=None,
                        help='Change device ID.')
    parser.add_argument('--bind', '-b', default=None,
                        help='Change IP address of control servers. Leave blank for all interfaces.'
                             '(Broadcast/LLMNR excluded)')
    parser.add_argument('--hdhr-webgui-port', '--hwp', default=None,
                        help='Specify HDHomeRun WebGUI port.')
    parser.add_argument('--hdhr-tuners',  dest='tuners', default=None,
                        help='Specify available HDHomeRun TV tuners.')
    parser.add_argument('--enable-dvbl-control', default=None,
                        help='Enable/Disable HDHomeRun Web GUI.')
    parser.add_argument('--enable-hdhr-webgui', default=None,
                        help='Enable/Disable HDHomeRun Web GUI.')
    parser.add_argument('--enable-hdhr-httpstream', default=None,
                        help='Enable/Disable HDHomeRun HTTPStream server.')
    parser.add_argument('--enable-hdhr-broadcast', default=None,
                        help='Enable/Disable HDHomeRun UDP Broadcast client.')
    parser.add_argument('--enable-hdhr-control', default=None,
                        help='Enable/Disable HDHomeRun TCP Control server.')

    args = parser.parse_args()

    # Load .toml settings
    configfile = 'config.toml'
    if args.config:
        configfile = args.config

    datafile = 'channels.toml'
    if args.data:
        datafile = args.data

    tomlconfig = dict()
    channeldata = dict()
    try:
        tomlconfig = toml.load(configfile)
    except FileNotFoundError:
        log.log(logging.ERROR, f'Config file {configfile} was not found, using command line parameters.')
    except toml.decoder.TomlDecodeError as e:
        log.log(logging.ERROR, f'Config file {configfile} has invalid syntax: {str(e)}. Bailing out.')
        exit(1)

    try:
        channeldata = toml.load(datafile)
    except FileNotFoundError:
        log.log(logging.ERROR, f'Config file {datafile} was not found, using command line parameters.')
    except toml.decoder.TomlDecodeError as e:
        log.log(logging.ERROR, f'Config file {datafile} has invalid syntax: {str(e)}. Bailing out.')
        exit(1)

    # Parse config variables
    try:
        toml_entry = tomlconfig['server']
    except KeyError:
        toml_entry = dict()

    for i in [
        ('server', ['bind', 'hdhr_webgui_port', 'enable_dvbl_control', 'enable_hdhr_webgui', 'enable_hdhr_httpstream',
                    'enable_hdhr_broadcast', 'enable_hdhr_control']),
        ('hdhomerun', ['firmware', 'device_id', 'hwmodel', 'model', 'tuners'])
    ]:
        cfg_entry = dict()
        for x in i[1]:
            if not getattr(args, x) == None:
                cfg_entry[x] = getattr(args, x)
            else:
                try:
                    tomlconfig[i[0]][x]
                except KeyError:
                    log.log(logging.ERROR, f'Config variable {i[0]}[{x}] is not set. Bailing out.')
                    exit(1)
                else:
                    cfg_entry[x] = tomlconfig[i[0]][x]
        config[i[0]] = cfg_entry

    config['channels'] = channeldata
    print(config)

    # Configure and start threads
    threads = list()
    if config['server']['enable_hdhr_webgui'] == True:
        hdhr_webgui_thread = threading.Thread(
            target=lambda: hdhr_create_http_mgmt_server().run(host=config['server']['bind'],
                                                              port=config['server']['hdhr_webgui_port'],
                                                              use_reloader=False, threaded=True), daemon=True)
        hdhr_webgui_thread.start()
        threads.append(hdhr_webgui_thread)
    if config['server']['enable_hdhr_httpstream'] == True:
        hdhr_http_stream_thread = threading.Thread(
            target=lambda: hdhr_create_http_stream_server().run(host=config['server']['bind'], port=5004,
                                                                use_reloader=False, threaded=True), daemon=True)
        hdhr_http_stream_thread.start()
        threads.append(hdhr_http_stream_thread)
    if config['server']['enable_hdhr_broadcast'] == True:
        hdhr_broadcast_thread = threading.Thread(
            target=lambda: HDHRUDPBroadcastServer(config=config).run(ip='', port=65001), daemon=True)
        hdhr_broadcast_thread.start()
        threads.append(hdhr_broadcast_thread)
    if config['server']['enable_hdhr_control'] == True:
        hdhr_control_thread = threading.Thread(
            target=lambda: HDHRTCPControlServer(config=config).run(ip=config['server']['bind'], port=65001), daemon=True)
        hdhr_control_thread.start()
        threads.append(hdhr_control_thread)
    if config['server']['enable_dvbl_control'] == True:
        dvbl_control_thread = threading.Thread(
            target=lambda: DVBLTCPControlServer(config=config).run(ip=config['server']['bind'], port=39877), daemon=True)
        dvbl_control_thread.start()
        threads.append(dvbl_control_thread)
    hdhr_llmnr_thread = threading.Thread(
        target=lambda: HDHRLLMNRServer(config=config).run(ip='', port=5355),
        daemon=True)
    hdhr_llmnr_thread.start() # not needed for now
    threads.append(hdhr_llmnr_thread)

    for thread in threads:
        thread.join()
