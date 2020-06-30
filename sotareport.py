#!/usr/bin/python3

import os
import sys
import requests
import datetime
from dateutil.parser import parse as parsedate
from time import strptime
import csv
from math import sin, cos, sqrt, atan2, radians
import readline
import signal

SUMMIT_DB_URL = 'https://www.sotadata.org.uk/summitslist.csv'
SUMMIT_DB_FILE = os.path.expanduser('~/.cache/sotareport/summitslist.csv')
SPACE_PADDING = 20

summits = {}
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

def update_summit_db():
	os.makedirs(os.path.dirname(SUMMIT_DB_FILE), exist_ok=True)
	r = requests.head(SUMMIT_DB_URL)
	try:
		file_last_updated = datetime.datetime.fromtimestamp(os.path.getmtime(SUMMIT_DB_FILE))
	except FileNotFoundError:
		file_last_updated = datetime.datetime.fromtimestamp(0)
	if parsedate(r.headers['last-modified']) > file_last_updated.replace(tzinfo=datetime.timezone.utc):
		print('Updating summit cache ', end='')
		r = requests.get(SUMMIT_DB_URL, allow_redirects=True, stream=True)
		with open(SUMMIT_DB_FILE, 'wb') as f:
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

def input_callsign(query):
	while True:
		call = input(query)
		if len(call) >= 3:
			return call
		else:
			print("Error: Callsign too short")

def input_time(query):
	while True:
		time = input(query)
		try:
			if len(time) == 4:
				time = time[0:2] + ':' + time[2:4]
			if time[1] == ':':
				time = '0' + time
			strptime(time, '%H:%M')
			return time
		except:
			print("Error: Invalid time format - use HHMM or HH:MM 24h UTC")

def input_date(query):
	while True:
		date = input(query)
		try:
			strptime(date, '%d/%m/%y')
			return date
		except:
			print("Error: Invalid date format - use DD/MM/YY")

def input_summit(query, allow_empty=False):
	while True:
		summit = input(query)
		if summit == '' and allow_empty:
			return summit
		try:
			s = summits[summit]
			return summit
		except KeyError:
			print("Error: Summit not found")

def signal_handler(sig, frame):
	print("\nExiting.")
	sys.exit(0)



signal.signal(signal.SIGINT, signal_handler)

try:
	output_file = sys.argv[1]
except:
	print("The sotareport SOTA Log Submit Tool")
	print("===================================\n")
	print("This tool will append the given log to the output file.\n")
	print("Usage: %s OUTPUTFILE" % sys.argv[0])
	sys.exit(1)

update_summit_db()
load_summit_db()

print_line()
print('Enter station info:')
callsign = input_callsign(strpad('Your Callsign: '))
summit = input_summit(strpad('Your Summit: '), True)
if summit:
	print(strpad('Found Summit: '), end='')
	print("%(SummitName)s (%(AltM)sm), %(RegionName)s, %(AssociationName)s" % summits[summit])
else:
	print(strpad('No summit: ') + 'Assuming chaser')
date = input_date(strpad('Date (DD/MM/YY): '))
print_line()

with open(output_file, 'a') as f:
	print("Adding log to '%s' - Press CTRL+C to close" % output_file)
	csvfile = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
	while True:
		print('Enter QSO #%i:' % (len(log)+1))
		time = input_time(strpad('Time (HHMM - UTC): '))
		remote_callsign = input_callsign(strpad('Callsign: '))
		freq = rlinput(strpad('Freq (21MHz/80m): '), freq).lower().replace('mhz', 'MHz').replace(' ', '')
		mode = rlinput(strpad('Mode (CW/SSB/FM): '), mode).upper()
		remote_summit = input_summit(strpad('S2S Summit: ' if summit else 'Chased Summit: '), bool(summit)) # don't allow empty value for chasers here
		if remote_summit:
			print(strpad('Found Summit: ') + "%(SummitName)s (%(AltM)sm), %(RegionName)s, %(AssociationName)s" % summits[remote_summit])
			if summit:
				print(strpad('Distance: ') + "%ikm" % summit_distance(summit, remote_summit))
		comment = input(strpad('Comment: '))
		log.append({
			'time': time,
			'remote_callsign': remote_callsign,
			'mode': mode,
			'freq': freq,
			'remote_summit': remote_summit,
			'comment': comment,
		})
		# [V2] [My Callsign][My Summit] [Date] [Time] [Band] [Mode] [His Callsign] [His Summit] [Notes or Comments]
		csvfile.writerow(['V2', callsign, summit, date, time, freq, mode, remote_callsign, remote_summit, comment])
		f.flush()
		print_line()