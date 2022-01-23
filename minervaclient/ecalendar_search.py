# ecalendar_search.py: Retrieve information about course descriptions and requirements from the eCalendar
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2018-2019 Ryan B Au

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import sys
from bs4 import BeautifulSoup
import requests
import time
import re

from . import pub_search
from .minerva_common import get_term_code, MinervaOutput, minerva_parser, OutputType

# Start of main functions


def ecalendar_exec(term_year, course_codes, page_parts=[], fmt=OutputType.json, inConsole=False):
    """The main ecalendar searching method. Outputs json data or prints out to console."""

    # Turn course_codes into a list of strings if it isn't already
    if type(course_codes) != list:
        course_codes = [convert_ecalendar_crse(course_codes)]
    else:
        course_codes = [convert_ecalendar_crse(c) for c in course_codes]

    # Convert the term
    term_year = convert_ecalendar_term(term_year)

    # Get the ecalendar dictionaries and put into a list
    info_list = [ecalendar_get(term_year, code) for code in course_codes]
    info_parts = ['title', 'overview', 'terms', 'instructors', 'notes',
                  'faculty_offer', 'offer_link', 'offer_link_text']  # Order of parts to output
    minerva_output = MinervaOutput(inConsole=inConsole, fmt=fmt)
    for crse in info_list:  # Go through each object
        pass


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
    search_codes = ['prereq', 'coreq']

    course_info = ecalendar_get(term_year, course_code)
    notes = course_info['notes']
    prereqs = []  # in the format [req and req and [this or [this and this] or this]]
    prereq = ""
    note = ""

    def _replacement_func(match):
        txt = match.group(0)
        return txt[:4] + "-" + txt[5:]
    for note in notes:
        if search_codes[search_type] in note.lower():
            note = re.sub(r'\w+(?:[^_]\d)+', _replacement_func, note)
            prereq = note.split(":")[1].strip().split(" ")
            break

    isAndMode = True  # it's either AND(True) or OR(False)
    prevMode = isAndMode
    counter = 0
    for word in prereq[::-1]:
        counter += 1
        isEnd = counter == len(prereq)
        # change mode to OR
        if 'or' == word.lower():
            isAndMode = False
        if 'and' == word.lower():
            isAndMode = True

        if word.lower() != u"or" and word.lower() != u"and":
            prereqs.insert(0, word.strip(" ,.()"))

        if (not prevMode and isAndMode) or (isEnd and not isAndMode):
            prereqs = [prereqs]
        prevMode = isAndMode
    return prereqs


def ecalendar_get(term_year, course_code, debug=False):
    """Gets a dictionary of information about a course, for the given term year and course 
    term_year takes the format of yyyy-yyyy, for example, 2018-2019
    course_code takes the format of cccc-xxx, for example, comp-206"""
    term_year, course_code = ecalendar_input_format(term_year, course_code)
    return ecalendar_query("https://www.mcgill.ca/study/"+term_year+"/courses/"+course_code, debug)


def ecalendar_get_search_page(lower=1, upper=None, step=None, debug=False):
    search_page_pattern = "https://www.mcgill.ca/study/2021-2022/courses/search?page={}"
    search_res_pattern = r'(?:https:\/\/www\.mcgill\.ca)?\/study\/([0-9]{4}-[0-9]{4})\/courses\/([a-z]{4}-[0-9]{3}[a-zA-Z0-9_]*)'

    r = None
    if upper is None:
        r = range(lower)
    elif step is None:
        r = range(lower, upper)
    else:
        r = range(lower, upper, step)

    for i in r:
        search_link = search_page_pattern.format(i)
        search_page = requests.get(search_link)
        soup = minerva_parser(search_page.content)
        for el in soup.findAll('a', href=True):
            link = el['href']
            match = re.findall(search_res_pattern, link)
            if len(match) > 0:
                year, course = match[0]
                yield ecalendar_get(year, course, debug)


def ecalendar_query(link, debug=False):
    page = requests.get(link)
    if page.status_code != 200:
        if debug:
            print('>', link, file=sys.stderr)
        raise Exception('Could not connect')

    content = page.content
    soup = minerva_parser(content)
    container = soup.find(id="inner-container")

    # Begin collecting content from webpage
    title = container.find(id="page-title").text.strip()
    catalog_terms = container.select(
        "#main-column p.catalog-terms")[0].text.strip()
    catalog_instructors = container.select(
        "#main-column p.catalog-instructors")[0].text.strip()
    catalog_notes = [el.text.strip()
                     for el in container.select("#main-column .catalog-notes p")]
    faculty_offer = container.select(
        "#main-column #content #content-inner .content .meta p")[0]
    faculty_offer_link = faculty_offer.select("a")[0]
    faculty_offer_link_text = "https://www.mcgill.ca" + \
        faculty_offer_link.attrs['href']
    overview_text = container.select(
        "#main-column #content #content-inner .content .content p")[0].text.strip()
    return {'title': title, 'terms': catalog_terms, 'instructors': catalog_instructors, 'notes': catalog_notes, 'faculty_offer': faculty_offer.text, 'offer_link': faculty_offer_link.text.strip(),
            'offer_link_text': faculty_offer_link_text, 'overview': overview_text}


def query_courses_by_subject(term, subject_code):
    """Get a list of all the courses of a given term, of given subject(s) from Minerva. 
    Accepts a term (of any form) and subject code(s) (single string or a list of strings), whether in the form COMP, COMP-206, or COMP-206-002"""
    if type(subject_code) == str:
        subject_code = [subject_code]
    subject_code = [code.upper() for code in subject_code]

    raw_subject_keys = [key[:-4]
                        for key in pub_search.search(get_term_code(term), subject_code)]
    raw_subject_keys.sort()
    subject_keys = []
    for key in raw_subject_keys:
        if key not in subject_keys:
            subject_keys.append(key)
    return subject_keys


def print_ecalendar(term_year, subject_code, page_parts=['title', 'overview'], time_interval=0.5, print_limit=None):
    """Testing code. Prints out all of the courses of given subject code(s) that is found by the minerva course info search (minervacient.pub_search.search)
    term_year may take any form.
    subject_code may be a list of strings, or a single string, case-insensitive ie. COMP, Poli, math, mATh, or FiGs
    page_parts by default displays 'title' and 'overview'. 
        Options include: 'terms', 'instructors', 'notes', 'faculty_offer', 'offer_link', 'offer_link_text'
    time_interval by default is 0.5 seconds, and is small pause between http requests, just in case the site blocks you for some reason"""
    minerva_output = MinervaOutput(inConsole=True)

    subject_keys = query_courses_by_subject(term_year, subject_code)
    # minerva_output.print(subject_keys)
    ecalendar_list = []
    counter = 0
    for code in subject_keys:
        code = code.lower()
        if print_limit is not None and counter > print_limit:
            break
        else:
            counter += 1
        try:
            counter += 1
            ecalendar_list.append(ecalendar_get(
                convert_ecalendar_term(term_year), code))
            minerva_output.print(". ", end="")
            time.sleep(time_interval)
        except Exception as e:
            minerva_output.print(str(e)+" " + code + " ", end="")
    minerva_output.print("")
    for ecalendar_obj in ecalendar_list:
        for key, value in list(ecalendar_obj.items()):
            if key in page_parts:
                minerva_output.print("%-20s" %
                                     (key.upper()) + filter_for_ascii(value))
        minerva_output.print("")
    return minerva_output.get_content()

# Start of helper functions:


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


def is_ecalendar_term(term):
    """Checks whether a given term code matches the eCalendar term format, 2018-2019
    Rules:
    9 characters long
    5th char is '-'
    first 4 char and last 4 are digits
    first section is number that is one less than one after
    """
    term = str(term)

    if (len(term) != 9):  # Must check for valid length to start substrings
        return False
    middle = term[4]   # middle char, supposed to be '-'
    first = term[:4]  # first four digits
    last = term[5:9]  # last four digits

    # is eCalendar year
    return first.isdigit() and last.isdigit() and int(last)-int(first) == 1 and middle == '-'


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
        return code_parts[0]+"-"+code_parts[1]  # gives formatted course code
    else:
        raise ValueError(
            'Must provide valid input for course code, (ie. comp-206, cCoM-206d5, ECON-208-100)')


def convert_ecalendar_term(term):
    """McGill eCalendar uses a different term/year format, so 201809, 201901, and 201905 all become 2018-2019, unless it already is 2018-2019"""

    if is_ecalendar_term(term):
        return term

    term = get_term_code(term)

    # only term format 201809, yyyymm format accpeted after this point
    if len(term) != 6:
        return term
    year = term[:4]
    month = term[-2:]

    if month == '09':
        return year + "-" + str(int(year)+1)
    elif month == '01' or month == '05':
        return str(int(year)-1) + "-" + year


def ecalendar_input_format(term_year, course_code):
    """eCalendar uses a different year system, so check the term_year and course_code inputs to make them the comply with yyyy-yyyy and cccc-xxx or cccc-xxxxx

    param term_year : acceptable inputs include any minerva or ecalendar term code
    param course_code : acceptable inputs include valid course code of any capitalization  (ie. cCOm-342d2)

    returns a tuple (term year, course_code) of format yyyy-yyyy, cccc-xxx, or ccc-xxxxx
    """
    term_year = str(term_year)
    course_code = str(course_code)

    course_code = convert_ecalendar_crse(course_code)
    term_year = convert_ecalendar_term(term_year)

    if is_ecalendar_crse(course_code) and is_ecalendar_term(term_year):
        return (term_year, course_code)  # gives tuple (term year, course_code)
    else:
        print(is_ecalendar_crse(course_code))
        raise ValueError(
            'Must provide valid input for course code and term year (minerva or ecalendar)')


def vsb_suggest(term, phrase, lower=1, upper=None, step=None, debug=False):
    suggest_pattern = "https://vsb.mcgill.ca/vsb/add_suggest.jsp?term={term}&cams=Distance_Downtown_Macdonald_Off-Campus&course_add={phrase}&page_num={index}"
    term = get_term_code(str(term))

    r = None
    if upper is None:
        r = range(lower)
    elif step is None:
        r = range(lower, upper)
    else:
        r = range(lower, upper, step)
    result = []
    for i in r:
        suggest_link = suggest_pattern.format(
            term=term, phrase=phrase, index=i)
        for res in vsb_suggest_query(suggest_link, debug):
            result.append(res)


def vsb_suggest_query(link, debug=False):
    if debug:
        print('>', link, file=sys.stderr)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
    }
    page = requests.get(link, headers=headers)
    if page.status_code != 200:
        if debug:
            print('>', link, file=sys.stderr)
        raise Exception('Could not connect')

    soup = BeautifulSoup(page.content, 'lxml')
    options = soup.findAll('rs')

    for opt in options:
        if opt['info'] != "" and opt.text != '_more_':
            yield opt.text, opt['info']


if __name__ == '__main__':
    # Test code to see what this can do
    # term_year = '201809'
    # subject_code = 'comp'
    # page_parts = ['title','overview']
    # time_interval = 0.5
    # print_ecalendar(term_year,subject_code)
    print(ecalendar_input_format('201809', 'cCOM-206d4'))
    print(ecalendar_input_format('FALL2018', 'comp-205'))
    print(ecalendar_input_format('2019-WINTER', 'ecse-323'))

    r'https:\/\/www\.mcgill\.ca\/study\/([0-9]{4}-[0-9]{4})\/courses\/([a-z]{4}-[0-9]{3}[a-zA-Z0-9_]*)'
    # Ecalendar page links
    # https://www.mcgill.ca/study/2021-2022/courses/search?page=548
    # VSB course search suggestions
    # https://vsb.mcgill.ca/vsb/add_suggest.jsp?term=202201&cams=Distance_Downtown_Macdonald_Off-Campus&course_add=ecse&page_num=0
