import json
from datetime import datetime
import csv
import io
import collections
import pprint
import typing
import icalendar
import types
import sys

default_date_format = "%Y-%m-%dT%H:%M:%S"

def flatten(d,parent="",sep="_"):
    items = []
    for k,v in d.items():
        name = (parent+sep+k) if parent else k
        if isinstance(v,collections.MutableMapping):
            items.extend(flatten(v,name,sep))
        else:
            items.append((name,v))
    return items
class Formattable(object):
    def stringify(self):
        """converts predetermined types in Formattable objects into strings; leaves other types alone"""
        d = self.get_dict()
        def proc(v):
            if isinstance(v,datetime):
                return v.strftime(default_date_format)
            elif isinstance(v,Event):
                return str(v)
            else:
                return v
        result = { k:proc(d[k]) for k in d }
        return result
    def flattened(self):
        return dict(flatten(self.stringify()))
    def json(self,singular=False):
        return json.dumps(self.stringify(), indent=2,sort_keys = True)
    def csv(self,singular=False):
        d = self.flattened()
        stringio = io.StringIO()
        k = list(d.keys())
        k.sort()
        writer = csv.DictWriter(stringio,k)
        writer.writeheader()
        writer.writerow(d)
        return stringio.getvalue()
    def yaml(self, human_readable=True,singular=False):
        # author: Nicholas Paun
        import yaml
        if human_readable:
            yaml.add_multi_representer(list,yaml.representer.SafeRepresenter.represent_list)
            yaml.add_multi_representer(tuple,yaml.representer.SafeRepresenter.represent_list)
        return yaml.dump(self)
    def sql(self,singular=False):
        pass
    def __str__(self):
        return pprint.pformat(self.stringify())
    def get_dict(self):
        return self.__dict__
    def dumps(obj,fmt_func=None):
        try:
            p = obj
            if type(fmt_func)==types.FunctionType:
                p = fmt_fun(obj)
            if type(p)==dict:
                for k,v in dict(flatten(p)).items():
                    setattr(self,k,v)
        except Exception as inst:
            print(inst)
        
class MultiFormattable(object):
    def __init__(self,formattables=None):
        self.formattables = None
        self.add(formattables)
    def add(o):
        """Accepts a single Formattable object, or list of Formattable objects"""
        f = formattables
        if not f:
            return False
        if type(formattables) != list:
            f = [formattables]

        f = [ i for i in f if isinstance(item,Formattable)]
        for item in f:
            self.formattables.append(item)
        if f:
            return True
    def stringify(self):
        return [ i.stringify() for i in self.formattables]
    def flattened_list(self):
        return [ i.flattened() for i in self.formattables ]
    def flattened_dict(self,key=None):
        if not key:
            key_works = all([ hasattr(item,key) for item in self.formattables ])
            if not key_works:
                return None
        try:
            return { getattr(i,key):flattened(i) for i in self.formattables }
        except Exception as e:
            sys.stderr.write(e)
            return None

class iCalendar(Formattable):
    def __init__(self):
        self.events = []
    def ics(self):
        pass
class iEvent(Formattable):
    def __init__(self):
        pass
    def ics(self):
        pass


class Calendar(Formattable):
    begin_cal = u"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Minervaclient//NONSGML minervac.icebergsys.net//EN"""
    end_cal = u"""
END:VCALENDAR"""
    def __init__(self):
        self.events = []
    def add_event(self,event):
        self.events.append(event)
    def to_ics(self):
        pass
class Event(Formattable):
    ics_format = {
        'uid': 'UID:{}',
        'summary': 'SUMMARY:{}',
        'stamp': 'DTSTAMP;VALUE=DATE-TIME:{}',
        'start': 'DTSTART;TZID=America/Montreal;VALUE=DATE-TIME:{}',
        'end': 'DTEND;TZID=America/Montreal;VALUE=DATE-TIME:{}',
        'description': 'DESCRIPTION:{}',
        'location': 'LOCATION:{}'
    }
    ics_order = ['uid','summary','stamp','start','end','description','location']
    ics_date = "%Y%m%dT%H%M%S"
    def __init__(self):
        # self.name = None
        # self.duration = None

        self.summary = None # This is the name of the event
        self.description = None
        self.location = None
        
        self.uid = None
        self.stamp = None # time of creation of file
        self.start = None
        self.end = None
    def set_uid_code(self,code):
        self.uid = "{}@minervac.icebergsys.net".format(code)
    def set_creation_stamp(self,timestamp=None):
        if timestamp is None:
            self.stamp = timestamp.utcnow().strftime(self.ics_date+'Z')
        else:
            self.stamp = timestamp.strftime(self.ics_date+'Z')
    def set_start(self,timestamp):
        self.start = timestamp.strftime(self.ics_date)
    def set_end(self,timestamp):
        self.end = timestamp.strftime(self.ics_date)
    def set_repeat_date_end(self,timestamp):
        self.date_end = timestamp.strftime(self.ics_date)
    def set_repeat_days_limit(self,value):
        self.by_day = int(value) if int(value) > 0 else 1
    def get_dict(self):
        return self.__dict__
    def ics(self):
        d = self.get_dict()
        result = "BEGIN:VEVENT\n"
        for k in self.ics_order:
            if k in d and d[k] is not None:
                result += self.ics_format[k].format(d[k]) + '\n'
        if 'date_end' in d or 'by_day' in d:
            result += "RRULE:FREQ=WEEKLY"
            try:
                result += ";UNTIL={}".format(d['date_end'])
            except:
                pass
            try:
                result += ";BYDAY={}".format(d['by_day'])
            except:
                pass
            result += '\n' 
        return result + "END:VEVENT"