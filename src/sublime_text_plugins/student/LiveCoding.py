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

DEBUG = True

menu_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu")
settings_file =os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.json")
if not os.path.exists(settings_file):
    with open(settings_file, 'w') as f:
        f.write("{\"server_address\": \"\", \"username\": \"\"}")
settings = json.load(open(settings_file, 'r'))
# print(settings)
default_menu = json.load(open(menu_file, 'r'))
colearningSERVER = "" #http://shiplu.pythonanywhere.com/colearning/"
if 'server_address' in settings:
	colearningSERVER = settings['server_address']
folderPath = os.path.join(os.path.expanduser('~'), 'CL')

colearningCookieFile = os.path.join(folderPath, "cookies")
feedbackFolder = os.path.join(folderPath, "FEEDBACK")
if not os.path.exists(folderPath):
	os.mkdir(folderPath)
if not os.path.exists(feedbackFolder):
	os.mkdir(feedbackFolder)
SYNC_INTERVAL = 30

loaded_problems = {}
last_saved_code = {}
last_saved_problems = None
student_id = None
session = ''
session_expiration_time = None

def send_all_codes():
	for problem_id, view in loaded_problems.items():
		code = view.substr(sublime.Region(0, view.size())).lstrip()
		if DEBUG:
			print(problem_id)
		if code == last_saved_code[problem_id]:
			continue
		last_saved_code[problem_id] = code
		data = {'content': code, 
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
			loadColearningFeedback(notif['type_id'])
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

def loadColearningFeedback(feedback_id):
	global feedbackFolder
	feedback = json.loads(colearningRequest("get_feedback/"+str(feedback_id), data={}))
	snapshot_filename = feedback['problem_name']+(".py" if feedback['language']=="Python" else ".java" if feedback['language']=='Java' else ".cpp")
	snapshot_filename = os.path.join(feedbackFolder, snapshot_filename)
	with open(snapshot_filename, 'w+') as f:
		f.write(feedback['code_snapshot'])
	
	feedback_filename = os.path.join(feedbackFolder, "feedback.txt")
	with open(feedback_filename, 'w+') as f:
		f.write(feedback['feedback'])

	sublime.run_command("new_window")
	current_window = sublime.active_window()
	current_window.set_layout({
			"cols": [0, 0.5, 1],
			"rows": [0, 1],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		})
	code_view = current_window.open_file(snapshot_filename)
	code_view.set_read_only(True)
	current_window.focus_group(1)
	feedback_view = current_window.open_file(feedback_filename)
	feedback_view.set_read_only(True)
	
	

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
		idx = 3
		while idx < len(menu[0]['children']):
			if menu[0]['children'][idx]['caption'] == 'Submit Code':
				break
			idx += 1

		if menu[0]['children'][idx]['caption'] != 'Submit Code':
			print('Submit code menu not found!')
			return
		idx -= 1
		for i in range(len(problem_info)):
			problem = problem_info[i]
			if i+2<idx:
				menu[0]['children'][i+2] = {"caption": problem['problem_name'], "command": "load_colearning_problem", 'id': "loadColearningProblem"+str(problem['id']), 'args': {'problem_id': problem['id']}}
			else:
				menu[0]['children'].insert(i+2, {"caption": problem['problem_name'], "command": "load_colearning_problem", 'id': "loadColearningProblem"+str(problem['id']), 'args': {'problem_id': problem['id']}})
		i = len(problem_info)
		while i+2<idx:
			menu[0]['children'].pop(i+2)
			idx -= 1
		
		with open(menu_file, 'w') as f:
			json.dump(menu, f)
		sublime.message_dialog("Problems has been updated.")

class colearningViewProblem(sublime_plugin.WindowCommand):
	def is_visible(self):
		return len(loaded_problems)> 0 and is_authenticated()

	def run(self):
		current_view = sublime.active_window().active_view()
		for problem_id, view in loaded_problems.items():
			if view == current_view:
				url = os.path.join(colearningSERVER, "problem/"+str(problem_id))
				webbrowser.open(url)
				return
		sublime.message_dialog("No problem selected.")

class loadColearningProblemCommand(sublime_plugin.TextCommand):
	def is_visible(self):
		return is_authenticated()

	def run(self, edit, problem_id):
		problem = colearningRequest('load_problem/'+str(problem_id), {}, 'GET')
		problem = json.loads(problem)
		filename = os.path.join(folderPath, problem['problem_name']+('.py' if problem['language']=='Python' else '.cpp' if problem['language']=='C++' else '.java'))
		with open(filename, 'w', encoding='utf-8') as f:
			f.write(problem['code'])

		if sublime.active_window().id() == 0:
			sublime.run_command('new_window')
		sublime.active_window().open_file(filename)
		loaded_problems[problem_id] = sublime.active_window().active_view()
		last_saved_code[problem_id] = ''

class colearningSubmitCode(sublime_plugin.WindowCommand):
	def is_visible(self):
		return is_authenticated()
	
	def run(self):
		current_view = sublime.active_window().active_view()
		for problem_id, view in loaded_problems.items():
			if view == current_view:
				code = view.substr(sublime.Region(0, view.size())).lstrip()
				data = {'problem_id': problem_id, 'category': 1, 'content': code}
				response = colearningRequest('editor_submission_handler', data, method='POST')
				sublime.message_dialog(response)
				return
		sublime.message_dialog("Nothing to be submitted!")

class saveColearningWorkspace(sublime_plugin.ApplicationCommand):
	def is_visible(self):
		return is_authenticated()
	
	def run(self):
		send_all_codes()

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
					rsp = json.loads(response.read().decode(encoding="utf-8"))
					# print(rsp)
					if rsp['code'] != 200:
						sublime.message_dialog('Login Failed!')
					else:
						sublime.message_dialog("Hi {0}, you have successfully logged in.".format(rsp['user']['first_name']))
						ck = cookies.SimpleCookie()
						ck.load(response.info()['Set-Cookie'])
						# print(ck['colearning_session'].value)
						# print(rsp)
						student_id = rsp['user']['id']
						session = ck['colearning_session'].value
						session_expiration_time = datetime.datetime.now() + datetime.timedelta(hours=2)
						# with open(colearningCookieFile, 'wb') as f:
						# 	pickle.dump({'colearning_session': session, 'session_expiration': session_expiration_time}, f)
						notification_scheduler(notification_stop_contidion)
						return
			except urllib.error.HTTPError as err:
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