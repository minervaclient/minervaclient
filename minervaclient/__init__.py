from . import reg, sched, exams, transcript, minerva_common, config, pub_search, mercury_search, ecalendar_search

__version__ = '0.0.0'
""" September 1, 2017 (nicholaspaun)
Notes:
1.  * You can now view your final exam schedule (`minervac sched -E`)
2.  * You can now query your transcript (`minervac transcript`)
3.  * A visual timetable feature has been implemented. (-V).
    * Calendar export is now available (vCalendar format only). (-C)
4.  * The command-line interface won't be modified anymore, only extended. Configuration format is still in flux.
    * Displaying course schedule information with custom reports.

"""

__version__ = '1.0.0'
""" June 20, 2018
New Features:

- Converted original project by [nicholaspaun](https://github.com/nicholaspaun/minervaclient/) into 
an installable pip package that will be added to the PyPi system for easier installation

- Added support for automatically installing the dependencies for this project such as `requests`, 
`beautifulsoup4`, and `urllib5`

- Added an explicit feature, `minervac search` in the command line app, for querying Minerva for 
course information on CRNs, instructors, times, dates, waitlists, and general availability

- The only command that works now is `minervac` which should replace the previous iteration's `mnvc` 
and `minervaclient`

- Updated the installation methods, but the majority of features only work if installing via build 
from source.  See [note](https://github.com/auryan898/minervaclient#install-via-pip)

"""

__version__ = '1.1.0'
""" Patch 1.1.0 - June 22, 2018
New Fixes:
- Now any form of installation has the same functionality
- Implement an on-screen login when running features that require Minerva login

"""

__version__ = '1.2.0'
""" Version 1.2.0 - June 25, 2018
New Features:

- An interactive shell feature, so that commands can be run one after the other without repeated Minerva logons.
  - Login credentials are retained for the duration that the shell runs
  - Separate commands for setting/changing login credentials, and for removing credentials/logging out
- Added some helpful login related functions to the library
- Added backwards compatibility for reg and sched (They still work)
- Added more help messages to the interpreter

Fixed Bugs:

- Fixed some bugs involving installations via pip
- Changed the subcommands reg and sched => register and schedule for human readability
- Fixed login-help bug in the interpreter
"""

__version__ = '1.3.0'
""" Version 1.3.0 - July 17, 2018

New Features:

- eCalendar scraping added to library
  - Scrape Course eCalendar page for Overview, Title, Notes, Faculty, Instructors, Terms
  - Requisite Courses Extraction (WIP)
  - Tool to convert typical term code to an eCalendar school year code
  - Includes tool to print the information of the all the available courses of a given subject
- Remembering of Minerva credentials in native terminal/console. Implemented `keyring` module for secure credentials storage in system keyring.
  - Made usage of 'keyring' an extra that will be installable by pip via `pip install minervaclient[cli_features]`
- Minerva search function now accepts course codes case insensitive (always converts to uppercase)
- Mercury Evaluation scraping tools added to library
  - Search for Instructors based on either a given name or ID number, can be partial, and obtain full name and ID number
  - Obtain the list of evaluation reports on a specific instructor, or on a specific course
  - Obtain the information from an evaluation report given a report ID number (ID is found in reports listings, and is temporary)
- The original minervac script has been moved to the `__main__` module for cross-platform compatibility
- main function in `__main__` module now accepts arguments in its parameters, that overrides its usage as a command line tool, and is now scriptable
- `html5lib` is now no longer a required package, however its usage is highly recommended for full functionality
- Performed the `futurize` script on package, overhauled all the code to be compatible with Python 3, preliminary tests show that it works in both now (Python 2.7 and Python 3.5+).

Bug Fixes:

- Fixed visual schedule creation missing file error
- Fixed inputting string into keyring data storing
- Several indentation inconsistencies were corrected
- Public Search is now case insensitive to course codes

"""
