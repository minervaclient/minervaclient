from __future__ import absolute_import
from __future__ import unicode_literals
# sched.py: Handler for schedule-related commands
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun

import requests
from .minerva_common import *
from . import sched_parse,sched_timetable,sched_ics



def course_details(term,report = 'default',visual = False,calendar = False,conflicts_only = False,no_conflicts = False):
    """Gets the courses schedule for the person based on their login details"""
    minerva_login()
    minerva_reg_menu()
    minerva_get('bwskfshd.P_CrseSchdDetl')
    r = minerva_post('bwskfshd.P_CrseSchdDetl',{'term_in': term})

    minerva_output = MinervaOutput(inConsole=True)

    if visual:
        minerva_output.append(sched_timetable.timetable_report(r.text,report))
    elif calendar:
        minerva_output.append(sched_ics.export_schedule(r.text,report))
    elif conflicts_only:
        minerva_output.append(sched_parse.conflict_report(r.text,report))
    else:
        minerva_output.append(sched_parse.course_details_report(r.text,report))
        if not no_conflicts:
            minerva_output.append(sched_parse.conflict_report(r.text,'conflicts'))
    return minerva_output.get_content()


