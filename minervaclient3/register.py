import urllib.request, urllib.parse, urllib.error
from .minerva_common import MinervaCommon, MinervaError, Course
from .minerva_formatter import Formattable

def register_courses(mnvc,term,crns,dry_run=False):
    courses = load_registration_page(mnvc,term)
    # RegInfo(courses.text) # DEBUG
    mnvc._save_page(courses,'{}register1.html'.format(mnvc.sid)) # DEBUG SAVE
    print("* You will be registered in the following CRNs " + str(crns))
    if not dry_run: # register courses
        reg_data = quick_add_insert(courses.text,crns) # returns the post data
        reg_result = mnvc._minerva_post('bwckcoms.P_Regs',reg_data)
        mnvc._save_page(reg_result,'{}register2_1.html'.format(mnvc.sid)) # DEBUG SAVE
        add_result = quick_add_status(reg_result.text)

        if add_result == MinervaError.reg_wait: # waitlist situation
            wait_request = quick_add_wait(reg_result.text)
            if wait_request:
                reg_result = mnvc._minerva_post('bwckcoms.P_Regs',wait_request)
                mnvc._save_page(reg_result,'{}register3_1.html'.format(mnvc.sid)) # DEBUG SAVE
            else:
                add_result = quick_add_issue("Waitlist really is full.")
        if add_result == MinervaError.reg_fail: # big fail of registration
            sys.exit(MinervaError.reg_fail)
        return add_result # Stopping the program here

class RegInfo(Formattable):
    course_keys = ['assoc_term_in','CRN_IN','start_date_in','end_date_in','SUBJ','CRSE','SEC','LEVL','CRED','TITLE']
    def __init__(self,text,fmt='text'):
        self.request = self.quick_show_info(text)
        self.request = self.clean_show_info(self.request)
        self.request = self.basic_show_info(self.request)

    def quick_show_info(self,text):
        html = MinervaCommon.minerva_parser(text)
        forms = html.body.find_all('form')
        reg = forms[1]
        input_boxes = reg.find_all(['input','select'])
        request = []

        for input_box in input_boxes:
            if not input_box.has_attr('name'):
                if input_box.has_attr('id'):
                    print("A problem occurred:")
                else:
                    continue

            if input_box.has_attr('value'): #This should always fail for a select.
                val = input_box['value']
            else:
                val = ''

            if val == 'Class Search':  #We want to register and not search,
                continue
            # if crns and input_box['name'] == 'CRN_IN' and val == '':  # Shove our CRN in the first blank field
            #     # print(input_box) # DEBUG
            #     val = crns.pop(0)
            try:
                request.append((input_box['name'], val))
            except KeyError:
                sys.exit(quick_add_issue("Wrong McGill ID or password."))
            
        return request
    def clean_show_info(self,request):
        return [ (name,val) for name,val in request if val != 'DUMMY' and val !='' ]
    def basic_show_info(self,request):
        input_pairs = [ (name,val) for name,val in request if name in self.course_keys ]
        cut_indices = [ i+1 for i in range(len(input_pairs)) if input_pairs[i][0] == 'TITLE' ]
        cut_indices.insert(0,0)
        lst_courses = [ dict(input_pairs[cut_indices[i]:cut_indices[i+1]]) for i in range(len(cut_indices)-1)]
        return [ str(self.create_course(dict(i))) for i in lst_courses ]
    def create_course(self,d):
        keys = ['term','crn','start_date','end_date','subject_code','course_code','section_code','grad_level','credit','title']
        pairs = dict(zip(keys,self.course_keys))
        return Course.dumps(d,pairs)

def quick_add_insert(text,crns):
    html = MinervaCommon.minerva_parser(text)
    forms = html.body.find_all('form')

    reg = forms[1]
    input_boxes = reg.find_all(['input','select'])
    request = []

    for input_box in input_boxes:
        if not input_box.has_attr('name'):
            if input_box.has_attr('id'):
                print("A problem occurred:")
            else:
                continue

        if input_box.has_attr('value'): #This should always fail for a select.
            val = input_box['value']
        else:
            val = ''

        if val == 'Class Search':  #We want to register and not search,
            continue
        if crns and input_box['name'] == 'CRN_IN' and val == '':  # Shove our CRN in the first blank field
            # print(input_box) # DEBUG
            val = crns.pop(0)
        try:
            request.append((input_box['name'], val))
        except KeyError:
            sys.exit(quick_add_issue("Wrong McGill ID or password."))
    
    
    return urllib.parse.urlencode(request)
def quick_add_status(text):
    html = MinervaCommon.minerva_parser(text)
    errtable = html.body.find('table',{'summary':'This layout table is used to present Registration Errors.'})
    if errtable is not None:
        error = errtable.findAll('td',{'class': "dddefault"})[0].a.text
        if error.startswith("Open"):
            print("* Must enter the waitlist section.")
            return MinervaError.reg_wait
        else:    
            print("\033[1m* Failed to register: \033[0m " + str(error))
            return MinervaError.reg_fail
def quick_add_wait(text):
    html = MinervaCommon.minerva_parser(text)
    forms = html.body.find_all('form')
    try:
        reg = forms[1]
    except IndexError:
        sys.exit(quick_add_issue("Registration not open yet."))

    inputs = reg.find_all(['input','select'])
    request = []
    actual_wait = False

    for input in inputs:
        
        if not input.has_attr('name'):
            if input.has_attr('id'):
                print("A problem occurred:")
            else:
                continue

        
        if input.has_attr('value'): #This should always fail for a select.
            val = input['value']
        else:
            val = ''


        if input.has_attr('id') and input['id'].startswith('waitaction'):
            val = 'LW'
            actual_wait = True

        request.append((input['name'], val))
    
        if actual_wait:
            return urllib.parse.urlencode(request)
        else:
            return False
def quick_add_issue(message):
    print("\033[1m* Failed to register: \033[0m " +  message + " [Message generated by Minervaclient.]")
    return MinervaError.reg_fail
def load_registration_page(mnvc,term):
    if not mnvc._minerva_login_request():
        raise ConnectionError('Could not login to Minerva')
    mnvc._minerva_reg_menu()
    mnvc._minerva_get("bwskfreg.P_AltPin")

    return mnvc._minerva_post("bwskfreg.P_AltPin",{'term_in':term})

# example registration
def test_one(dry_run=False):
    # initialize
    mnvc = MinervaCommon()
    # login
    mnvc.initial_login()
    print(mnvc._minerva_login_request())
    # register without attempting to check anything first
    term = '202001' # input
    # crns = ['20714','20715']
    crns = []
    mnvc._minerva_reg_menu()
    mnvc._minerva_get("bwskfreg.P_AltPin")

    courses = mnvc._minerva_post("bwskfreg.P_AltPin",{'term_in':term})
    RegInfo(courses.text)
    mnvc._save_page(courses,'{}register1.html'.format(mnvc.sid)) # DEBUG SAVE
    print("* You will be registered in the following CRNs " + str(crns))
    if not dry_run: # register courses
        reg_data = quick_add_insert(courses.text,crns) # returns the post data
        reg_result = mnvc._minerva_post('bwckcoms.P_Regs',reg_data)
        mnvc._save_page(reg_result,'{}register2_1.html'.format(mnvc.sid)) # DEBUG SAVE
        add_result = quick_add_status(reg_result.text)

        if add_result == MinervaError.reg_wait: # waitlist situation
            wait_request = quick_add_wait(reg_result.text)
            if wait_request:
                reg_result = mnvc._minerva_post('bwckcoms.P_Regs',wait_request)
                mnvc._save_page(reg_result,'{}register3_1.html'.format(mnvc.sid)) # DEBUG SAVE
            else:
                add_result = quick_add_issue("Waitlist really is full.")
        if add_result == MinervaError.reg_fail: # big fail of registration
            sys.exit(MinervaError.reg_fail)
        return add_result # Stopping the program here
