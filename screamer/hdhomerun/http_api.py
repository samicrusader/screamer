from flask import current_app, Blueprint, request
import xml.etree.cElementTree as ElementTree

bp = Blueprint('http_api', __name__, url_prefix='/')


@bp.route('/lineup.xml', methods=['GET'])
def lineup():
    # create xml
    root = ElementTree.Element('Lineup')

    print(current_app.app_config['channels'])

    for _, channel in current_app.app_config['channels'].items():
        program = ElementTree.SubElement(root, 'Program')
        ElementTree.SubElement(program, 'GuideNumber').text = \
            str(channel['master_channel']) + '.' + str(channel['virtual_channel'])
        ElementTree.SubElement(program, 'GuideName').text = channel['name']
        ElementTree.SubElement(program, 'VideoCodec').text = 'MPEG2'
        ElementTree.SubElement(program, 'AudioCodec').text = 'AC3'
        ElementTree.SubElement(program, 'URL').text = \
            f'http://{request.host}:5004/auto/v{str(channel["master_channel"]) + "." + str(channel["virtual_channel"])}'

    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + ElementTree.tostring(root).decode()
