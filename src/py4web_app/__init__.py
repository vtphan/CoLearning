# check compatibility
import py4web

assert py4web.check_compatible("0.1.20190709.1")

# by importing db you expose it to the _dashboard/dbadmin
from .models import db, create_admin_account, create_global_parameter

# by importing controllers you expose the actions defined in it
from . import controllers

# optional parameters
__version__ = "0.0.1"
__author__ = "Shiplu <shiplu.cse.du@gmail.com.com>"
__license__ = "Not decided yet"

msg = create_admin_account(email='mhwlader@memphis.edu', username='mhwlader', first_name='Shiplu', last_name='Hawlader', password='abcd123456')
# create_global_parameter("inclass_active_update_frequency", 10)
# create_global_parameter("inclass_passive_update_frequency", 120)
# create_global_parameter("homework_active_update_frequency", 30)
# create_global_parameter("homework_passive_update_frequency", 300)