# auth_search.py: Search for available places in requested courses (via the Minerva interface)
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from future import standard_library # TODO: why future import standard_library shows error on pylinter (py3)
standard_library.install_aliases()

import urllib.request, urllib.parse, urllib.error, sys
from . import auth_search_parse
from .minerva_common import *


def make_course_request(term,subjects):
    """Perform a request to the minerva site, no context included."""
    request = [
        ('rsts','dummy'),
        ('crn','dummy'),     # This is the CRN
        ('term_in', term),         # Term of search
        ('sel_day','dummy'),
        ('sel_schd','dummy'),
        ('sel_insm','dummy'),
        ('sel_camp','dummy'),
        ('sel_levl','dummy'),
        ('sel_sess','dummy'),
        ('sel_instr','dummy'),
        ('sel_ptrm','dummy'),
        ('sel_attr','dummy'),
        ('sel_subj','dummy')]

    for subj in subjects:
        request.append(('sel_subj',subj))
    request.extend([
        ('sel_crse',''),    # Course code
        ('sel_title',''),
        ('sel_schd','%'),
        ('sel_from_cred',''),
        ('sel_to_cred',''),
        ('sel_levl','%'),
        ('sel_ptrm','%'),
        ('sel_instr','%'),
        ('sel_attr','%'),
        ('begin_hh','0'),
        ('begin_mi','0'),
        ('begin_ap','a'),
        ('end_hh','0'),
        ('end_mi','0'),
        ('end_ap','a'),
        ('SUB_BTN','Get Course Sections'),
        ('path','1')
    ])    #This is seriously what Minerva shoves into a search form

    return urllib.parse.urlencode(request)

def dummy_course_request(term):
    return "rsts=dummy&crn=dummy&term_in=" + term + "&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy&sel_crse=&sel_title=&sel_from_cred=&sel_to_cred=&sel_ptrm=dummy&begin_hh=0&begin_mi=0&end_hh=0&end_mi=0&begin_ap=x&end_ap=y&path=1&SUB_BTN=Advanced+Search" # Copied and pasted

def search(term,course_codes):
    """Full search function, and returns the parsed data from minerva"""
    subjects = []
    for code in course_codes:
        subjects.append(code.split("-")[0])
        # subjects.append(code)

    # initial_login()
    # if localsys_has_login() and DEBUG:
    #     print("Using system credenials")
    minerva_login()
    minerva_get("bwskfcls.p_sel_crse_search")
    minerva_post("bwskfcls.bwckgens.p_proc_term_date",{'p_calling_proc': 'P_CrseSearch','search_mode_in': 'NON_NT', 'p_term': term})
    r = minerva_post("bwskfcls.P_GetCrse",dummy_course_request(term))
    
    
    r = minerva_post("bwskfcls.P_GetCrse_Advanced",make_course_request(term,subjects))
    return auth_search_parse.search_parse(r.text)
    # return r.text

def beautify_course_info(e, Debug=False):
    # accept a specific course's information in the form of a dictionary and formats it to look nice for the command line interface. 
    # set Debug to True to see the all of the original keys and values paired together concatenated to the end of the original outpute
    seats_remain = str(e['wait']['rem']) +"/" + str(e['wait']['cap'])
    seats_actual = str(e['wait']['act']) +"/" + str(e['wait']['cap'])
    wait_remain = str(e['reg']['rem']) +"/" + str(e['reg']['cap'])
    wait_actual = str(e['reg']['act']) +"/" + str(e['reg']['cap'])
    capacity = str(e['reg']['cap'])
    result = [
        str(e['_code']) + " CRN: "+ str(e['crn']) +" | "+ e['title'],
        str(e['type']) +" Instructor: "+ dequebecify(e['instructor']) +" | Credits: "+str( e['credits'] ) ,
        "Capacity: "+ capacity +" | Seats(remains): " + seats_remain + " | Waitlist(remains): " + wait_remain,
        "Seats(actual): " + seats_actual + " | Waitlist(actual): " + wait_actual,
        str(e['location']) + " " + str(e['days']) + " " + " | Period: " + str(e['date']),
        ""        
    ]
    result0 = ""
    for key,value in list(e.items()):
        try:
            result0 += key + "=>" + str(value) + " | "
        except:
            result0 += key + "=>" + dequebecify(value) + " | "
    # return "\n".join(result)
    return "\n".join(result) + ((result0) if Debug else "")
