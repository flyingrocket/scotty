#! /usr/bin/env python3

import argparse
import inquirer
import os
# from pprint import pprint
import re
import sys
import yaml

# -----------------------------------------------
# Arguments
# -----------------------------------------------
parser = argparse.ArgumentParser('Cd into remote directories...')

parser.add_argument('-c', '--configfile', help='config yaml file', required=True)

parser.add_argument('--interactive', '-i', help='use server aliases', required=False, action='store_true')

args = parser.parse_args()

# -----------------------------------------------
# Valdate
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
