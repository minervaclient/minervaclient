# Minervaclient
### The Minerva Client

`minervac` is a CLI client for Minerva's course registration facilities. The program can be run either **without** a Minerva login to: 

- search for course information,

Or **with** a Minerva login to:  

- display your current course schedule, final exam schedule, or transcript, and register for courses by CRN or course code.  

- Course schedules can be formatted with custom reports, conflicts are detected, and HTML timetables, as well as importable calendar files, can be produced.   

Previously registered courses are recorded and `minervac` will only attempt registration for the remaining courses on each run.
The program is implemented in Python and currently is very hacky. Pull requests welcome. If you have ideas for features or have found a bug, please open an issue.

![Registering for a course](http://i.imgur.com/9FciOtv.png)  
**[More screenshots](#screenshots)**

## See also

* A [departmental or faculty advisor](https://www.mcgill.ca/students/advising/advisordirectory). Link valid as of 6th June, 2018 
* **[Last Known Update April 11th, 2018]** When choosing courses, you may find the [`McGill Enhanced`](https://tinyurl.com/McGillEnhancedFeatures) Chrome extension useful: https://tinyurl.com/McGillEnhancedFeatures
* **[Deprecated/Offline]** If you don't need to make changes to your registration, look into [`Minervabot`](https://github.com/zafarali/minerva-bot) instead. Its source code could be insightful: https://github.com/zafarali/minerva-bot
* **[It's a bit old]** The website [Simplify McGill](https://www.simplifymcgill.com/first-year) is great as an informational resource if you're a first year, good not only for course registration, but also for surviving at McGill in general
* **[Be careful]** If you haven't already found it there's also a [subreddit](https://reddit.com/r/mcgill) for McGill if you have any genearl questions.

# Changelog

### **Unreleased**
Features to be added in the future include:

- (Library) Documentation to make this a proper API for more reusability and other spin-off projects like a full website, maybe Android/iOS apps.
- (CLI) Temporary remembering of Minerva credentials in native terminal/console to prevent the need for repeated logons for every command call.
- (CLI/Library) Create commands to alter settings that config.py contains  
- (CLI/Library) Integrate the scripts from extras/ into the main package, either as part of the library or as a Command Line Tool  
- (CLI) Streamline interactive shell, and provide comprehensive help messages and documentation
- (CLI) Allow username and password entry as arguments in native command line tool

### **Version 1.2.0 - June 25, 2018**

#### New Features:

- An interactive shell feature, so that commands can be run one after the other without repeated Minerva logons.
  - Login credentials are retained for the duration that the shell runs
  - Separate commands for setting/changing login credentials, and for removing credentials/logging out
- Added some helpful login related functions to the library
- Added backwards compatibility for `reg` and `sched` (They still work)
- Added more help messages to the interpreter

#### Fixed Bugs

- Fixed some bugs involving installations via pip
- Changed the subcommands `reg` and `sched` => `register` and `schedule` for human readability
- Fixed login-help bug present in the interpreter


### **Version 1.1.0 - June 22, 2018**

#### New Feature:

- Updated the installation methods, now any form of installation has the same functionality
- Implement an on-screen login when running features that require Minerva login


### **Version 1.0.0 - June 20, 2018**

#### New Features:

- Converted original project by [nicholaspaun](https://github.com/nicholaspaun/minervaclient/) into an installable pip package that will be added to the PyPi system for easier installation
- Added support for automatically installing the dependencies for this project such as `requests`, `beautifulsoup4`, and `urllib5`
- Added an explicit feature, `minervac search` in the command line app, for querying Minerva for course information on CRNs, instructors, times, dates, waitlists, and general availability
- the only command that works now is `minervac` which should replace the previous iteration's `mnvc` and `minervaclient`
- Updated the installation methods, but the majority of features only work if installing via build from source.  See [note](https://github.com/auryan898/minervaclient#install-via-pip)

***
### **Version 0.0.0 - September 1, 2017 (nicholaspaun)**

#### Notes:

1.  * You can now view your final exam schedule (`minervac schedule -E`)
2.  * You can now query your transcript (`minervac transcript`)
3.  * A visual timetable feature has been implemented. (-V).
    * Calendar export is now available (vCalendar format only). (-C)
4.  * The command-line interface won't be modified anymore, only extended. Configuration format is still in flux.
    * Displaying course schedule information with custom reports.



## Goals

The goals of this project are to create a simple and high-quality interface for the most-used features of Minerva. The user interface will be designed in accordance with UNIX priciples, thus, `minervac` will be easily programmable. Additionally, `minervac` will clearly explain how it is connecting to Minerva and provide a starting point for other projects that attempt to use the Minerva "API". This project is free and open-source. Forks and projects that use this should try to be open-source as well.

## Installation: Build from Source for Python 2.7

1. Download the source code.
2. `minervac` uses the `requests`, `beautifulsoup4`, and `html5lib` modules for Python.
  * A good way to install them is probably with `pip`: `sudo pip install requests beautifulsoup4 html5lib`
3. Edit `config.py` to setup various settings
4. Run `python setup.py install` or `sudo python setup.py install`
5. You may now run `minervac -h` for help information.  This just works for Unix/Linux but it's iffy for Windows.  You might need some bash command prompt for it to work on Windows ex. Git Bash, Cygwin

## Install via pip

1. Run `pip install minervaclient` or `sudo pip install minervaclient`
2. Use `minervac -h` to get help information.  
NOTE: At the time of this writing, all features of the application should work, now that login occurs everytime the application is run

## Usage

It's way simpler than actually using Minerva!

**NOTE:** Any `minervaclient` or `mnvc` command should be replaced with `minervac` in this new version!

* **Interactive Shell:** `minervac shell`
  * commands should involve using `search`, `register

* **Course Information Search:** `minervac search`
  * To retrieve the information from all the sections of a course: `minervac search -t 201809 COMP-202 MATH-133` (Fall 2018)
  * To retrieve the information from just one section: `minervac search -t 201901 POLI-200-002` (Winter 2019)
  * To retrieve just availability from classes: `minervac search -A -t 201805 CCOM-206 FRSL-100-001 MATH-133-018` (Summer 2018)
  * To retrieve just Lectures: `minervac search -L -t 201809 COMP-202`
  * To retrieve just Tutorials: `minervac search -T -t 201809 COMP-202`
  * **NOTE:** Minerva Credentials are not required for this feature and therefore is the most secure in the sense you don't expose your passwords to any hackers or children that find their way onto your computer...
  * **ALSO NOTE:** Waitlist/Availability information can get kinda weird so if it says 0/0 it's probably completely full but check Minerva for these weird things.

* **Registration:** `minervac register`
    * To register for a set of courses: `minervac register -t FALL2016 COMP-251-001 MATH-240-001`
    * To register by CRN (faster): `minervac register -t 2016-FALL 814 30302 30`
    * To save previously-registered courses and only register for what remains: `minervac register -j compstuff -t 2016-FALL COMP-273-002 COMP-396-001`
    * **NOTE:** An option to search without logging in is provided. However, only waitlist information can be determined in this way, and its quality may be poor.
* **Scheduling:** `minervac schedule`
    * To display your schedule: `minervac schedule -t WINTER2017`
    * To display more details (`-l`), or less (`-s`): `minervac schedule -lt SUMMER-2017` or `minervac schedule -st 2016WINTER-SUP`
    * To use a custom report (edit `config.py`): `minervac schedule -t WINTER2017 -r magicreport`
    * To export your timetable to a HTML file: `minervac schedule -t 2016SUMMER -V > ~/summer-schedule.html`
        * Edit `config.py` to change the way courses are formatted and `sched_timetable.css` to adjust the styling.
        * **Hint:** Click on a building name to get directions. Hover over courses to see an explanation of the color code.
    * To export your course schedule to an iCalendar file: `minervac schedule -Ct 2017-WINTER > mcgill-winter-2017.ics`
        * You can also export your final exam schedule, like this: `minervac schedule -ECt FALL2016 > mcgill-fall-2016-finals.ics`.
        * The resulting file can be imported into your favorite calendar application (Google Calendar, and the Mac OS X Calendar work.)
        * This format may also be called ICS or vCalendar.
    * To display your final exam schedule: `minervac schedule -t FALL2016 -E`
* **Transcripts:** `minervac transcript`
    * To display your transcript: `minervac transcript`
    * The term argument is optional, and more than one term can be specified: `minervac transcript -t FALL2016,2017-SUMMER`
    * Reports (`-r`) and the long (`-l`) and short (`-s`) shortcuts can be used. (See *Scheduling* above.)
    * To display only your program information (`-S`) and GPA (`-C`): `minervac transcript -SC`
    * To display some miscellaneous transcript information as well (`-P`): `minervac transcript -P`
* For a full description of available options: `minervac -h`
* A few useful extra scripts are included in the `extras/` folder:
    * **Note**: These tools are more experimental than `minervac` itself and might not work so well.
    * `grablrs.py`: Downloads LRS lecture recordings.
    * `transcript-monitor.sh`: Allows you to monitor your unofficial transcript for new grades.


## Scheduling registration

* Put it in your `crontab`. This way, the `minervac` will automatically be run at the time interval you choose, and you will receive an email indicating the status of your course registration job.
    * If you don't have `cron`, you may need to write a long-running loop or use your OS' job scheduling facility. Oh, and by the way, your OS sucks.
* An example crontab line: `00     *       *       *       *       minervac -dj compstuff -t 2016FALL 814 20620 33`
.  
* Some ideas:
    * Set the `MAILTO` option to your email address, or pipe the output to `mail`.
    * You can receive this information as a SMS text message. Look up the email-to-SMS gateway for your cellular carrier. For example, `MAILTO=2505551234@msg.telus.com`

## Further development

* Displaying degree evaluation reports.
* **Won't implement:** While it would be trivial to support dropping courses, I am worried that this may mess up people's schedules as Minerva does not perform truly atomic transactions. Furthermore, it may mess up my own schedule and so I don't want to test it. If you're braver than I am, please send me a pull request.

Extra Features to look into:

* Support output formatters and more control over what this program prints.
* Allow querying for courses from the CLI, and use a SQL database to allow for fancy queries.
* Integrate the course selection satisfiability solver to recommend what you can register for.
* Prerequisite/Corequisite Information
* Mercury Course Evaluations
* Link to course syllabuses
* Program Outlines for different Majors/Minors

## WARNING

1. You are solely responsible for deciding if `minervac` is compliant with McGill's policies, and if you want to assume this risk.
    * Start reading here: [McGill Policy on the Responsible Use of IT Resources](http://www.mcgill.ca/secretariat/files/secretariat/responsible-use-of-mcgill-it-policy-on-the.pdf), but there are most definitely more policies that may be applicable to this program and its use.
2. `minervac` might mess up your course schedule in a very bad sort of way.
3. The final exam data might be unpleasantly wrong, as it is generated from a <s>messed up</s><ins>pretty high-quality</ins> PDF. **Progress at McGill!**

4. `minervac` might suddenly stop working if Minerva is changed.
5. Minerva is a horrible, horrible system and trying to extend this program may lead to a horrible headache.
6. This program was badly written, in a rush, and might have some serious design flaws.
7. May give CS hipsters a headache.


## Applicability outside McGill

Minerva is a Banner installation (Release 8.7, to be precise), so you may be able to adapt the program to work for your university or college. Try to edit `minerva_common.py` with the correct URL to your student information system. A quick way to check if you've got Banner is to Google for "bwckgens" and your institution's name.

## Screenshots

<a href="http://i.imgur.com/J97ekip.png"><img src="http://i.imgur.com/J97ekip.png" width="80%"></a> <a href="http://i.imgur.com/kQfGPnb.png"><img src="http://i.imgur.com/kQfGPnb.png" width="80%"></a>
