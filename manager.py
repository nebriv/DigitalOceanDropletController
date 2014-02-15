import thread
import time
from time import sleep
from random import choice
import os
import argparse
import ConfigParser

import requests
import pickle



# Creates blank Global Vars

API_ID = ""
API_KEY = ""
managerServerID = ""
imageID = ""
sizeID = ""
hostname = ""
url = ""
serverList = []
timeoutList = []
verbose = False

#List of times for api calls to digital ocean. An average of this is used to for timeouts.
averagetimeout = [4]
activetimeout = 0
keyID = ""
totalServers = 5


class Droplet:
    def __init__(self, region, image, key, size, hostname):
        """
        This class creates the droplet object.
        """

        self.hostname = str(hostname)
        self.imageID = str(image)
        self.sizeID = str(size)
        self.region = str(region)

        if key:
            self.keyID = str(key)
        else:
            self.keyID = None
        self.DropletID = "N/A"

    def build(self):
        """
        Name:           build

        Description:    Sends API call to D.O. to create new droplet

        Actions:        Uses the non standard requests library to send API call to D.O.
                            Check to see if an SSH Key was passed.
                        Uses globally set vars; API_ID and API_KEY

                        Checks if droplet was created properly or if an error occurred.

                        Uses API documentation located at: https://cloud.digitalocean.com/api_access
        """

        # Checks verbosity level to print creation start message
        if verbose:
            print "Creating new droplet: " + self.hostname

        # Attempts to send D.O. API call, uses non-standard "requests" library
        try:
            # Checks to see if a SSHKey is identified, sets API call result as r
            if self.keyID:
                r = requests.get(
                    "https://api.digitalocean.com/droplets/new?client_id=" + API_ID + "&api_key=" + API_KEY + "&name=" +
                    self.hostname + "&size_id=" + self.sizeID + "&image_id=" + self.imageID + "&region_id=" +
                    self.region + "&ssh_key_ids=" + self.keyID,
                    timeout=500)
            # Sets API call result as r
            else:
                r = requests.get(
                    "https://api.digitalocean.com/droplets/new?client_id=" + API_ID + "&api_key=" + API_KEY + "&name=" +
                    self.hostname + "&size_id=" + self.sizeID + "&image_id=" + self.imageID + "&region_id=" +
                    self.region, timeout=500)
        # Returns error if API call times out
        except requests.exceptions.Timeout:
            print "The API call for: ", self.hostname, " timed out"

        # Sets the result of the above API call as result
        result = r.json()

        # If the API call was not successful
        if result['status'] != "OK":
            if verbose:
                print "Failed Creating Droplet"
                if verbose > 1:
                    print result['error_message']
            self.status = "Failed"
        else:
            # Sets returned droplet ID and sets the status to new
            self.DropletID = str(result['droplet']['id'])
            self.status = "new"

    def setID(self, newid):
        """
        Name:           setID

        Description:    Sets the DropletID to a new value, or initializes that var

        Input:          Requires a new Droplet ID passed as an int

        Actions:        Sets the objects DropletID to a new ID
        """

        self.DropletID = str(newid)

    def display(self):
        """
        Name:           display

        Description:    Prints information regarding the Droplet Object

        Input:          none

        Actions:        Prints objects variables with identifying text before information
                        Prints; hostname, DropletID, region, IP, status
        """
        #Prints information about Droplet Object
        print "Droplet Hostname: " + self.hostname
        print "      Droplet ID: " + self.DropletID
        print "  Droplet Region: " + self.region
        print "      Droplet IP: " + self.IP
        print "  Droplet Status: " + self.status
        print "------------------------------"

    def getIP(self):
        """
        Name:           getIP

        Description:    returns the IP for a droplet using the D.O. API

        Input:          none

        Actions:        Uses the non standard requests library to send API call to D.O.
                        Returns the IP Address unless an error occurs. If an error occurs, it will return the error.
        """
        r = requests.get(
            "https://api.digitalocean.com/droplets/" + self.DropletID + "?client_id=" + API_ID + "&api_key=" + API_KEY)
        result = r.json()
        if result['status'] == "OK":
            return str(result['droplet']['ip_address'])
        else:
            # TODO raise error instead of return error
            return result['error_message']

    def setIP(self, newip):
        """
        Name:           setIP

        Description:    Set the objects IP Address to the passed variable

        Input:          Requires new IP Address to be passed
        """
        self.IP = str(newip)

    def getID(self):
        """
        Name:           getID

        Description:    Returns the objects ID

        Input:          none

        Actions:        Returns the objects droplet ID as a string
        """
        return str(self.DropletID)

    def getHostname(self):
        """
        Name:           getHostname

        Description:    Returns the objects hostname

        Input:          none

        Actions:        Returns the objects droplet ID as a string
        """
        return str(self.hostname)

    def isActive(self):
        """
        Name:           isActive

        Description:    Uses the D.O. API to check the status of a droplet

        Input:          none

        Actions:        Uses the non standard requests library to send API call to D.O.
                        Uses the objects DropletID var to check the status.
                        Returns True if active else returns False
        """
        # Uses the requests library to call D.O. API
        # TODO use the getStatus function instead of redefining API call
        r = requests.get(
            "https://api.digitalocean.com/droplets/" + self.DropletID + "?client_id=" + API_ID + "&api_key=" + API_KEY)
        # Store results of API call in var result
        result = r.json()
        # Checks if returned status is active
        if result['droplet']['status'] == "active":
            return True
        else:
            return False

    def getStatus(self):
        """
        Name:           getStatus

        Description:    Checks the status of a droplet using D.O. API

        Input:          none

        Actions:        Uses the non-standard "requests" library to send API call to D.O.
                        Returns the status of the droplet as a strings
        """
        r = requests.get(
            "https://api.digitalocean.com/droplets/" + self.DropletID + "?client_id=" + API_ID + "&api_key=" + API_KEY)
        result = r.json()
        return str(result['droplet']['status'])

    def setStatus(self, newstatus):
        """
        Name:           setStatus

        Description:    Sets the status of the object

        Input:          A status

        Actions:        Sets the passed status as the objects status
        """
        self.status = str(newstatus)

    def waitTillActive(self):
        """
        Name:           waitTillActive

        Description:    Uses the function isActive to check droplets status waits before it checks again

        Input:          none

        Actions:        Checks the status of the object, if not failed it will start a self timer
                        While the previously registered status is still new, and the time is less than the timeout
                            Uses the isActive function to check status
                            If not active will be reasonably impatient

                        returns status, even if timeout error
        """
        # Checks if the status is not equal to failed
        if self.status != "Failed":
            # Creates a var of how long the function has been waiting for droplet to become active
            self.startUpTime = 0
            # Loops through as the status is set to new
            while self.status == "new":
                # Checks if the time taken is less than the the set amount of time
                if self.startUpTime <= activetimeout:
                    # Uses the isActive function to determine if the droplet is active
                    if self.isActive():
                        self.status = "active"
                    else:
                        # Depending on startUpTime, this will sleep for a set amount of time.
                        # This makes the program reasonably impatient
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
                # If the droplet does not become active within the specified activeTimeout value
                # TODO should this raise an error rather than set the status?
                else:
                    self.status = "Error: Did not become active within time limit"
        return self.status

    def destroy(self):
        """
        Name:           destroy

        Description:    Uses the D.O. API to destroy droplets based on ID

        Input:          none

        Actions:        Uses the D.O. API to destroy and scrub server data
                        Waits for ok status, prints completed message, sets status to destroyed
                        If error occurs, will set error to status
                        Returns status even if error
        """
        # Uses the D.O. API to destroy and scrub droplets
        r = requests.get(
            "https://api.digitalocean.com/droplets/" + self.DropletID + "/destroy/?client_id=" + API_ID + "&api_key=" +
            API_KEY + "&scrub_data=1")
        result = r.json()
        # Checks to make sure the call was "OK"
        if result['status'] == "OK":
            if verbose:
                print "Destroyed droplet " + str(self.DropletID)
            self.status = "destroyed"
        else:
            self.status = result['error_message']
        return self.status


def countDroplets():
    """
    Name:           countDroplets

    Description:    Counts how many droplets are on the account that are not the manager droplet and are active

    Input:          none

    Actions:        Uses the D.O. API to get a list of all droplets on the account
                    Loops through returned droplets and counts how many are not the manager and have an active status
                    Returns a string of the count
    """
    # Uses the D.O API to get all droplets on the account
    r = requests.get('https://api.digitalocean.com/droplets/?client_id=' + API_ID + '&api_key=' + API_KEY)
    result = r.json()
    # Starts with 0 before counting droplets
    count = 0
    # Loops through all returned droplets
    for droplet in result['droplets']:
        # Checks to makes sure its not the manager droplet
        if droplet['name'] != "Manager":
            # Makes sure the droplet is active before adding it to the count
            if droplet['status'] == 'active':
                count += 1
    return str(count)


def rebuildLists():
    """
    Name:           rebuildLists

    Description:    Drops the activelist.txt and the global serverList var, rebuilds based on data from D.O. API call

    Input:          none

    Actions:        Sets the global serverList var to be modified
                    Uses D.O. API to get all droplets on the account
                    Drops the existing serverList
                    Loops through reported droplets from D.O.
                        Checks to ensure the droplet is not the manager
                        Creates new droplet object with region, ID, SSH Key, droplet size, and host name
                            Uses the getSSHKeys function to get the SSH Key
                        Once object has been created, use objects functions to set respective object vars;
                            setStatus, setIP, and setID
                        Adds the object to the list
                    Outputs Server list to activelist.txt
                    Returns serverList
    """
    # Allows global serverList to be modified
    global serverList

    # Uses D.O. API to get all droplets on the account
    r = requests.get('https://api.digitalocean.com/droplets/?client_id=' + API_ID + '&api_key=' + API_KEY)
    result = r.json()
    # Sets global var serverList to clear the list
    serverList = []
    # Loops through all returned droplets
    for droplet in result['droplets']:
        # Checks to makes sure the current droplet is not the manager droplet
        if droplet['name'] != "Manager":
            if verbose > 1:
                print "Adding droplet " + str(droplet['id'])
            # Creates new droplet object, passing it the info from the D.O. API call
            curDroplet = Droplet(droplet['region_id'], droplet['image_id'], getSSHKeys(keyID), droplet['size_id'],
                                 droplet['name'])
            # Sets the status of the newly created droplet object
            curDroplet.setStatus(droplet['status'])
            # Sets the IP Address of the newly created droplet object
            curDroplet.setIP(droplet['ip_address'])
            # Sets the ID of the newly created droplet object
            curDroplet.setID(droplet['id'])
            # Appends the newly created object to the global serverList if it is an active droplet
            if curDroplet.status == "active":
                serverList.append(curDroplet)
    # Open the activelist.txt file in write binary mode
    with open('activelist.txt', 'wb') as output:
        # Compresses the list and writes it to the output file
        pickle.dump(serverList, output)
    if verbose > 1:
        print "Done rebuilding server list"
    # Returns the global serverList
    return serverList


def getSizeID(wantedSize):
    """
    Name:           getSizeID

    Description:    Sets the size ID to the requested size, returns 512MB option if fails

    Input:          Wanted size in string ex. 512MB

    Actions:        Sets default to 512MB
                    Uses D.O. API to check available sizes
                    Compares sizes with requested size
                    If found returns the respective sizeId
    """
    # Sets default sizeid to 33 (512MB)
    sizeId = "33"
    r = requests.get("https://api.digitalocean.com/sizes/?client_id=" + API_ID + "&api_key=" + API_KEY)
    result = r.json()
    for size in result['sizes']:
        # Checks if wantedSize is in the returned sizes
        if size['name'] == wantedSize:
            sizeId = size['id']
    return str(sizeId)


def getImageID(imageName):
    """
    Name:           getImageID

    Description:    Gets available images from D.O. and returns the string of the requested image

    Input:          The image Name

    Actions:        Uses the D.O. API to get available images
                    Attempts to find requested image name in available images
                    returns image ID
    """
    # Uses D.O. API to get available images
    r = requests.get(
        "https://api.digitalocean.com/images/?client_id=" + API_ID + "&api_key=" + API_KEY + "&filter=my_images")
    result = r.json()
    #print result
    # Searches through to see if imageName is in returned values
    for image in result['images']:
        if image['name'] == imageName:
            imageID = image['id']
    # TODO should return false or raise error if not found or both
    # TODO should be able to use a standard D.O. image as a default, if not specified in config.
    return str(imageID)


def getRegions():
    """
    Name:           getRegions

    Description:    Gets available regions from D.O.

    Input:          none

    Actions:        Uses the D.O API to get available regions (locations)
                    Adds values to list
                    Returns list
    """
    regions = []
    # Uses D.O. API to get available regions
    r = requests.get("https://api.digitalocean.com/regions/?client_id=" + API_ID + "&api_key=" + API_KEY)
    result = r.json()
    # Loops through and adds regions to list
    for region in result['regions']:
        regions.append(str(region['id']))
    return regions


def getSSHKeys(keyName):
    """
    Name:           getSSHKeys

    Description:    Gets SSHKeys from D.O. and returns the request Key ID

    Input:          SSH Key Name

    Actions:        Goes through D.O. API and gets available SSH Keys
                    Returns SSH Key ID in String
    """
    # TODO Should this return None if the SSHKey is not set or false/raise an error if not found
    # Uses D.O. to get available SSH Keys
    r = requests.get("https://api.digitalocean.com/ssh_keys/?client_id=" + API_ID + "&api_key=" + API_KEY)
    result = r.json()
    # Searches through to see if keyName is in the returned values
    for key in result['ssh_keys']:
        if key['name'] == keyName:
            keyid = key['id']
    return str(keyid)


def createDroplet(regions, image, size, sshkey, name):
    """
    Name:           createDroplet

    Description:    creates D.O. droplet based on passed parameters, adds servers to either serverList or timeoutList

    Input:          The following parameters need to be passed; Regions - A list of all available regions
                                                                Base Image - Name of Base Image
                                                                Size - Size of desired droplet ex. 512MB
                                                                SSH Key - Name of SSH Key
                                                                Name - desired hostname

    Actions:        Chooses a random region from the passed region list
                    Checks if SSH Key is initialized and creates the droplet object
                    Uses the following functions to pass appropriate values; getImageID, getSSHKeys, getSizeID
                    Once droplet object has been created, call objects build function.
                    Checks the time it took to create object and adds value to averagetimeout list
                    Adds the newly created droplet object to serverList
                    Uses objects waitTillActive function to check if the object became active
                    If object became active:
                        Uses the objects getIP function to set the objects IP Address
                    Else:
                        Removes its self from list, decrements totalServers count
                        Checks if the status was not failed
                            Adds object to timeoutList
    """
    # Sets global var to be modified
    global totalServers
    global serverList
    global averagetimeout

    # TODO Add functionality to not rand
    # Sets a random region from passed region list
    selectedRegion = choice(regions)
    # Starts timer for average timeout list
    start = time.time()
    # Determines if the sshkey is identified
    if sshkey:
        curDroplet = Droplet(selectedRegion, getImageID(image), getSSHKeys(sshkey), getSizeID(size), name)
    else:
        curDroplet = Droplet(selectedRegion, getImageID(image), None, getSizeID(size), name)
    # Runs the objects build function
    curDroplet.build()
    # Stops the averagetimeout timer
    elapsed = (time.time() - start)
    # Adds the averagetimeout timer to the list
    averagetimeout.append(elapsed)
    # Adds the created droplet to the serverList
    serverList.append(curDroplet)
    # Uses the objects waitTillActive function
    curDroplet.waitTillActive()

    if curDroplet.status == "active":
        # Sets the objects IP using the objects function
        curDroplet.IP = curDroplet.getIP()
        if verbose > 1:
            print curDroplet.DropletID + " is active"
    else:
        # Removes the object from the list if its status is not active
        serverList.remove(curDroplet)
        totalServers -= 1
        # TODO Add Verbosity error reporting if status is error - Not sure if this should be done here, or when building the object above.
        if curDroplet.status != "Failed":
            timeoutList.append(curDroplet)


def getAverage():
    """
    Name:           getAverage

    Description:    Keeps the 10 most recent times in the averagetimeout list and returns the average time + .5 second

    Input:          none

    Actions:        Gets the global averagetimeout list
                    Removes the oldest time value if the list has more than 10 values
                    Performs float calc for average and adds a .5 second padding
                    Returns padded float time
    """
    global averagetimeout

    # if longer than 10, will remove the "oldest" value
    if len(averagetimeout) > 10:
        averagetimeout.pop(0)
    # Returns the average time as a float with a .5 sec time padding
    return sum(averagetimeout) / float(len(averagetimeout)) + .5


def ParseCommandLine():
    """
    Name:           ParseCommandLine

    Description:    Uses argparse Standard library to parse passed CLI arguments

    Input:          none

    Actions:        Creates parser object
                    adds the following arguments; action - start, stop, status, rebuild = Required)
                                                  quantity - how many to start or stop = Default: 5
                                                  hostname - desired hostname = Default: value from config
                                                  timeout - timeout limit in seconds = Default: 600
                                                  verbose - verbosity and debug messages
    """
    # Creates parser object
    parser = argparse.ArgumentParser(description="Start, stop, and manage Digital Ocean Droplets.")
    # Specifies the action, this is required
    parser.add_argument('-a', choices=['start', 'stop', 'status', 'rebuild'],
                        help='Specify the action desired: start, stop, status, rebuild', required=True)
    # Specifies the number of droplets to start or stop
    parser.add_argument('-q', help='Specify the number of droplets (Default is 5)', type=int, default=5)
    # Specifies a custom hostname
    parser.add_argument('-n', help='Specify the hostname of the droplets (Default is identified in the config)',
                        type=str, default=hostname)
    # Specifies a custom timeout
    parser.add_argument('-t', help='Specify timeout limit (in seconds) (default is 600 seconds)', type=int, default=600)
    # Specifies the amount of verbosity the program will have, vv will enable debug
    parser.add_argument('--verbose', '-v', help="Add v to have limited verbosity, add another v to give debug messages",
                        action='count')
    return parser.parse_args()


def ConfigFileParser():
    """
    Name:           ConfigFileParser

    Description:    Parses the config file and sets global variables

    Input:          config file settings.conf needed in directory

    Actions:        Create parser object
                    Read the settings.conf file located in the directory
                    Sets the global variables;
                        API_ID, API_KEY, managerServerID, imageID, keyID, sizeID, hostname, and url
    """

    global API_ID
    global API_KEY
    global managerServerID
    global imageID
    global keyID
    global sizeID
    global hostname
    global url

    # Creates a config file object
    config = ConfigParser.ConfigParser()
    # Read the settings.conf file into the config object
    config.read('settings.conf')

    # Uses the config object to read and set the global vars
    API_ID = config.get('DigitalOceanAPI', 'API_ID')
    API_KEY = config.get('DigitalOceanAPI', 'API_KEY')
    managerServerID = config.get('DigitalOceanSettings', 'managerServerID')
    imageID = config.get('DigitalOceanDropletSettings', 'image')
    # Checks if the SSHKey exists else sets the key to false
    try:
        keyID = config.get('DigitalOceanDropletSettings', 'key')
    except ValueError:
        keyID = None
    sizeID = config.get('DigitalOceanDropletSettings', 'size')
    hostname = config.get('DigitalOceanDropletSettings', 'hostname')

    # TODO use the defined URL instead of calling it defining it each time (where possible)
    url = 'https://api.digitalocean.com/droplets/?client_id=' + API_ID + '&api_key=' + API_KEY


def main():
    """
    Name:           main

    Description:    Interprets input from user and interacts with droplet objects to manage D.O. Droplets (VPS's)

    Input:          none

    Actions:
    """

    # Creates totalTime var to start timer of full application run
    totalTime = time.time()

    global hostname
    global serverList
    global timeoutList
    global verbose
    global activetimeout
    global totalServers


    ConfigFileParser()

    theArgs = ParseCommandLine()

    args = vars(theArgs)
    action = args['a']
    totalServers = args['q']
    activetimeout = args['t']
    hostname = args['n']
    hostname.replace(' ', '_').lower()
    hostname = hostname + "-"
    verbose = args['verbose']

    # TODO move start action to individual function
    if action == "start":
        regions = getRegions()
        curServer = 1
        print "Creating " + str(totalServers) + " droplets"

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
            avgTime = getAverage()
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
            with open('activelist.txt', 'rb') as inputFile:
                newList = pickle.load(inputFile)
                serverList = serverList + newList
            with open('activelist.txt', 'wb') as outputFile:
                pickle.dump(serverList, outputFile)
        else:
            with open('activelist.txt', 'wb') as outputFile:
                pickle.dump(serverList, outputFile)

        if len(timeoutList) > 0:
            if os.path.exists('timeoutlist.txt'):
                with open('timeoutlist.txt', 'rb') as inputFile:
                    newList = pickle.load(inputFile)
                    timeoutList = timeoutList + newList
                with open('timeoutlist.txt', 'wb') as outputFile:
                    pickle.dump(timeoutList, outputFile)
            else:
                with open('timeoutlist.txt', 'wb') as outputFile:
                    pickle.dump(timeoutList, outputFile)

    # TODO move stop action to individual function
    elif action == "stop":
        if os.path.exists('activelist.txt'):
            with open('activelist.txt', 'rb') as inputFile:
                serverList = pickle.load(inputFile)

        else:
            if verbose:
                print "No activelist.txt, maybe no servers are running?"
            exit()

        if os.path.exists('timeoutlist.txt'):
            with open('timeoutlist.txt', 'rb') as inputFile:
                timeoutList = pickle.load(inputFile)

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
                print "Destroying " + str(totalServers) + " droplets in 3 seconds"
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

    # TODO move status to individual function
    elif action == "status":
        digiOceanCount = countDroplets()
        try:
            print "There are " + str(digiOceanCount) + " droplets currently running"
            with open('activelist.txt', 'rb') as input:
                    serverList = pickle.load(input)
            if verbose:
                for server in serverList:
                    server.display()
        except IOError:
            if verbose:
                print "No servers are currently active"
        if int(digiOceanCount) != len(serverList):
            print "Number of servers reported by Digital Ocean's API does not match the current server list. Rebuilding list now"
            rebuildLists()
            if verbose:
                with open('activelist.txt', 'rb') as input:
                    serverList = pickle.load(input)
                for server in serverList:
                    server.display()

    # TODO Keep consistent, move to separate function (rebuildLists will work)
    elif action == "rebuild":
        rebuildLists()

    #Timer should stop regardless of verbosity.
    totalTime = (time.time() - totalTime)
    # If verbose, print totalTime var
    if verbose:
        print "Total time to create: " + str(totalTime)

if __name__ == '__main__':
    main()
