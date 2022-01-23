#!/usr/bin/env python
# minervaclient: The command-line interface
# This file is from Minervac, a command-line client for Minerva
# <http://npaun.ca/projects/minervac>
# (C) Copyright 2016-2017 Nicholas Paun
# (C) Copyright 2018-2019 Ryan B Au


from __future__ import print_function
from builtins import input
from builtins import object
from minervaclient import reg,sched,exams,transcript,pub_search
from minervaclient.minerva_common import *
from minervaclient import minerva_common
from minervaclient import config

from cmd import Cmd
import getpass
import argparse,sys,json
state = {}

def parse_register(subp):
    parser = subp.add_parser('register', help='Register for a set of courses', aliases=['reg'], add_help=False  )
    parser.add_argument("-t","--term",help="The term (e.g. FALL2016, 201609, etc.) in which to register for these courses",required=True)
    parser.add_argument("-j","--job",help="A unique name. When this argument is given, only registration will only be attempted for remaining courses in the job.\n\nNOTE: It is recommended that you use the -R option with this feature (https://github.com/nicholaspaun/minervaclient/wiki/Registrable-courses-and-jobs). ")
    parser.add_argument("-A","--require-all",help="Only register for courses if all of the requested courses are available. NOTE: Only allowed when course codes are given.",action="store_true")
    parser.add_argument("-R","--require-reg",help="Only register for courses if you can enter the class or the waitlist. NOTE: Only allowed when course codes are given..",action="store_true")
    parser.add_argument("-n","--no-register",help="Don't actually perform registration.",action="store_true")
    parser.add_argument("-P","--public-search",help="[BUGGY] Do not log into Minerva to search !!! This option can only be used to register for the waitlist !!!",action="store_true")
    parser.add_argument("-v", "--verbose", help="Show details about the HTTP requests sent to Minerva",action="store_true")
    parser.add_argument("-q","--quiet",help="[TODO] Only print output for successful registration",action="store_true")
    parser.add_argument("-h", "--help", default=argparse.SUPPRESS, action='help', help="Displays the help message for this subcommand")
    parser.add_argument('course',nargs='+',help="A series of CRNs (e.g. 814 202) or course codes (POLI-244-001 COMP-251-002), but not both.")
    parser.set_defaults(which='register')

def parse_schedule(subp):
    parser = subp.add_parser('schedule',help='Display your course schedule', aliases=['sched'], add_help=True)
    parser.add_argument("-t","--term",help="The term (e.g. FALL2016, 201609, etc.) for which to display the schedule",required=True)
    parser.add_argument("-D","--diff-set",help="[TODO] Monitor the requested report for any changes compared with the previous reports in the diff set")
    parser.add_argument("-r","--report",help="choose which schedule report to display (see config.py to configure")
    parser.add_argument("-l","--long",help="Show a detailed report of the schedule",action="store_true")
    parser.add_argument("-s","--short",help="Show a brief report of the schedule",action="store_true")
    parser.add_argument("-V","--visual",help="Export a visual course timetable",action="store_true")
    parser.add_argument("-C","--calendar",help="Export a calendar for the course schedule (or exam schedule if -E is also given)",action="store_true")
    parser.add_argument("-E","--exams",help="Show the final exam schedule for your courses.",action="store_true")
    parser.add_argument("--conflicts-only",help="Only show course conflicts",action="store_true")
    parser.add_argument("--no-conflicts",help="Don't show course conflicts",action="store_true")
    parser.add_argument("-f","--format",help="[TODO] Choose text format for the displayed report")
    parser.add_argument("-v", "--verbose", help="Show details about the HTTP requests sent to Minerva",action="store_true")
    # parser.add_argument("-h", "--help", default=argparse.SUPPRESS, action='help', help="Displays the help message for this subcommand")
    parser.set_defaults(which='schedule')

def parse_transcript(subp):
    parser = subp.add_parser('transcript',help='Display your transcript', add_help=False)
    parser.add_argument("-t","--term",help="The term or terms, separated by commas for which to display the transcript. If no term is specified, records from all terms will be displayed")
    parser.add_argument("-D","--diff-set",help="[TODO] Monitor the requested report for any changes compared with the previous reports in the diff set")
    parser.add_argument("-r","--report",help="Choose which transcript report to display (see config.py to configure")
    parser.add_argument("-l","--long",help="Show a detailed report of the transcript",action="store_true")
    parser.add_argument("-s","--short",help="Show a brief report of the transcript",action="store_true")
    parser.add_argument("-G","--grades",help="Include grades in the report",action="store_true")
    parser.add_argument("-C","--credit",help="Include credit/GPA information in the report",action="store_true")
    parser.add_argument("-S","--summary",help="Include a summary (program, status, etc). in the report",action="store_true")
    parser.add_argument("-P","--header",help="Show the transcript header, which includes personal information and previous education, etc.",action="store_true")
    parser.add_argument("-f","--format",help="[TODO] Choose text format for the displayed report")
    parser.add_argument("-v", "--verbose", help="Show details about the HTTP requests sent to Minerva",action="store_true")
    parser.add_argument("-h", "--help", action='help', help="Displays the help message for this subcommand")
    parser.set_defaults(which='transcript')

def parse_search(subp):
    parser = subp.add_parser('search',help='Search for a course', add_help=False)
    parser.add_argument("-t","--term",help="The term (e.g. FALL2016, 201609, etc.) in which to register for these courses",required=True)
    parser.add_argument("-C","--course-type",help="Manually enter the type of section to view (e.g. Lecture, Conference, \"Midterm Exam\", Tutorial)")
    parser.add_argument("-L", "--lecture-only", help="Show only courses that are Lecture types",action="store_true")
    parser.add_argument("-T", "--tutorial-only", help="Show only courses that are Tutorial types",action="store_true")
    parser.add_argument("-A", "--availability-only", help="Show only availability information",action="store_true")
    parser.add_argument("-v", "--verbose", help="Show details about the HTTP requests sent to Minerva",action="store_true")
    parser.add_argument("-d", "--debug", help="Show details about the HTTP requests sent to Minerva",action="store_true")
    parser.add_argument("-q","--quiet",help="[TODO] Only print output for successful registration",action="store_true")
    parser.add_argument("-h", "--help", default=argparse.SUPPRESS, action='help', help="Displays the help message for this subcommand")
    parser.add_argument('course',nargs='+',help="A series of full course codes or general course codes (POLI-244-001 COMP-251-002 FACC-100) ")
    parser.set_defaults(which='search')

def parse_shell(subp):
    parser = subp.add_parser('shell',help='Start the Minerva Client Interpreter', add_help=False)
    parser.add_argument("-v", "--verbose", help="Show details about the HTTP requests sent to Minerva",action="store_true")
    parser.add_argument("-q","--quiet",help="[TODO] Only print output for successful registration",action="store_true")
    parser.add_argument("-h", "--help", default=argparse.SUPPRESS, action='help', help="Displays the help message for this subcommand")
    parser.set_defaults(which='shell')

def parse_login(subp):
    parser = subp.add_parser('login',help='Enter login credentials for temporary usage', add_help=False)
    parser.add_argument("-u", "--username", help='Provide your Minerva ID number')
    parser.add_argument("-p", "--password", help='Provide your Minerva PIN number \nNOTE: HIGHLY DO NOT RECOMMEND, LEAVES PASSWORD UNPROTECTED.  SHOULD USE NORMAL PROMPT')
    parser.add_argument("-r", "--re-login", help='Repress repeat login message', action="store_true")
    parser.add_argument("-v", "--verbose", help="Show more details",action="store_true")
    parser.add_argument("-q","--quiet",help="Repress repeat login message",action="store_true")
    parser.add_argument("-h", "--help", default=argparse.SUPPRESS, action='help', help="Displays the help message for this subcommand")
    parser.set_defaults(which='login')

def parse_logout(subp):
    parser = subp.add_parser('logout',help='Delete the login credentials, ie. logout', add_help=False)
    parser.add_argument("-v", "--verbose", help="Show more details",action="store_true")
    parser.add_argument("-q","--quiet",help="Repress messages",action="store_true")
    parser.add_argument("-h", "--help", default=argparse.SUPPRESS, action='help', help="Displays the help message for this subcommand")
    parser.set_defaults(which='logout')

def main(args_strings=[]):
    usage_msg = ("minervac [-h]\n                "
    "{register,reg,schedule,sched,transcript,search,shell,login,logout}")
    ap = argparse.ArgumentParser(usage=usage_msg)
    ap.register('action', 'parsers', AliasedSubParsersAction)
    subp = ap.add_subparsers(help = 'Minervaclient subcommands')

    parse_register(subp)
    parse_schedule(subp)
    parse_transcript(subp)
    parse_search(subp)
    parse_shell(subp)
    parse_login(subp)
    parse_logout(subp)

    args = None
    if len(args_strings)>0:
        args = ap.parse_args(args_strings)
    else:
        args = ap.parse_args()
        
    if args.verbose:
        set_loglevel(True)
    
    if args.which == 'login':
        exec_login(args)
    elif args.which == 'logout':
        if not hasattr(args,'help'):
            minerva_logout(inConsole=True)
    elif args.which == 'register':
        if not hasattr(args,'help'):
            initial_login(inConsole=True)
        exec_reg(args)
    elif args.which == 'schedule':
        if not hasattr(args,'help'):
            initial_login(inConsole=True)
        exec_sched(args)
    elif args.which == 'transcript':
        if not hasattr(args,'help'):
            initial_login(inConsole=True)
        exec_transcript(args)
    elif args.which == 'search':
        exec_search(args)
    elif args.which == 'shell':
        exec_shell(args)

def course_ref_type(arg):
    return arg[0].isalpha()

def get_state_filename():
    import os
    return os.path.dirname(os.path.abspath(sys.argv[0])) + "/state.dat"

def save_state(job,data):
    global state
    f = open(get_state_filename(),"w")
    state[job].extend(data)
    f.write(json.dumps(state))
    f.close()

def restore_state(job,courses):
    global state
    state = json.loads(open(get_state_filename()).read())
    if job in state:
        courses = list(set(courses) - set(state[job]))
        print(">>>",courses,"<<<")
    else:
        state[job] = []

    return courses

def exec_reg(args):
    codes_given = course_ref_type(args.course[0])
    term = get_term_code(args.term)

    if args.job is None:
        args.job = False

    for course in args.course:
        if codes_given != course_ref_type(course):
            print("\033[1;31mERROR:\033[0m Course codes cannot be combined with CRNs")
            sys.exit(MinervaError.user_error)

    
    if args.job:
        courses = restore_state(args.job,args.course)
        if not courses:
            print("\033[1;32m**** Congratulations, you've gotten into all your courses ****\033[1m")
            sys.exit(0)
    else:
        courses = args.course

    if codes_given:
        data = reg.check_register(term,courses,require_all=args.require_all,require_reg=args.require_reg,dry_run=args.no_register,public_search=args.public_search)
    else:

        if args.require_all or args.require_reg:
            print("\033[1;31mERROR:\033[0m When using CRNs, it is not possible to verify the state of classes before attempting registration.")
            sys.exit(MinervaError.user_error)
        elif args.public_search:
            print("\033[1;31mERROR:\033[0m This feature is implemented only when searching by course code")
            sys.exit(MinervaErrror.user_error)

        data = reg.fast_register(term,courses,dry_run=args.no_register)

    
    # If we're still here, nothing bad happened, hopefully
    if args.job:
        save_state(args.job,data)

def exec_sched(args):
    term = get_term_code(args.term)
    # report = timetable_default | cal_exams | cal_default | conflicts | exams_default | long | short | default
    if args.report is not None:
        report = args.report
    elif args.visual:
        report = 'timetable_default'
    elif args.calendar:
        if args.exams:
            report = 'cal_exams'
        else:
            report = 'cal_default'
    elif args.conflicts_only:
        report = 'conflicts'
    elif args.exams:
        report = 'exams_default'
    elif args.long:
        report = 'long'
    elif args.short:
        report = 'short'
    else:
        report = 'default'
    # visual = False | True & 'timetable_default'
    # calendar = False | True & ('cal_exams' | 'cal_default')
    # conflicts_only = False | True & 'conflicts'
    # no_conflicts = False | True
    if not args.exams:
        sched.course_details(term,report,visual=args.visual,calendar=args.calendar,conflicts_only=args.conflicts_only,no_conflicts=args.no_conflicts)
    else:
        exams.final_exams(term,report,calendar=args.calendar)

def exec_transcript(args):
    if args.term is None:
        terms = None
    else:
        terms = []
        for term in args.term.split(','):
            terms.append(get_term_code(term))


    if args.report is not None:
        report = args.report
    elif args.long:
        report = 'transcript_long'
    elif args.short:
        report = 'transcript_short'
    else:
        report = 'transcript_default'


    show = ['summary','credit','grades']
    if args.summary or args.grades or args.credit:
        show = []

    if args.summary:
        show.append('summary')
    if args.credit:
        show.append('credit')
    if args.grades:
        show.append('grades')
    if args.header:
        show.append('header')

    transcript.get_transcript(terms,report,show)

def exec_search(args):
    codes_given = course_ref_type(args.course[0])
    term = get_term_code(args.term)
    courses = args.course

    # print courses
    print("")
    cType = ""
    if(args.course_type is not None):
        cType = args.course_type
    elif(args.lecture_only):
        cType = "Lecture"
    elif(args.tutorial_only):
        cType = "Tutorial"
    
    pub_search.print_search(term, courses, cType, avail=args.availability_only, verbose=args.verbose, Debug=args.debug)

def exec_login(args):
    sid = ""
    pin = ""
    can_repeat = True
    if args.username is not None:
        sid = args.username
    if args.password is not None:
        pin = args.password
    if (not (args.quiet or args.re_login)) and( has_login() or localsys_has_login()):
        try:
            if eval(input("Do you want to re-enter your login information? (y/n) default:[y]")) == 'n':
                return
        except SyntaxError:
            pass

    try:
        initial_login(sid=sid, pin=pin, inConsole=True, reLogin=True)
    except ValueError as e:
        print(e)
        print("\nProper values must be given for login")

    print("Login Successful")

def exec_shell(args):
    interpreter = MinervaShell()
    interpreter.cmdloop()

class AliasedSubParsersAction(argparse._SubParsersAction):
    # Thanks to @sampsyo for dedicating this code to the public domain
    # that adds an aliasing feature to argparse subcommands for python 2
    # https://gist.github.com/sampsyo/471779
    class _AliasedPseudoAction(argparse.Action):
        def __init__(self, name, aliases, help):
            dest = name
            if aliases:
                dest += ' (%s)' % ','.join(aliases)
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=help) 

    def add_parser(self, name, **kwargs):
        if 'aliases' in kwargs:
            aliases = kwargs['aliases']
            del kwargs['aliases']
        else:
            aliases = []

        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)

        # Make the aliases work.
        for alias in aliases:
            self._name_parser_map[alias] = parser
        # Make the help text reflect them, first removing old help entry.
        if 'help' in kwargs:
            help = kwargs.pop('help')
            self._choices_actions.pop()
            pseudo_action = self._AliasedPseudoAction(name, aliases, help)
            self._choices_actions.append(pseudo_action)

        return parser

class ShellWrapper(object):
    def __init__(self):
        self.ap = argparse.ArgumentParser()
        self.ap.register('action', 'parsers', AliasedSubParsersAction)
        self.subp = self.ap.add_subparsers(help = 'Minervaclient subcommands')

        parse_register(self.subp)
        parse_schedule(self.subp)
        parse_transcript(self.subp)
        parse_search(self.subp)
        parse_login(self.subp)

class CommandWrapper(Cmd):
    def __init__(self, cmd_parent, line_args, command_name, command_function, try_login = False):
        # super(CommandWrapper,self).__init__()
        
        try:
            args = cmd_parent.ap.parse_args((command_name+" "+line_args).split())
            if args.verbose:
                set_loglevel(True)
            if not has_login() and try_login and not hasattr(args,'help'):
                initial_login(inConsole=True)
            command_function(args)
        except SystemExit:
            return
        except Exception as e:
            print(e)
            return

        
class MinervaShell(Cmd):
    wrapper = ShellWrapper()
    ap = wrapper.ap
    subp = wrapper.subp
    subcommand_desc = {
        "register (reg)":"Register for a set of courses",
        "schedule (sched)":"Display your course schedule",
        "transcript":"Display your transcript",
        "search":"Search for a course",
        "login":"Set login credentials for this session",
        "logout":"Remove the login credentials for this session"
    }
    
    def preloop(self):
        """Introduction message that is printed just before the interpreter is initialized"""
        print("\nWelcome to the Minerva Client interpreter!")
        
        # self.help_introduction()
        self.do_help("")
        

        self.prompt = "\nminervac$ "
    def do_help(self,s):
        """Help introduction message"""
        if s != "":
            Cmd.do_help(self,s)
            return
        
        print("\nYour login information will be retained for the duration of this session")
        print("Possible shell commands include:\n")
        
        for name, descript in list(self.subcommand_desc.items()):
            print("\t%-20s" % (name) + descript)
        print("\n\t%-20s" % ("exit") + "Exit the interpreter, and end this session")
        print("\nHelp commands take the form of either:\n help reg || ? reg || reg -h || reg --help")
        
    def do_search(self,s):
        i = CommandWrapper(self,s,"search",exec_search)
    def do_exit(self,s):
        if "-h" in s or "--help" in s:
            self.help_exit()
        else:
            return True
    def do_schedule(self,s):
        i = CommandWrapper(self,s,"schedule",exec_sched, True)
    def do_sched(self,s):
        self.do_schedule(s)
    def do_transcript(self,s):
        i = CommandWrapper(self,s,"transcript",exec_transcript, True)
    def do_register(self,s):
        i = CommandWrapper(self,s,"register",exec_reg, True)
    def do_reg(self,s):
        self.do_register(s)    
    def do_login(self,s):
        if ("-h" in s) or ("--help" in s) or ("help" in s):
            print("usage(shell only): minervac$ login")
            print("\nSet login credentials for this session")
        else:
            i = CommandWrapper(self,s,"login",exec_login)
    def do_logout(self,s):
        if ("-h" in s) or ("--help" in s) or ("help" in s):
            print("usage(shell only): minervac logout")
            print("\nRemoves the Minerva credentials from this session")
        else:
            minerva_logout(inConsole=True)
            print("Logout Successful")
    
    def help_search(self):
        self.do_search("-h")
    def help_schedule(self):
        self.do_schedule("-h")
    def help_sched(self):
        self.help_schedule()
    def help_transcript(self):
        self.do_transcript("-h")
    def help_register(self):
        self.do_register("-h")
    def help_reg(self):
        self.help_register()
    def help_login(self):
        self.do_login("-h")
    def help_logout(self):
        self.do_logout("-h")
    def help_exit(self):
        print("usage(shell only): minervac$ exit")
        print("\nExit the interpreter, and end this session")

    
if __name__ == '__main__':
    main()

"""
Possible tests include:
minervac sched -h
minervac schedule -h
minervac reg -h
minervac register -h
minervac transcript -h
minervac search -h
minervac shell

Test in the command shell include the above commands (w/o minervac) and:
login
login -u 123456789
login -p h23456
login -u 123456789 -p h23456
logout
login -u 123456789 -p h23456

"""