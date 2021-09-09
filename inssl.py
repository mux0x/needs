#!/usr/bin/python3
import ssl, socket , argparse 
import signal
from termcolor import colored
import sys
import time
import threading
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="domains file")
parser.add_argument("-n", "--orgname", help="organization name")
parser.add_argument("-o", "--output", help="output file")
args = parser.parse_args()


def chssl(i,n,o):
    l = [l.strip() for l in open(i)]
    for hostname in l:
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
                s.connect((hostname, 443))
                cert = s.getpeercert()

            subject = dict(x[0] for x in cert['subject'])
            issued_to = subject['organizationName']
            if issued_to == n:
                f = open(o, "a")
                f.write(hostname + "\n")
                f.close()
                print(colored(hostname + " is in the ssl cert", 'green'))
        except:
            print(colored(hostname + " isn't valid or ins't in the ssl cert" , 'red'))

def main():
    try:
        thread = threading.Thread(target=chssl,args=(args.input,args.orgname,args.output,))
        thread.daemon = True  # let the parent kill the child thread at exit
        thread.start()
        while thread.is_alive():
            thread.join()  # time out not to block KeyboardInterrupt
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

