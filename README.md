DigitalOceanDropletController
=============================

Uses Digital Ocean's RESTful API to spin up and shutdown droplets.

usage: manager.py [-h] -a {start,stop,status,rebuild} [-q Q] [-n N] [-t T]
                  [--verbose]
                  
Start and stop Digital Ocean Droplets.

optional arguments:
  -h, --help            show this help message and exit
  -a {start,stop,status,rebuild}
                        Specify the action desired: start, stop, status,
                        rebuild
  -q Q                  Specify the number of droplets (Default is 5)
  -n N                  Specify the hostname of the droplets (Default is
                        'server-')
  -t T                  Specify timeout limit (in seconds) (default is 600
                        seconds)
  --verbose, -v         Add v to have limited verbosity, add another v to give
                        debug messages

Installation
=============================
Clone the repo, modify the settings.conf.dist to contain your DigitalOcean API information and then rename it to settings.conf

Contact
=============================

@Nebriv https://benvirgilio.com/

@Marleyjaffe http://marleyjaffe.com/
