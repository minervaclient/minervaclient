import pytest
from minervaclient3 import minerva_common,register
from io import StringIO
mnvc = minerva_common.MinervaCommon()
mnvc.initial_login()
def test_register_courses():
    print(register.register_courses(mnvc,'201909',[]))
