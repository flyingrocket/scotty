#! /usr/bin/env python3

import argparse
import glob
import inquirer
from iterfzf import iterfzf
import inspect
import os

# from pprint import pprint
import re
import subprocess
import sys
import yaml

# -----------------------------------------------
# Variables
# -----------------------------------------------
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)

appname = "scotty"
homedir = os.path.abspath(os.getenv("HOME"))
default_browse_dirs = f"{homedir}/.{appname}/conf.d/"
default_browse_dirs = f"/etc/{appname}/conf.d/,{homedir}/.{appname}/conf.d/"

# -----------------------------------------------
# Arguments
# -----------------------------------------------
parser = argparse.ArgumentParser("Ssh into remote directories...")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-c", "--config-file", help="config yaml file", required=False)

# browse configuration files
group.add_argument(
    "-b",
    "--browse",
    help="browse through all available configs",
    required=False,
    action="store_true",
)

# browse configuration files
parser.add_argument(
    "--browse-dirs",
    help=f"browse dir(s) - seperated by comma - for available config files. defaults to {default_browse_dirs}",
    default=default_browse_dirs,
    required=False,
)

parser.add_argument(
    "--interactive",
    "-i",
    help="use interactive mode",
    required=False,
    action="store_true",
)

parser.add_argument(
    "--fuzzy-search",
    "-f",
    help="fuzzy find within directory",
    required=False,
    action="store_true",
)

parser.add_argument(
    "--fuzzy-depth",
    "-d",
    help="fuzzy find depth",
    required=False,
    default=3,
)

args = parser.parse_args()

# -----------------------------------------------
# Functions
# -----------------------------------------------
def confirm(message="", default="Y", choices=["y", "n"], force_script_exit=True):

    if not message == "":
        print(message)

    answer = None
    choices = [item.lower() for item in choices]

    choices_display = list(
        map(lambda x: x.upper() if x.lower() == default.lower() else x, choices)
    )

    if force_script_exit:
        continue_text = "Continue?"
    else:
        continue_text = "Your answer:"

    while answer not in choices:
        script_exit = False
        answer = input(f"{continue_text} [" + "/".join(choices_display) + "] ").lower()

        # set empty answer to default
        if answer == "":
            answer = default.lower()

        # exit script
        if answer == "n":
            if force_script_exit:
                script_exit = True

    if script_exit:
        print("Exiting...")
        sys.exit()
    else:
        return answer


def fail(message_text):
    callerframerecord = inspect.stack()[1]  # 0 represents this line
    # 1 represents line at caller
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)

    text = "{}, line {} \n{}".format(info.filename, info.lineno, message_text)
    print(text)
    sys.exit()


# capture the output of a command
def sub_check(cmd, directory=""):

    cmd = re.sub(" +", " ", cmd)

    # if directory == "":
    #     directory = app_base_dir

    try:
        output = subprocess.check_output(
            # cmd, shell=True, cwd=directory, encoding="UTF-8"
            cmd,
            shell=True,
            encoding="UTF-8",
        )
    except subprocess.CalledProcessError:
        sys.exit()

    return output.strip()


# run a command
def sub_run(cmd, directory=""):

    cmd = re.sub(" +", " ", cmd)

    # if directory == "":
    #     directory = app_base_dir

    try:
        subprocess.run(
            cmd,
            check=True,
            universal_newlines=True,
            # cwd=directory,
            shell=True,
        )
    except subprocess.CalledProcessError:
        sys.exit()


# -----------------------------------------------
# Get config file
# -----------------------------------------------
config_file = args.config_file

if args.config_file:
    if re.match("^~\/", config_file):
        file_path = os.path.abspath(config_file.replace("~", homedir))
    elif re.match("^\.\/", config_file) or re.match("^\/", config_file):
        file_path = os.path.abspath(config_file)
    else:
        file_path = os.path.abspath("./" + config_file)
elif args.browse:
    # search paths

    config_dirs_found = []

    for path in args.browse_dirs.split(","):
        if os.path.exists(path):
            config_dirs_found.append(os.path.abspath(path))
        else:
            # only fail if specific paths are given
            if not args.browse_dirs == default_browse_dirs:
                sys.exit(f"Config dir {path} not found!")

    print(f"Browse '{args.browse_dirs}' directories...")

    if not len(config_dirs_found):
        sys.exit(f"No config dirs found.")

    config_files = []
    for path in config_dirs_found:
        path = path.rstrip("/")
        config_files += glob.glob(f"{path}/*.yml")

    if not len(config_files):
        sys.exit(f"No config files found!")

    config_files.sort()

    file_path = iterfzf(config_files, multi=False, exact=True)

else:
    sys.exit()

if not os.path.exists(file_path):
    sys.exit(f'Config file "{file_path}" not found!')

# -----------------------------------------------
# Read config file
# -----------------------------------------------
# read the yaml file
with open(file_path) as file:
    # config = yaml.load(file, Loader=yaml.SafeLoader)

    if re.search(".+\.ya?ml$", file_path):
        try:
            config = yaml.load(file, Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            print(e)
            sys.exit("Exception in parsing yaml file " + file_path + "!")
    else:
        sys.exit("{} file not supported!".format(file_path))

# -----------------------------------------------
# Get list of servers
# -----------------------------------------------
servers_display = []
for fqdn, metadata in config["servers"].items():

    description = [fqdn.ljust(40)]

    # for field in ['locations', 'description']:
    for field in ["description"]:
        if field in metadata:

            if isinstance(metadata[field], list):
                data = ",".join(metadata[field])
            else:
                data = metadata[field]

            description.append(f"{data}".ljust(20))

    description = " ".join(description)

    servers_display.append(description)

servers_display.sort()

selected_server = iterfzf(servers_display, multi=False, exact=True)

# -----------------------------------------------
# Get list of locations
# -----------------------------------------------
selected_server = selected_server.split(" ")[0]

print(f"Show locations for {selected_server}...")

locations = []

if "locations" not in config["servers"][selected_server]:
    print("No locations defined...")
    sys.exit(1)

# configuration for server
for key in config["servers"][selected_server]["locations"]:
    if key in config["locations"]:
        for location in config["locations"][key]:
            locations.append(location)

if not len(locations):
    print("No location found...")
    sys.exit(1)

locations.append("/")

home_dir = sub_check(f"ssh {selected_server} 'eval echo $HOME'")
locations.append(home_dir)
# locations.append("~")  # home dir
locations.append("")  # home dir (default)

locations.sort()

selected_location = iterfzf(locations, multi=False, exact=True)

if selected_location == "":
    selected_location = home_dir

if args.fuzzy_search:
    cmd = f"ssh {selected_server} find {selected_location} -maxdepth {args.fuzzy_depth} -type d"
    content = sub_check(cmd)
    str_list = content.split("\n")
    str_list = list(filter(None, str_list))  # remove empty values

    # filter out hidden dirs
    directories = []
    for item in str_list:
        print(item)
        if not re.search("\/\.", item):
            directories.append(item)

    if not len(directories):
        print("No directories found!")
        sys.exit(1)

    selected_location = iterfzf(directories, multi=False, exact=True)

if not selected_location:
    print("Directory is empty!")
    sys.exit(1)

# -----------------------------------------------
# Execute command
# -----------------------------------------------
cmd = f'ssh {selected_server} -t "cd {selected_location}; bash --login"'

if args.interactive:
    print(cmd)
    answer = input(f"Continue? [Y/n]")

sub_run(cmd)
