from __future__ import print_function
import requests
from bs4 import BeautifulSoup
import time

from . import pub_search
from .minerva_common import get_term_code

def filter_for_ascii(text, placeholder="_"):
    """Some unicode characters are used in the eCalendar, and some command line consoles don't like this, so this script replaces characters that give Exceptions
    placeholder is '_' by default """
    result = ""
    for letter in text:
        try:
            result += str(letter)
        except Exception:
            result += placeholder
    return result

import re
def ecalendar_get_reqs(term_year, course_code, search_type=0):
    """Extract the Requisite courses from a given course's Notes section on eCalendar.  
    Output takes the form of a jagged list, where lists embedded indicated different types of requirement.

    term_year can be any valid term for ecalendar_get()
    course_code can be any valid course_code for ecalendar_get()
    search_type is either 0 or 1, 0 for Prerequisites, and 1 for Corequisites
    
    Example:  COMP 202, COMP 206, and MATH 263 or (MATH 241 and MATH 233) =>  [COMP-202, COMP-206, [MATH-263, [MATH-241, MATH-233] ] ]
    
    TODO: Make this more advanced and able to handle more use cases other than those similar to the examples given
    """
    # \w++(?:[^_]\d)++
    # \w++(?:[^_]\d)++|(?<=, )or|and
    search_codes = ['prereq','coreq']

    course_info = ecalendar_get(term_year,course_code)
    notes = course_info['notes']
    prereqs = [] # in the format [req and req and [this or [this and this] or this]]
    prereq = ""
    note = ""
    def _replacement_func(match):
        txt = match.group(0)
        return txt[:4] + "-" + txt[5:]
    for note in notes:
        if search_codes[search_type] in note.lower():
            note = re.sub(r'\w+(?:[^_]\d)+',_replacement_func,note)
            prereq = note.split(":")[1].strip().split(" ")
            break
            
    isAndMode = True # it's either AND(True) or OR(False)
    prevMode = isAndMode
    counter = 0
    for word in prereq[::-1]:
        counter += 1
        isEnd = counter==len(prereq)
        # change mode to OR
        if 'or' == word.lower():
            isAndMode = False
        if 'and' == word.lower():
            isAndMode = True
        
        if word.lower() != u"or" and word.lower() != u"and":
            prereqs.insert(0,word.strip(" ,.()"))

        if (not prevMode and isAndMode) or (isEnd and not isAndMode):
            prereqs = [ prereqs ]
        prevMode = isAndMode
    return prereqs

def ecalendar_get(term_year, course_code, debug=False):
    """Gets a dictionary of information about a course, for the given term year and course 
    term_year takes the format of yyyy-yyyy, for example, 2018-2019
    course_code takes the format of cccc-xxx, for example, comp-206"""
    term_year, course_code = ecalendar_input_format(term_year,course_code)
    page = requests.get("https://www.mcgill.ca/study/"+term_year+"/courses/"+course_code)
    if page.status_code != 200:
        if debug:
            print(course_code)
        raise Exception('Could not connect')

    content = page.content
    soup = BeautifulSoup(content,'html.parser')
    container = soup.find(id="inner-container")

    # Begin collecting content from webpage
    title = container.find(id="page-title").text.strip()
    catalog_terms = container.select("#main-column p.catalog-terms")[0].text.strip()
    catalog_instructors = container.select("#main-column p.catalog-instructors")[0].text.strip()
    catalog_notes = [ el.text.strip() for el in container.select("#main-column .catalog-notes p")]
    faculty_offer = container.select("#main-column #content #content-inner .content .meta p")[0]
    faculty_offer_link = faculty_offer.select("a")[0]
    faculty_offer_link_text = "https://www.mcgill.ca"+faculty_offer_link.attrs['href']
    overview_text = container.select("#main-column #content #content-inner .content .content p")[0].text.strip()
    return {'title': title, 'terms':catalog_terms, 'instructors':catalog_instructors, 'notes':catalog_notes, 'faculty_offer':faculty_offer.text, 'offer_link':faculty_offer_link.text.strip(), 
    'offer_link_text':faculty_offer_link_text, 'overview':overview_text}

def convert_ecalendar_term(term):
    """McGill eCalendar uses a different term/year format, so 201809, 201901, and 201905 all become 2018-2019, unless it already is 2018-2019"""
    year_pt1 = term[:4]
    year_pt2 = term[5:9]
    if len(term)==9 and year_pt1.isdigit() and year_pt2.isdigit():
        return year_pt1+"-"+year_pt2

    term = get_term_code(term)
    year = term[:4]
    month = term[-2:]
    
    if month=='09':
        return year + "-" + str(int(year)+1)
    elif month=='01' or month=='05':
        return str(int(year)-1) + "-" + year

def ecalendar_input_format(term_year,course_code):
    """eCalendar uses a different year system, so check the term_year and course_code inputs to make them the comply with yyyy-yyyy and cccc-xxx or cccc-xxxxx"""
    course_code = course_code.lower()
    term_year = convert_ecalendar_term(term_year)

    codes = course_code.split("-")
    code_pt1 = codes[0]
    code_pt2 = codes[1]
    # if "-" in code_pt2:
    #     code_pt2 = code_pt2[ : code_pt2.find('-') ]
    if code_pt1.isalpha():
        return (term_year, code_pt1+"-"+code_pt2)
    else:
        raise ValueError('Input must be valid values in the format yyyy-yyyy, cccc-xxx ex. 2018-2019, comp-206')

def query_courses_by_subject(term, subject_code):
    """Get a list of all the courses of a given term, of given subject(s) from Minerva. 
    Accepts a term (of any form) and subject code(s) (single string or a list of strings), whether in the form COMP, COMP-206, or COMP-206-002"""
    if type(subject_code) == str:
        subject_code = [subject_code]
    subject_code = [ code.upper() for code in subject_code]
    
    raw_subject_keys = [ key[:-4] for key in pub_search.search(get_term_code(term), subject_code)]
    raw_subject_keys.sort()
    subject_keys = []
    for key in raw_subject_keys:
        if key not in subject_keys:
            subject_keys.append(key)
    return subject_keys

def print_ecalendar(term_year, subject_code, page_parts = ['title','overview'], time_interval = 0.5, print_limit=None):
    """Testing code. Prints out all of the courses of given subject code(s) that is found by the minerva course info search (minervacient.pub_search.search)
    term_year may take any form.
    subject_code may be a list of strings, or a single string, case-insensitive ie. COMP, Poli, math, mATh, or FiGs
    page_parts by default displays 'title' and 'overview'. 
        Options include: 'terms', 'instructors', 'notes', 'faculty_offer', 'offer_link', 'offer_link_text'
    time_interval by default is 0.5 seconds, and is small pause between http requests, just in case the site blocks you for some reason"""
    subject_keys = query_courses_by_subject(term_year, subject_code)
    # print(subject_keys)
    ecalendar_list = []
    counter = 0
    for code in subject_keys: 
        code = code.lower()
        if print_limit is not None and counter > print_limit:
            break
        else:
            counter+=1
        try:
            counter+=1
            ecalendar_list.append( ecalendar_get(convert_ecalendar_term(term_year), code) )
            print( ". ",end="")
            time.sleep(time_interval)
        except Exception, e:
            print( str(e)+" " + code + " ",end="")
    print("")
    for ecalendar_obj in ecalendar_list:
        for key,value in ecalendar_obj.items():
            if key in page_parts:
                    print("%-20s" % (key.upper()) +  filter_for_ascii(value))
        print("")

# Test code to see what this can do
# term_year = '201809'
# subject_code = 'comp'
# page_parts = ['title','overview']
# time_interval = 0.5
# print_ecalendar(term_year,subject_code)
