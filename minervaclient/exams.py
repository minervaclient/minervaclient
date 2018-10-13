from __future__ import absolute_import
from __future__ import unicode_literals
# exams.py: Handler for requests for final exam schedules
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun

import requests
from .minerva_common import *
from . import exams_parse,exams_ics



def final_exams(term,report = 'exams_default',calendar = False):
    """Gets the final exam schedule, optionally in the form of a report or as a calendar"""
    if calendar:
        return exams_ics.export_schedule(term,report)
    else:
        return exams_parse.final_exam_schedule(term,report)


