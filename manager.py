import requests
import thread
import time
from time import sleep
from random import choice
import json
import os
import argparse
import pickle
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('settings.conf')

API_ID = config.get('DigitalOceanAPI', 'API_ID')
API_KEY = config.get('DigitalOceanAPI', 'API_KEY')

managerServerID = config.get('DigitalOceanSettings', 'managerServerID')

imageID = config.get('DigitalOceanDropletSettings', 'image')
keyID = config.get('DigitalOceanDropletSettings', 'key')
sizeID = config.get('DigitalOceanDropletSettings', 'size')
hostname = config.get('DigitalOceanDropletSettings', 'hostname')

url = 'https://api.digitalocean.com/droplets/?client_id='+API_ID+'&api_key='+API_KEY

#List of times for api calls to digital ocean. An avagerage of this is used to for timeouts.
averagetimeout = [4]

serverList = []
timeoutList = []
confirmDestroy = []

parser = argparse.ArgumentParser(description="Start and stop Digital Ocean Droplets.")
parser.add_argument('-a', choices=['start', 'stop', 'status', 'rebuild'], help='Specify the action desired: start, stop, status, rebuild', required=True)

#Need to require number of droplets if action = start


parser.add_argument('-q', help='Specify the number of droplets (Default is 5)', type=int, default = 5)
parser.add_argument('-n', help='Specify the hostname of the droplets (Default is \'server-\')', type=str, default = "server")
parser.add_argument('-t', help='Specify timeout limit (in seconds) (default is 600 seconds)', type=int, default=600)
parser.add_argument('--verbose', '-v', help="Add v to have limited verbosity, add another v to give debug messages", action='count')
args = vars(parser.parse_args())
action = args['a']
totalServers = args['q']
activetimeout = args['t']
hostname = args['n']
hostname.replace(' ', '_').lower()
hostname = hostname + "-"
verbose = args['verbose']
		
class Droplet:
	def __init__(self, region, image, key, size, hostname):
		self.hostname = str(hostname)
		self.imageID = str(image)
		self.sizeID = str(size)
		self.region = str(region)
		self.keyID = str(key)
		self.DropletID = "N/A"
		
	def build(self):
		if verbose:
			print "Creating new droplet: "+self.hostname
		try:
			r = requests.get("https://api.digitalocean.com/droplets/new?client_id="+API_ID+"&api_key="+API_KEY+"&name="+self.hostname+"&size_id="+self.sizeID+"&image_id="+self.imageID+"&region_id="+self.region+"&ssh_key_ids="+self.keyID, timeout=500)
		except requests.exceptions.Timeout:
			print "YO THIS SHIT TIMED OUT"
		
		result = r.json()
		if result['status'] != "OK":
			if verbose:
				print "Failed Creating Droplet"
				if verbose > 1:
					print result['error_message']
			self.status = "Failed"
		else:
			self.DropletID = str(result['droplet']['id'])
			self.status = "new"

	def setID(self, newid):
		self.DropletID = str(newid)
	
	def display(self):
		print "Droplet Hostname: "+self.hostname
		print "      Droplet ID: "+self.DropletID
		print "  Droplet Region: "+self.region
		print "      Droplet IP: "+self.IP
		print "  Droplet Status: "+self.status
		print "------------------------------"

	def getIP(self):
		r = requests.get("https://api.digitalocean.com/droplets/"+self.DropletID+"?client_id="+API_ID+"&api_key="+API_KEY)
		result = r.json()
		if result['status'] == "OK":
			return str(result['droplet']['ip_address'])
		else:
			return result['error_message']
	
	def setIP(self, newip):
		self.IP = str(newip)
		
	def getID(self):
		return str(self.DropletID)

	def getHostname(self):
		return str(self.hostname)

	def isActive(self):
		r = requests.get("https://api.digitalocean.com/droplets/"+self.DropletID+"?client_id="+API_ID+"&api_key="+API_KEY)
		result = r.json()
		if result['droplet']['status'] == "active":
			return True
		else:
			return False

	def getStatus(self):
		r = requests.get("https://api.digitalocean.com/droplets/"+self.DropletID+"?client_id="+API_ID+"&api_key="+API_KEY)
		result = r.json()
		return str(result['droplet']['status'])

	def setStatus(self, newstatus):
		self.status = str(newstatus)
		
	def waitTillActive(self):
		if self.status != "Failed":
			r = requests.get("https://api.digitalocean.com/droplets/"+self.DropletID+"?client_id="+API_ID+"&api_key="+API_KEY)
			result = r.json()
			#print "Waiting for "+serverID+" to become active"
			self.startUpTime = 0
			while self.status == "new":
				if self.startUpTime <= activetimeout:
					r = requests.get("https://api.digitalocean.com/droplets/"+self.DropletID+"?client_id="+API_ID+"&api_key="+API_KEY)
					result = r.json()
					if result['droplet']['status'] == "active":
						self.status = "active"
					else:
						if self.startUpTime < 1:
							sleep(60)
							self.startUpTime += 60
						elif self.startUpTime <= 60:
							sleep(10)
							self.startUpTime += 10
						elif self.startUpTime <= 90:
							sleep(7)
							self.startUpTime += 7
						else:
							sleep(5)
							self.startUpTime += 5
				else:
					self.status = "Error: Did not become active within time limit"
		return self.status
		#if verbose > 1:
		#	print serverID+" is active"

	def destroy(self):
		r = requests.get("https://api.digitalocean.com/droplets/"+self.DropletID+"/destroy/?client_id="+API_ID+"&api_key="+API_KEY+"&scrub_data=1")
		result = r.json()
		if result['status'] == "OK":
			if verbose:
				print "Destroyed droplet "+str(self.DropletID)
			self.status = "destroyed"
		else:
			self.status = result['error_message']
		return self.status

def countDroplets():
	r = requests.get('https://api.digitalocean.com/droplets/?client_id='+API_ID+'&api_key='+API_KEY)
	result = r.json()
	count = 0
	for droplet in result['droplets']:
		if droplet['name'] != "Manager":
			if droplet['status'] == 'active':
				count = count + 1
	return str(count)


def rebuildLists():
	global serverList
	r = requests.get('https://api.digitalocean.com/droplets/?client_id='+API_ID+'&api_key='+API_KEY)
	result = r.json()
	serverList = []
	for droplet in result['droplets']:
		if droplet['name'] != "Manager":
			if verbose > 1:
				print "Adding droplet " + str(droplet['id'])
			curDroplet = Droplet(droplet['region_id'], droplet['image_id'], getSSHKeys(keyID), droplet['size_id'], droplet['name'])
			curDroplet.setStatus(droplet['status'])
			curDroplet.setIP(droplet['ip_address'])
			curDroplet.setID(droplet['id'])
			serverList.append(curDroplet)
	with open('activelist.txt', 'wb') as output:
		pickle.dump(serverList, output)
	if verbose > 1:
		print "Done rebuilding server list"
	return serverList


def getSizeID(wantedSize):
	sizeid = "33"
	r = requests.get("https://api.digitalocean.com/sizes/?client_id="+API_ID+"&api_key="+API_KEY)
	result = r.json()
	for size in result['sizes']:
		if size['name'] == wantedSize:
			sizeid = size['id']
	return str(sizeid)
	
def getImageID(imageName):
	r = requests.get("https://api.digitalocean.com/images/?client_id="+API_ID+"&api_key="+API_KEY+"&filter=my_images")
	result = r.json()
	#print result
	for image in result['images']:
		if image['name'] == imageName:
			imageID = image['id']
	return str(imageID)

def getRegions():
	regions = []
	r = requests.get("https://api.digitalocean.com/regions/?client_id="+API_ID+"&api_key="+API_KEY)
	result = r.json()
	for region in result['regions']:
		regions.append(str(region['id']))
	return regions

def getSSHKeys(keyName):
	r = requests.get("https://api.digitalocean.com/ssh_keys/?client_id="+API_ID+"&api_key="+API_KEY)
	result = r.json()
	for key in result['ssh_keys']:
		if key['name'] == keyName:
			keyid = key['id']
	return str(keyid)

def createDroplet(regions, image, size, sshkey, name):
	global totalServers
	global DropletList
	selectedRegion = choice(regions)
	start = time.time()
	curDroplet = Droplet(selectedRegion, getImageID(image), getSSHKeys(sshkey), getSizeID(size), curHostname)
	curDroplet.build()
	elapsed = (time.time() - start)
	averagetimeout.append(elapsed)
	serverList.append(curDroplet)
	curDroplet.waitTillActive()
	if curDroplet.status == "active":
		curDroplet.IP = curDroplet.getIP()
		if verbose > 1:
			print curDroplet.DropletID + " is active"
	else:
		#print curDroplet.DropletID + " " + curDroplet.status
		serverList.remove(curDroplet)
		totalServers -= 1
		if curDroplet.status != "Failed":
			timeoutList.append(curDroplet)

def getAverage(list):
	if len(list) > 10:
		list.pop(0)
	return sum(list) / float(len(list)) + .5

	
	
if action == "start":
	totalTime = time.time()
	regions = getRegions()
	curServer = 1
	print "Creating "+ str(totalServers) +" droplets"

	countingServers = totalServers

	while curServer < (countingServers + 1):
		curHostname = hostname + str(curServer)

		curServer += 1
		params = regions, imageID, sizeID, keyID, curHostname
		
		try:
			if verbose > 1:
				print "Starting create thread for " + curHostname
			thread.start_new_thread(createDroplet, params)
		except:
			if verbose > 1:
				print "Thread died or something..."
		avgTime = getAverage(averagetimeout)
		if verbose > 1:
			print "Waiting average creation time: " + str(avgTime)
		sleep(avgTime)
		

	activeServers = 0

	activeList = []

	start = time.time()
	if verbose:
		print "Waiting for droplets to become active."
	while activeServers < totalServers:
		for server in serverList:
			#print "Checking " + server.getHostname() + " - " +server.status
			if server.status != "new":
				if server not in activeList:
					activeServers += 1
					activeList.append(server)
		
		#if verbose > 1:
			#print str(activeServers) + " of " + str(totalServers) + " are active"
		sleep(2)
		#os.system('clear')
	elapsed = (time.time() - start)

	del activeList
	print "Done creating droplets."
	if verbose:
		print "After " + str(elapsed) + " seconds, all droplets are up!"

	if verbose > 1:
		for server in serverList:
			server.display()

	if verbose:
		print str(len(timeoutList)) + " servers timed out during creation."
			
	if verbose > 1:
		print "Saving current list of servers..."			
		
	if os.path.exists('activelist.txt'):
		with open('activelist.txt', 'rb') as input:
			newList = pickle.load(input)
			serverList = serverList + newList
		with open('activelist.txt', 'wb') as output:
			pickle.dump(serverList, output)
	else:	
		with open('activelist.txt', 'wb') as output:
			pickle.dump(serverList, output)

	if len(timeoutList) > 0:
		if os.path.exists('timeoutlist.txt'):
			with open('timeoutlist.txt', 'rb') as input:
				newList = pickle.load(input)
				timeoutList = timeoutList + newList
			with open('timeoutlist.txt', 'wb') as output:
				pickle.dump(timeoutList, output)
		else:	
			with open('timeoutlist.txt', 'wb') as output:
				pickle.dump(timeoutList, output)
	if verbose:
		totalTime = (time.time() - totalTime)
		print "Total time to create: " + str(totalTime)
	
elif action == "stop":
	totalTime = time.time()
	if os.path.exists('activelist.txt'):
		with open('activelist.txt', 'rb') as input:
			serverList = pickle.load(input)
			
	else:
		if verbose:
			print "No activelist.txt, maybe no servers are running?"
		exit()
		
	if os.path.exists('timeoutlist.txt'):
		with open('timeoutlist.txt', 'rb') as input:
			timeoutList = pickle.load(input)

	count = 0
	if len(serverList) > 0:
		if totalServers >= len(serverList):
			print "Destroying all droplets in 3 seconds"
			sleep(3)
			while len(serverList) > 0:
				for server in serverList:
					if server.getStatus() == "active":
						server.destroy()
						serverList.remove(server)
					else:
						if verbose > 1:
							print server.getID() + " status not active"
		else:
			print "Destroying "+ str(totalServers) + " droplets in 3 seconds"
			sleep(3)
			while count <= totalServers - 1:
				for server in serverList:
					if count >= totalServers:
						break
					if server.getStatus() == "active":
						server.destroy()
						serverList.remove(server)
						count += 1
					else:
						if verbose > 1:
							print server.getID() + " status not active"
							
	else:
		if verbose:
			print "There are no active servers to kill"
	
	if verbose:
		print "Checking for dead servers"
		
	if len(timeoutList) > 0:
		if verbose:
			print "Waiting 120 Seconds, then destroying servers that timed out."
		sleep(120)
		while len(timeoutList) > 0:
			for server in timeoutList:
				server.waitTillActive()
				server.destroy()
				timeoutList.remove(server)
	else:
		if verbose > 1:
			print "No dead servers"
	
	if len(serverList) > 0:
		if verbose > 1:
			print "Saving current list of servers..."
		with open('activelist.txt', 'wb') as output:
			pickle.dump(serverList, output)
	else:
		if verbose > 1:
			print "Deleting list of active servers"
		try:
			os.remove("activelist.txt")
		except:
			pass
	if len(timeoutList) > 0:
		with open('timeoutlist.txt', 'wb') as output:
			pickle.dump(timeoutList, output)
	else:
		if verbose > 1:
			print "Deleting list of timed out servers"
		try:
			os.remove("timeoutlist.txt")
		except:
			pass
	print "Done destroying droplets"
	
	if verbose:
		totalTime = (time.time() - totalTime)
		print "Total time to destroy: " + str(totalTime)
	
elif action == "status":
	digiOceanCount = countDroplets()
	try:
		print "There are " + str(digiOceanCount) + " droplets currently running"
		if verbose:
			with open('activelist.txt', 'rb') as input:
				serverList = pickle.load(input)
			for server in serverList:
				server.display()
	except IOError:
		if verbose:
			print "No servers are currently active"
	if int(digiOceanCount) !=  len(serverList):
		print "Number of servers reported by Digital Ocean's API does not match the current server list. Rebuilding list now"
		rebuildLists()
		if verbose:
			with open('activelist.txt', 'rb') as input:
				serverList = pickle.load(input)
			for server in serverList:
				server.display()
	
elif action == "rebuild":
	rebuildLists()
	
# print "Confirm all are destroyed:"
# for server in serverList:
# 	print server.display()
