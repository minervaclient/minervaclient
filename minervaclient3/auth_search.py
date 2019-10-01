import urllib.request, urllib.parse, urllib.error
import sys
from datetime import datetime

from .minerva_common import MinervaCommon,MinervaState,Course
from .minerva_formatter import flatten

def search(mnvc, term, course_codes,singular=False,fmt='',**kwargs):
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

    courses_obj = post_search(mnvc,term,course_codes,singular)
    full_codes = []
    # This used to be a bunch of for loops, but it's fine as a giant single line :D
    full_codes = { course:courses_obj[course] for course in courses_obj if (not all( [ (code.upper() not in course) for code in course_codes ] )) }
    filtered_codes = {}
    if kwargs:
        for course in full_codes:
            for key in kwargs:
                if key.lower() in full_codes[course] and (str(kwargs[key]).upper() in str(full_codes[course][key]).upper()):
                    filtered_codes[course] = full_codes[course]
    else:
        filtered_codes = full_codes

    if fmt.lower() == 'json':
        return json.dumps(filtered_codes)
    elif fmt.lower() == 'dictionary':
        return filtered_codes # return the data retrieved from Minerva for the codes given as arguments
    else:
        return [ _create_course(filtered_codes[o]) for o in filtered_codes ] # return the data retrieved from Minerva for the codes given as arguments
    # elif fmt.lower() == 'text':
    #     return beautify_courses(filtered_codes)
    # elif fmt.lower() == 'calendar':
    #     return calendrify_courses(filtered_codes)

def dummy_course_request(term):
    # Copied and pasted
    return "rsts=dummy&crn=dummy&term_in=" + term + "&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy&sel_crse=&sel_title=&sel_from_cred=&sel_to_cred=&sel_ptrm=dummy&begin_hh=0&begin_mi=0&end_hh=0&end_mi=0&begin_ap=x&end_ap=y&path=1&SUB_BTN=Advanced+Search" 

def build_request(term,codes):
    """Perform a request to the minerva site, no context included."""
    one_course = False
    if type(codes)==list and len(codes)==1:
        codes = codes[0]
    if type(codes)==str:
        one_course = True

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

    if not one_course:
        for code in codes:
            subj = code.split("-")[0].upper()
            request.append(('sel_subj',subj))
        request.append(('sel_crse',''))
        print('normal')
    else:
        try:
            code = codes
            subj = code.split("-")[0].upper()
            crse = code.split("-")[1].upper()
            request.append(('sel_subj',subj))
            request.append(('sel_crse',crse))
            print('new')
        except:
            code = codes
            subj = code.split("-")[0].upper()
            request.append(('sel_subj',subj))
            request.append(('sel_crse',''))
            print('backup')

    request.extend([
        # ('sel_crse',''),    # Course code
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

def post_search(mnvc,term,course_codes,singular=False):
    """Full search function, and returns the parsed data from minerva"""
    subjects = course_codes
    # for code in course_codes:
    #     subjects.append(code.split("-")[0])
        # subjects.append(code)

    # initial_login()
    # if localsys_has_login() and DEBUG:
    #     print("Using system credenials")

    if not mnvc._minerva_login_request():
        return None
    # So it turns out these aren't necessary???
    # mnvc._minerva_get("bwskfcls.p_sel_crse_search") # So it turns out these aren't necessary?
    # mnvc._minerva_post("bwskfcls.bwckgens.p_proc_term_date",{'p_calling_proc': 'P_CrseSearch','search_mode_in': 'NON_NT', 'p_term': term})
    # r = mnvc._minerva_post("bwskfcls.P_GetCrse",dummy_course_request(term))
    def post(subjects):
        return parse_search(term,mnvc._minerva_post("bwskfcls.P_GetCrse_Advanced",build_request(term,subjects)).text)
    def multi_post(subjects):
        return {k: v for d in [ post(subject) for subject in subjects ] for k, v in d.items()}

    if not singular:
        return post(subjects) # normal version, gets everything
    else:
        # abnormal version, makes a request for each course given
        return multi_post(subjects)

    # return r.text

def parse_search(term,text):

    text = text.replace('&nbsp;',' ') # This is really dumb, but I don't want know how Python handles Unicode
    html = MinervaCommon.minerva_parser(text)
    table = html.body.find('table',{'summary':'This layout table is used to present the sections found'})
    tr = table.findAll('tr')[2:]
    records = {}
    for row in tr:
        cells = row.findAll('td')
        record = parse_entry(cells)

        if record is None:
            continue
        elif record['subject'] is None: #This is notes, or additional days. I don't care about it right now
            continue
            
        record['_code'] = "{}-{}-{}".format(record['subject'],record['course'],record['section'])

        determine_state(record)

        records[record['_code']] = record
        record['start_date'] = 'TBA' if record['date']=='' or record['date']=='TBA' else datetime.strptime(record['date'].split('-')[0]+term[:4],'%m/%d%Y')
        record['end_date']   = 'TBA' if record['date']=='' or record['date']=='TBA' else datetime.strptime(record['date'].split('-')[1]+term[:4],'%m/%d%Y')
        record['start_time'] = 'TBA' if record['time']=='' or record['time']=='TBA' else datetime.strptime(record['time'].split('-')[0]+term[:4],'%I:%M %p%Y')
        record['end_time']   = 'TBA' if record['time']=='' or record['time']=='TBA' else datetime.strptime(record['time'].split('-')[1]+term[:4],'%I:%M %p%Y')
        record['term'] = term

    return records

def parse_entry(cells):
    if cells is None:
        return None

    if len(cells) < 20:
        return None

    record = {}
    if cells[0].abbr is not None and cells[0].abbr.text == "C":
        record['select'] = MinervaState.closed
    else:
        record['select'] = MinervaState.possible

    keys = ['crn','subject','course','section','type','credits','title','days','time']
    # print(cells) # DEBUG
    for cell,key in zip(cells[1:10],keys):
        cell = cell.text.encode('ascii','ignore')  # Because this stuff is used elsewhere in the program
        if cell == ' ': cell = None
        record[key] = cell.decode('utf-8') if type(cell) is bytes else cell

    record['reg'] = {}
    reg_keys = ['cap','act','rem']
    for cell,key in zip(cells[10:13],reg_keys):
        cell = cell.text
        if not cell.isdigit(): cell = -1000
        record['reg'][key] = (cell)

    record['wait'] = {}
    wait_keys = ['cap','act','rem']    
    for cell,key in zip(cells[13:16],wait_keys):
        cell = cell.text
        if not cell.isdigit(): cell = -1000
        record['wait'][key] = (cell)
        
    
    keys = ['instructor','date','location','status']
    for cell,key in zip(cells[16:],keys):
        cell = cell.text
        if cell == ' ': cell = None
        record[key] = cell.decode('utf-8') if type(cell) is bytes else str(cell)
    record['cap'] = str(record['reg']['cap'])
    record['wl_cap'] = str(record['wait']['cap'])
    record['wl_rem'] = str(record['wait']['rem'])
    record['wl_act'] = str(record['wait']['act'])

    

    return record

def determine_state(record):
    if record['select'] == MinervaState.closed:
        record['_state'] = record['select']
    elif int(record['reg']['rem']) > 0:
        if int(record['wait']['act']) <= 0:
            record['_state'] = MinervaState.register
        elif record['wait']['rem'] > 0:
            record['_state'] = MinervaState.wait_places_remaining
        else:
            record['_state'] = MinervaState.full_places_remaining
    elif int(record['wait']['rem']) > 0:
        record['_state'] = MinervaState.wait
    elif int(record['wait']['rem']) <= 0:
        record['_state'] = MinervaState.full
    else:
        record['_state'] = MinervaState.unknown

pair_keys = {
    'credit':'credits',
    'subject_code':'subject',
    'crn_code':'crn',
    'course_code':'course',
    'section_code':'section',
    'section_type':'type',
    'days_active':'days',
    'activity_status':'status',
    'whole_code':'_code',
    'waitlist_occupied':'wait_act',
    'waitlist_remaining':'wait_rem',
    'waitlist_capacity':'wait_cap',
    'seats_occupied':'reg_act',
    'seats_remaining':'reg_rem',
    'seats_capacity':'reg_cap',
}

def _create_course(obj):
    f = [ (k,(v)) for k,v in flatten(obj) ]
    return Course.dumps(dict(f),pair_keys)

