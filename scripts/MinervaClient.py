from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library # TODO: why future import standard_library shows error on pylinter (py3)
standard_library.install_aliases()
from builtins import str
from builtins import input
from builtins import range
from builtins import object

class MinervaClient(object):
    def __init__(self):
        print("Hello")
    @staticmethod
    def ecal_search():
        """Retrieves courses' information from McGill's ECalendar.  """
        pass
    @staticmethod
    def pub_search(parameter_list):
        """Retrieves information about a course from Minerva without requiring login
        credentials.  Useful for obtaining information about the course such as
        CRNs, Sections, Section Types, Intructors, Times, or Locations.  Not 
        good for retrieving realtime waitlist/seat information. use 
        MinervaClient.auth_search for retrieving up-to-date information."""
        pass
    def auth_search(self):
        """Retrieves information about a course from Minerva, but requiring login
        credentials.  Useful for obtaining information about the course such as
        CRNs, Sections, Section Types, Intructors, Times, or Locations.  This is
        good for retrieving realtime waitlist/seat information unlike pub_search."""
        raise NotImplementedError
    def transcript(self):
        """Retrieves student's transcript information from Minerva."""
        raise NotImplementedError
    def schedule(self):
        """Retrieves student's schedule information from Minerva."""
        raise NotImplementedError
    def register(self):
        """Attempts to register the user into a course through Minerva, given a 
        CRN or Course Code."""
        raise NotImplementedError

class MinervaState(object):
    register,wait,closed,possible,unknown,wait_places_remaining,full,full_places_remaining,only_waitlist_known = list(range(9))
class MinervaError(object):
    reg_ok,reg_fail,reg_wait,course_none,course_not_found,user_error,net_error,require_unsatisfiable = list(range(8))

import config
# from . import config
import requests,sys
import datetime
import getpass
from datetime import datetime as dt
import unicodedata
import json

try:
    import keyring as local_credentials
except ImportError:
    # from . import credentials as local_credentials
    print("Error must install 'keyring' for this feature")

class MinervaCommon(object):
    iso_date = {
        'date': '%Y-%m-%d',
        'time': '%H:%M',
        'full': '%Y%m%dT%H%M%S'
    }
    minerva_date = {
        'date': '%b %d, %Y',
        'time': '%I:%M %p',
        'full': '%b %d, %Y %I:%M %p'
    }
    def __init__(self):
        # self.username=""
        # self.password=""
        self.sid=""
        self.pin=""
        self.cookie_data = {}
        self.referer = ""
        self.session = requests.Session()
        self.verbose = False

    def _minerva_get(self, func):
        """A GET request to minerva that accepts a string: the GET request arguments.
        
        """
        if self.verbose:
            sys.stderr.write("? " + func + "\n")

        # global referer
        url = "https://horizon.mcgill.ca/pban1/" + func
        r = self.session.get(url,cookies = self.cookie_data, headers={'Referer': self.referer})
        self.referer = url
        return r
    def _minerva_post(self, func, req):
        """A POST request to minerva that accepts a string for URL arguments and the data for the POST request.

        """
        if self.verbose:
            sys.stderr.write("> " + func + "\n")

        # global referer
        url = "https://horizon.mcgill.ca/pban1/" + func
        r = self.session.post(url,data = req,cookies = self.cookie_data,headers = {'Referer': self.referer})
        self.referer = url
        return r
    def _minerva_login_request(self):
        """Login http request is sent for the user, utilizing the credentials stored
        for the sid(minerva only) and pin(minerva only)
        """
        self._minerva_get("twbkwbis.P_WWWLogin")
        self._minerva_post("twbkwbis.P_ValLogin",{'sid': self.sid, 'PIN': self.pin})
        self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_MainMnu")
    def _minerva_reg_menu(self):
        self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_StuMainMnu")
        self._minerva_get('twbkwbis.P_GenMenu?name=bmenu.P_RegMnu&param_name=SRCH_MODE&param_val=NON_NT')
    def _minerva_records_menu(self):
        self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_StuMainMnu")
        self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_AdminMnu")
    
    def set_email_credentials(self):
        """Sets the values for the username and password (from mcgill email)
        """
        self.sid = sid
        self.pin = pin
        local_credentials.set_password('minervaclient_username','minerva',str(sid))
        local_credentials.set_password('minervalcient_password','minerva',str(pin))
    def set_minerva_credentials(self, sid="",pin=""):
        """Sets the values for the sid and pin (for minerva only)
        """
        self.sid = sid
        self.pin = pin
        local_credentials.set_password('minervaclient_sid','minerva',str(sid))
        local_credentials.set_password('minervalcient_pin','minerva',str(pin))
    def load_email_credentials(self):
        """Retrieves the computer stored values for the username and password 
        (from mcgill email)"""
        sid = local_credentials.get_password('minervaclient_sid','minerva')
        pin = local_credentials.get_password('minervalcient_pin','minerva')
        if (sid is not None and pin is not None):
            self.sid = sid
            self.pin = pin
        else: # When there are no stored credentials?
            self.sid = ""
            self.pin = ""
    def load_sid_credentials(self):
        """Retrieves the computer stored values for the sid and pin 
        (for minerva only)"""
        sid = local_credentials.get_password('minervaclient_username','minerva')
        pin = local_credentials.get_password('minervalcient_password','minerva')
        if (sid is not None and pin is not None):
            self.sid = sid
            self.pin = pin
        else: # When there are no stored credentials?
            self.sid = ""
            self.pin = ""
    def del_email_credentials(self):
        """Removes the computer stored values for the username and password 
        (from mcgill email)"""
        try:
            local_credentials.delete_password('minervaclient_username','minerva')
            local_credentials.delete_password('minervalcient_password','minerva')
            return True
        except local_credentials.errors.PasswordDeleteError:
            # print "Minerva user is already logged out"
            print("Minerva credentials do not exist")
            return False
    def del_sid_credentials(self):
        """Removes the computer stored values for the username and password 
        (from mcgill email)"""
        try:
            local_credentials.delete_password('minervaclient_sid','minerva')
            local_credentials.delete_password('minervalcient_pin','minerva')
            return True
        except local_credentials.errors.PasswordDeleteError:
            # print "Minerva user is already logged out"
            print("Minerva credentials do not exist")
            return False
    def initial_login(self):
        """A single method to handle set the initial values for the sid and 
        pin, maybe based on computer stored values, given parameters, or 
        user input"""
        pass
    def verify_sid_credentials(self):
        """Verifies that the instance values for sid and pin are valid values
        
        for the pin:
        Exactly 6 characters
        At least one number and one letter (lower case only)
        Must not contain the same character three or more times
        No special or accented characters (e.g. &, *, $)
        
        """
        is_sid_bad = not str(self.sid).isdigit() or len(str(self.sid)) != 9
        is_pin_bad = len(self.pin) != 6 or not (self.pin.islower() and self.pin.isalnum())
        for char in self.pin: # no character repeatedt least athrice
            if self.pin.count(char) >= 3:
                is_pin_bad = False
        if bad_sid and bad_pin:
            sys.stderr.write('SID must be a 9 digit number ID and PIN must be 6 characters long')
        if bad_sid:
            sys.stderr.write('SID must be a 9 digit number ID')
        if bad_pin:    
            sys.stderr.write('PIN must be 6 characters long')
        return not is_sid_bad and not is_pin_bad
    def verify_email_credentials(self):
        """Verifies that the instance values for username (mcgill email) and 
        password are valid values
        """
        is_sid_bad = not str(self.sid).isdigit() or len(str(self.sid)) != 9
        is_pin_bad = len(self.pin) != 6 or not (self.pin.islower() and self.pin.isalnum())
        for char in self.pin: # no character repeatedt least athrice
            if self.pin.count(char) >= 3:
                is_pin_bad = False
        if bad_sid and bad_pin:
            sys.stderr.write('Email must be a valid McGill Email')
        return not is_sid_bad and not is_pin_bad


    @staticmethod
    def get_term_code(term):
        """Converts different variations of term codes into the yyyymm format for HTTP requests
        acceptable codes include:  FALL09, 2016-FALL, SUMMER-2017, 2016SUMMER, 2017-WINTER, 201809, 201701
        """
        if len(term) < 6: # in case term too small to cut
            return term

        part_codes = {'FALL': '09', 'FALL-SUP': '10', 'WINTER': '01', 'WINTER-SUP': '02', 'SUMMER': '05', 'SUMMER-SUP': '06'}
        if term == "PREVIOUSEDUCATION":
            return '000000' # Sort first
        elif term.isdigit(): # Term code 201809...
            return term
        elif term[0].isdigit(): #Year first, 2016-FALL, 2016SUMMER
            year = term[0:4]  # First four digits
            if term[4] == '-': # get season after dash (if exists)
                part = term[5:] 
            else:
                part = term[4:]
            part = part_codes[part.upper()] # convert season to number

        else:
            year = term[-4:]
            if term[-5] == '-':
                part = term[:-5]
            else:
                part = term[:-4]
            
            part = part_codes[part.upper()]

        return year + part
    @staticmethod
    def get_status_code(status, short = False):
        """Converts status code phrase to a simplified code if it isn't already simplified.
        Examples: 'Registered' => 'R' or 'Web Drop' => 'DROP'
        """
        if short:
            status_codes = {'Registered': 'R','Web Registered': 'R','(Add(ed) to Waitlist)': 'WL', 'Web Drop': 'DROP','Web Withdrawn Course': 'W'}
        else:
            status_codes = {'Registered': 'R','Web Registered': 'RW','(Add(ed) to Waitlist)': 'LW', 'Web Drop': 'DW', 'Web Withdrawn Course': 'WW'}

        return status_codes[status] if status in status_codes else status
    @staticmethod
    def get_type_abbrev(ctype):
        """Converts course type to an abbreviation"""
        ctypes = {'Lecture': 'Lec','Tutorial': 'Tut','Conference': 'Conf','Seminar': 'Sem','Laboratory': 'Lab','Student Services Prep Activity': 'StudSrvcs'}
        if ctype in ctypes:
            return ctypes[ctype]
        else:
            return ctype
    @staticmethod
    def get_bldg_abbrev(location):
        """Doesn't really do much. Just tries a few tricks to shorten the names of buildings."""
        subs = {
            'Building': '', 'Hall': '', 'Pavilion': '','House': '','Centre': '', 'Complex': '',
            'Library': 'Lib.', 'Laboratory': 'Lab.',
            'Biology': 'Bio.', 'Chemistry': 'Chem.',' Physics': 'Phys.', 'Engineering': 'Eng.', 'Anatomy': 'Anat.', 'Dentistry': 'Dent.', 'Medical': 'Med.', 'Life Sciences': 'Life Sc.'
        }
    @staticmethod
    def get_minerva_weekdays(weekend = False):
        """ Returns the minerva weekdays, and accepts an optional boolean paramter for weekends included 
        Minerva days include 'M'onday 'T'uesday 'W'ednesday Thu'R'sday 'F'riday 'S'aturday and  S'U'nday """
        if weekend:
            return ['M','T','W','R','F','S','U']
        else:
            return ['M','T','W','R','F']
    @staticmethod
    def get_real_weekday(minerva_day):
        """Convert from Minerva day to real day name
        Minerva days include 'M'onday 'T'uesday 'W'ednesday Thu'R'sday 'F'riday 'S'aturday and  S'U'nday """
        days = {'M': 'Monday','T':'Tuesday','W': 'Wednesday','R': 'Thursday','F': 'Friday','S': 'Saturday','U': 'Sunday'}
        return days[minerva_day]
    @staticmethod
    def get_ics_weekday(minerva_day):
        """Minerva days include 'M'onday 'T'uesday 'W'ednesday Thu'R'sday 'F'riday 'S'aturday and  S'U'nday """
        days = {'M': 'MO','T': 'TU','W': 'WE','R': 'TH','F': 'FR','S': 'SA', 'U': 'SU'}
        return days[minerva_day]
    @staticmethod
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
    @staticmethod
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
    @staticmethod
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
    @staticmethod
    def lg_to_gpa(letter_grade):
        """Convert letter grade to GPA score
        Example: B+ => 3.3"""
        return {'A': '4.0','A-': '3.7','B+': '3.3', 'B': '3.0', 'B-': '2.7', 'C+': '2.3', 'C': '2.0','D': '1.0','F': '0'}[letter_grade]
    @staticmethod
    def dequebecify(input):
        """ Normalizes text to pure english
        From <http://stackoverflow.com/questions/517923>
        This function only transliterates French diacritics.
        If you need to separate Quebec from Canada, try:
        roc,qc = canada.sovereignty_referendum('quebec')"""

        return ''.join(c for c in unicodedata.normalize('NFD', input) if unicodedata.category(c) != 'Mn')
    @staticmethod
    def get_bldg_name(code):
        """Converts building short code into building name, if not in database, return the argument passed.
        If we don't know, just stick with what we have.
        Example: SADB => Strathcona Anatomy & Dentistry Building | Hello => Hello"""
        try:
            f = open('buildings.json')
        except Exception:
            return code
        buildings = json.loads(f.read())
        if code in buildings:
            return buildings[code]['name']
        else:
            return code #If we don't know, just stick with what we have
    
    @staticmethod
    def _minervac_sanitize(text):
        """Encodes given text to ASCII"""
        return text.encode('ascii','ignore')
    @staticmethod
    def text_sanitize(text):
        """Encodes given text to ASCII"""
        return text.encode('ascii','ignore')

import requests,urllib.request,urllib.parse,urllib.error,io,csv,sys

class PubSearch(object):
    """Contains the functions used to perform a course search on Minerva"""
    def search(parameter_list):
        """Retrieves information on courses """
        pass
    def _build_request(parameter_list):
        """Helper function that builds the POST request that would pull 
        relevant course information from Minerva. Based on the given 
        term code (201809) and course codes (COMP-202 or COMP-202-000 
        or just COMP)
            Example: build_request('201809', ['COMP-202', 'FRSL'])
        """
        pass
    def _post_search(parameter_list):
        """ Helper function that performs the POST request to retrieve 
        the data and returns a logical python dictionary based on the request"""
        pass
    def _parse_search(parameter_list):
        """ Converts the HTTP request data from Minerva into a logical 
        format in a python dictionary.
        """
        # stream = io.StringIO(text.encode('ascii','ignore'))
        # print(type(text))
        pass
    
