#! /usr/bin/env python3

import argparse
import glob
import inquirer
import os
# from pprint import pprint
import re
import sys
import yaml

appname = 'scotty'

# -----------------------------------------------
# Arguments
# -----------------------------------------------
parser = argparse.ArgumentParser('Beam me up to remote directories...')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-c', '--configfile', help='config yaml file', required=False)
group.add_argument('-b', '--browse', help='browse through all available configs', required=False, action='store_true')
group.add_argument('-d', '--configdir', help='browse through given config dir', required=False)

parser.add_argument('--interactive', '-i', help='use interactive mode', required=False, action='store_true')

args = parser.parse_args()

# -----------------------------------------------
# Get config file
# -----------------------------------------------
homedir = os.getenv("HOME")
config_file = args.configfile

if args.configfile:
    if re.match("^~\/", config_file):
        file_path = os.path.abspath(config_file.replace('~', homedir))
    elif re.match("^\.\/", config_file) or re.match("^\/", config_file):
        file_path = os.path.abspath(config_file)
    else:
        file_path = os.path.abspath('./' + config_file)
else:
    # search paths
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)

    paths_found = []

    if args.configdir:
        paths_search = [args.configdir]
    else:
        confdir_current = dname + '/conf.d/'
        confdir_home = os.path.abspath(homedir) + f'/.{appname}/conf.d/'
        confdir_global = f'/etc/{appname}/conf.d/'

        paths_search = [confdir_home, confdir_global]

    for path in paths_search:
        if os.path.exists(path):
            paths_found.append(path)

    paths_search_display = ', '.join(paths_search)

    if not len(paths_found):
        sys.exit(f'No config dirs found: {paths_search_display}')

    config_files = []
    for path in paths_found:
        config_files += glob.glob(f"{path}*.yml")

    if not len(config_files):
        sys.exit(f'No config files found: {paths_search_display}')

    questions = [inquirer.List('select_path', message=f'Select config file:', choices=config_files,),]
    answers = inquirer.prompt(questions)
    file_path = answers['select_path']

if not os.path.exists(file_path):
    sys.exit(f'Config file "{file_path}" not found!')

# -----------------------------------------------
# Valdate config file
# -----------------------------------------------
file_path = os.path.abspath(args.configfile)
if not os.path.exists(file_path):
    print('Config file does not exist.')
    sys.exit(1)

# read the yaml file
with open(file_path) as file:
    # config = yaml.load(file, Loader=yaml.SafeLoader)

    if re.search('.+\.ya?ml$', file_path):
        try:
            config = yaml.load(file, Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            print(e)
            sys.exit('Exception in parsing yaml file ' + file_path + '!')
    else:
        sys.exit('{} file not supported!'.format(file_path))

# -----------------------------------------------
# Get list of servers
# -----------------------------------------------
servers_display = []
for fqdn, metadata in config['servers'].items():

    description = [fqdn.ljust(40)]

    # for field in ['locations', 'description']:
    for field in ['description']:
        if field in metadata:

            if isinstance(metadata[field], list):
                data = ','.join(metadata[field])
            else:
                data = metadata[field]

            description.append(f'{data}'.ljust(20))

    description = ' '.join(description)

    servers_display.append(description)

servers_display.sort()
questions = [inquirer.List('select_server', message=f'Select server:', choices=servers_display,),]
answers = inquirer.prompt(questions)
selected_server = answers['select_server']

# -----------------------------------------------
# Get list of locations
# -----------------------------------------------
selected_server = selected_server.split(' ')[0]

print(f'Show locations for {selected_server}...')

locations = []

if 'locations' not in config['servers'][selected_server]:
    print('No locations defined...')
    sys.exit(1)

# configuration for server
for key in config['servers'][selected_server]['locations']:
    if key in config['locations']:
        for location in config['locations'][key]:
            locations.append(location)

if not len(locations):
    print('No location found...')
    sys.exit(1)

locations.sort()
questions = [inquirer.List('select_location', message=f'Select location:', choices=locations,),]
answers = inquirer.prompt(questions)
selected_location = answers['select_location']

# -----------------------------------------------
# Execute command
# -----------------------------------------------
cmd = f'ssh {selected_server} -t "cd {selected_location}; bash --login"'

if args.interactive:
    print(cmd)
    answer = input(f'Continue? [Y/n]')

os.system(cmd)
