#!/usr/bin/python3
import sys
import ssl
import socket
import argparse
from termcolor import colored
from multiprocessing.dummy import Pool as ThreadPool

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="domains file")
parser.add_argument("-n", "--orgname", help="organization name")
parser.add_argument("-o", "--output", help="output file")
parser.add_argument("-t", "--threads", help="threads number ")
args = parser.parse_args()
l = [l.strip() for l in open(args.input)]

if isinstance(args.threads, str):
    pool = ThreadPool(int(args.threads))
else:
    pool = ThreadPool(6)

def chssl(hostname):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.connect((hostname, 443))
            cert = s.getpeercert()

        subject = dict(x[0] for x in cert['subject'])
        issued_to = subject['organizationName']
        if issued_to == args.orgname:
            f = open(args.output, "a")
            f.write(hostname + "\n")
            f.close()
            print(colored(hostname + " is in the ssl cert", 'green'))
    except:
        print(colored(hostname + " isn't valid or isn't in the ssl cert" , 'red'))


def main():
    try:
        results = pool.map(chssl , l)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)

if isinstance(args.input, str):
    if isinstance(args.orgname,str):
        if isinstance(args.output,str):
            main()
        else:
            print("Please enter the organization name as -o output.txt")
    else:
        print("Please enter the organization name as -n GitHub, Inc.")
else:
    print("Please enter your domains file as -i domains.txt")
