from __future__ import absolute_import
from __future__ import unicode_literals
# transcript.py: Handler for transcript-related commands.
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun

import requests
from .minerva_common import *
from . import transcript_parse

def get_transcript(terms = None,report = 'transcript_default',show = ['summary','credit','grades']):
    """Gets the student's transcript, optionally showing summary, credits, or grades"""
    minerva_login()
    minerva_records_menu()
    r = minerva_get("bzsktran.P_Display_Form?user_type=S&tran_type=V")
    return transcript_parse.transcript_report(r.text,terms,report,show)
