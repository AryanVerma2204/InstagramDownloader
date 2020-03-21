#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# Copyright (c) 2019-2020, Gianluca Fiore
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
###############################################################################

__author__ = "Gianluca Fiore"
__license__ = "GPL"
__version__ = "0.3"
__date__ = "20191118"
__email__ = "forod.g@gmail.com"
__status__ = "beta"

import sys
from os import chdir
from os.path import basename, splitext
from datetime import datetime, timedelta
from itertools import takewhile, dropwhile
import argparse
import logging
import instaloader

MAINPATH='/mnt/documents/c/Tempstuff/instagram/'
LOGFILE= MAINPATH + basename(splitext(__file__)[0]) + '.log'
DEFAULTSTARTDATE = [2019, 1, 1]

def argument_parser():
    cli_parser = argparse.ArgumentParser()

    cli_parser.add_argument("-s", "--startdate",
            action="store",
            type=int,
            nargs=3,
            help="the date from which starting downloading images. Type it separately like YYYY MM DD, as in 2018 01 01",
            dest="startdate")
    cli_parser.add_argument("-u", "--update",
            action="store_true",
            help="update only previously downloaded profiles",
            dest="update")
    cli_parser.add_argument("action",
            nargs="?",
            default="run")

    opts = cli_parser.parse_args()
    return opts

# take a file path and get a list with all its content
def lastcheck_date(cFile):
    datenumbers = []
    try:
        with open(cFile, "r") as f:
            for l in f:
                try:
                    datenumbers.append(int(l))
                except ValueError:
                    # timestamp in file will raise ValueError. Ignoring it as we don't need last line
                    pass
            
        f.close()
    except FileNotFoundError:
        # if "lastcheck" file is not present, treat this specific directory as a "run" operation
        return DEFAULTSTARTDATE

    return datenumbers

# Mass download function taking charge of the "run" and "update" operations
def massDownload(instance, startdate, enddate, operation):
    FILE = 'IG_SL.md'
    NOT_FOUND_FILE = 'IG_not_found.txt'
    # Emptying the not found file
    open(NOT_FOUND_FILE, 'w').close()
    with open(FILE) as f:
        content = f.readlines()
        content = ([x.strip() for x in content]) # remove whitespace characters
        for profilename in content:
            if profilename.startswith('#'):
                # commenting out a profilename in FILE will mean skipping it
                continue
            if operation == "update":
                lastcheckeddate = lastcheck_date(profilename + "/lastcheck")
                startdate = datetime(lastcheckeddate[0], lastcheckeddate[1], lastcheckeddate[2]) + timedelta(days=1)
            try:
                posts = instaloader.Profile.from_username(instance.context, profilename).get_posts()
                for p in dropwhile(lambda p: p.date > enddate, takewhile(lambda p: p.date > startdate, posts)):
                    instance.download_post(p, profilename)
            except instaloader.exceptions.ProfileNotExistsException:
                logging.info("Profile " + profilename + " was not found")
                with open(NOT_FOUND_FILE, 'a') as n:
                    n.write(profilename + "\n")
                    n.close()
            except instaloader.exceptions.QueryReturnedNotFoundException:
                # Image not found. Could have been deleted by user, skip it
                logging.info("Image " + posts.url + " not found")
                pass
            except instaloader.exceptions.ConnectionException:
                # Resource not available, maybe anymore. Skip it
                logging.info("Resource not available")
                pass
            except TypeError as e:
                print("Error while downloading profile " + profilename)
                print("Error was: " + str(e))
                logging.debug("Error while downloading profile " + profilename)
                logging.debug(str(e))
                sys.exit(1)

            LASTCHECKFILE = profilename + "/lastcheck"
            try:
                with open(LASTCHECKFILE, "w") as t:
                    t.write("\n".join([enddate.year.__str__(), enddate.month.__str__(), enddate.day.__str__()]))
                    t.write("\n" + enddate.__str__())
                    t.close()
            except IOError:
                logging.debug('Could not write lastcheck file for profile ' + options.action)
                pass

    f.close()


def main():
    options = argument_parser()

    logging.basicConfig(filename=LOGFILE, level=logging.WARNING)

    # get instance
    L = instaloader.Instaloader(download_videos=False, download_video_thumbnails=False, download_geotags=False, download_comments=False, save_metadata=False, post_metadata_txt_pattern="", request_timeout=10.0)
    L.login('NNNNNNN', 'XXXXXXXX')

    chdir(MAINPATH)

    # Set the timespan we want images between
    if options.startdate:
        if len(options.startdate) < 3:
            cli_parser.print_help()
        SINCEDATE = datetime(options.startdate[0], options.startdate[1], options.startdate[2])
    else:
        # default  to DEFAULTSTARTDATE values
        SINCEDATE = datetime(DEFAULTSTARTDATE[0], DEFAULTSTARTDATE[1], DEFAULTSTARTDATE[2])

    TODAY = datetime.today()

    if options.action == "run":
        massDownload(L, SINCEDATE, TODAY, "run")
    elif options.action == "update":
        massDownload(L, SINCEDATE, TODAY, "update")
    else:
        # if no "run" nor "update", assume it is a single profile name it was given and download just that
        posts = instaloader.Profile.from_username(L.context, options.action).get_posts()
        for p in dropwhile(lambda p: p.date > TODAY, takewhile(lambda p: p.date > SINCEDATE, posts)):
            L.download_post(p, options.action)


        LASTCHECKFILE = options.action + "/lastcheck"
        try:
            with open(LASTCHECKFILE, "w") as t:
                t.write("\n".join([TODAY.year.__str__(), TODAY.month.__str__(), TODAY.day.__str__()]))
                t.write("\n" + TODAY.__str__())
                t.close()
        except IOError:
            logging.debug('Could not write lastcheck file for profile ' + options.action)
            pass


if __name__ == '__main__':
    status = main()
    sys.exit(status)
