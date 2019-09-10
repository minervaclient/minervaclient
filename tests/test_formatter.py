import pytest
import minervaclient3.minerva_formatter as minerva_formatter
from io import StringIO
from datetime import datetime
import time

def test_formattable_class():
    stringify_test = {'birthdate': '1989-01-21T00:00:00', 'age': 42, 'children': {'lisa': 3, 'rob': 13}, 'things': ['tea', 'box', 'car'], 'name': 'bob'}
    flattened_test = {'things': ['tea', 'box', 'car'], 'children_rob': 13, 'age': 42, 'birthdate': '1989-01-21T00:00:00', 'children_lisa': 3, 'name': 'bob'}
    json_test = '{\n  "age": 42,\n  "birthdate": "1989-01-21T00:00:00",\n  "children": {\n    "lisa": 3,\n    "rob": 13\n  },\n  "name": "bob",\n  "things": [\n    "tea",\n    "box",\n    "car"\n  ]\n}'
    csv_test = 'age,birthdate,children_lisa,children_rob,name,things\r\n42,1989-01-21T00:00:00,3,13,bob,"[\'tea\', \'box\', \'car\']"\r\n'
    yaml_test = '!!python/object:test_formatter.Thing\nage: 42\nbirthdate: 1989-01-21 00:00:00\nchildren:\n  lisa: 3\n  rob: 13\nname: bob\nthings:\n- tea\n- box\n- car\n'
    str_test = "{'age': 42,\n 'birthdate': '1989-01-21T00:00:00',\n 'children': {'lisa': 3, 'rob': 13},\n 'name': 'bob',\n 'things': ['tea', 'box', 'car']}"
    # sql_test = 
    class Thing(minerva_formatter.Formattable):
        def __init__(self):
            self.name = 'bob'
            self.age = 42
            self.children = {"lisa":3,'rob':13}
            self.things = ['tea','box','car']
            self.birthdate = datetime.strptime('1989-01-21','%Y-%m-%d')
    t = Thing()
    assert t.stringify() == stringify_test,'stringify test failed, format/order of key/values might be inconsistent'
    assert t.flattened() == flattened_test,'flattened test failed, format/order of key/values might be inconsistent'
    assert t.json() == json_test,'json test failed, format/order of key/values might be inconsistent'
    assert t.csv() == csv_test,'csv test failed, format/order of key/values might be inconsistent'
    assert t.yaml() == yaml_test,'yaml test failed, format/order of key/values might be inconsistent'
    assert str(t) == str_test,'str test failed, format/order of key/values might be inconsistent'

def test_event_creation():
    e = minerva_formatter.Event()
    # assert e.ics()=='BEGIN:VEVENT\nEND:VEVENT','failed empty event entry'
    e.set_uid_code('comp-273-004')
    e.set_creation_stamp(datetime(year=2019,month=3,day=25,hour=7,minute=54,second=4))
    e.set_start(datetime(year=2019,month=9,day=10,hour=13))
    e.set_end(datetime(year=2019,month=9,day=10,hour=14))
    e.set_repeat_date_end(datetime(year=2019,month=10,day=10))
    e.set_repeat_days_limit(15)

    e.summary = 'Example Event 1'
    e.description = 'just testing the event creation'
    e.location = 'McConnell 204'

    result_test = 'BEGIN:VEVENT\nUID:comp-273-004@minervac.icebergsys.net\nSUMMARY:Example Event 1\nDTSTAMP;VALUE=DATE-TIME:20190325T075404Z\nDTSTART;TZID=America/Montreal;VALUE=DATE-TIME:20190910T130000\nDTEND;TZID=America/Montreal;VALUE=DATE-TIME:20190910T140000\nDESCRIPTION:just testing the event creation\nLOCATION:McConnell 204\nRRULE:FREQ=WEEKLY;UNTIL=20191010T000000;BYDAY=15\nEND:VEVENT'
    assert e.ics() == result_test, 'event entry creation test failed'