# check compatibility
import py4web

assert py4web.check_compatible("0.1.20190709.1")

# by importing db you expose it to the _dashboard/dbadmin
from .models import db, create_global_parameter

# by importing controllers you expose the actions defined in it
from . import controllers

# optional parameters
__version__ = "0.2"
__author__ = "Shiplu Hawlader and Vinhthuy Phan"
__license__ = "Not decided yet"
