HydrOffice SSP
===========

![logo](https://bitbucket.org/ccomjhc/hyo_ssp/raw/tip/hydroffice/ssp/gui/media/favicon.png)

The `hyo_ssp` package can be used to deal with sound speed profiles.

About HydrOffice
-----------------------

HydrOffice is a research development environment for ocean mapping. Its aim is to provide a collection of hydro-packages to deal with specific issues in such a field, speeding up both algorithms testing and research-2-operation.

About this hydro-package
-----------------------

This package provides functionalities to deal with sound speed profiles.

Freezing
-----------------------

### Pyinstaller

* `pyinstaller --clean -y SSP.1file.spec`
* `pyinstaller --clean -y SSP.1folder.spec`

Useful Mercurial commands
-----------------------

### Merge a branch to default

* `hg update default`
* `hg merge 1.0.0`
* `hg commit -m"Merged 1.0.2 branch with default" -ugiumas`
* `hg update 1.0.0`
* `hg commit -m"Close 1.0.2 branch" -ugiumas --close-branch`

### Open a new branch

* `hg update default`
* `hg branch 1.0.1`
* `hg commit -m"Created 1.0.3 branch" -ugiumas`
    
Other info
----------

* Bitbucket: [https://bitbucket.org/ccomjhc/hyo_ssp](https://bitbucket.org/ccomjhc/hyo_ssp)
* Project page: [http://ccom.unh.edu/project/hydroffice](http://ccom.unh.edu/project/hydroffice)
* License: BSD-like license (See [COPYING](https://bitbucket.org/ccomjhc/hyo_ssp/raw/tip/COPYING.txt))