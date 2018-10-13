from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library # TODO: why future import standard_library shows error on pylinter (py3)
standard_library.install_aliases()
from builtins import str
# pub_search.py: Search for available places in requested courses (via the Display Dynamic Schedule interface)
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun
# (C) Copyright 2018-2019 Ryan B Au

import requests,urllib.request,urllib.parse,urllib.error,io,csv,sys
from .minerva_common import *

def build_request(term,codes):
    """Builds the POST request that would pull relevant course information from Minerva. 
    Based on the given term code (201809) and course codes (COMP-202 or COMP-202-000 or just COMP)
    Example: build_request('201809', 'COMP-202')
    """

    term = get_term_code(term)

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

    for code in codes:
        req.append(('sel_subj',code.split("-")[0].upper()))
    
    return urllib.parse.urlencode(req)

def search(term,course_codes):
    """Performs the POST request that pulls course information from Minerva"""
    request = build_request(term,course_codes)
    sys.stderr.write("> bwckgens.csv\n")
    result = requests.post("https://horizon.mcgill.ca/rm-PBAN1/bwckgens.csv",request)
    return parse_results(result.text)

def quick_search(term, course_codes, course_type=""):
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
    # get the course data from Minerva. includes all of the courses that share the same subject(s) as the course_codes parameter
    courses_obj = search(term,course_codes)
    
    # find all of the full course codes that exist in the search query
    final_codes = []
    full_codes = []
    for course_code in course_codes: # course_code could be COMP-202 or something like COMP-200-001 or something like COMP-361D1-001
        course_code = course_code.upper()
        counter = 1
        if(course_code in courses_obj):
            full_codes.append(course_code) # if the course_code fits the format of COMP-200-001 or COMP-361D1-001 then just to list and move on
            continue
        else:
            # if the first code of COMP-202-001 is in the obj, then continue incrementing
            full_code = course_code + str(counter).join("-000".rsplit('0'*len(str(counter)),1)) 
        
        while (full_code.upper() in courses_obj) and (counter <= 999):
            full_codes.append(full_code)
            counter += 1 
            full_code = course_code + str(counter).join("-000".rsplit('0'*len(str(counter)),1))

    # only keep course codes of a specified type as defined by course_type, or leave it an empty string to get all
    for full_code in full_codes:
        aType = courses_obj[full_code.upper()]['type']
        if (course_type in aType):
            final_codes.append(full_code)

    # a tuple of the relevant course codes (eg. COMP-200-001 CCOM-206-018 ...) and the courses object retrieved from Minerva
    # the courses object contains all of the courses with the same subject (eg. COMP, ECSE, POLI) in a dictionary 
    # with keys in the form of course codes
    return (final_codes, courses_obj)

def print_search(term,course_codes, cType, avail=False, verbose=False, Debug=False):
    """Print out all of the courses and their variations really nicely for the command line interface"""
    minerva_output = MinervaOutput(inConsole=True)

    full_codes, courses_obj = quick_search(term,course_codes, cType)
    if(Debug):
        minerva_output.print(full_codes)
    full_codes.sort()

    for full_code in full_codes:
        course = courses_obj[full_code.upper()]
        if(avail and not (verbose or Debug)):
            minerva_output.print(str(course['_code']), end=' ')
            minerva_output.print(" CRN: %-6s" % (str(course['crn'])), end=' ')
            minerva_output.print(" Capacity: %-4s" % ( str(course['reg']['cap']) ), end=' ')
            minerva_output.print(" Seats (remain): %-8s" % ( str(course['wait']['rem']) +"/" + str(course['wait']['cap']) ), end=' ')
            minerva_output.print(" Seats (actual): %-8s" % ( str(course['wait']['act']) +"/" + str(course['wait']['cap']) ), end=' ')
            minerva_output.print(" Waitlist (remain): %-8s" % ( str(course['wl_rem']) + "/" +str(course['wl_cap']) ), end=' ')
            minerva_output.print(" Waitlist (actual): %-8s" % ( str(course['wl_act']) + "/" +str(course['wl_cap']) ))
        else:
            minerva_output.print(beautify_course_info(course, (verbose or Debug)))
    return minerva_output.get_content()

def beautify_course_info(e, Debug=False):
    # accept a specific course's information in the form of a dictionary and formats it to look nice for the command line interface. 
    # set Debug to True to see the all of the original keys and values paired together concatenated to the end of the original outpute
    seats_remain = str(e['wait']['rem']) +"/" + str(e['wait']['cap'])
    seats_actual = str(e['wait']['act']) +"/" + str(e['wait']['cap'])
    wait_remain = str(e['wl_rem']) + "/" +str(e['wl_cap'])
    wait_actual = str(e['wl_act']) + "/" +str(e['wl_cap'])
    capacity = str(e['reg']['cap'])
    result = [
        str(e['_code']) + " CRN: "+ str(e['crn']) +" | "+ e['title'],
        e['type'] +" Instructor: "+ e['instructor'] +" | Credits: "+str( e['credits'] ) ,
        "Capacity: "+ capacity +" | Seats(remains): " + seats_remain + " | Waitlist(remains): " + wait_remain,
        "Seats(actual): " + seats_actual + " | Waitlist(actual): " + wait_actual,
        e['location'] + " " + e['days'] + " " + e['time'] + " | Period: " + e['date'],
        ""        
    ]
    result0 = ""
    for key,value in list(e.items()):
        result0 += key + "=>" + str(value) + " | "
    # return "\n".join(result)
    return "\n".join(result) + ((result0) if Debug else "")


def parse_results(text):
    # converts the HTTP request data from Minerva into a logical format in a python dictionary
    
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

    
    return records
