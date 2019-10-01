import requests
import time
import re


from .minerva_common import MinervaCommon
from . import pub_search

def search(term,course_codes,progress=False):
    if type(course_codes) != list:
        course_codes = [ (course_codes) ]
    else:
        course_codes = [ (c) for c in course_codes]

    result = []

    for course_code in course_codes:
        if len(course_code.split('-'))==1: # If the course_code is just a subject
            result.extend(query_courses_by_subject(term,course_code))
        else:
            result.append(course_code)
    # print(result)
    return specific_search(term,result,progress=progress)

def query_courses_by_subject(term, subject_code):
    """Get a list of all the courses of a given term, of given subject(s) from Minerva. 
    Accepts a term (of any form) and subject code(s) (single string or a list of strings), whether in the form COMP, COMP-206, or COMP-206-002"""
    if type(subject_code) == str:
        subject_code = [subject_code]
    subject_code = [ code.upper() for code in subject_code]
    
    raw_subject_keys = [ key[:-4] for key in pub_search.search(MinervaCommon.get_term_code(term), subject_code,fmt='dictionary')]
    raw_subject_keys.sort()
    subject_keys = []
    for key in raw_subject_keys:
        if key not in subject_keys:
            subject_keys.append(key)
    return subject_keys

def specific_search(term,course_codes, progress=False):
    """The main ecalendar searching method"""
    # Turn course_codes into a list of strings if it isn't already
    if type(course_codes) != list:
        course_codes = [ convert_ecalendar_crse(course_codes) ]
    else:
        course_codes = [ convert_ecalendar_crse(c) for c in course_codes]

    # Convert the term into "ecalendar term"
    term = convert_ecalendar_term(term)

    # Get the ecalendar dictionaries and put into a list
    courses_list = [ ecalendar_get(term,code, progress=progress) for code in course_codes ]
    return courses_list

def ecalendar_get(term, course_code, progress=False, debug=False):
    """Gets a dictionary of information about a course, for the given term year and course 
    term takes the format of yyyy-yyyy, for example, 2018-2019
    course_code takes the format of cccc-xxx, for example, comp-206"""
    term, course_code = ecalendar_input_format(term,course_code)
    page = requests.get("https://www.mcgill.ca/study/"+term+"/courses/"+course_code)
    if page.status_code != 200:
        if debug or progress:
            print(course_code)
        raise Exception('Could not connect')
    if progress:
        print(course_code)
    content = page.content
    soup = MinervaCommon.minerva_parser(content)
    container = soup.find(id="inner-container")
    
    result = {}

    # Begin collecting content from webpage
    result['years'] = term
    result['title'] = container.find(id="page-title").text.strip()
    result['terms'] = container.select("#main-column p.catalog-terms")[0].text.strip()
    result['instructors'] = container.select("#main-column p.catalog-instructors")[0].text.strip()
    result['notes'] = [ el.text.strip() for el in container.select("#main-column .catalog-notes p")]
    result['_faculty_offer'] = container.select("#main-column #content #content-inner .content .meta p")[0]
    result['offer_link_text'] = result['_faculty_offer'].text
    result['offer_link'] = "https://www.mcgill.ca"+result['_faculty_offer'].select("a")[0].attrs['href']
    result['overview'] = container.select("#main-column #content #content-inner .content .content p")[0].text.strip()
    return result

def is_ecalendar_term(term):
    """Checks whether a given term code matches the eCalendar term format, 2018-2019
    Rules:
    9 characters long
    5th char is '-'
    first 4 char and last 4 are digits
    first section is number that is one less than one after
    """
    term = str(term)

    if (len(term)!=9): # Must check for valid length to start substrings
        return False
    middle = term[4]   # middle char, supposed to be '-'
    first  = term[:4]  # first four digits
    last   = term[5:9] # last four digits

    return first.isdigit() and last.isdigit() and int(last)-int(first) ==1 and middle == '-' # is eCalendar year
    
def is_ecalendar_crse(course_code):
    """Checks whether a given crse code matches the eCalendar crse format, code-900 (ccc-xxx or ccc-xxxcx)
    Rules:
    at least 7 char in length
    two sections separated by '-'
    first section is letters
    second is alphanumeric, first 3 are numbers
    """
    code = str(course_code)
    if len(code) < 7 or code[4] != '-':
        return False
    code = code.split('-')
    return code[0].isalpha() and code[1].isalnum() and code[1][:3].isdigit()

def convert_ecalendar_crse(course_code):
    """McGill eCalendar uses a different course code format, so valid codes COMP-206D1-001 become comp-206d5"""
    course_code = str(course_code)

    course_code = course_code.lower()

    code_parts = course_code.split("-")

    if code_parts[0].isalpha() and code_parts[1].isalnum():
        return code_parts[0]+"-"+code_parts[1] # gives formatted course code
    else:
        raise ValueError('Must provide valid input for course code, (ie. comp-206, cCoM-206d5, ECON-208-100): {}'.format(course_code))

def convert_ecalendar_term(term):
    """McGill eCalendar uses a different term/year format, so 201809, 201901, and 201905 all become 2018-2019, unless it already is 2018-2019"""
    
    if is_ecalendar_term(term):
        return term

    term = MinervaCommon.get_term_code(term)
    
    # only term format 201809, yyyymm format accpeted after this point
    if len(term)!=6: 
        return term
    year = term[:4]
    month = term[-2:]
    
    if month=='09':
        return year + "-" + str(int(year)+1)
    elif month=='01' or month=='05':
        return str(int(year)-1) + "-" + year

def ecalendar_input_format(term,course_code):
    """eCalendar uses a different year system, so check the term and course_code inputs to make them the comply with yyyy-yyyy and cccc-xxx or cccc-xxxxx
    
    param term : acceptable inputs include any minerva or ecalendar term code
    param course_code : acceptable inputs include valid course code of any capitalization  (ie. cCOm-342d2)

    returns a tuple (term year, course_code) of format yyyy-yyyy, cccc-xxx, or ccc-xxxxx
    """
    term = str(term)
    course_code = str(course_code)
    
    course_code = convert_ecalendar_crse(course_code)
    term = convert_ecalendar_term(term)

    if is_ecalendar_crse(course_code) and is_ecalendar_term(term):
        return (term, course_code) # gives tuple (term year, course_code)
    else:
        print (is_ecalendar_crse(course_code))
        raise ValueError('Must provide valid input for course code and term year (minerva or ecalendar)')


pair_keys = {
    'description':'overview',
    'instructor':'instructors',
    'faculty':'offer_link_text',

}
def _create_course(obj):
    # def proc(k,v): # For processing the values to convert them
    #     return v
    # obj = { k,proc(k,v) for k,v in obj.items() }
    return Course.dumps(obj,pair_keys)