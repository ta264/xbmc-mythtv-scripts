#! /usr/bin/python

import MythTV
import tvdb_api
from optparse import OptionParser
import dateutil.parser
import os, sys, subprocess
from xbmcjson import XBMC

class MYLOG(MythTV.MythLog):
  "A specialised logger"

  def __init__(self, db):
    "Initialise logging"
    MythTV.MythLog.__init__(self, '', db)

  def log(self, msg, level = MythTV.MythLog.INFO):
    "Log message"
    # prepend string to msg so that rsyslog routes it to mythcommflag.log logfile
    MythTV.MythLog.log(self, MythTV.MythLog.FILE, level, 'mythutil: ' + msg.rstrip('\n'))

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

def get_extension(path):
    splitpath = path.split('.')
    return splitpath[-1]

def get_skip_list(program):
    chanid = program.chanid
    startts = program.recstartts.mythformat()
    command = "mythutil -q --getskiplist --chanid %s --starttime %s" % (chanid, startts)
    args = command.split(" ")

    outp = subprocess.check_output(args).strip()
    skiplist = outp[22::].replace("-", " ").split(",")
    return skiplist

def write_skip_list(skiplist, dest):
    with open(dest, 'w') as f:
        f.write("FILE PROCESSING COMPLETE\n")
        f.write("------------------------\n")
        for entry in skiplist:
            f.write(entry + "\n")

def create_link(program, folder):
    source = backend.getCheckfile(program)
    extension = get_extension(source)
    linkname = os.path.join(show_name(program), season_string(program), format_name(program))
    linkdest = os.path.join(folder, linkname + "." + extension)

    # make sure destination exists
    sdest = linkdest.split('/')
    for i in range(2,len(sdest)):
        tmppath = "/" + os.path.join(*sdest[:i])
        if not os.access(tmppath, os.F_OK):
            logger.log('Creating directory ' + tmppath)
            os.mkdir(tmppath)

    # create the link
    logger.log('Symlinking ' + linkname)
    if os.path.islink(linkdest):
      os.unlink(linkdest)
    os.symlink(source, linkdest)

    # add comskip file
    logger.log('Writing comskip file for ' + linkname)
    comskipdest = os.path.join(folder, linkname + ".txt")
    write_skip_list(get_skip_list(program), comskipdest)

def remove_links(folder):
    for path,dirs,files in os.walk(folder, topdown=False):
        for fname in files:
            tmppath = os.path.join(path, fname)
            if os.path.islink(tmppath):
                os.unlink(tmppath)
            elif get_extension(tmppath) == "txt":
                os.remove(tmppath)
            else:
                raise Exception('Non-link file found in destination path.')
        os.rmdir(path)

t = tvdb_api.Tvdb()

try:
    database = MythTV.MythDB()
    backend = MythTV.MythBE()
except MythTV.MythBEError:
    sys.exit(1)


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

# Set up logging
MYLOG.loadOptParse(parser)
MYLOG._setmask(MYLOG.FILE)
logger = MYLOG(db=database)
logger.log('Initializing')

# Connect to XBMC
xbmc = XBMC("http://localhost:8000/jsonrpc")

opts, args = parser.parse_args()

if opts.dest is None:
    print "Must specify an output directory!"
    sys.exit(0)

if opts.chanid and opts.starttime:
    # starttime = dateutil.parser.parse(str(opts.starttime) + "UTC")
    logger.log('Creating single link.  Chanid %d starttime %d' % (opts.chanid, opts.starttime))
    starttime = dateutil.parser.parse(str(opts.starttime))
    rec = backend.getRecording(opts.chanid, starttime)
    # if rec is not None:
    create_link(rec, opts.dest)

    logger.log('Scanning XBMC library')
    xbmc.VideoLibrary.Scan()

else:
    # remove old links
    logger.log('Remove old links')
    remove_links(opts.dest)

    logger.log('Getting recordings')
    recordings = backend.getRecordings()

    logger.log('Creating new links')
    for program in recordings:
      if opts.all or tvdb_ref(program) is not None:
        if program.recgroup != "LiveTV":
          create_link(program, opts.dest)

    logger.log('Scanning XBMC library')
    xbmc.VideoLibrary.Scan()
    logger.log('Cleaning XBMC library')
    xbmc.VideoLibrary.Clean()

logger.log('Done')

