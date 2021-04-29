# LiveCoding
# Author: Shiplu Hawlder, 2020
#
import sublime, sublime_plugin
import urllib.parse
import urllib.request
import os
import json
import datetime
import threading
from http import cookies
import webbrowser
import pickle

import sched
import time
import math
from shutil import copyfile

DEBUG = True

menu_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu")
menu_backup_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu.bk")
settings_file =os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.json")
if not os.path.exists(settings_file):
    with open(settings_file, 'w') as f:
        f.write("{\"server_address\": \"\", \"username\": \"\"}")
settings = json.load(open(settings_file, 'r'))
# print(settings)
copyfile(menu_backup_file, menu_file)
default_menu = json.load(open(menu_file, 'r'))
colearningSERVER = "" #http://shiplu.pythonanywhere.com/colearning/"
if 'server_address' in settings:
	colearningSERVER = settings['server_address']
folderPath = os.path.join(os.path.expanduser('~'), 'CL')

colearningCookieFile = os.path.join(folderPath, "cookies")
# feedbackFolder = os.path.join(folderPath, "FEEDBACK")
# commentFolder = os.path.join(folderPath, "COMMENTS")

if not os.path.exists(folderPath):
	os.mkdir(folderPath)

# if not os.path.exists(feedbackFolder):
# 	os.mkdir(feedbackFolder)

# if not os.path.exists(commentFolder):
# 	os.mkdir(commentFolder)

SYNC_INTERVAL = 30

loaded_problems = {}
# loaded_comments = {}
last_saved_code = {}
problem_max_points = {}
problem_attempts = {}
problem_deadlines = {}
# last_saved_comments = {}
last_saved_problems = None
student_id = None
session = ''
session_expiration_time = None

def send_all_codes():
	for problem_id, view in loaded_problems.items():
		code = view.substr(sublime.Region(0, view.size())).rstrip()
		# comment = loaded_comments[problem_id].substr(sublime.Region(0, loaded_comments[problem_id].size())).rstrip()
		if DEBUG:
			print(problem_id)
		if code == last_saved_code[problem_id]:
			continue
		last_saved_code[problem_id] = code
		# last_saved_comments[problem_id] = comment
		data = {'content': code, 
				# 'comment': comment,
				'problem_id': problem_id, 
				'student_id': student_id
				}
		if DEBUG:
			print("Saving problem "+str(problem_id))
		colearningRequest('save_workspace', data=data, method='POST')


def code_sending_scheduler(stop_condition):
	try:
		send_all_codes()
	except Exception as e:
		print(e)
	if not stop_condition.is_set():
		threading.Timer(SYNC_INTERVAL, code_sending_scheduler, [stop_condition]).start()

code_sending_stop_condition = threading.Event()
code_sending_scheduler(code_sending_stop_condition)

def get_notification():
	response = colearningRequest('get_editor_notification', data={},method='GET')
	if response is not None and response!="" and len(response)<500:
		notif = json.loads(response)
		print(notif)
		if notif['type'] is not None and notif['type'] == "feedback":
			sublime.message_dialog("You have a new feedback.")
			# loadColearningFeedback(notif['type_id'])
		else:
			sublime.message_dialog(notif['message'])

def notification_scheduler(stop_codition):
	try:
		get_notification()
		sublime.run_command("load_colearning_problem_info")
	except Exception as e:
		print(e)
	if not stop_codition.is_set():
		threading.Timer(SYNC_INTERVAL, notification_scheduler, [stop_codition]).start()

notification_stop_contidion = threading.Event()
# notification_scheduler(notification_stop_contidion)

class TestCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print("Hello World")

def colearningRequest(path, data, method='GET'):
	global colearningSERVER
	url = urllib.parse.urljoin(colearningSERVER, path)
	load = urllib.parse.urlencode(data).encode('utf-8')
	req = urllib.request.Request(url, load, method=method)
	if session is not None and session != '':
		req.add_header("Cookie", "colearning_session="+session)
	try:
		with urllib.request.urlopen(req, None, 5) as response:
			return response.read().decode(encoding="utf-8")
	except urllib.error.HTTPError as err:
		if DEBUG:
			sublime.message_dialog("{0}".format(err))
	except urllib.error.URLError as err:
		if DEBUG:
			sublime.message_dialog("{0}\nCannot connect to server.".format(err))
	print('Error making request')
	return "Error"

# def loadColearningFeedback(feedback_id):
# 	global feedbackFolder
# 	feedback = json.loads(colearningRequest("get_feedback/"+str(feedback_id), data={}))
# 	snapshot_filename = feedback['problem_name']+(".py" if feedback['language']=="Python" else ".java" if feedback['language']=='Java' else ".cpp")
# 	snapshot_filename = os.path.join(feedbackFolder, snapshot_filename)
# 	with open(snapshot_filename, 'w+') as f:
# 		f.write(feedback['code_snapshot'])
	
# 	feedback_filename = os.path.join(feedbackFolder, "feedback.txt")
# 	with open(feedback_filename, 'w+') as f:
# 		f.write(feedback['feedback'])

# 	sublime.run_command("new_window")
# 	current_window = sublime.active_window()
# 	current_window.set_layout({
# 			"cols": [0, 0.5, 1],
# 			"rows": [0, 1],
# 			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
# 		})
# 	code_view = current_window.open_file(snapshot_filename)
# 	code_view.set_read_only(True)
# 	current_window.focus_group(1)
# 	feedback_view = current_window.open_file(feedback_filename)
# 	feedback_view.set_read_only(True)
	
	

# class loadColearningProblemInfo(sublime_plugin.TextCommand):
# 	def run(self, edit):
# 		w = sublime.active_window()
# 		print(w.id(), w.active_view().id())

class loadColearningProblemInfo(sublime_plugin.ApplicationCommand):
	def is_visible(self):
		return is_authenticated()

	def run(self):
		global last_saved_problems
		problem_info = colearningRequest("get_problem_info", {}, 'GET')
		problem_info = json.loads(problem_info)
		if last_saved_problems == problem_info:
			# print("Not updating problems")
			return
		last_saved_problems = problem_info
		menu = default_menu.copy()
		p = []
		idx = 2
		while idx < len(menu[0]['children']):
			if menu[0]['children'][idx]['caption'] == '-':
				break
			idx += 1

		if menu[0]['children'][idx]['caption'] != '-':
			print('Login menu not found!')
			return
		
		for i in range(len(problem_info)):
			problem = problem_info[i]
			problem_menu = {"caption": problem['problem_name'], "id": problem['problem_name']+"_menu",\
					 "children": [{"caption": "Reload Code", "command": "load_colearning_problem", 'id': "loadColearningProblem"+str(problem['id']),\
						  'args': {'problem_id': problem['id']}}, {"caption": "Submit Code", "id": "colearningSubmitCode",\
							   "command": "colearning_submit_code", 'args': {'problem_id': problem['id']}}, \
								   {"caption": "View on App", "id": "colearningViewProblem", "command": "colearning_view_problem", 'args': {'problem_id': problem['id']}},\
									   {"caption": "Save", "id": "saveColearningWorkspace", "command": "save_colearning_workspace"}, \
									   {"caption": "Ask for Help", "id": "colearningAskForHelp", "command": "colearning_ask_for_help", 'args': {'problem_id': problem['id']}}]}
			if i+2<idx:
				menu[0]['children'][i+2] = problem_menu
			else:
				menu[0]['children'].insert(i+2, problem_menu)
		i = len(problem_info)
		while i+2<idx:
			menu[0]['children'].pop(i+2)
			idx -= 1
		
		with open(menu_file, 'w') as f:
			json.dump(menu, f)
		sublime.message_dialog("Problems has been updated.")

class colearningViewProblem(sublime_plugin.WindowCommand):

	def run(self, problem_id):
		url = os.path.join(colearningSERVER, "view_problem/"+str(problem_id))
		webbrowser.open(url)

class colearningHelpOthers(sublime_plugin.WindowCommand):
	def is_visible(self):
		return is_authenticated()
		
	def run(self):
		url = os.path.join(colearningSERVER, "help_message_list")
		webbrowser.open(url)

def get_due_time(deadline):
	now = datetime.datetime.utcnow()
	if deadline<=now:
		return 'expired'
	diff = deadline - now
	s = ""
	if diff.days>1:
		s+=str(diff.days)+" days "
	elif diff.days==1:
		s+=str(diff.days)+" day "
	seconds = math.floor(int(diff.total_seconds()))
	hours = seconds // 3600
	seconds = seconds % 3600
	minutes = seconds // 60
	seconds = seconds % 60
	if hours>1:
		s += str(hours)+" hours "
	elif hours == 1:
		s += str(hours) + " hour "
	if minutes>1:
		s += str(minutes)+" minutes "
	else:
		s += str(minutes) + " minute "
	if seconds>1:
		s += str(seconds)+" seconds"
	else:
		s += str(seconds) + " second"
	
	return s

class colearningProblemInformation(sublime_plugin.WindowCommand):
	def run(self, problem_id):
		sublime.message_dialog("Due in: "+get_due_time(problem_deadlines[problem_id])+"\nMax Point: "+str(problem_max_points[problem_id])+"\nNumber of attempt allowed: "+str(problem_attempts[problem_id]))


class loadColearningProblemCommand(sublime_plugin.TextCommand):
	def is_visible(self):
		return is_authenticated()

	def run(self, edit, problem_id):
		problem = colearningRequest('load_problem/'+str(problem_id), {}, 'GET')
		problem = json.loads(problem)
		code_filename = os.path.join(folderPath, problem['problem_name']+('.py' if problem['language']=='Python' else '.cpp' if problem['language']=='C++' else '.java'))
		
		sublime.run_command('new_window')
		current_window = sublime.active_window()
		if os.path.exists(code_filename):
			code_view = current_window.open_file(code_filename)
			response = sublime.yes_no_cancel_dialog(os.path.basename(code_filename)+" already exists. Do you want to keep the local file?", "Yes", "Load from remote workspace")
			if response == sublime.DIALOG_NO:
				response = sublime.ok_cancel_dialog("Warning: loading from remote workspace will overwrite local file", "Overwrite!")
				if response == True:
					with open(code_filename, 'w', encoding='utf-8') as f:
						f.write(problem['code'])
					code_view = current_window.open_file(code_filename)
		else:
			with open(code_filename, 'w', encoding='utf-8') as f:
				f.write(problem['code'])
			code_view = current_window.open_file(code_filename)
	
		loaded_problems[problem_id] = code_view
		# loaded_comments[problem_id] = comment_view
		last_saved_code[problem_id] = ''
		# last_saved_comments[problem_id] = ''
		# problem_deadlines[problem_id] = datetime.datetime.strptime(problem['deadline'], "%Y-%m-%d %H:%M:%S")
		# problem_attempts[problem_id] = problem['attempts']
		# problem_max_points[problem_id] = problem['max_points']
		# print(problem)

class colearningSubmitCode(sublime_plugin.WindowCommand):
	def is_visible(self):
		return is_authenticated()
	
	def run(self, problem_id):
		send_all_codes()
		view = loaded_problems[problem_id]
		code = view.substr(sublime.Region(0, view.size())).rstrip()		
		data = {'problem_id': problem_id, 'category': 1, 'content': code}
		response = colearningRequest('editor_submission_handler', data, method='POST')
		sublime.message_dialog(response)
		

class saveColearningWorkspace(sublime_plugin.ApplicationCommand):
	def is_visible(self):
		return is_authenticated()
	
	def run(self):
		send_all_codes()

class colearningAskForHelp(sublime_plugin.ApplicationCommand):
	def is_visible(self):
		return is_authenticated()
	
	def run(self, problem_id):
		global student_id
		send_all_codes()
		self.problem_id = problem_id
		url = os.path.join(colearningSERVER, "student_workspace_view/"+str(student_id)+"/"+str(problem_id))
		webbrowser.open(url)
		# sublime.active_window().show_input_panel("Explain the problem you are facing:", "", self.send_message, None, self.cancel_sending_message)
	
	def send_message(self, message):
		if message=="":
			sublime.message_dialog("Your help request message is too short.")
			return
		response = colearningRequest("save_help_request", {'message': message, 'problem_id': self.problem_id}, method='POST')
		sublime.message_dialog(response)

	def cancel_sending_message(self):
		sublime.message_dialog("Your help request has been canceled.")

class colearningLogin(sublime_plugin.ApplicationCommand):
	def __init__(self):
		self.email = ""

	def is_visible(self):
		global colearningSERVER
		return not is_authenticated() and colearningSERVER != ""
	
	def run(self):
		# try:
		# 	with open(gemsFILE, 'r') as f:
		# 		info = json.loads(f.read())
		# except:
		# 	info = dict()
		# if 'Email' not in info:
		# 	info['Email'] = ''
		if sublime.active_window().id() == 0:
			sublime.run_command('new_window')
		username = ""
		if 'username' in settings:
			username = settings['username']
		sublime.active_window().show_input_panel("Username:", username, self.getEmail, None, None)

	def getEmail(self, email):
		email = email.strip()
		if len(email)>0:
			panel = sublime.active_window().show_input_panel("Password:", "", self.getPassword, None, None)
			panel.settings().set("password", True)
			self.email = email
			if email != settings['username']:
				settings['username'] = email
				with open(settings_file, 'w') as f:
					json.dump(settings, f)
			
		else:
			sublime.message_dialog("Email cannot be empty.")
	
	def getPassword(self, password):
		global colearningSERVER
		global session
		global session_expiration_time
		global student_id
		global folderPath
		
		password = password.strip()
		if len(password)>0:
			data = {'email': self.email, 'password': password}
			url = urllib.parse.urljoin(colearningSERVER, 'auth/api/login')
			load = json.dumps(data).encode('utf-8')
			headers = {
				"Content-Type": "application/json",
				"Accept": "application/json",
			}
			# print(url, load, end="\n")
			req = urllib.request.Request(url, load, method='POST', headers=headers)
			# req.add_header('Conent-Type', 'application/json')
			try:
				with urllib.request.urlopen(req, None, 10) as response:
					print(response)
					rsp = json.loads(response.read().decode(encoding="utf-8"))
					# print(rsp)
					if rsp['code'] != 200:
						sublime.message_dialog('Login Failed!')
					else:
						ck = cookies.SimpleCookie()
						ck.load(response.info()['Set-Cookie'])
						folderPath = os.path.join(folderPath, rsp['user']['username'])
						if not os.path.exists(folderPath):
							os.mkdir(folderPath)
						url = urllib.parse.urljoin(colearningSERVER, 'get_app_id')
						req  = urllib.request.Request(url, method='GET')
						response = urllib.request.urlopen(req, None, 10)
						app_id = response.read().decode(encoding="utf-8")
						folderPath = os.path.join(folderPath, app_id)
						if not os.path.exists(folderPath):
							os.mkdir(folderPath)
						
						# print(ck['colearning_session'].value)
						# print(rsp)
						student_id = rsp['user']['id']
						session = ck['colearning_session'].value
						session_expiration_time = datetime.datetime.now() + datetime.timedelta(hours=2)
						# with open(colearningCookieFile, 'wb') as f:
						# 	pickle.dump({'colearning_session': session, 'session_expiration': session_expiration_time}, f)
						sublime.message_dialog("Hi {0}, you have successfully logged in.".format(rsp['user']['first_name']))
						notification_scheduler(notification_stop_contidion)
						return
			except urllib.error.HTTPError as err:
				# if err.code == 400:
				# 	response = urllib.request.urlopen(req, None, 10)
				# 	rsp = json.loads(response.read().decode(encoding="utf-8"))
				# 	sublime.message_dialog(rsp['message'])
				# else:
				sublime.message_dialog("{0}".format(err))
			except urllib.error.URLError as err:
				sublime.message_dialog("{0}\nCannot connect to server.".format(err))
			print('Something is wrong')
		else:
			sublime.message_dialog('Password cannot be empty.')


class colearningLogout(sublime_plugin.ApplicationCommand):

	def is_visible(self):
		return is_authenticated()
	
	def run(self):
		global session
		global colearningCookieFile
		session =''
		if os.path.exists(colearningCookieFile):
			os.remove(colearningCookieFile)
		sublime.message_dialog('You have been logged out successfully!')

class colearningSetServerAddressCommand(sublime_plugin.WindowCommand):
	def run(self):
		if 'server_address' in settings:
			server = settings['server_address']
		else:
			server = ""
		sublime.active_window().show_input_panel("Server Address:", server, self.set_server_address, None, None)
	
	def set_server_address(self, server_address):
		server_address = server_address.strip()
		if server_address=="":
			sublime.message_dialog("Server address can not be empty!")
			return
		if not server_address.startswith('http://'):
			server_address = "http://"+server_address
		if not server_address.endswith('/'):
			server_address = server_address + "/"
		
		global colearningSERVER
		url = urllib.parse.urljoin(server_address, "check_address")
		load = urllib.parse.urlencode({}).encode('utf-8')
		req = urllib.request.Request(url, load, method='GET')
		try:
			with urllib.request.urlopen(req, None, 5) as response:
				res = response.read().decode(encoding="utf-8")
				if res == "correct":
					colearningSERVER = server_address
					sublime.message_dialog("Server address set successfully.")
					if server_address != settings['server_address']:
						settings['server_address'] = server_address
						with open(settings_file, 'w') as f:
							json.dump(settings, f)
					return
		except urllib.error.HTTPError as err:
			if DEBUG:
				sublime.message_dialog("{0}".format(err))
		except urllib.error.URLError as err:
			if DEBUG:
				sublime.message_dialog("{0}\nCannot connect to server.".format(err))
		sublime.message_dialog("Invalid server address!")

def is_authenticated():
	global session
	global session_expiration_time
	global colearningCookieFile
	# if session == '' and os.path.exists(colearningCookieFile):
	# 	with open(colearningCookieFile, 'rb') as f:
	# 		cookies = pickle.load(f)
	# 		session = cookies['colearning_session']
	# 		session_expiration_time = cookies['session_expiration']
	if session != '' and session_expiration_time>=datetime.datetime.now():
		return True
	return False


def plugin_loaded():
	pass
def plugin_unloaded():
	code_sending_stop_condition.set()
	notification_stop_contidion.set()

	with open(menu_file, 'w') as f:
		json.dump(default_menu, f)
		
	with open(settings_file, 'w') as f:
		json.dump(settings, f)   