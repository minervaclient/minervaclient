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
        self.mnvc = MinervaCommon()
    def login(self, sid="", pin="", inConsole=False, reLogin=False, temporary=False, verbose=None):
        self.mnvc.initial_login(sid=sid, pin=pin, inConsole=inConsole, reLogin=reLogin, temporary=temporary, verbose=verbose)
    @staticmethod
    def ecal_search():
        """Retrieves courses' information from McGill's eCalendar.  """
        pass
    @staticmethod
    def pub_search(term,course_codes,**kwargs):
        """Retrieves information about a course from Minerva without requiring login
        credentials.  Useful for obtaining information about the course such as
        CRNs, Sections, Section Types, Intructors, Times, or Locations.  Not 
        good for retrieving realtime waitlist/seat information. use 
        MinervaClient.auth_search for retrieving up-to-date information."""
        return PubSearch.search(term,course_codes, **kwargs)
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

from keyrings.cryptfile.cryptfile import CryptFileKeyring
kr = CryptFileKeyring()

class MinervaConfig(object):
    def __init__(self):
        self.settings_obj = {}
        self.descriptions = {
            'default':'Determines whether the passwords are set to default',
            'use_stored_credentials':'If value is "email" or "minerva", then use stored credentials regularly. Default: "false"'
        }
        self.defaults_obj = {
            'default':'true',
            'use_stored_credentials':'false'
        }
        self.kr = CryptFileKeyring()
    def __getitem__(self,key):
        return self.settings_obj[key]
    def __setitem__(self,key,value):
        self.settings_obj[key] = value
    def get_settings(self, keyring_pass='', inConsole=False):
        """Loads the settings from the computer's keyring"""
        
        if keyring_pass == '' and inConsole:
            self.kr.keyring_key = getpass.getpass() # only when in the console and no argument already given
        self.kr.keyring_key = keyring_pass

        # check if it's the first time for keys
        if self.kr.get_password('minervaclient_default','minerva') is None:
            self.default_settings()
        for key in self.descriptions.keys():
            self[key] = self.kr.get_password('minervaclient_'+key,'minerva')
    def set_settings(self):
        """Takes the current settings and persists the changes to computer storage"""
        for key, item in self.settings_obj.items():
            self.kr.set_password('minervaclient_'+key,'minerva',item)
    def default_settings(self, inConsole=False):
        """Resets the current settings to original"""
        for key, item in self.defaults_obj.items():
            self.kr.set_password('minervaclient_'+key,'minerva',item)
    def list_settings(self):
        result = [ i for i in self.settings_obj.keys() ]
        result.sort()
        return result
    

import config
# from . import config
import requests,sys
import datetime
import getpass
from datetime import datetime as dt
import unicodedata
import json
import re

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
        self.is_minerva_based = True # Determines whether the stored credentials are mcgill email or minerva id login
        # self.username=""
        # self.password=""
        self.sid = ""
        self.pin =""
        self.mcgill_id = ""

        self.cookie_data = {}
        self.referer = ""
        self.session = requests.Session()
        self.verbose = False
        self.show_err = True

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
        for the sid and pin
        """
        if not self.verify_email_credentials(self.sid,self.pin,verbose=False) and not self.verify_sid_credentials(self.sid,self.pin,verbose=False):
            raise ValueError("Invalid credentials given. Set a proper SID and PIN before logging in")
        sid = self.sid
        pin = self.pin
        self._minerva_get("twbkwbis.P_WWWLogin")
        self._minerva_post("twbkwbis.P_ValLogin",{'sid': sid, 'PIN': pin})
        r = self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_MainMnu")
        m = re.search(r'(Please select one of the login methods below)+', r.content)
        return m is None
    def _minerva_reg_menu(self):
        self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_StuMainMnu")
        return self._minerva_get('twbkwbis.P_GenMenu?name=bmenu.P_RegMnu&param_name=SRCH_MODE&param_val=NON_NT')
    def _minerva_records_menu(self):
        self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_StuMainMnu")
        return self._minerva_get("twbkwbis.P_GenMenu?name=bmenu.P_AdminMnu")
    def get_student_id(self):
        if self.verify_sid_credentials(self.sid,self.pin,verbose=False):
            self.mcgill_id = self.sid
        else:
            # locate the student id on the minerva webpage after logging in
            pass

    def set_minerva_credentials(self, sid="",pin="", verbose=None):
        """Sets the values for the sid and pin (for minerva only)
        """
        if verbose is None: verbose = self.show_err
        self.sid = sid
        self.pin = pin
        try:
            local_credentials.set_password('minervaclient_sid','minerva',str(sid))
            local_credentials.set_password('minervalcient_pin','minerva',str(pin))
            return True
        except Exception as e:
            if verbose: sys.stderr.write(e+'\n')
            return False
    def load_sid_credentials(self):
        """Retrieves the computer stored values for the sid and pin 
        (for minerva only)"""
        sid = local_credentials.get_password('minervaclient_sid','minerva')
        pin = local_credentials.get_password('minervalcient_pin','minerva')
        if (sid is not None and pin is not None):
            self.sid = sid
            self.pin = pin
            return True
        else: # When there are no stored credentials?
            self.sid = ""
            self.pin = ""
            return False
    def del_email_credentials(self, verbose=None):
        """(Deprecated) Removes the computer stored values for the username and password 
        (from mcgill email), does not change instance variables"""
        if verbose is None: verbose = self.show_err
        try:
            local_credentials.delete_password('minervaclient_username','minerva')
            local_credentials.delete_password('minervalcient_password','minerva')
            return True
        except local_credentials.errors.PasswordDeleteError:
            # print "Minerva user is already logged out"
            if verbose: sys.stderr.write("Minerva credentials do not exist.\n")
            return False
    def del_sid_credentials(self, verbose=None):
        """Removes the computer stored values for the username and password 
        (from mcgill email), does not change instance variables"""
        if verbose is None: verbose = self.show_err
        try:
            local_credentials.delete_password('minervaclient_sid','minerva')
            local_credentials.delete_password('minervalcient_pin','minerva')
            return True
        except local_credentials.errors.PasswordDeleteError:
            # print "Minerva user is already logged out"
            if verbose: sys.stderr.write("Minerva credentials do not exist.\n")
            return False
    def verify_sid_credentials(self, sid, pin, verbose=None):
        """Verifies that the values for sid and pin are valid values

        for the pin:
        Exactly 6 characters
        At least one number and one letter (lower case only)
        Must not contain the same character three or more times
        No special or accented characters (e.g. &, *, $)
        
        """
        if verbose is None: verbose = self.show_err
        bad_sid = not str(sid).isdigit() or len(str(sid)) != 9
        bad_pin = len(pin) != 6 or not (pin.islower() and pin.isalnum())
        for char in pin: # no character repeatedt least athrice
            if pin.count(char) >= 3:
                bad_pin = False
        if verbose:
            if bad_sid and bad_pin:
                sys.stderr.write('SID must be a 9 digit number ID and PIN must be 6 characters long\n')
            if bad_sid:
                sys.stderr.write('SID must be a 9 digit number ID\n')
            if bad_pin:    
                sys.stderr.write('PIN must be 6 characters long\n')
        return not bad_sid and not bad_pin
    def verify_email_credentials(self,username, password, verbose=None):
        """Verifies that the instance values for username (mcgill email) and 
        password are valid values
        """
        if verbose is None: verbose = self.show_err
        bad_username = not re.match(r'[\w]+\.[\w\.]+@(mail\.mcgill|mcgill)\.ca',username)
        good_password = len(password) >= 8 and len(password) <= 18 and (' ' not in password)
        bad_password = not good_password # this is the most terrible thing I've ever done but it's verbose

        for char in password: # no character repeated at least thrice
            if password.count(char) >= 3:
                bad_password = False
        if bad_username and bad_password and verbose:
            sys.stderr.write('Email must be a valid McGill Email, and a valid McGill Password\n')
        return not bad_username and not bad_password
    def initial_login(self, sid="", pin="", inConsole=False, reLogin=False, temporary=False, verbose=None):
        """A single method to handle setting the initial values for the sid and 
        pin, maybe based on computer stored values, given parameters, or 
        user input. Always resets the values if given invalid credentials
        Scenario 1: initial_login() -> loads sid and pin credentials
        Scenario 2: initial_login(sid="...",pin="...") -> sets sid and pin and uses them
        Scenario 3: initial_login(inConsole=True) -> Does prompt to determine preferred login method and set the credentials.  Prompts first to change existing credentials.
        Scenario 4: initial_login(sid='...',inConsole=True) -> prompts to determine preferred login method and set remaining credentials. Does not prompt to change credentials.
        """
        if verbose is None: verbose = self.show_err
        # temp_username = self.username
        # temp_password = self.password
        before_sid = self.sid # the sid before changing
        before_pin = self.pin # the pin before changing

        loaded_login = False
        
        # Tries loading credentials from the computer first
        if not temporary and not self.load_sid_credentials():
            # attempts and fails loading either stored credential sets
            pass

    
        # Initial check to see if the loaded credentials are valid
        if self.verify_email_credentials(self.sid,self.pin,verbose=False):
            loaded_login = True
            self.is_minerva_based = False
        if self.verify_sid_credentials(self.sid,self.pin,verbose=False):
            loaded_login = True
            self.is_minerva_based = True

        # At this point, loaded_login says whether instance credentials are legitimate or not.  is_minerva_based says if it is a SID instead of email

        if inConsole: # Ask for credentials only if they aren't already given as parameters.  'sid' and 'pin' are then set afterwards or left blank
            print('Credentials are stored locally on your computer, never uploaded to a server.')
            # ask to rewrite existing login, exit if no
            if loaded_login and not reLogin:
                ans = raw_input('Do you wish to overwrite the existing login[y/n]? Default[y]: ').lower()
                if ans != None and ans == 'n':
                    return
            # Then prompt for credentials, if they haven't already been given as arguments
            sid = raw_input('Enter Minerva Username/Email: ') if sid == '' else sid
            pin = getpass.getpass(prompt='Enter Minerva Password: ') if pin == '' else pin

        # Variables ordered by priority
        # 'sid' or 'pin' are either set or blank
        # 'self.sid' and 'self.pin' are the loaded values
        # 'temp_sid' and 'temp_pin' are the before values

        # Set the instance sid and pin if the given sid and pin are not blank strings
        if sid != '' and pin != '': # permanent change to the stored credentials
            if not temporary:
                self.set_minerva_credentials(sid=sid,pin=pin)
            else:
                self.sid = sid
                self.pin = pin
        # Verifies instance values
        if not ( self.verify_sid_credentials(self.sid,self.pin,verbose=False) or self.verify_email_credentials(self.sid,self.pin,verbose=False) ):
            raise ValueError("Invalid credentials given.")

        # Final check to see if the loaded credentials are valid
        if self.verify_email_credentials(self.sid,self.pin,verbose=False):
            loaded_login = True
            self.is_minerva_based = False
        if self.verify_sid_credentials(self.sid,self.pin,verbose=False):
            loaded_login = True
            self.is_minerva_based = True
    
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

import requests,urllib.request,urllib.parse,urllib.error,io,csv,sys,datetime

class PubSearch(object):
    """Contains the functions used to perform a course search on Minerva"""
    @staticmethod
    def search(term,course_codes,fmt='',**kwargs):
        """term is in the form of 201809 where 2018 is the year (2016, 2017...), and 09 is for Fall (01 for Winter, 05 for Summer)
        course_codes is a list and elements may come in the form of:
            general course code, like COMP-202, to retrieve all different sections of it (eg. COMP-202-001, COMP-202-002...)
                AND/OR
            a specific course code with its section number, can be given (eg. COMP-202-001)
        valid course_type values include Lecture, Tutorial, or any other similar type
        
        TODO: waitlist, availability, tutorials/lectures, 

        This returns a tuple of the relevant course codes (eg. COMP-200-001 CCOM-206-018 ...) and the courses object retrieved from Minerva
        the courses object contains all of the courses with the same subject (eg. COMP, ECSE, POLI) in a dictionary 
        with keys in the form of course codes
        Input: ('201809', ['COMP-200', 'CCOM-206-018'])
        Example: (['COMP-200-001', 'COMP-200-002', 'COMP-200-003', 'CCOM-206-018'], {all courses' data})
        {all courses' data}['COMP-200-002'] => {just the info for COMP-200-002}
        """
        courses_obj = PubSearch._post_search(term,course_codes)
        full_codes = []
        
        # This used to be a bunch of for loops, but it's fine as a giant single line :D
        full_codes = { course:courses_obj[course] for course in courses_obj if (not all( [ (code.upper() not in course) for code in course_codes ] )) }
        filtered_codes = {}
        if kwargs:
            for course in full_codes:
                for key in kwargs:
                    if key.lower() in full_codes[course] and (str(kwargs[key]).upper() in str(full_codes[course][key]).upper()):
                        filtered_codes[course] = full_codes[course]
        else:
            filtered_codes = full_codes

        if fmt == 'json':
            return json.dumps(filtered_codes)
        elif fmt == 'text':
            return PubSearch._beautify_courses(filtered_codes)
        elif fmt == 'dictionary':
            return filtered_codes # return the data retrieved from Minerva for the codes given as arguments
        elif fmt == 'calendar':
            return PubSearch._calendrify_courses(filtered_codes)
        else:
            return filtered_codes # return the data retrieved from Minerva for the codes given as arguments
    @staticmethod
    def _beautify_courses(course_codes):
        """When given an object of courses' info, returns a formatted string version of the information."""
        result = ""
        for course, e in course_codes.items():
            result += "{0} CRN: {1} | {2} \n".format(e['_code'], e['crn'], e['title'])
            result += "{0} Instructor: {1} | Credits: {2}\n".format(e['type'], e['instructor'], e['credits'])
            result += "Capacity: {0} | Seats(remain): {1}/{0} | Waitlist(remains): {2}/{3}\n".format(e['cap'],e['wait']['rem'],e['wl_rem'],e['wl_cap'])
            result += "Seats(actual): {0}/{1} | Waitlist(actual): {2}/{3}\n".format(e['wait']['act'],e['cap'],e['wl_act'],e['wl_cap'])
            result += "{} {} {} | Period: {}\n\n".format(e['location'],e['days'],e['time'],e['date'])
        return result
    @staticmethod
    def _calendrify_courses(course_codes):
        def simplify_course(course):
            return [
                course['_code'],
                course['title'],
                'crn: '+course['crn'],
                course['location'],
                course['time'],
                course['days'],
            ]
        def get_first_time(simple_course):
            return datetime.datetime.strptime(simple_course[-2][:8], '%I:%M %p')
        def pack_course(simple_course):
            pass
        # height = 100
        # width = 100
        # result = [[['',0,0] for y in range(height)] for x in range(width)] # [x][y][char, index, priority]
        days = 'MTWRF'
        u_list = [simplify_course(course_codes[course]) for course in course_codes]
        u_list.sort(key=get_first_time)
        o_list = [[],[],[],[],[]]

        max_col_len = 0
        for course in u_list:
            for day in course[-1]: # days
                o_list[days.find(day)].append(course)
                if len(o_list[days.find(day)]) >= max_col_len:
                    max_col_len = len(o_list[days.find(day)])
        result = ""
        row_format = '|'+('{:<17.17}|'*5)+'\n'
        break_format = '+'+ '{:<17.17}+'.format("-"*17)*5 + '\n'
        
        # The days header
        result+= break_format
        result+= row_format.format(*days)
        result+= break_format

        for row in range(max_col_len):
            for i in range(5):
                data_pts = [ "" if len(o_list[col])<=row else o_list[col][row][i] for col in range(5)]
                result+=row_format.format(*data_pts)
            result+= break_format
        return result
    @staticmethod
    def _build_request(term,subj_codes):
        """Helper function that builds the POST request that would pull 
        relevant course information from Minerva. Based on the given 
        term code (201809) and course subject codes (COMP-202 or COMP-202-000 
        or just COMP).  Collects entire subject from Minerva (as up to date as VSB)
            Example: build_request('201809', ['COMP-202', 'FRSL'])
        """
        
        term = MinervaCommon.get_term_code(term)
        req = [
        ('sel_crse',''),
        ('sel_title',''),
        ('begin_hh','0'),
        ('begin_mi','0'),
        ('begin_ap','a'),
        ('end_hh','0'),
        ('end_mi','0'),
        ('end_ap','a'),
        ('sel_dunt_code',''),
        ('sel_dunt_unit',''),
        ('sel_from_cred',''),
        ('sel_to_cred',''),
        ('sel_coll',''),
        ('call_value_in','UNSECURED'),
        ('display_mode_in','LIST'),
        ('search_mode_in',''),
        ('term_in',term),
        ('sel_subj','dummy'),
        ('sel_day','dummy'),
        ('sel_ptrm','dummy'),
        ('sel_ptrm','%'),
        ('sel_camp','dummy'),
        ('sel_schd','dummy'),
        ('sel_schd','%'),
        ('sel_sess','dummy'),
        ('sel_instr','dummy'),
        ('sel_instr','%'),
        ('sel_attr','dummy'),
        ('sel_attr','%'),
        ('crn','dummy'),
        ('rsts','dummy'),
        ('sel_levl','dummy'),
        ('sel_levl','%'),
        ('sel_insm','dummy'),
        ]

        for code in subj_codes:
            req.append(('sel_subj',code.split("-")[0].upper()))
        
        return urllib.parse.urlencode(req)
    @staticmethod
    def _post_search(term,course_codes):
        """ Helper function that performs the POST request to retrieve 
        the data and returns a logical python dictionary based on the request"""
        request = PubSearch._build_request(term,course_codes)
        sys.stderr.write("> bwckgens.csv\n") # TODO: should remove this line?
        result = requests.post("https://horizon.mcgill.ca/rm-PBAN1/bwckgens.csv",request)
        return PubSearch._parse_search(result.text)
    @staticmethod
    def _parse_search(text):
        """ Converts the HTTP request data from Minerva into a logical 
        format in a python dictionary.
        """
        # stream = io.StringIO(text.encode('ascii','ignore'))
        # print(type(text))
        if type(text) == type(u''):
            text = text.encode('ascii','ignore')
            text = text.decode('utf-8','strict')
        elif type(text) == str:
            pass
        stream = io.StringIO(text)
        field_names = ['crn','subject','course','section','type','credits','title','days','time','cap','wl_cap','wl_act','wl_rem','instructor','date','location','status']
        file = csv.DictReader(stream,field_names)

        records = {}
        first = True
        for row in file:
            if row['subject'] is None or row['subject'] == 'Subject':
                continue

            if row['cap'] == '':
                continue

            if row['wl_rem'] == '':
                row['wl_rem'] = -1000

            row['_code'] = "-".join([row['subject'],row['course'],row['section']])
            row['select'] = MinervaState.only_waitlist_known

            row['reg'] = {}
            row['reg']['cap'] = int(row['cap'])
            
            row['wait'] = {}
            row['wait']['cap'] = int(row['wl_cap'])
            row['wait']['act'] = int(row['wl_act'])
            row['wait']['rem'] = int(row['wl_rem'])

            if row['wait']['rem'] > 0:
                row['_state'] = MinervaState.wait
            else:
                row['_state'] = MinervaState.unknown

            records[row['_code']] = row

        
        return record
class ECalendarSearch(object):
    pass
class AuthSearch(object):
    pass
class MercurySearch(object):
    pass
class CourseRegister(object):
    pass
class CourseSchedule(object):
    pass
class CourseTranscript(object):
    pass
import json
if __name__ == '__main__':
    mnvc = MinervaClient()
    obj = mnvc.pub_search('201901',['ECSE-205-001','ECSE-205-002','ECSE-223-001','ECSE-223-003','COMP-302-001','ECON-209-003','URBP-201-001','URBP-201-004','COMP-273-001'],fmt='calendar')
    text = json.dumps(obj)
    # for col in obj:
    #     for e in col:
    #         print(e[0], end=' ')
    #     print()
    print(obj)
    # <--Testing the MinervaCommon.initial_login-->
    # mnvc.initial_login(sid="260822502",inConsole=True,temporary=True)
    # mnvc._minerva_login_request()
    # if not mnvc._minerva_login_request():
    #     print('Login Unsuccessful')
    # else:
    #     print('Login Successful')
