import gpxpy
import logging
import utm

from sportorg.models.memory import race, ControlPoint
from sportorg.language import _

def import_coordinates_from_gpx(gpx_file_name):
    with open(gpx_file_name) as gpx_file:
        obj = race()
        gpx = gpxpy.parse(gpx_file)
        cps = {}
        for wpt in gpx.waypoints:
            code = wpt.name
            if code.isdigit():
                code = int(code)
            else:
                code = code.lower().strip()
            utm_coords = utm.from_latlon(wpt.latitude, wpt.longitude)
            x = int(utm_coords[0])
            y = int(utm_coords[1])
            cps[code] = (x, y)
        
        start_x = 0
        start_y = 0

        if 'start' in cps:
            start_x = cps['start'][0]
            start_y = cps['start'][1]

        for code, (x, y) in cps.items():
            cp = ControlPoint()
            cp.code = code
            cp.x = x - start_x
            cp.y = y - start_y
            obj.controls[cp.code] = cp
        logging.info(_('Imported {} control points from GPX file. Total {}').format(len(cps), len(obj.controls)))


