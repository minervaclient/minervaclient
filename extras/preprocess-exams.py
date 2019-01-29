import sys, json

YYYY_MM = "2019-04"
f = open(sys.argv[1]).readlines()

structs = {}

for l in f:
	course,sec,title,date,time,bldg,room,rows,fst,lst = l.strip().split("\t")
	subj,course = course.split(" ")
	code = "-".join([subj,course,sec])

	if code not in structs:
		day,nil = date.split("-")
		date = YYYY_MM + day

		if bldg == "Take" and room == "Home":
			note_th = "[Take Home exam]"
			room = ""
			bldg = ""
		else:
			note_th = ""
		
		if bldg == "OFF SITE" and room == "OFF SITE":
			note_id = "[Off Site exam]"
			room = ""
			bldg = ""
		else:
			note_id = ""

		structs[code] = {
                	'_code': code,
                	'_note_id': note_id,
                	'_note_th': note_th,
                	'course': course,
                	'subject': subj,
                	'section': sec,
                	'time': time,
                	'date': date,
                	'loc': []
       		 }



	structs[code]['loc'].append({
	'building': bldg,
	'from': fst,
	'to': lst,
	'room': room,
	'rows': rows
	 })


data = {
                'version': 2019012900, # yyyymmddvv (we don't do anything with this yet but it's supposed to let us see if the file was updated or not)
		'api': 1, # Minervaclient file format version
                'source': 'https://www.mcgill.ca/students/exams/files/students.exams/<fill this in>', # URL file was downloaded from
}

structs['__DATA__'] = data

print json.dumps(structs,indent=4,sort_keys=True)
