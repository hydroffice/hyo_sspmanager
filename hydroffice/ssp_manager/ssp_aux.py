from __future__ import absolute_import, division, print_function, unicode_literals

import logging

log = logging.getLogger(__name__)

from .ssp_dicts import Dicts
from .helper import SspError


class SspAux(object):

    @classmethod
    def purge_flagged_samples(cls, data):
        """ delete the flagged samples (if any) returning only the unflagged samples """

        # isolate the good points
        good_pts = (data[Dicts.idx['flag'], :] == 0)
        return data[:, good_pts]

    @classmethod
    def douglas_peucker_1d(cls, start, end, tolerance, data):
        """
        Recursive implementation
        NB: in this case the flag indicates keep as opposed to the usual case where it indicates reject
        """

        # We always keep end points
        data[Dicts.idx['flag'], start] = 1
        data[Dicts.idx['flag'], end] = 1

        slope = (data[Dicts.idx['speed'], end] - data[Dicts.idx['speed'], start]) / \
                (data[Dicts.idx['depth'], end] - data[Dicts.idx['depth'], start])

        max_dist = 0
        max_ind = 0
        for ind in range(start + 1, end):
            dist = abs(data[Dicts.idx['speed'], start] +
                       slope * (data[Dicts.idx['depth'], ind] - data[Dicts.idx['depth'], start]) -
                       data[Dicts.idx['speed'], ind])

            if dist > max_dist:
                max_dist = dist
                max_ind = ind

        if max_dist <= tolerance:
            return

        else:
            data[Dicts.idx['flag'], max_ind] = 1
            cls.douglas_peucker_1d(start, max_ind, tolerance, data)
            cls.douglas_peucker_1d(max_ind, end, tolerance, data)

    @classmethod
    def thin_ssp(cls, tolerance, data):
        # - 1000 points for: EM2040, EM710, EM302 and EM122;
        # - 570 points for: EM3000, EM3002, EM1002, EM300, EM120
        # TODO: the resulting profile must be less than 30kB

        # pre-purge data from all the flagged samples
        data = cls.purge_flagged_samples(data)

        # call to the recursive algorithm
        cls.douglas_peucker_1d(0, data.shape[1] - 1, tolerance, data)

        # find the points that have survived the thinning
        good_pts = (data[Dicts.idx['flag'], :] == 1)

        # set flag to '1' for all points
        data[Dicts.idx['flag'], :] = 1

        # now unflag the points we want to keep, those that survived thinning
        data[Dicts.idx['flag'], good_pts] = 0

        # return back the data after purging those samples that were tossed out
        return cls.purge_flagged_samples(data)

    @classmethod
    def get_km_prefix(cls, kng_format):
        # Build output string (PDS2000 requires MV as prefix)
        if kng_format == Dicts.kng_formats['S00']:
            output = '$MVS00,00000,'

        elif kng_format == Dicts.kng_formats['S10']:
            output = '$MVS10,00000,'

        elif kng_format == Dicts.kng_formats['S01']:
            output = '$MVS01,00000,'

        elif kng_format == Dicts.kng_formats['S11']:
            output = '$MVS11,00000,'

        elif kng_format == Dicts.kng_formats['S02']:
            output = '$MVS02,00000,'

        elif kng_format == Dicts.kng_formats['S12']:
            output = '$MVS12,00000,'

        elif kng_format == Dicts.kng_formats['ASVP']:
            output = ""

        else:
            raise SspError("unknown kng format: %s" % kng_format)

        return output
