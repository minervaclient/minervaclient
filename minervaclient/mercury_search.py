from __future__ import print_function
import requests
from bs4 import BeautifulSoup
import time

from minervaclient import pub_search
from minervaclient.minerva_common import get_term_code
from minervaclient.minerva_common import *

def minerva_page_content_get(minerva_link):
    """An abbreviated version of minerva authenticated get requests (set to inConsole mode)
    Requires the programmer to run initial_login (with parameters set) before using this method.
    """    
    minerva_login()
    page = minerva_get(minerva_link)
    return page.content

def mercury_listitem_extract(content):
    """Takes the important data from the content of a webpage that lists mercury evaluation reports"""
    soup = BeautifulSoup(content,'html.parser')
    courses = soup.select('table#results_table tr')[1:]
    info_list = []
    for course in courses:
        crse_dict = {}
        crse_dict['id'] = course.attrs['id']
        cells = course.select("td")
        crse_dict['term'] = cells[0].text.strip()
        crse_dict['course_code'] = cells[1].text.strip() + " " + cells[2].text.strip()
        crse_dict['course_type'] = cells[3].text.strip()
        crse_dict['course_title'] = dequebecify(cells[4].text.strip())
        crse_dict['course_inst'] = dequebecify(cells[5].text.strip())
        crse_dict['course_rating'] = cells[6].text.strip()
        crse_dict['temp_report_id'] = course.find("a").attrs["id"]
        info_list.append(crse_dict)
    return info_list

def mercury_report_extract(content):
    """Takes the important data from the content of a webpage for a specific mercury evaluation report"""
    soup = BeautifulSoup(content,'html.parser')
    question_tables = soup.select('table.cemainborder')
    
    report_title = soup.select('table h3')[0].text.strip(' -')
    term = soup.select('b')[0].text.split(':')[1].strip(' -')
    instructor = soup.select('b')[1].text.split(':')[1].strip(' -')
    total_responses = soup.select('table td.ceborder')[2].text.strip(' -')
    total_enrol = soup.select('table td.ceborder')[4].text.strip(' -')
    rate_response = soup.select('table td.ceborder')[6].text.strip(' -')
    report_data = {
        'report_title':report_title,
        'term':term,
        'instructor':instructor,
        'total_responses':total_responses, 
        'total_enrol':total_enrol, 
        'rate_response':rate_response,
        }
    
    quest_list = []
    for question in question_tables:
        title = question.select('.ceheader.ceheader-title')[0].text.strip(' -')
        prompt = question.select('.ceheader.ceheader-question')[0].text.strip(' -')
        valid_resp = question.select('td.ceborder.ctrtext')[0].text.strip(' -')
        blank_resp = question.select('td.ceborder.ctrtext')[1].text.strip(' -')
        mean_std_dev = question.select('td.ceborder.ctrtext')[2].text.strip(' -')
        std_dev_of_mean = question.select('td.ceborder.ctrtext')[3].text.strip(' -')
        el_responses = question.select('table.graph_table tr') # List of soup elements of the evaluation options
        responses = [] # List of the string responses categories
        for response in el_responses:
            responses.append({
                'percent':response.select('.graph_pct')[0].text.strip(' -'),
                'votes':response.select('.graph_count')[0].text.strip(' -'),
                'label':response.select('.graph_desc')[0].text.strip(' -'),
                })
        quest_list.append({
            'title':title,
            'prompt':prompt,
            'valid_resp':valid_resp,
            'blank_resp':blank_resp,
            'mean_std_dev':mean_std_dev,
            'std_dev_of_mean':std_dev_of_mean,
            'responses':responses,
            })
    report_data['questions'] = quest_list
    return (question_tables,report_data)

def mercury_course_get(course_code):
    """Gets the list of Mercury evaluations on a given course (format: CCCC-NNN, example: POLI-200, ECSE-361D1"""
    course_code = course_code.upper().split("-")
    subject = course_code[0]
    index = course_code[1]
    content = minerva_page_content_get("bzskmcer.p_display_form?form_mode=ar&subj_tab_in="+subject+"&crse_in="+index)
    return mercury_listitem_extract(content)

def mercury_teacher_get(teacher_name="",teacher_id=None):
    """Gets the list of a teacher(instructor)'s evaluations, given an id or name"""
    teacher_name, teacher_id = mercury_teacherids_search(teacher_name=teacher_name,teacher_id=teacher_id)
    content = minerva_page_content_get("bzskmcer.p_display_form?form_mode=ar&inst_tab_in="+teacher_id)
    return mercury_listitem_extract(content)

def mercury_report_get(review_id):
    """Gets a specific evaluation report for a given course from any of the teacher or course evaluations lists"""
    # bzskmcer.p_display_form?form_mode=vr&eid=C923A9CF5F067BD13D55E7C747A526B795A3DD199113D2428FF929F9EB41A0E9
    content = minerva_page_content_get("bzskmcer.p_display_form?form_mode=vr&eid="+review_id)
    return mercury_report_extract(content)

def mercury_teacherids_get(is_reversed=False):
    """Retrieves all teacher's names (key) and their corresponding McGill IDs (value) as a dictionary. 
    Option to reverse keys/values for different usages.
    Example key/value pair is: { u'Hello Friend' , '123456789' }"""
    content = (minerva_page_content_get("bzskmcer.p_display_form"))
    # soup = BeautifulSoup(content, 'html.parser')
    inst_ids = {}
    # inst_options = soup.find(id="inst_id")
    counter = 0
    start_point = content.rfind("inst_id") + 28
    id_options = [ el for el in content[start_point:].split("\n") if "<OPTION" in el ]
    for el in id_options:
        value = el[15:24]
        words = [ (word).strip(" .") for word in el[26:].split(",")[::-1] ]
        key   = (words[0] + " " + words[1])
        key = dequebecify(key.decode('utf8'))
        if not is_reversed:
            inst_ids[key] = value
        else:
            inst_ids[value] = key
    return inst_ids

def mercury_teacherids_search(teacher_name="",teacher_id=None):
    """When given either a part of the teacher's name, or the teacher's id, both are reported from Minerva
    Example: (teacher_name="Vyb") => ( u'Barry R Vybi', '123456789' )
    TODO: Check for edge use cases, and ensure that any future changes to Minerva's interface
        don't break this feature.
    """
    inst_ids = mercury_teacherids_get(teacher_id is not None)

    items = inst_ids.keys()
    search_val = teacher_name if teacher_id is None else str(teacher_id)
    for item in items:
        if search_val.lower() in item.lower():
            return (item, inst_ids[item]) if teacher_id is None else (inst_ids[item] , item)
