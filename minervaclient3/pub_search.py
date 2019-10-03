import requests
import urllib.request,urllib.parse,urllib.error
import io,csv,sys
from datetime import datetime
from .minerva_common import MinervaCommon,MinervaState,Course
from .minerva_formatter import flatten

def search(term,course_codes,fmt='',**kwargs):
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
    if type(course_codes)!=list:
        course_codes = [course_codes]
    courses_obj = post_search(term,course_codes)
    full_codes = []

    # Filter out only the codes that you want
    # This used to be a bunch of for loops, but it's fine as a giant single line :D
    full_codes = { course:courses_obj[course] for course in courses_obj if (not all( [ (code.upper() not in course) for code in course_codes ] )) }
    
    # Filter the codes even further using the kwargs. kwargs supplied could be: 'type':'Lecture', 'instructor':'John'
    filtered_codes = {}
    if kwargs:
        for course in full_codes:
            for key in kwargs:
                if key.lower() in full_codes[course] and (str(kwargs[key]).upper() in str(full_codes[course][key]).upper()):
                    filtered_codes[course] = full_codes[course]
    else:
        filtered_codes = full_codes

    if fmt == 'json':
        return json.dumps(filtered_codes)
    elif fmt == 'dictionary':
        return filtered_codes # return the data retrieved from Minerva for the codes given as arguments
    else:
        # return filtered_codes # return the data retrieved from Minerva for the codes given as arguments
        return [ _create_course(filtered_codes[o]) for o in filtered_codes ] # return the data retrieved from Minerva for the codes given as arguments
    # elif fmt == 'text':
    #     return PubSearch._beautify_courses(filtered_codes)
    # elif fmt == 'calendar':
    #     return PubSearch._calendrify_courses(filtered_codes)

def post_search(term,course_codes):
    """ Helper function that performs the POST request to retrieve 
    the data and returns a parsed python dictionary based on the request"""
    request = build_request(term,course_codes)
    # sys.stderr.write("> bwckgens.csv\n") # DEBUG TODO: should remove this line?
    result = requests.post("https://horizon.mcgill.ca/rm-PBAN1/bwckgens.csv",request)
    return parse_search(result.text,MinervaCommon.get_term_code(term))

def build_request(term,subj_codes):
    """Helper function that builds the POST request that would pull 
    relevant course information from Minerva. Based on the given 
    term code (201809) and course subject codes (COMP-202 or COMP-202-000 
    or just COMP).  Collects entire subject from Minerva (as up to date as VSB)
        Example: build_request('201809', ['COMP-202', 'FRSL'])
    """
    
    term = MinervaCommon.get_term_code(term)
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

    for code in subj_codes:
        req.append(('sel_subj',code.split("-")[0].upper()))
    
    return urllib.parse.urlencode(req)

def parse_search(text,term):
    """ Converts the HTTP request data from Minerva into a logical 
    format in a python dictionary.
    """
    # stream = io.StringIO(text.encode('ascii','ignore'))
    # print(type(text))
    if type(text) == type(u''):
        text = text.encode('ascii','ignore')
        text = text.decode('utf-8','strict')
    elif type(text) == str:
        pass
    # print(text) # DEBUG
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


        # metadata that's useful to us in minervaclient
        row['_code'] = "-".join([row['subject'],row['course'],row['section']])
        row['select'] = MinervaState.only_waitlist_known
        if  type(row['wl_rem'])==str and row['wl_rem'] != '' and (row['wl_rem'].isdigit() and int(row['wl_rem']) > 0):
            row['_state'] = MinervaState.wait
        else:
            row['_state'] = MinervaState.unknown
        
        row['start_date'] = 'TBA' if row['date']=='' or row['date']=='TBA' else datetime.strptime(row['date'].split('-')[0]+term[:4],'%m/%d%Y')
        row['end_date']   = 'TBA' if row['date']=='' or row['date']=='TBA' else datetime.strptime(row['date'].split('-')[1]+term[:4],'%m/%d%Y')
        row['start_time'] = 'TBA' if row['time']=='' or row['time']=='TBA' else datetime.strptime(row['time'].split('-')[0]+term[:4],'%I:%M %p%Y')
        row['end_time']   = 'TBA' if row['time']=='' or row['time']=='TBA' else datetime.strptime(row['time'].split('-')[1]+term[:4],'%I:%M %p%Y')
        row['term'] = term
        # Weird math that isn't very accurate in the first place
        # if row['wl_rem'] == '':
        #     row['wl_rem'] = -1000
        # row['reg'] = {}
        # row['reg']['cap'] = int(row['cap'])        
        # row['wait'] = {}
        # row['wait']['cap'] = int(row['wl_cap'])
        # row['wait']['act'] = int(row['wl_act'])
        # row['wait']['rem'] = int(row['wl_rem'])
        

        records[row['_code']] = row

    
    return records

# flattened_course_obj_keys = [
    # ('credits', '0.000'), #N
    # ('subject', 'MATH'), #N
    # ('course', '133'), #N
    # ('title', 'Linear Algebra and Geometry.'), #X

    # ('instructor', 'TBA'), #X
    # ('type', 'Tutorial'), #N
    # ('crn', '13427'), #N
    # ('section', '014'), #N
    # ('days', 'F'), #N 
    # ('time', '03:35 PM-04:25 PM'), #X
    # ('date', '09/03-12/03'), #X 
    # ('location', 'RPHYS 114'), #X
    # ('status', 'Active'), #N

    # ('_code', 'MATH-133-014'),

    # ('wl_rem', '0'),
    # ('wait_act', 0),
    # ('cap', '68'),
    # ('wait_rem', 0),
    # ('wl_cap', '0'),
    # ('wait_cap', 0),
    # ('reg_cap', 68),
    # ('wl_act', '0'),

    # ('select', 8),
    # ('_state', 4),
# ]
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
}
def _create_course(obj):
    return Course.dumps(dict(flatten(obj)),pair_keys)




