import pytest
import minervaclient3.minerva_common as minerva_common
from io import StringIO
mnvc = minerva_common.MinervaCommon()
def test_date_format():
    global mnvc
    from datetime import datetime as dt
    iso_date = mnvc.iso_date
    minerva_date = mnvc.minerva_date
    check_iso = {
        'date': '%Y-%m-%d',     # 2019-04-23 datetime
        'time': '%H:%M',        # 23:54
        'full': '%Y%m%dT%H%M%S' # 20190423T235458
    }
    check_minerva = {
        'date': '%b %d, %Y', # Jan 01, 2013 datetime
        'time': '%I:%M %p',  # 12:04 PM
        'full': '%b %d, %Y %I:%M %p' # Jan 01, 2013 12:04 PM
    }

    for k in check_iso:
        assert iso_date[k] == check_iso[k], "iso_date test failed"
    for k in check_minerva:
        assert minerva_date[k] == check_minerva[k], "minerva_date test failed"

def test_login(monkeypatch):
    mnvc0 = minerva_common.MinervaCommon()
    def input_function(arg,f,*args):
        str_input = StringIO("\n".join(arg))
        monkeypatch.setattr('sys.stdin',str_input)
        f(*args)

    # sid and email verification tests
    sid_tests={
        ('123456789','llllll',True)
    }
    email_tests={
        ('ryan.johnson2@mail.mcgill.ca','hello123',True)
    }
    
    for sid,pin,val in sid_tests:
        assert mnvc0.verify_sid_credentials(sid,pin,verbose=True)==val,"sid verification test failed"
    for user,pswd,val in email_tests:
        assert mnvc0.verify_email_credentials(user,pswd,verbose=True)==val, "email verification test failed"
    print('passed sid and email verification tests')
    original_sid = ''
    original_pin = ''

    if mnvc0.load_sid_credentials():
        original_sid = mnvc0.sid
        original_pin = mnvc0.pin
        assert mnvc0.verify_sid_credentials(original_sid,original_pin,verbose=True),"Invalid sid credentials were stored"
    


