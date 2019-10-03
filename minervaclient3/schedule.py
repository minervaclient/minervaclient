import requests
import urllib.parse
from datetime import datetime as dt

from .minerva_common import MinervaCommon,MinervaConfig,Course
from .minerva_formatter import flatten

def schedule(mnvc,term):
    if not mnvc._minerva_login_request():
        return None
    r = mnvc._minerva_post('bwskfshd.P_CrseSchdDetl',{'term_in': term})
    reg,wait = parse_schedule(r.text)
    return ([ _create_course(i) for i in reg],[ _create_course(i) for i in wait])

def day_index(days):
    m_weekdays = MinervaCommon.get_minerva_weekdays()
    index = ""
    for day in days:
        index += str(m_weekdays.index(day) + 1)

    return days
    return index.ljust(7,'0')

pair_keys = {
    'building':'_building',
    'whole_code':'_code',
    'end_date':'_date_end',
    'start_date':'_date_start',
    'days_active':'_day_idx',
    'map_link':'_link_gmaps',
    'room':'_room',
    'start_time':'_time_start',
    'end_time':'_time_end',
    'instructor':'instructors',
    'course_code':'course',
    'credit':'credits',
    'grad_level':'level',
    'section_code':'section',
    'subject_code':'subject',
    'section_type':'type',
}
def _create_course(obj):
    def parse(k,v):
        if '_date_' in k:
            return dt.strptime(v,MinervaConfig.date_fmt['full_date'])
        elif '_time_' in k:
            return dt.strptime(v,MinervaConfig.date_fmt['short_time'])
        else:
            return v
    d = { k:parse(k,v) for k,v in dict(flatten(obj)).items()}
    # print(d)
    return Course.dumps(d,pair_keys)

def parse_schedule(text,separate_wait = True):
    html = MinervaCommon.minerva_parser(text)
    tbls_course = html.body.find_all('table',{'summary': 'This layout table is used to present the schedule course detail'})
    tbls_sched = html.body.find_all('table',{'summary': 'This table lists the scheduled meeting times and assigned instructors for this class..'})

    entries = []
    wait_entries = []
    for course,sched in zip(tbls_course,tbls_sched):
        entry = {}

        title,course_name,section = course.caption.text.split(" - ")
        entry['title'] = title[:-1] # No period
        entry['subject'],entry['course'] = course_name.split(" ")
        entry['section'] = section
        entry['_code'] = "-".join([entry['subject'],entry['course'],entry['section']])
        
        course_table = course.findAll('td')
        if len(course_table) == 8:
            fields = ['term','crn','status','instructor','grade_mode','credits','level','campus']
        elif len(course_table) == 10:
            fields = ['term','crn','status','wait_pos','wait_notify_expires','instructor','grade_mode','credits','level','campus']
        for field,cell in zip(fields,course_table):
            entry[field] = cell.text.strip().replace("\n","; ")
            if entry[field] == '':
                entry[field] = '{0}'

        entry['instructor'] = entry['instructor'].replace(', ','')            
        entry['_instructor_sn'] = entry['instructor'].split('; ')[0].split(' ')[-1]

        if entry['credits'][-4:] == '.000': #Strip decimals when irrelevant
            entry['credits'] = entry['credits'][:-4]


        entry['_status_desc'],entry['_status_date'] = entry['status'].split(" on ")
        entry['_status_desc'] = MinervaCommon.get_status_code(entry['_status_desc'],short=True)
        
        # entry['_status_date'] = dt.strptime(entry['_status_date'],'%b %d, %Y').strftime(MinervaConfig.date_fmt['short_date'])

        if 'wait_notify_expires' in entry and entry['wait_notify_expires'] is not None and entry['wait_notify_expires'] != '{0}':
            entry['wait_notify_expires'] = dt.strptime(entry['wait_notify_expires'],MinervaCommon.minerva_date['full']).strftime(MinervaConfig.date_fmt['short_datetime'])
            entry['_action_desc'] = "[\033[1;32mReg by " + entry['wait_notify_expires'] + "\033[0m]"
        elif 'wait_pos' in entry:
            entry['_action_desc'] = "[#" + entry['wait_pos'] + " on waitlist]"
        else:
            entry['_action_desc'] = ''

        if entry['_status_desc'] == 'W':
            entry['_action_desc'] = '[Withdrawn from this course]'


        sched_table = sched.findAll('td')
        fields = ['time_range','days','location','date_range','type','instructors']

        for field,cell in zip(fields,sched_table):
            entry[field] = cell.text.strip()


        entry['_day_idx'] = day_index(entry['days'])        
        entry['type'] = MinervaCommon.get_type_abbrev(entry['type'])

        loc_bits =  entry['location'].rsplit(" ",1)

        if len(loc_bits) == 2:
            entry['_building'],entry['_room'] = loc_bits
        else:
            entry['_building'] = loc_bits[0]
            entry['_room'] = ''

        entry['_building'] = entry['_building'].strip()
        entry['_link_gmaps'] = "http://maps.google.com/?" + urllib.parse.urlencode([('saddr','My Location'),('daddr',entry['_building'] + ", Montreal")])
        # print(entry['_building'])
        try: 
            entry['_building'] = MinervaCommon.get_bldg_abbrev(entry['_building']).strip()
        except:
            pass # Can't abbreviate building name
        
        t_bits = entry['time_range'].split(" - ")
        if len(t_bits) == 2:    
            t_start,t_end = entry['time_range'].split(" - ")
            t_start = dt.strptime(t_start,MinervaCommon.minerva_date['time']).strftime(MinervaConfig.date_fmt['short_time'])
            t_end = dt.strptime(t_end,MinervaCommon.minerva_date['time']).strftime(MinervaConfig.date_fmt['short_time'])
            t_range = '-'.join([t_start,t_end])
            entry['_time'] = {}
            entry['_time']['start'] = t_start
            entry['_time']['end'] = t_end
            entry['time_range'] = t_range
        else:
            entry['time_range'] = t_bits[0]

        d_start,d_end = entry['date_range'].split(" - ")
        d_start = dt.strptime(d_start,MinervaCommon.minerva_date['date']).strftime(MinervaConfig.date_fmt['full_date'])
        d_end = dt.strptime(d_end,MinervaCommon.minerva_date['date']).strftime(MinervaConfig.date_fmt['full_date'])
        d_range = ' / '.join([d_start,d_end]) #ISO made me do it
        entry['_date'] = {'start': d_start,'end': d_end}
        entry['date_range'] = d_range

        
        if ('wait_pos' in entry and 'wait_pos' is not None and separate_wait) or entry['_status_desc'] == 'W':
            wait_entries.append(entry)
        else:
            entries.append(entry)

    if separate_wait:
        return (entries,wait_entries)
    else:
        return entries


# Only way we could test it
# def test_main():
#     mnvc = MinervaCommon()
#     mnvc.initial_login()

#     term = '201909'

#     if not mnvc._minerva_login_request():
#         return None
#     # mnvc._minerva_reg_menu()
#     # mnvc._minerva_get('bwskfshd.P_CrseSchdDetl')
#     r = mnvc._minerva_post('bwskfshd.P_CrseSchdDetl',{'term_in': term})
#     # print(r.text)
#     reg,wait = parse_schedule(r.text)
#     return [ (_create_course(obj)).get_dict() for obj in reg][0]