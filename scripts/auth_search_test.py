from __future__ import print_function
from minervaclient import auth_search as auth
from minervaclient import pub_search as pub
from minervaclient import minerva_common
from minervaclient.minerva_common import dequebecify

def beautify_course_info(e, Debug=False):
    # accept a specific course's information in the form of a dictionary and formats it to look nice for the command line interface. 
    # set Debug to True to see the all of the original keys and values paired together concatenated to the end of the original outpute
    seats_remain = str(e['wait']['rem']) +"/" + str(e['wait']['cap'])
    seats_actual = str(e['wait']['act']) +"/" + str(e['wait']['cap'])
    wait_remain = str(e['reg']['rem']) +"/" + str(e['reg']['cap'])
    wait_actual = str(e['reg']['act']) +"/" + str(e['reg']['cap'])
    capacity = str(e['reg']['cap'])
    result = [
        str(e['_code']) + " CRN: "+ str(e['crn']) +" | "+ e['title'],
        str(e['type']) +" Instructor: "+ dequebecify(e['instructor']) +" | Credits: "+str( e['credits'] ) ,
        "Capacity: "+ capacity +" | Seats(remains): " + seats_remain + " | Waitlist(remains): " + wait_remain,
        "Seats(actual): " + seats_actual + " | Waitlist(actual): " + wait_actual,
        str(e['location']) + " " + str(e['days']) + " " + " | Period: " + str(e['date']),
        ""        
    ]
    result0 = ""
    for key,value in list(e.items()):
        try:
            result0 += key + "=>" + str(value) + " | "
        except:
            result0 += key + "=>" + dequebecify(value) + " | "
    # return "\n".join(result)
    return "\n".join(result) + ((result0) if Debug else "")

minerva_common.initial_login(inConsole=True)

courses_list = ['MATH-133','MATH-140','MATH-222']
courses_obj = auth.search('201809', courses_list)
total_students = 0

for full_code, course_obj in courses_obj.items():
    # print(full_code, course_obj)
    if (course_obj['type'] != 'Lecture' or not ((course_obj['subject']+'-'+course_obj['course']) in courses_list) ):
        continue
    curr = course_obj['reg']['act']
    total_students += curr
    # print(beautify_course_info(course_obj, True))
    print(course_obj['_code'], '|', course_obj['title'])
    print('The running total # of students:',total_students)
    print()
