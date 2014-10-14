#! /usr/bin/python

import MythTV
import tvdb_api
from optparse import OptionParser
import dateutil.parser
import os, sys

t = tvdb_api.Tvdb()

try:
    database = MythTV.MythDB()
    backend = MythTV.MythBE()
except MythTV.MythBEError:
    sys.exit(1)


def tvdb_ref(program):
    dbref = program.inetref
    
    if (dbref is None) or (dbref[0:8] != "ttvdb.py"):
        try:
            ref = int(t[program.title]['id'])
        except tvdb_api.tvdb_shownotfound:
            ref = None
        return ref
    else:
        return int(dbref[9::])

def show_name(program):
    ref = tvdb_ref(program)
    if ref is not None:
        return t[ref]['seriesname']
    else:
        return program.title

def episode_number(program):

    season = program.season
    episode = program.episode
    syndicated = program.syndicatedepisode

    if syndicated is None and season == 0:
        return (0,0)
    
    if season == 0:
        data = str(syndicated)[1::].split("S")
        season = int(data[1])
        episode = int(data[0])

    return (season, episode)

def episode_name(program):
    
    (season, episode) = episode_number(program)
    ref = tvdb_ref(program)
    if ref is not None:
        return t[ref][season][episode]['episodename']
    elif program.subtitle is not None:
        return program.subtitle
    else:
        return ""

def episode_string(program):

    (season, episode) = episode_number(program)

    outp = "S"

    if season < 10:
        outp = outp + "0"
    outp = outp + str(season) + "E"

    if episode < 10:
        outp = outp + "0"
    outp = outp + str(episode)

    return outp

def season_string(program):

    (season, episode) = episode_number(program)
    outp = "Season "
    if season < 10:
        outp += "0"
    outp += str(season)
    return outp

def format_name(program):

    outp = show_name(program) + " - " \
           + episode_string(program) + " - " \
           + episode_name(program)
    return outp

def create_link(program, folder):
    linkname = os.path.join(show_name(program), season_string(program), format_name(program))
    source = backend.getCheckfile(program)
    dest = os.path.join(folder, linkname)

    # make sure destination exists
    sdest = dest.split('/')
    for i in range(2,len(sdest)):
        tmppath = "/" + os.path.join(*sdest[:i])
        if not os.access(tmppath, os.F_OK):
            os.mkdir(tmppath)

    os.symlink(source, dest)

def remove_links(folder):
    for path,dirs,files in os.walk(folder, topdown=False):
        for fname in files:
            tmppath = os.path.join(path, fname)
            if not os.path.islink(tmppath):
                raise Exception('Non-link file found in destination path.')
            os.unlink(tmppath)
        os.rmdir(path)

parser = OptionParser(usage="usage: %prog [options] [jobid]")
parser.add_option("--dest", action="store", type="str", dest="dest",
                  help="""Specify the directory for the links.  If no pathname
                  is given, links will be created in the show_names directory
                  inside of the current MythTV data directory on this machine.
                  
                  WARNING: ALL symlinks within the destination directory and its
                  subdirectories (recursive) will be removed.""")
parser.add_option("--chanid", action="store", type="int", dest="chanid",
                  help="""Create a link only for the specified recording file.  This argument
                  must be used in combination with --starttime.  This argument may be used
                  in a custom user-job, or through the event-driven notification system's
                  "Recording Started" event.""")
parser.add_option("--starttime", action="store", type="int", dest="starttime",
                  help="""Create a link only for the specified recording file.  This argument
                  must be used in combination with --chanid.  This argument may be used
                  in a custom user-job, or through the event-driven notification system's
                  "Recording Started" event.""")
parser.add_option("--all", action="store_true", dest="all", default=False,
                  help="""Create a link for all files, even if not known to tvdb.""")

opts, args = parser.parse_args()

if opts.dest is None:
    print "Must specify an output directory!"
    sys.exit(0)

if opts.chanid and opts.starttime:
    # starttime = dateutil.parser.parse(str(opts.starttime) + "UTC")
    starttime = dateutil.parser.parse(str(opts.starttime))
    rec = backend.getRecording(opts.chanid, starttime)
    # if rec is not None:
    create_link(rec, opts.dest)

else:
    # remove old links
    remove_links(opts.dest)

    recordings = backend.getRecordings()
    for program in recordings:
        if opts.all or tvdb_ref(program) is not None:
            create_link(program, opts.dest)

