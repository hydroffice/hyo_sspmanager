********
In brief
********

The SSP hydro-package has been developing with the aim to merge together functionalities present in several
applications that process sound speed profiles (SSP) for underwater acoustic systems.

The initial core functionalities come from SVP Editor, an application originally developed at the `Center for
Coastal and Ocean Mapping (CCOM, UNH) <http://ccom.unh.edu/>`_ by Jonathan Beaudoin (`Multibeam Advisory Committee
<http://mac.unols.org/>`_)
under the NSF grant 1150574, to provide pre-processing tools to help bridge the gap between
sound speed profiling instrumentation and multibeam echosounder acquisition systems.

In the conversion from this original implementation to the current hydro-package several improvements have been
introduced to enhance code maintainability, to make it available in the Pydro environment, as well as to also
to support Python 3 (from the original Python 2 only implementation) and to store the collected data for further
processing and analysis.


Operation modes
===============

Currently, the hydro-package can operate in two mutually exclusive operation modes:

1.	*Operator Mode*
2.	*Server Mode*

The :ref:`operator_mode` represents the primary mode, and it is used to convert data from different source formats,
to graphically edit them, and to export/send the resulting profiles for use by underwater acoustic systems.
Optional steps are the augmentation with measurements from a reference cast (to either improve salinity modeling
or extrapolate the cast to the required depth), either manually specifiying a loaded profile as reference cast,
or deriving the reference from oceanographic models (currently, WOA09 and RTOFS) as described
in :ref:`app_a_oceanographic_atlases`.

The :ref:`server_mode` was developed to deliver WOA/RTOFS-derived synthetic SSPs to one or more network clients in
a continuous manner, enabling opportunistic mapping while underway. Given the uncertainty of such an approach,
this mode is expected to only be used in transit, capturing the current position and using it as input to lookup
into the selected oceanographic model.


Currently implemented features
==============================

* Import of several commonly used sensor/file formats:

  * Castaway (.csv)
  * Digibar Pro (.txt), and S (.csv)
  * Idronaut (.txt)
  * Seabird (.cnv)
  * XBT, XSV, and XCTD Sippican (.EDF)
  * XBT Turo (.nc)
  * University of New Brunswick (.unb)
  * Valeport Midas (.000), MiniSVP (.txt), and Monitor (.000),

* Network reception of data from:

  * Sippican systems
  * Moving Vessel Profiler (MVP) systems

* Data visualization and interactive graphical inspection (e.g., outlier removal, point additions) of sound speed, temperature and salinity profiles

* Use of the World Ocean Atlas of 2009 (WOA09) and Real-Time Ocean Forecast System (RTOFS) for tasks such as:

  * Salinity augmentation for Sippican XBT probes
  * Temperature/salinity augmentation for Sippican XSV probes and SVP sensors
  * Vertical extrapolation of measured profiles
  * Creation of synthetic sound speed profiles from the model of choice

* Augmentation of sound speed profile surface layer with measured surface sound speed (from Kongsberg SIS only)

* Designation of a reference profile, for example from a deep CTD, for use in tasks such as:

  * Salinity augmentation for Sippican XBT probes
  * Temperature/salinity augmentation for Sippican XSV probes and SVP sensors
  * Vertical extrapolation of measured profiles

* Export of several file formats:

  * Caris (.svp) (V2, multiple casts supported)
  * Comma separated values (.csv)
  * Elac Hydrostar (.sva)
  * Hypack (.vel)
  * IXBLUE (.txt)
  * Kongsberg Maritime (.asvp)
  * Sonardyne (.pro)
  * University of New Brunswick (.unb)

* Network transmission of processed casts to data acquisition systems (see :ref:`app_b_connection_settings`):

  * Kongsberg Maritime SIS
  * QPS QINSy
  * Reson PDS2000
  * Hypack

* Persistent storage of collected SSP data
