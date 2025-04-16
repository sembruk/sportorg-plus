import gpxpy
import csv
import logging
import utm
from sportorg.libs.iof import parser as iof_parser

from sportorg.models.memory import race, ControlPoint
from sportorg.language import _

def custom_sort_key(k):
    if k == 'start':
        return (0,)  # Lowest possible rank
    elif k == 'finish':
        return (3,)  # Highest possible rank
    try:
        num = int(k)
        return (1, num)
    except (ValueError, TypeError):
        return (2, str(k))

def sort_and_add_control_points(cps):
    if 'start' not in cps:
        logging.info(_('Start control point not found, using default (0, 0)'))
        cps['start'] = (0, 0)
    if 'finish' not in cps:
        cps['finish'] = cps['start']
    start_x = cps['start'][0]
    start_y = cps['start'][1]

    obj = race()

    cp_dict = {}
    for cp in obj.control_points:
        cp_dict[str(cp.code)] = cp

    for code, (x, y) in cps.items():
        cp = ControlPoint()
        cp.code = str(code)
        cp.x = x - start_x
        cp.y = y - start_y
        if cp.code in cp_dict:
            cp.score = cp_dict[cp.code].score
        else:
            cp.score = 0
            if code.isdigit():
                cp.score = int(cp.code)//10
        cp_dict[cp.code] = cp
    obj.control_points = [v for k,v in sorted(cp_dict.items(), key=lambda item: custom_sort_key(item[0]))]
    logging.info(_('Imported {} control points from file. Total {}').format(len(cps), len(obj.control_points)))


def import_coordinates_from_gpx(gpx_file_name):
    with open(gpx_file_name, encoding='utf-8-sig') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        cps = {}
        for wpt in gpx.waypoints:
            code = wpt.name
            code = code.lower().strip()
            utm_coords = utm.from_latlon(wpt.latitude, wpt.longitude)
            x = int(utm_coords[0])
            y = int(utm_coords[1])
            cps[code] = (x, y)
        sort_and_add_control_points(cps)

def import_coordinates_from_csv(csv_file_name):
    with open(csv_file_name) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        cps = {}
        for row in reader:
            code = row[0].lower().strip()
            x = int(row[1])
            y = int(row[2])
            cps[code] = (x, y)
        sort_and_add_control_points(cps)

def import_coordinates_from_iof_xml(iof_xml_file_name):
    with open(iof_xml_file_name, encoding='utf-8-sig') as iof_file:
        parse_results = iof_parser.parse(iof_file)
        if not len(parse_results):
            logging.error(_('Cannot parse IOF XML file'))
            return

        for result in parse_results:
            if result.name == 'CourseData':
                cps = {}
                if 'controls' not in result.data:
                    logging.error(_('Controls not found in IOF XML file'))
                    return
                for control in result.data['controls']:
                    code = control['id'].lower().strip()
                    if code == 's' or code == 's1':
                        code = 'start'
                    if code == 'f' or code == 'f1':
                        code = 'finish'
                    lat = float(control['position']['lat'])
                    lng = float(control['position']['lng'])
                    utm_coords = utm.from_latlon(lat, lng)
                    x = int(utm_coords[0])
                    y = int(utm_coords[1])
                    cps[code] = (x, y)
                sort_and_add_control_points(cps)
             

