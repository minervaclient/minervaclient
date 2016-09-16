import requests
from minerva_common import *
import transcript_parse

def get_transcript(terms = None,report = 'transcript_default',show = ['info','grades','gpa']):
    minerva_login()
    minerva_records_menu()
    r = minerva_get("bzsktran.P_Display_Form?user_type=S&tran_type=V")
    transcript_parse.transcript_report(r.text,terms,report,show)

get_transcript()
