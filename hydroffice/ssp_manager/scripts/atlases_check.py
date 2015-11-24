from __future__ import absolute_import, division, print_function, unicode_literals

import sys
from builtins import input
from ..atlases.woa09checker import Woa09Checker

if Woa09Checker.is_present():
    print("WOA09 present")
    sys.exit(0)

ans = input("download it (y/n)?  ")
ans.lower()
if ans == "y" or ans == "yes":
    print("downloading")
    chk = Woa09Checker(verbose=True)
    if chk.present:
        print("downloaded")
    else:
        print("issues")
else:
    print("exiting")





