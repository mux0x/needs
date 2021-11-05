#!/usr/bin/env python3

#imports

import argparse
import time
from zapv2 import ZAPv2
from termcolor import colored
import subprocess
import psutil
import requests

end = False;
def logo():
        print(colored('''\n\n 

                                            /$$$$$$           
                                           /$$$_  $$          
         /$$$$$$/$$$$  /$$   /$$ /$$   /$$| $$$$\ $$ /$$   /$$
        | $$_  $$_  $$| $$  | $$|  $$ /$$/| $$ $$ $$|  $$ /$$/
        | $$ \ $$ \ $$| $$  | $$ \  $$$$/ | $$\ $$$$ \  $$$$/ 
        | $$ | $$ | $$| $$  | $$  >$$  $$ | $$ \ $$$  >$$  $$ 
        | $$ | $$ | $$|  $$$$$$/ /$$/\  $$|  $$$$$$/ /$$/\  $$
        |__/ |__/ |__/ \______/ |__/  \__/ \______/ |__/  \__/
                                                      
    ''', 'red', attrs=[]))
        print(colored('                      [+] Automated spider using zap proxy', 'cyan', attrs=['bold']))
        print(colored('                      [+] github @mux0x','cyan',attrs=['bold']))
        print("")
        print(colored('########################################################################', 'green', attrs=[]))
        print("")


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--site", help="single url to spider")
parser.add_argument("-a", "--apikey", help="zap proxy api key")
parser.add_argument("-p", "--port", help="port that zap proxy is using")
parser.add_argument("-o", "--output", help="output file")
parser.add_argument("-c", "--cookies", help="cooikes value for authentication e.g. key1=value;key2=value2=")

args = parser.parse_args()

logo()
# basics
def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

if isinstance(args.port,str):
    print(colored("[+] opening ZAP proxy",'cyan',attrs=['bold']))
    zaprun=subprocess.Popen('/opt/zaproxy/zap.sh -daemon -host 0.0.0.0 -port %s -config "api.addrs.addr.name=.*" -config "api.addrs.addr.regex=true" -config "api.key=%s"' %(args.port , args.apikey),shell=True,stdout=subprocess.DEVNULL)
    def spider(site):    
        target = site
        apiKey = args.apikey
        zap = ZAPv2(apikey=apiKey)
        if isinstance(args.cookies,str):
            r = requests.get('http://localhost:%s/JSON/replacer/action/addRule/?apikey=%s&description=cookie_for_spider&enabled=true&matchType=REQ_HEADER&matchRegex=false&matchString=Cookie&replacement=%s&initiators=' % (args.port,args.apikey,args.cookies))
        zap = ZAPv2(apikey=apiKey, proxies={'http': 'http://127.0.0.1:%s' % (args.port), 'https': 'http://127.0.0.1:%s' % (args.port)})
        print(colored('[+] Spidering target {}'.format(target),'cyan',attrs=['bold']))
        scanID = zap.spider.scan(target)
        while int(zap.spider.status(scanID)) < 100:
            # Poll the status until it completes
            print(colored('[+] Spider progress : {}%'.format(zap.spider.status(scanID)),'cyan'))
            time.sleep(1)

        print(colored('Spider has completed for %s !' % (site),'green',attrs=['bold']))
        out = '\n'.join(map(str, zap.spider.results(scanID)))
        f = open(args.output, "a")
        f.write(out + "\n")
        f.close()


def main(site):
    try:
        spider(site)
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)

time.sleep(5)
if isinstance(args.site, str):
    main(args.site)
elif isinstance(args.sites, str):
    sites = [l.strip() for l in open(args.sites)]
    for x in sites:
        main(x)
if isinstance(args.cookies,str):
    r2 = requests.get('http://localhost:%s/JSON/replacer/action/removeRule/?apikey=%s&description=cookie_for_spider' % (args.port,args.apikey))
time.sleep(0.1)
kill(zaprun.pid)
