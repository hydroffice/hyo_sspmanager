from __future__ import absolute_import, division, print_function, unicode_literals

import logging

log = logging.getLogger(__name__)

from .helper import SspError


class Dicts(object):

    @classmethod
    def first_match(cls, dct, val):
        # print(dct, val)
        values = [key for key, value in dct.items() if value == val]
        if len(values) != 0:
            return values[0]
        else:
            raise SspError("Unknown value: %s" % val)

    import_formats = {
        'CASTAWAY': 0,
        'IDRONAUT': 1,
        'SAIV': 2,
        'DIGIBAR_PRO': 3,
        'DIGIBAR_S': 4,
        'SIPPICAN': 5,
        'SEABIRD': 6,
        'TURO': 7,
        'UNB': 8,
        'VALEPORT_MIDAS': 9,
        'VALEPORT_MONITOR': 10,
        'VALEPORT_MINI_SVP': 11
    }

    import_extensions = {
        0: "csv",
        1: "txt",
        2: "txt",
        3: "txt",
        4: "csv",
        5: "edf",
        6: "cnv",
        7: "nc",
        8: "unb",
        9: "000",
        10: "000",
        11: "txt"
    }

    probe_types = {
        'Unknown': 0,
        'Synthetic': 1,
        'SVP': 2,
        'Castaway': 3,
        'Idronaut': 4,
        'S2': 5,
        'SBE': 6,
        'XBT': 7,
        'Deep Blue': 8,
        'T-10': 9,
        'T-11 (Fine Structure)': 10,
        'T-4': 11,
        'T-5': 12,
        'T-5/20': 13,
        'T-7': 14,
        'XSV-01': 15,
        'XSV-02': 16,
        'XCTD-1': 17,
        'XCTD-2': 18,
        'MONITOR SVP 500': 20,
        'MIDAS SVP 6000': 21,
        'MiniSVP': 22,
        'MVP': 23,
    }

    sensor_types = {
        'Unknown': 0,
        'Synthetic': 1,
        'SVP': 2,
        'CTD': 3,
        'XBT': 4,
        'XSV': 5,
        'XCTD': 6,
        'SVPT': 7,
        'MVP': 8,
    }

    source_types = {
        'Raw': 0,
        'User': 1,
        'Atlas': 2,
        'Interp': 3,
        'SurfaceSensor': 4,
        'Woa09Extend': 5,
        'Woa13Extend': 6,
        'RtofsExtend': 7,
        'UserRefExtend': 8,
    }

    idx = {  # A dictionary so we can easily lookup data
        'depth': 0,
        'speed': 1,
        'temperature': 2,
        'salinity': 3,
        'source': 4,
        'flag': 5,
    }

    export_formats = {

    }

    kng_formats = {
        'ASVP': 0,
        'S00': 1,
        'S01': 2,
        'S10': 3,
        'S11': 4,
        'S02': 5,
        'S12': 6,
        'S22': 7,
    }

    export_extensions = {
        'ASVP': "asvp",
        'PRO': "pro",
        'VEL': "vel",
        'HIPS': "svp",
        'IXBLUE': "txt",
        'UNB': "unb",
        'ELAC': "sva",
        'CSV': "csv"
    }

    extension_sources = {
        'WOA09': 0,
        'WOA13': 1,
        'RTOFS': 2
    }

    salinity_sources = {
        'WOA09': 0,
        'WOA13': 1,
        'RTOFS': 2
    }

    temp_sal_sources = {
        'WOA09': 0,
        'WOA13': 1,
        'RTOFS': 2
    }

    sis_server_sources = {
        'WOA09': 0,
        'WOA13': 1,
        'RTOFS': 2
    }

    ssp_directions = {
        'up': 0,
        'down': 1
    }

    inspections_mode = {
        'Zoom': 0,
        'Flag': 1,
        'Unflag': 2,
        'Insert': 3
    }

    data_types = {
        'raw': 0,
        'prc': 1,
        'sis': 2,
        'hyp': 3
    }
