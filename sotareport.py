#!/usr/bin/env python3

import os
import sys
import requests
import datetime
from dateutil.parser import parse as parsedate
import csv
from math import sin, cos, sqrt, atan2, radians
import readline
import argparse
import traceback

SUMMIT_DB_URL = 'https://www.sotadata.org.uk/summitslist.csv'
SUMMIT_DB_FILE = os.path.expanduser('~/.cache/sotareport/summitslist.csv')
NAMES_DB_URL = 'https://hb9sota.ch/names_hb9bin/names.csv'
NAMES_DB_FILE = os.path.expanduser('~/.cache/sotareport/names.csv')
SPACE_PADDING = 20

summits = {}
names = {}
log = []
mode = ''
freq = ''

def geo_distance(lat1, lon1, lat2, lon2):
	# approximate radius of earth in km
	R = 6373.0

	lat1 = radians(lat1)
	lon1 = radians(lon1)
	lat2 = radians(lat2)
	lon2 = radians(lon2)

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	return R * c

def update_db(name, url, dbfile):
	os.makedirs(os.path.dirname(dbfile), exist_ok=True)
	r = requests.head(url)
	try:
		file_last_updated = datetime.datetime.fromtimestamp(os.path.getmtime(dbfile))
	except FileNotFoundError:
		file_last_updated = datetime.datetime.fromtimestamp(0)
	if parsedate(r.headers['last-modified']) > file_last_updated.replace(tzinfo=datetime.timezone.utc):
		print('Updating %s cache ' % name, end='')
		r = requests.get(url, allow_redirects=True, stream=True)
		with open(dbfile, 'wb') as f:
			for chunk in r.iter_content(1024*1024):
				sys.stdout.write('.')
				sys.stdout.flush()
				f.write(chunk)
			sys.stdout.write("\n")


def load_summit_db():
	f = open(SUMMIT_DB_FILE, 'r')
	f.readline() # skip first line that looks like "SOTA Summits List (Date=29/06/2020)"
	for summit in csv.DictReader(f):
		summits[summit['SummitCode']] = summit

def load_name_db():
	try:
		f = open(NAMES_DB_FILE, 'r')
		for e in csv.DictReader(f):
			names[e['Call']] = e['Name']
	except:
		traceback.print_exc()
		pass

def summit_distance(summit1, summit2):
	s1 = summits[summit1]
	s2 = summits[summit2]
	return geo_distance(float(s1['Latitude']), float(s1['Longitude']), float(s2['Latitude']), float(s2['Longitude']))

def print_line():
	print('#'*70)

def strpad(s):
	return ' '*(SPACE_PADDING-len(s)) + s

def rlinput(prompt, prefill=''):
	readline.set_startup_hook(lambda: readline.insert_text(prefill))
	try:
		return input(prompt)
	finally:
		readline.set_startup_hook()

def input_callsign(query, default=''):
	while True:
		call = rlinput(query, default).upper()
		if len(call) >= 3:
			if call in names:
				print(strpad('Found in HB9SOTA: ') + 'Name: %s' % names[call])
			return call
		else:
			print("Error: Callsign too short")

def input_time(query, default=''):
	while True:
		if isinstance(default, datetime.time):
			default = default.strftime('%H:%M')
		time = rlinput(query, default)
		try:
			if len(time) == 4:
				time = time[0:2] + ':' + time[2:4]
			if time[1] == ':':
				time = '0' + time
			return datetime.datetime.strptime(time, '%H:%M').time()
		except:
			print("Error: Invalid time format - use HHMM or HH:MM 24h UTC")

def input_date(query, default=''):
	while True:
		if isinstance(default, datetime.date):
			default = default.strftime('%d.%m.%Y')
		date = rlinput(query, default)
		try:
			return datetime.datetime.strptime(date, '%d.%m.%Y').date()
		except:
			print("Error: Invalid date format - use DD.MM.YYYY")

def input_summit(query, allow_empty=False, default=''):
	while True:
		summit = rlinput(query, default).upper()
		if summit == '' and allow_empty:
			return summit
		try:
			s = summits[summit]
			return summit
		except KeyError:
			print("Error: Summit not found")

def query_qso(default={'time': '', 'remote_callsign': '', 'freq': None, 'mode': None, 'rst_gvn': '', 'rst_rec': '', 'remote_summit': '', 'comment': ''}):
	global freq
	global mode
	default = default.copy() # default from function header is readonly
	default['mode'] = mode if default['mode'] == None else default['mode']
	default['freq'] = freq if default['freq'] == None else default['freq']
	time = input_time(strpad('Time (HHMM - UTC): '), default['time'])
	remote_callsign = input_callsign(strpad('Callsign: '), default['remote_callsign'])
	freq = rlinput(strpad('Freq (7MHz/21MHz): '), default['freq']).lower().replace('mhz', 'MHz').replace(' ', '')
	mode = rlinput(strpad('Mode (CW/SSB/FM): '), default['mode']).upper()
	rst_gvn = "" if args.no_rst else rlinput(strpad('RST given: '), default['rst_gvn']).upper()
	rst_rec = "" if args.no_rst else rlinput(strpad('RST received: '), default['rst_rec']).upper()
	remote_summit = input_summit(strpad('S2S Summit: ' if summit else 'Chased Summit: '), bool(summit), default['remote_summit']) # don't allow empty value for chasers here
	if remote_summit:
		print(strpad('Found Summit: ') + "%(SummitName)s (%(AltM)sm), %(RegionName)s, %(AssociationName)s" % summits[remote_summit])
		if summit:
			print(strpad('Distance: ') + "%ikm" % summit_distance(summit, remote_summit))
	comment = rlinput(strpad('Comment: '), default['comment'])
	return {
		'time': time,
		'remote_callsign': remote_callsign,
		'freq': freq,
		'mode': mode,
		'remote_summit': remote_summit,
		'rst_gvn': rst_gvn,
		'rst_rec': rst_rec,
		'comment': comment,
	}

def write_csv(filename, mode):
	with open(filename, mode) as f:
		csvfile = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
		for l in log:
			# add RST to comment as CSV spec lacks RST field
			comments = []
			if l['comment']:
				comments.append(l['comment'])
			if l['rst_gvn']:
				comments.append('GVN: %s' % l['rst_gvn'])
			if l['rst_rec']:
				comments.append('REC: %s' % l['rst_rec'])
			comment = ', '.join(comments)

			# [V2] [My Callsign][My Summit] [Date] [Time] [Band] [Mode] [His Callsign] [His Summit] [Notes or Comments]
			csvfile.writerow(['V2', callsign, summit, date.strftime('%d/%m/%y'), l['time'].strftime('%H:%M'), l['freq'], l['mode'], l['remote_callsign'], l['remote_summit'], comment])

def update_backup():
	write_csv('.'+args.output_file+'.bak', 'w')

def command_handler():
	print("\x1b[2K\rAvailable Commands:")
	print('E <num> : Edit QSO <num>')
	print('C       : Continue entering logs')
	print('S       : Save and exit')
	while True:
		try:
			cmd = input('cmd> ').upper()
			if cmd == '' or cmd == 'C':
				return
			elif cmd.startswith('E'):
				try:
					qso = int(cmd.split(' ')[1])
					print('Edit QSO #%i:' % qso)
					l = query_qso(log[qso-1])
					log[qso-1] = l
					update_backup()
				except (ValueError, IndexError):
					print("Error: Invalid QSO index")
			elif cmd == 'D':
				import pdb; pdb.set_trace()
			elif cmd == 'S':
				write_csv(args.output_file, 'a')
				os.unlink('.'+args.output_file+'.bak')
				sys.exit(0)
		except KeyboardInterrupt:
			input('Press Ctrl+C to quit without saving - or press ENTER to return to CMD prompt.')


parser = argparse.ArgumentParser(description="This tool will append the given log to the output file.")
parser.add_argument("-r", "--no-rst", help="Don't ask for RST", action="store_true")
parser.add_argument("output_file", help="Write CSV to this file")
args = parser.parse_args()

update_db('summit', SUMMIT_DB_URL, SUMMIT_DB_FILE)
load_summit_db()

update_db('name', NAMES_DB_URL, NAMES_DB_FILE)
load_name_db()

print_line()
print('Enter station info:')
callsign = input_callsign(strpad('Your Callsign: ')).upper()
summit = input_summit(strpad('Your Summit: '), True)
if summit:
	print(strpad('Found Summit: ') + "%(SummitName)s (%(AltM)sm), %(RegionName)s, %(AssociationName)s" % summits[summit])
else:
	print(strpad('No summit: ') + 'Assuming chaser')
date = input_date(strpad('Date (DD.MM.YYYY): '))
print_line()

print("Adding log to '%s' - Press CTRL+C to edit previous QSOs or exit" % args.output_file)
while True:
	print('Enter QSO #%i:' % (len(log)+1))
	try:
		l = query_qso()
		log.append(l)
		update_backup()
		print_line()
	except KeyboardInterrupt:
		command_handler()
		print_line()
