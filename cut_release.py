#!/usr/bin/env python
# * coding: utf8 *
"""
Releaser: Package up the python toolbox and related files for downloading

Usage:
 cut_release (major|minor|patch) [--python-version=<version>]
 cut_release publish

Options:
  --python-version=<version>    the desktop (2) or pro (3) tool to release [default: 3]
"""

from json import dump, load
from pathlib import Path
from zipfile import ZipFile

from docopt import docopt
from git import Repo

BUMP_TYPES = ['major', 'minor', 'patch']
BRANCHES = {'3': 'master', '2': 'py-2'}
VERSION_NAMES = {'3': 'PRO_VERSION_NUMBER', '2': 'VERSION_NUMBER'}
CONVENTIONAL_COMMITS = {'3': 'py-3', '2': 'py-2'}
BUILD_ASSETS = [Path('src') / 'agrcgeocoding' / 'geocode.py',
                Path('src') / 'AGRC Geocode Tools.pyt'] + [Path('tool-version.json')]
TOOL_ZIP = Path('tool') / 'AGRC Geocode Tools.zip'


def cut_release(args):
    """main method
    """
    python_version = args['--python-version']
    print(f'release branch: {BRANCHES[python_version]}')

    repo = Repo(Path(__file__).resolve().parent)
    git_cli = repo.git

    release_type = BUMP_TYPES[2]
    if args['major']:
        release_type = BUMP_TYPES[0]
    elif args['minor']:
        release_type = BUMP_TYPES[1]

    print(f'release type: {release_type}')

    current_version = get_version(python_version)
    print(f'prior version: {current_version}')

    if python_version == '2':
        desktop_branch = BRANCHES['2']
        git_cli.checkout(desktop_branch)

        new_version = bump(current_version, release_type)
        set_version(python_version, new_version)

        build_zip()

        release_commit(git_cli, new_version, python_version, include_zip=True)

        #: switch back to master
        git_cli.checkout(BRANCHES['3'])
        set_version(python_version, new_version)

        release_commit(git_cli, new_version, python_version, tag=False)
    else:
        new_version = bump(current_version, release_type)
        set_version(python_version, new_version)

        build_zip()

        release_commit(git_cli, new_version, python_version, include_zip=True)

    print(f'new version: {new_version}')


def release_commit(git_cli, new_version, python_version, include_zip=False, tag=True):
    """make release commit
    """
    git_cli.add('tool-version.json')

    if include_zip:
        git_cli.add(TOOL_ZIP)

    scope = CONVENTIONAL_COMMITS[python_version]

    git_cli.commit(m=f'release({scope}): v{new_version}')

    if tag:
        git_cli.tag(f'v{new_version}-{scope}')


def build_zip():
    """bundle files into zip
    """
    with ZipFile(TOOL_ZIP, 'w') as zip_file:
        for filename in BUILD_ASSETS:
            zip_file.write(filename, filename.name)


def bump(current_version, release_type):
    """bump the version number based on the release type
    """
    parts = [int(part) for part in current_version.split('.')]

    #: increment appropriate version number
    bump_type_index = BUMP_TYPES.index(release_type)
    parts[bump_type_index] += 1

    #: reset any lower parts to zero
    for lower_part in BUMP_TYPES[bump_type_index + 1:]:
        parts[BUMP_TYPES.index(lower_part)] = 0

    return '.'.join([str(part) for part in parts])


def get_version(python_version):
    """get the appropriate version number from tool-version.json
    """
    with open('tool-version.json', 'r') as version_file:
        version_json = load(version_file)
        return version_json[VERSION_NAMES[python_version]]


def set_version(python_version, new_version):
    """update the version number in tool-version.json
    """
    with open('tool-version.json', 'r+') as version_file:
        version_json = load(version_file)

        version_json[VERSION_NAMES[python_version]] = new_version

        version_file.seek(0)
        version_file.truncate()
        dump(version_json, version_file, indent=2)
        version_file.write('\n')


def publish():
    """push new commits/tags to GitHub
    """
    repo = Repo(Path(__file__).resolve().parent)
    git_cli = repo.git

    for branch in BRANCHES.values():
        git_cli.push('origin', branch, tags=True)


if __name__ == '__main__':
    options = docopt(__doc__)

    if options['publish']:
        publish()
    else:
        cut_release(options)
