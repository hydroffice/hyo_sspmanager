from __future__ import absolute_import, division, print_function  # unicode_literalsimport osimport sysfrom setuptools import setupfrom setuptools import find_packagesfrom setuptools.command.test import test as test_commandhere = os.path.abspath(os.path.dirname(__file__))def is_windows():    """ Check if the current OS is Windows """    return (sys.platform == 'win32') or (os.name is "nt")def txt_read(*paths):    """Build a file path from *paths* and return the textual contents."""    with open(os.path.join(here, *paths), 'r') as f:        return f.read()# ---------------------------------------------------------------------------#                      Populate dictionary with settings# ---------------------------------------------------------------------------if 'bdist_wininst' in sys.argv:    if len(sys.argv) > 2 and ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):        print("Error: bdist_wininst must be run alone. Exiting.")        sys.exit(1)# Create a dict with the basic information# This dict is eventually passed to setup after additional keys are added.setup_args = dict()setup_args['name'] = 'hydroffice ssp'setup_args['version'] = '0.2.0'setup_args['url'] = 'https://bitbucket.org/gmasetti/hyo_ssp/'setup_args['license'] = 'BSD license'setup_args['author'] = 'Giuseppe Masetti (CCOM,UNH); Brian R. Calder (CCOM, UNH); Matthew Wilson (NOAA, OCS)'setup_args['author_email'] = 'gmasetti@ccom.unh.edu; brc@ccom.unh.edu; matt.wilson@noaa.gov'## descriptive stuff#description = 'Sound speed profile library and tools.'setup_args['description'] = descriptionif 'bdist_wininst' in sys.argv:    setup_args['long_description'] = descriptionelse:    setup_args['long_description'] = (txt_read('README.rst') + '\n\n\"\"\"\"\"\"\"\n\n' +                                      txt_read('HISTORY.rst') + '\n\n\"\"\"\"\"\"\"\n\n' +                                      txt_read('AUTHORS.rst') + '\n\n\"\"\"\"\"\"\"\n\n' +                                      txt_read(os.path.join('docs', 'how_to_contribute.rst')) +                                      '\n\n\"\"\"\"\"\"\"\n\n' + txt_read(os.path.join('docs', 'banner.rst')))setup_args['classifiers'] = \    [  # https://pypi.python.org/pypi?%3Aaction=list_classifiers        'Development Status :: 1 - Planning',        'Intended Audience :: Science/Research',        'Natural Language :: English',        'License :: OSI Approved :: BSD License',        'Operating System :: OS Independent',        'Programming Language :: Python',        'Programming Language :: Python :: 2',        'Programming Language :: Python :: 2.7',        'Programming Language :: Python :: 3',        'Programming Language :: Python :: 3.4',        'Topic :: Scientific/Engineering :: GIS',        'Topic :: Office/Business :: Office Suites',    ]setup_args['keywords'] = "hydrography ocean mapping survey ssp"## code stuff## requirementssetup_args['setup_requires'] =\    [        "setuptools",        "wheel",    ]setup_args['install_requires'] =\    [        "hydroffice.ssp",        # "wxpython",    ]# hydroffice namespace, packages and other filessetup_args['namespace_packages'] = ['hydroffice']setup_args['packages'] = find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "*.test*",                                                ])setup_args['package_data'] =\    {        '':        [            '*.png', '*.ico',            'config.ini',            'docs/*.pdf',        ],    }setup_args['data_files'] = []setup_args['test_suite'] = "tests"setup_args['entry_points'] =\    {        'gui_scripts':        [            #'ssp_gui = hydroffice.ssp.gui.hyo_gui:gui',            'SSP_gui = hydroffice.ssp.oldgui.gui:gui',        ],    }setup_args['options'] = \    {        "bdist_wininst":        {            "bitmap": "hydroffice/ssp/gui/media/hydroffice_wininst.bmp",        }    }# ---------------------------------------------------------------------------#                            Do the actual setup now# ---------------------------------------------------------------------------# print(" >> %s" % setup_args['packages'])setup(**setup_args)