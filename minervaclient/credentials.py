from __future__ import unicode_literals
from builtins import object
# Copy this file to credentials_local.py and edit the settings
# ONLY EDIT THIS FILE WITH A REAL TEXT EDITOR (No TextEdit or Notepad, ever!)

id = 'McGill ID here'
pin = 'Minerva PIN here'
always_dry_run = False


def get_password(*args):
    return None


def set_password(*args):
    pass


def delete_password(*args):
    pass


class errors(object):
    class PasswordDeleteError(Exception):
        pass
