from __future__ import absolute_import, division, print_function, unicode_literals

from ..ssp_aux import SspAux
from ..ssp_dicts import Dicts
import numpy as np


if __name__ == '__main__':
    test0_num_samples = 18
    test0 = np.zeros((len(Dicts.idx.keys()), test0_num_samples, ))

    test0[Dicts.idx['flag'], 2:12] = 1
    print("partially flagged:\n%s\nsize: %s" % (test0, test0.shape[1]))

    test0 = SspAux.purge_flagged_samples(test0)
    print("purged:\n%s\nsize: %s\n" % (test0, test0.shape[1]))

    test0[Dicts.idx['flag'], :] = 1
    print("fully flagged:\n%s\nsize: %s" % (test0, test0.shape[1]))

    test0 = SspAux.purge_flagged_samples(test0)
    print("purged:\n%s\nsize: %s" % (test0, test0.shape[1]))