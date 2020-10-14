# check compatibility
import py4web

assert py4web.check_compatible("0.1.20190709.1")

# by importing db you expose it to the _dashboard/dbadmin
from .models import db, create_admin_account

# by importing controllers you expose the actions defined in it
from . import controllers

# optional parameters
__version__ = "0.0.1"
__author__ = "Shiplu <shiplu.cse.du@gmail.com.com>"
__license__ = "Not decided yet"

msg = create_admin_account(email='mhwlader@memphis.edu', username='mhwlader', first_name='Shiplu', last_name='Hawlader', password='abcd123456')
