# pub_search.py: Search for available places in requested courses (via the Display Dynamic Schedule interface)
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun

import requests,urllib,StringIO,csv,sys
from minerva_common import *

def build_request(term,codes):
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

	for code in codes:
		req.append(('sel_subj',code.split("-")[0]))
	
	return urllib.urlencode(req)

def search(term,course_codes):
	request = build_request(term,course_codes)
	sys.stderr.write("> bwckgens.csv\n")
	result = requests.post("https://horizon.mcgill.ca/rm-PBAN1/bwckgens.csv",request)
	return parse_results(result.text)

def quick_search(term,course_codes, cType=""):
	#TODO: waitlist, availability, tutorials/lectures, 
	courses_obj = search(term,course_codes)
	# for key, value in courses_obj.items():
	# 	for course_code in course_codes:
	# 		if(course_code in key):
	# 			print parse_course_info(value)
	
	# find all of the full course codes that exist in from the search query
	final_codes = []
	full_codes = []
	for course_code in course_codes:
		counter = 1
		if(course_code in courses_obj):
			full_codes.append(course_code)
			continue
		else:
			full_code = course_code[:8] + str(counter).join("-000".rsplit('0'*len(str(counter)),1))
		
		while (full_code in courses_obj) and (counter <= 999):
			full_codes.append(full_code)
			counter += 1 
			full_code = course_code[:8] + str(counter).join("-000".rsplit('0'*len(str(counter)),1))

	for full_code in full_codes:
		aType = courses_obj[full_code]['type']
		if (cType in aType):
			final_codes.append(full_code)

	return (final_codes, courses_obj)

def print_search(term,course_codes, cType, avail=False):
	# print out all of the courses and their variations really nicely
	full_codes, courses_obj = quick_search(term,course_codes, cType)
	# print full_codes
	full_codes.sort()

	for full_code in full_codes:
		course = courses_obj[full_code]
		if(avail):
			print str(course['_code']),
			print " CRN: %-6s" % (str(course['crn'])),
			print " Seats Remaining: %-8s" % ( str(course['wait']['rem']) +"/" + str(course['wait']['cap']) ),
			print " Waitlist: %-8s" % ( str(course['wl_rem']) + "/" +str(course['wl_cap']) )
		else:
			print parse_course_info(course)

def parse_course_info(e):
	result = [
		e['title'],
		e['type'] +" Instructor: "+ e['instructor'] +" | Credits: "+str( e['credits'] ) ,
		str(e['_code']) + " CRN: "+ str(e['crn']) + " Seats Remaining: " + str(e['wait']['rem']) +"/" + str(e['wait']['cap']) + " Waitlist: " + str(e['wl_rem']) + "/" +str(e['wl_cap']),
		e['location'] + " " + e['days'] + " " + e['time'] + " Period: " + e['date'],
		""		
	]
	result0 = ""
	for key,value in e.items():
		result0 += key + "=>" + str(value) + " "
	# return "\n".join(result)
	return "\n".join(result)


def parse_results(text):
	stream = StringIO.StringIO(text.encode("ascii","ignore"))
	field_names = ['crn','subject','course','section','type','credits','title','days','time','cap','wl_cap','wl_act','wl_rem','instructor','date','location','status']
	file = csv.DictReader(stream,field_names)

	records = {}
	first = True
	for row in file:
		if row['subject'] is None or row['subject'] == 'Subject':
			continue

		if row['cap'] == '':
			continue

		if row['wl_rem'] == '':
			row['wl_rem'] = -1000

		row['_code'] = "-".join([row['subject'],row['course'],row['section']])
		row['select'] = MinervaState.only_waitlist_known

		row['reg'] = {}
		row['reg']['cap'] = int(row['cap'])
		
		row['wait'] = {}
		row['wait']['cap'] = int(row['wl_cap'])
		row['wait']['act'] = int(row['wl_act'])
		row['wait']['rem'] = int(row['wl_rem'])

		if row['wait']['rem'] > 0:
			row['_state'] = MinervaState.wait
		else:
			row['_state'] = MinervaState.unknown

		records[row['_code']] = row

	
	return records
