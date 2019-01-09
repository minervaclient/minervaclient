# reg.py: Enrol in registrable courses, via the Quick Add/Drop interface
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str

import requests
import urllib.request, urllib.parse, urllib.error
import sys

from . import reg_parse,auth_search,pub_search
from .minerva_common import *

def get_registered(term):
    minerva_get("bwskfreg.P_AltPin")
    r = minerva_post("bwskfreg.P_AltPin",{'term_in': term})
    return r.text

def reg_courses(text,crns):
    request = reg_parse.quick_add_insert(text,crns)
    r = minerva_post('bwckcoms.P_Regs',request)
    result = reg_parse.quick_add_status(r.text)
    if result == MinervaError.reg_wait:
        wait_request = reg_parse.quick_add_wait(r.text)
        if wait_request:
            r = minerva_post('bwckcoms.P_Regs',wait_request)
            result = reg_parse.quick_add_status(r.text)
        else:
            result = reg_parse.quick_add_issue("Waitlist really is full.")


    if result == MinervaError.reg_fail:
        sys.exit(MinervaError.reg_fail)

def fast_register(term,crns,dry_run = False):
    """Attempts to register for a course by CRN without checking for room
    Example: fast_register('201609',['814'])
    """
    minerva_login()
    minerva_reg_menu()

    courses = get_registered(term)

    print("* You will be registered in the following CRNs " + str(crns))
    if not dry_run:
        reg_courses(courses,crns)
    
    return crns

def check_register(term,course_codes,require_all = False,require_reg = False,dry_run = False,public_search = False):
    """Attempts to register for a course by course code, first checking for room in the course

    Example: check_register('201609',['COMP-206-001','MATH-240-001'])
    """
    if public_search:
        courses = pub_search.search(term,course_codes)
    else:
        minerva_login()
        minerva_reg_menu()
        courses = auth_search.search(term,course_codes)

    crns,course_ok = check_courses(courses,course_codes,require_all,require_reg)

    if public_search:
        minerva_login()
        mineva_reg_menu() # TODO: figure out what it means and define this method

    current = get_registered(term)


    print("* You will be registered in the following CRNs " + str(crns))
    if not dry_run:
        reg_courses(current,crns)

    return course_ok




def check_courses(courses,codes,require_all = False,require_reg = False):
    """Checks a series of given courses and codes, queries Minerva to see the status of being able to register for these"""
    minerva_output = MinervaOutput(inConsole=True)

    crns = []
    course_ok = []

    for code in codes:
        valid_state = False

        if code not in courses:
            minerva_output.print("* Course %s cannot be found. Failure." % code)
            sys.exit(MinervaError.course_not_found)

        course = courses[code]
        minerva_output.write("[" + code + "] ")

        if course['select'] == MinervaState.possible:
            minerva_output.write("* Minerva permits registration ")
            if course['_state'] == MinervaState.register:
                minerva_output.write("in course.\n")
                valid_state = True
            elif course['_state'] == MinervaState.wait:
                minerva_output.write("on waitlist.\n")
                valid_state = True
                minerva_output.print("\t\t You will be in position " + str(course['wait']['act'] + 1) + ".")
            elif course['_state'] == MinervaState.wait_places_remaining:
                minerva_output.write("on waitlist, and places remain in the course.\n")
                valid_state = True
                minerva_output.print("\t\t You will be in position " + str(course['wait']['act'] + 1) + ".")
            elif course['_state'] == MinervaState.full:
                minerva_output.write("but waitlist is reported full.\n")
            elif course['_state'] == MinervaState.full_places_remaining:
                minerva_output.write("but waitlist is reported full (places remain in the class).\n")
            else:
                minerva_output.write("but the current state is unexpected.\n")

            if not require_reg or (require_reg and valid_state):
                crns.append(course['crn'])
                course_ok.append(course['_code'])
        elif course['select'] == MinervaState.only_waitlist_known:
            if course['_state'] == MinervaState.wait:
                minerva_output.print("* Minerva indicates room on waitlist.")
                valid_state = True
                crns.append(course['crn'])
                course_ok.append(course['_code'])
            else:
                minerva_output.print("* Minerva does not show room on waitlist.")
        else:
            minerva_output.print("* Minerva prohibits registration.")
            minerva_output.print("\t\t The status on Minerva is " + course['status'])
    # return minerva_output.get_content()

    if require_all and len(courses) != len(crns):
        minerva_output.print("* Some courses cannot be registered. The require all constraint is unsatisfiable.")
        sys.exit(MinervaError.require_unsatisfiable)
    elif len(crns) == 0:
        minerva_output.print("* No courses can be registered. Failure.")
        sys.exit(MinervaError.course_none)

    return (crns,course_ok)


