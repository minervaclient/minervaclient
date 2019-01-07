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


# total_students = 0

# for full_code, course_obj in courses_obj.items():
#     # print(full_code, course_obj)
#     if (course_obj['type'] != 'Lecture' or not ((course_obj['subject']+'-'+course_obj['course']) in courses_list) ):
#         continue
#     curr = course_obj['reg']['act']
#     total_students += curr
#     # print(beautify_course_info(course_obj, True))
#     print(course_obj['_code'], '|', course_obj['title'])
#     print('The running total # of students:',total_students)
#     print()
courses_list = [
    # 'MATH-133',
    # 'COMP-250',
    # 'COMP-206',
    # 'ECSE-202',
    'CCOM-206',
    'FACC-250',
    'ECSE-200',
    'ECSE-223',
    'ECSE-222',
    'MATH-240',
    'MATH-262',
    'MATH-263',
    'ECSE-321',
    'FACC-300'
]
import time
while(True):
    try:
        courses_obj = auth.search('201901', courses_list)
    except:
        continue
    for full_code, course_obj in courses_obj.items():
        # print(full_code, course_obj)
        if (course_obj['type'] != 'Lecture' or not ((course_obj['subject']+'-'+course_obj['course']) in courses_list) ):
            continue
        
        # print(beautify_course_info(course_obj, True))
        if (course_obj['wait']['rem']>0): # Waitlist has an opening
            print(course_obj['_code'], '|', course_obj['title'])
            print('Actual Wait:',str(course_obj['wait']['act'])+'/'+str(course_obj['wait']['cap']),'Remaining Wait:',str(course_obj['wait']['rem'])+'/'+str(course_obj['wait']['cap']))
            if (course_obj['reg']['rem']>0): # Seats has an opening
                print('Actual Reg:',str(course_obj['reg']['act'])+'/'+str(course_obj['reg']['cap']),'Remaining Reg:',str(course_obj['reg']['rem'])+'/'+str(course_obj['reg']['cap']))
            print()
        else:
            print(course_obj['_code'], end=' ')
    print('\n',"-"*50)
    break