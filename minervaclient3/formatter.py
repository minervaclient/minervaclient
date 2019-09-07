import json
import datetime
import csv
import io
import collections
import pprint
import typing

def _serializer(x):
    if isinstance(x,Event):
        return str(x)
    else:
        return x.__dict__
def flatten(d,parent="",sep="_"):
    items = []
    for k,v in d.items():
        name = (parent+sep+k) if parent else k
        if isinstance(v,collections.MutableMapping):
            items.extend(flatten(v,name,sep))
        else:
            items.append((name,v))
    return dict(items)
class Formattable(object):
    def stringify(self):
        """converts predetermined objects in Formattable objects into strings; leaves basic types alone"""
        d = self.__dict__
        def proc(v):
            if isinstance(v,datetime.datetime):
                return x.strftime("%Y-%m-%dT%H:%M:%S")
            elif isinstance(v,Event):
                return str(v)
            else:
                return v
        result = { (k,proc(d[k])) for k in d }
        return result
    def flattened(self):
        return flatten(self.stringify())
    def json(self):
        # author: Nicholas Paun
        return json.dumps(self,default=(lambda x:x.__dict__), indent=2,sort_keys = True)
    def csv(self):
        d = self.flattened()
        stringio = io.StringIO()
        writer = csv.DictWriter(stringio,d.keys())
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
        return pprint.pformat(self)

class Event(Formattable):
    def __init__(self):
        self.start
        self.end
        self.duration
        self.title
        self.location