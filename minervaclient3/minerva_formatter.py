import json
from datetime import datetime
import csv
import io
import collections
import pprint
import typing

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
        d = self.__dict__
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
    def json(self):
        return json.dumps(self.stringify(), indent=2,sort_keys = True)
    def csv(self):
        d = self.flattened()
        stringio = io.StringIO()
        k = list(d.keys())
        k.sort()
        writer = csv.DictWriter(stringio,k)
        writer.writeheader()
        writer.writerow(d)
        return stringio.getvalue()
    def yaml(self, human_readable=True):
        # author: Nicholas Paun
        import yaml
        if human_readable:
            yaml.add_multi_representer(list,yaml.representer.SafeRepresenter.represent_list)
            yaml.add_multi_representer(tuple,yaml.representer.SafeRepresenter.represent_list)
        return yaml.dump(self)
    def sql(self):
        pass
    def __str__(self):
        return pprint.pformat(self.stringify())

class Calendar(Formattable):
    begin_cal = u"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Minervaclient//NONSGML minervac.icebergsys.net//EN"""
    end_cal = u"""
END:VCALENDAR"""
    def __init__(self):
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
    def ics(self):
        d = self.__dict__
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