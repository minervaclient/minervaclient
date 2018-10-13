from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str
from builtins import input
from builtins import range
from builtins import object
# minerva_common.py: Common functions and definitions for working with Minerva
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun

from . import config
import requests,sys
import datetime
import getpass
from datetime import datetime as dt

SID=""
PIN=""
cookie_data = {}
referer = ""
s = requests.Session()

def minerva_get(func):
    """A GET request to minerva that accepts a string: the GET request arguments.
    
    """
    if verbose:
        sys.stderr.write("? " + func + "\n")

    global referer
    url = "https://horizon.mcgill.ca/pban1/" + func
    r = s.get(url,cookies = cookie_data, headers={'Referer': referer})
    referer = url
    return r

def minerva_post(func,req):
    """A POST request to minerva that accepts a string for URL arguments and the data for the POST request.
    
    """
    if verbose:
        sys.stderr.write("> " + func + "\n")

    global referer
    url = "https://horizon.mcgill.ca/pban1/" + func
    r = s.post(url,data = req,cookies = cookie_data,headers = {'Referer': referer})
    referer = url
    return r

def verify_login():
    bad_sid = not str(SID).isdigit() or len(str(SID)) != 9
    bad_pin = len(PIN) != 6
    if bad_sid and bad_pin:
        raise ValueError('SID must be a 9 digit number ID and PIN must be 6 characters long')
    if bad_sid:
        raise ValueError('SID must be a 9 digit number ID')
    if bad_pin:    
        raise ValueError('PIN must be 6 characters long')

try:
    import keyring as local_credentials
except ImportError:
    from . import credentials as local_credentials
def localsys_logout():
    """Deletes the values for SID and PIN from the computer you are on, and returns boolean value, whether deletion was successful or not.
    Good for command line tools"""
    try:
        local_credentials.delete_password('minervaclient_sid','minerva')
        local_credentials.delete_password('minervalcient_pin','minerva')
        return True
    except local_credentials.errors.PasswordDeleteError:
        # print "Minerva user is already logged out"
        print("Minerva credentials do not exist")
        return False

def localsys_get_login():
    """Retrieves the login credentials from the computer you are on.
    Good for command line tools"""
    try:
        sid = local_credentials.get_password('minervaclient_sid','minerva')
        pin = local_credentials.get_password('minervalcient_pin','minerva')
        if sid is None or pin is None:
            raise Exception("No credentials detected")
        return (sid, pin)
    except Exception as e:
        print(str(e))
        return ("","")

def localsys_has_login():
    """Checks the computer for the presence of login credentials.
    Good for command line tools"""
    sid = local_credentials.get_password('minervaclient_sid','minerva')
    pin = local_credentials.get_password('minervalcient_pin','minerva')
    return sid is not None and pin is not None

def localsys_prompt_login(sid="",pin="",temporary=False):
    """Prompts user for login credentials that aren't already given via the parameters. 
    Good for command line tools"""
    if sid == "":
        sid = eval(input("Enter your Minerva ID number: "))
    if pin == "":
        pin = getpass.getpass("Enter your PIN number: ")
    if not temporary:
        local_credentials.set_password('minervaclient_sid','minerva',str(sid))
        local_credentials.set_password('minervalcient_pin','minerva',str(pin))
    return sid, pin

def initial_login(sid="", pin="", inConsole=False, reLogin=False, temporary=False):
    """ Set the global values for the Student ID number and Personal Information Number (password) without sending http request to Minerva.
    Throws error if these values are still not given """
    global SID
    global PIN
    # inConsole takes precedence
    if inConsole:
        # check keyring
        if not temporary:
            if localsys_has_login() and not reLogin:
                SID, PIN = localsys_get_login()
            else:
                SID, PIN = localsys_prompt_login(sid=sid,pin=pin, temporary=temporary)
    # check param if not inConsole
    if not inConsole:
        if localsys_has_login(): # get login from local system too
            SID, PIN = localsys_get_login()
        if sid !="":
            SID = sid # sid is isolated so that just this can be set
        if pin !="":
            PIN = pin # pin is isolated so that just this can be set

    # check global
    if not has_login():
        raise ValueError('SID and PIN values must be given at some point.  Run "minerva_common.initial_login(sid,pin)"')

    verify_login()
        
def minerva_logout(inConsole=False):
    """Logout for the user by altering the credentials, the global variables SID and PIN.
    
    """
    global SID
    global PIN
    SID = ""
    PIN = ""
    if inConsole:
        localsys_logout()

def has_login():
    global SID
    global PIN
    return not (SID=="" or PIN=="")

def minerva_login(sid="", pin=""):
    """Login http request is sent for the user, utilizing the credentials from the arguments, sid and pin or from the global variables SID and PIN.
   Throws error if these values are empty strings
    """
    global SID
    global PIN
    if(sid=="" or pin==""):
        if not has_login():
            raise ValueError('SID and PIN values must be given at some point.  Run "minerva_common.initial_login(sid,pin)"')
            return
        sid=SID
        pin=PIN
    else:
        SID=sid 
        PIN=pin
    verify_login()
    
    minerva_get("twbkwbis.P_WWWLogin")
    minerva_post("twbkwbis.P_ValLogin",{'sid': sid, 'PIN': pin})
    minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_MainMnu")

def minerva_reg_menu():
    minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_StuMainMnu")
    minerva_get('twbkwbis.P_GenMenu?name=bmenu.P_RegMnu&param_name=SRCH_MODE&param_val=NON_NT')

def minerva_records_menu():
    minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_StuMainMnu")
    minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_AdminMnu")

class MinervaState(object):
        register,wait,closed,possible,unknown,wait_places_remaining,full,full_places_remaining,only_waitlist_known = list(range(9))
class MinervaError(object):
    reg_ok,reg_fail,reg_wait,course_none,course_not_found,user_error,net_error,require_unsatisfiable = list(range(8))


def get_term_code(term):
    """Converts different variations of term codes into the yyyymm format for HTTP requests
    
    acceptable codes include:  FALL09, 2016-FALL, SUMMER-2017, 2016SUMMER, 2017-WINTER
    """
    part_codes = {'FALL': '09', 'FALL-SUP': '10', 'WINTER': '01', 'WINTER-SUP': '02', 'SUMMER': '05', 'SUMMER-SUP': '06'}
    if term == "PREVIOUSEDUCATION":
        return '000000' # Sort first
    elif term.isdigit(): # Term code
        return term
    elif term[0].isdigit(): #Year first
        year = term[0:4]
        if term[4] == '-':
            part = term[5:]
        else:
            part = term[4:]
        part = part_codes[part.upper()]

    else:
        year = term[-4:]
        if term[-5] == '-':
            part = term[:-5]
        else:
            part = term[:-4]
        
        part = part_codes[part.upper()]

    return year + part

def get_status_code(status,short = False):
    """Converts status code phrase to a simplified code if it isn't already simplified.
    Examples: 'Registered' => 'R' or 'Web Drop' => 'DROP'
    """
    if short:
            status_codes = {'Registered': 'R','Web Registered': 'R','(Add(ed) to Waitlist)': 'WL', 'Web Drop': 'DROP','Web Withdrawn Course': 'W'}
    else:
            status_codes = {'Registered': 'R','Web Registered': 'RW','(Add(ed) to Waitlist)': 'LW', 'Web Drop': 'DW', 'Web Withdrawn Course': 'WW'}

    return status_codes[status] if status in status_codes else status

def get_type_abbrev(ctype):
    """Converts course type to an abbreviation"""
    ctypes = {'Lecture': 'Lec','Tutorial': 'Tut','Conference': 'Conf','Seminar': 'Sem','Laboratory': 'Lab','Student Services Prep Activity': 'StudSrvcs'}
    if ctype in ctypes:
        return ctypes[ctype]
    else:
        return ctype


def get_bldg_abbrev(location):
    """Doesn't really do much. Just tries a few tricks to shorten the names of buildings."""
    subs = {
            'Building': '', 'Hall': '', 'Pavilion': '','House': '','Centre': '', 'Complex': '',
            'Library': 'Lib.', 'Laboratory': 'Lab.',
            'Biology': 'Bio.', 'Chemistry': 'Chem.',' Physics': 'Phys.', 'Engineering': 'Eng.', 'Anatomy': 'Anat.', 'Dentistry': 'Dent.', 'Medical': 'Med.', 'Life Sciences': 'Life Sc.'
    }

    for sub in subs:
        location = location.replace(sub,subs[sub])

    return location

def get_minerva_weekdays(weekend = False):
    """ Returns the minerva weekdays, and accepts an optional boolean paramter for weekends included 
    Minerva days include 'M'onday 'T'uesday 'W'ednesday Thu'R'sday 'F'riday 'S'aturday and  S'U'nday """
    if weekend:
        return ['M','T','W','R','F','S','U']
    else:
        return ['M','T','W','R','F']

def get_real_weekday(minerva_day):
    """Convert from Minerva day to real day name
    Minerva days include 'M'onday 'T'uesday 'W'ednesday Thu'R'sday 'F'riday 'S'aturday and  S'U'nday """
    return get_real_weekday.map[minerva_day]
get_real_weekday.map = {'M': 'Monday','T':'Tuesday','W': 'Wednesday','R': 'Thursday','F': 'Friday','S': 'Saturday','U': 'Sunday'}

def get_ics_weekday(minerva_day):
    """Minerva days include 'M'onday 'T'uesday 'W'ednesday Thu'R'sday 'F'riday 'S'aturday and  S'U'nday """
    return {'M': 'MO','T': 'TU','W': 'WE','R': 'TH','F': 'FR','S': 'SA', 'U': 'SU'}[minerva_day]

def minervac_sanitize(text):
    """Encodes given text to ASCII"""
    return text.encode('ascii','ignore')

def get_degree_abbrev(degree):
    """Replaces long names of degrees to shorter names of those degrees
    
    Example: Bachelor of Science => BSc"""
    subs = {
        'Bachelor of Science': 'BSc',
        'Master of Science': 'MSc',
        'Master of Science, Applied': 'MScA',
        'Bachelor of Arts': 'BA',
        'Master of Arts': 'MA',
        'Bachelor of Arts and Science': 'BAsc',
        'Bachelor of Engineering': 'BEng',
        'Bachelor of Software Engineering': 'BSE',
        'Master of Engineering': 'MEng',
        'Bachelor of Commerce': 'BCom',
        'Licentiate in Music': 'LMus',
        'Bachelor of Music': 'BMus',
        'Master of Music': 'MMus',
        'Bachelor of Education': 'BEd',
        'Master of Education': 'MEd',
        'Bachelor of Theology': 'BTh',
        'Master of Sacred Theology': 'STM',
        'Master of Architecture': 'MArch',
        'Bachelor of Civil Law': 'BCL',
        'Bachelor of Laws': 'LLB',
        'Master of Laws': 'LLM',
        'Bachelor of Social Work': 'BSW',
        'Master of Social Work': 'MSW',
        'Master of Urban Planning': 'MUP',
        'Master of Business Administration': 'MBA',
        'Master of Management': 'MM',
        'Bachelor of Nursing (Integrated)': 'BNI',
        'Doctor of Philosophy': 'PhD',
        'Doctor of Music': 'DMus'
    } #Most of these degrees probably won't work with minervac, but this list may be slightly useful
    for sub in subs:
        degree = degree.replace(sub,subs[sub])
    
    return degree

def get_program_abbrev(program):
    """Abbreviates a program's name
    
    Example: Major Concentration => Major"""
    program = program.replace('Major Concentration','Major').replace('Minor Concentration','Minor') #Who cares?
    majors = []
    minors = []
    other = []

    for line in program.split("\n"):
        if line.startswith("Major"):
            majors.append(line.split("Major ")[1])
        elif line.startswith("Honours"):
                majors.append(line)
        elif line.startswith("Minor"):
            minors.append(line.split("Minor ")[1])
        else:
            other.append(line)

    
    program = ", ".join(majors)
    if minors:
        program += "; Minor " + ", ".join(minors)
    if other:
        program += " [" + ", ".join(other) + "]"

    return program

def get_grade_explanation(grade,normal_grades = False):
    """Converts grade explanation code to logical english
    
    Example HH => To be continued """
    explanation = {
        'HH': 'To be continued',
        'IP': 'In progress',
        'J': 'Absent',
        'K': 'Incomplete',
        'KE': 'Further extension granted',
        'K*': 'Further extension granted',
        'KF': 'Incomplete - Failed',
        'KK': 'Completion requirement waived',
        'L': 'Deferred',
        'LE': 'Deferred - extension granted',
        'L*': 'Deferred - extension granted',
        'NA': 'Grade not yet available',
        '&&': 'Grade not yet available',
        'NE': 'No evaluation',
        'NR': 'No grade reported by the instructor (recorded by the Registrar)',
        'P': 'Pass',
        'Q': 'Course continues in following term',
        'R': 'Course credit',
        'W': 'Permitted to withdraw',
        'WF': 'Withdraw - failing',
        'WL': 'Faculty permission to withdraw from a deferred examination',
        'W--': 'No grade: student withdrew from the University',
        '--': 'No grade: student withdrew from the University',
        'CO': 'Complete [Academic Integrity Tutorial]',
        'IC': 'Incomplete [Academic Integrity Tutorial]'
    }

    normal_explanation = {
        'A': '85 - 100',
        'A-': '80 - 84',
        'B+': '75 - 79',
        'B': '70 - 74',
        'B-': '65 - 69',
        'C+': '60 - 64',
        'C': '55 - 59',
        'D': '50 - 54',
        'F': '0 - 49',
        'S': 'Satisfactory',
        'U': 'Unsatisfactory'
    }

    if normal_grades:
        explanation.update(normal_explanation)

    if grade in explanation:
        return explanation[grade]
    else:
        return ''

def lg_to_gpa(letter_grade):
    """Convert letter grade to GPA score
    Example: B+ => 3.3"""
    return {'A': '4.0','A-': '3.7','B+': '3.3', 'B': '3.0', 'B-': '2.7', 'C+': '2.3', 'C': '2.0','D': '1.0','F': '0'}[letter_grade]

verbose = False
def set_loglevel(set_verbose):
    global verbose
    verbose = set_verbose

def is_verbose():
    global verbose
    return verbose

def dequebecify(input):
    """ Normalizes text to pure english
    From <http://stackoverflow.com/questions/517923>
    This function only transliterates French diacritics.
    If you need to separate Quebec from Canada, try:
    roc,qc = canada.sovereignty_referendum('quebec')"""

    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', input)
            if unicodedata.category(c) != 'Mn')

def fetch_buildings_table():
    """Downloads the information on buildings"""

    repo = config.data_source[0]
    url = repo + "buildings.json"

    if is_verbose():
        print("D", url)

    print("Downloading buildings database.....")

    r  = requests.get(url)
    buildings_json = r.text.encode('UTF-8')
    if r.status_code != 200:
        print("\033[1;31mFailed to download buildings table.")
        sys.exit(1)

    f = open('buildings.json','w')
    f.write(buildings_json)
    f.close()
    return buildings_json


def get_bldg_name(code):
    """Converts building short code into building name, if not in database, return the argument passed.
    If we don't know, just stick with what we have.
    Example: SADB => Strathcona Anatomy & Dentistry Building | Hello => Hello"""
    import json
    try:
        f = open('buildings.json')
    except Exception:
        fetch_buildings_table()
        return get_bldg_name(code)

    buildings = json.loads(f.read())

    if code in buildings:
        return buildings[code]['name']
    else:
        return code #If we don't know, just stick with what we have

class MinervaOutput(object):
    output_string = ""
    output_dict = {}
    def __init__(self, inConsole=False, isJson=False, isCsv=False):
        self.inConsole = inConsole
        self.isJson = isJson
        self.isCsv = isCsv

    def get_content(self):
        """Return the content stored either json, csv, or humean readable format"""
        return self.output_string

    def write(self, data):
        self.output_string += str(data)
        if self.inConsole:
            # if in the console, we're outputting to the sys.stdout
            sys.stdout.write(data)
    
    def print(self, *args, **kwargs):
        """Wrapper for potential usage of print function (py3)"""
        data = " ".join(map(str,args))
        self.output_string += str(data) + "\n"
        if self.inConsole:
            # if in the console, we're printing the output
            print(data, **kwargs)
    def append(self, data):
        """For appending any string data to the output_string"""
        self.output_string += data + '\n'

iso_date  = {
        'date': '%Y-%m-%d',
        'time': '%H:%M',
        'full': '%Y%m%dT%H%M%S'
}

minerva_date = {
        'date': '%b %d, %Y',
        'time': '%I:%M %p',
        'full': '%b %d, %Y %I:%M %p'
}
