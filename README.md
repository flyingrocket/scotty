# scotty

## Description

Ssh into servers at bookmarked locations. A configuration (yaml) file may be passed to the script with the -c flag. Alternatively, you can browse and interact with scotty with the -b flag. In that case, yaml files are expected to reside in ~/.scotty/conf.d or /etc/scotty/conf.d.

## Installation

Obviously an ssh client must be installed with ssh key-based authentication.

Install pip packages:

```bash
pip install -r requirements.txt
```

## Usage

See -h for options

```bash
./scotty.py -h
```

Output:

```text
usage: Beam me up to remote directories... [-h] (-c CONFIGFILE | -b | -d CONFIGDIR) [--interactive]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configfile CONFIGFILE
                        config yaml file
  -b, --browse          browse through all available configs
  -d CONFIGDIR, --configdir CONFIGDIR
                        browse through given config dir
  --interactive, -i     use interactive mode
```

## Examples

See example config file.
