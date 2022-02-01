#!/usr/bin/env python3
import time
import unicodedata
import string
import signal
import subprocess
import os
import shlex
import sys
import xattr
import json
import plistlib
import logging
import requests
import argparse
import validators
import re
import frontmatter
#from lockfile import LockFile, LockTimeout
from datetime import datetime, timedelta
from random import random
from smtplib import SMTP_SSL as SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from validators import ValidationFailure
from os.path import exists

# Source: https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
def clean_filename(filename):
    whitelist = "-_.() %s%s" % (string.ascii_letters, string.digits)
    char_limit = 255

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    
    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    # clean multiple, leading and trailing whitespace
    cleaned_filename = ' '.join(cleaned_filename.split())
    if len(cleaned_filename)>char_limit:
        logger.warning("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))

    return cleaned_filename[:char_limit] 


#def exit():
#    try:
#        lock.release()
#    finally:
#        exit()


def main(url, *, output_dir, output_filename, script_dir, log_dir, log_level, file_log_level):

    #subprocess.run(["/usr/bin/killall","Safari"], capture_output=True, check=False, timeout=15)
    logger.info("Start saving website..." + url + " to " + output_filename)

    if not exists(os.path.join(output_dir,output_filename)):
        try:
            #logger.debug("Resetting System Events")
            #subprocess.run(["/usr/bin/killall","System Events"], capture_output=True, check=False, timeout=15)
            #subprocess.run(["/usr/bin/osascript",os.path.join(script_dir,'reset_systemevents.scpt')], timeout=20)
            #time.sleep(10)

            try:
                output = subprocess.run(["/usr/bin/osascript",os.path.join(script_dir,"save_website.scpt"),url,output_filename,output_dir], capture_output=True, text=True, timeout=180)
            except subprocess.TimeoutExpired as e:
                logger.error(str(e).rstrip('\n'))

            time.sleep(2)

            #xattr.setxattr(output_file,'user.url',bytes(url.encode('utf-8')))
            output_file = os.path.join(output_dir, output_filename)
            comment = url
            xattr.setxattr(output_file,'com.apple.metadata:kMDItemFinderComment',plistlib.dumps(comment, fmt=plistlib.FMT_BINARY))
            xattr.setxattr(output_file,'com.apple.metadata:kMDItemWhereFroms',plistlib.dumps(url, fmt=plistlib.FMT_BINARY))
            
			#file_time = time.mktime(connected_date.timetuple())
            #os.utime(output_file, (file_time, file_time))

        except AssertionError as e:
            logger.error(str(e).rstrip('\n'))
        except Exception as e:
            logger.exception(e)
    else:
        logger.warning("Not doing anything, file already exists")

    # Make very sure Safari is not runnning anymore
    #time.sleep(2)
    #subprocess.run(["/usr/bin/osascript","-e",'tell application "Safari" to quit'], capture_output=False, timeout=5)
    #subprocess.run(["/usr/bin/killall","Safari"], capture_output=True, check=False, timeout=15)

def sigint_handler(signal, frame):
    logger.warning("Interrupted")
    sys.exit(0)


def send_mail(subject, heading, content):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = "save_website <your@email.com>"
    msg['To'] = "your@email.com"
    text = "{}\n\n{}".format(heading,content)
    html = "<h3>{}</h3><pre style='font-size: smaller'>{}</pre>".format(heading, content)

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    smtp = SMTP('smtp.fastmail.com', 465)
    smtp.ehlo()
    smtp.login('your@email.com', '<secret-password>')
    try:
        logger.debug("Sending e-mail...")
        smtp.sendmail("save_website <your@email.com>","your@email.com",msg.as_string())
    except Exception as e:
        logger.exception(e)
    finally:
        smtp.quit()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    
    default_dir = "/Users/mdbraber/iCloud Drive/save_website/"

    parser = argparse.ArgumentParser(description="Save websites to PDF via Safari ")
    parser.add_argument('--clip-file', default="")
    parser.add_argument('--url', default="")
    parser.add_argument('--title', default="")
    parser.add_argument('--output-dir', default="")
    parser.add_argument('--output-filename', default="")
    parser.add_argument('--script-dir', default=default_dir)
    parser.add_argument('--log-dir', default=default_dir)
    parser.add_argument("--log-level", default="debug")
    parser.add_argument("--file-log-level", default="debug", help="Log level for file-based logging")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }


    log_level = levels.get(args.log_level.lower())
    if log_level is None:
        raise ValueError(
            "log level given: {}"
            "-- must be one of: {}".format(args.log_level, ' | '.join(levels.keys())))

    file_log_level = levels.get(args.file_log_level.lower())
    if file_log_level is None:
        raise ValueError(
            "log level given: {}"
            "-- must be one of: {}".format(args.file_log_level, ' | '.join(levels.keys())))

    log_filename=os.path.join(args.log_dir,'save_website.log')
    log_format='%(asctime)s [%(levelname)-8s] %(message)s'
    log_datefmt='%Y-%m-%d %H:%M:%S'

    #logging.basicConfig(level=logging.DEBUG, format=log_format, datefmt=log_datefmt)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logger = logging.getLogger('logger')
    # logger.setLevel(args.verbose)
	# Always be verbose on the command-line
    #logger.setLevel(log_level)
  
    if not args.quiet:
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(log_format, datefmt=log_datefmt))
        sh.setLevel(log_level)
        logger.addHandler(sh)
 
    fh = logging.FileHandler(filename=log_filename, encoding='utf-8')
    fh.setFormatter(logging.Formatter(log_format, datefmt=log_datefmt))
    fh.setLevel(file_log_level)
    logger.addHandler(fh)
    
    kwargs = {k:v for k,v in vars(args).items() if v is not None}
    #lock = LockFile(os.path.join(args.script_dir, "save_website"))

    #try:
    #    lock.acquire(timeout=2)
    #except LockTimeout:
    #    exit("Couldn't acquire lock") 

    if args.clip_file: 
       try:
           clip = frontmatter.load(args.clip_file)
           output_filename = os.path.splitext(os.path.basename(args.clip_file))[0] + ".pdf"
           url = clip['url']
           if isinstance(url, ValidationFailure):
                   logger.error("Not a valid URL")
                   exit()
       except IOError as e:
           logger.error("Can't open clip-file for reading. Exiting")
           exit()
    elif (args.title != "" and args.url != ""):
        url = args.url
        output_filename = clean_filename(args.title)
    else:
        logger.error("No clip-file or URL/title given. Exiting")
        exit() 

    try:
        main(url = url,
             output_dir = args.output_dir,
             output_filename = output_filename,
             script_dir = args.script_dir,
             log_dir = args.log_dir,
             log_level = args.log_level,
             file_log_level = args.file_log_level)
    except AssertionError as e:
        logger.error(e)
        try:
            content = "Error running save_website.py:\n\n{}".format(last_log_lines())
            send_mail("ERROR save_website", "Error saving website, see below", content)
        except Exception as e:
            logger.error("Error sending e-mail: {}".format(e))
    finally:
        logger.debug("Quitting Safari")
        subprocess.run(["/usr/bin/osascript","-e",'tell application "Safari" to quit'], capture_output=False, timeout=15)
        time.sleep(1)
        subprocess.run(["/usr/bin/killall","Safari"], capture_output=True, check=False, timeout=15)
        logger.info("Done\n")
