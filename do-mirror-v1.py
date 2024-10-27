#!/usr/bin/env python3
#
# Little script to create a static mirror of the project list, wrap infos,
# wraps, and patch zips available in the v1 api database.
#
# Copyright (C) 2023 Tim-Philipp Müller <tim centricular com>
#
# SPDX-License-Identifier: MPL-2.0

import argparse
import hashlib
import os
import shutil
import sys

import configparser
import json
import urllib.request
from urllib.parse import urlparse

# root@wrapdb:/home/legeana/wrapweb/wrapweb# grep route api.py 
# @BP.route('/v1/query/byname/<project>', methods=['GET'])
# @BP.route('/v1/query/get_latest/<project>', methods=['GET'])
# @BP.route('/v1/projects')
# @BP.route('/v1/projects/<project>')
# @BP.route('/v1/projects/<project>/<branch>/<int:revision>/get_wrap')
# @BP.route('/v1/projects/<project>/<branch>/<int:revision>/get_zip')

api = 'v1'

SCRIPTDIR = os.path.realpath(os.path.dirname(__file__))

parser = argparse.ArgumentParser(prog='do-mirror-v1', description='Meson wrapdb v1 api contents mirror')
parser.add_argument('output_directory', type=str)
args = parser.parse_args()

print('Output directory:', args.output_directory)
base_name = f'{api}-static'
base_dir = os.path.join(args.output_directory, base_name)
os.makedirs(base_dir, exist_ok=True)

#############################################################################
#
# Download projects list
#
#############################################################################

# hyphen for file vs. dir
projects_fn = os.path.join(base_dir, '-', 'projects')
os.makedirs(os.path.dirname(projects_fn), exist_ok=True)

projects_url = f'https://wrapdb.mesonbuild.com/{api}/projects'
projects_url_path = urlparse(projects_url).path

print('Downloading', projects_url, '-->', projects_fn)

res = urllib.request.urlretrieve(projects_url, projects_fn)

with open(projects_fn) as f:
    projects_json = json.load(f)

#############################################################################
#
# Download each version of each project
#
#############################################################################

for project in projects_json['projects']:

    print()
    print('Project:', project)
    print()

    #############################################################################
    #
    # Download project version list
    #
    #############################################################################

    # hyphen for file vs. dir
    project_fn = os.path.join(base_dir, 'projects', '-', project)
    os.makedirs(os.path.dirname(project_fn), exist_ok=True)

    project_url = f'https://wrapdb.mesonbuild.com/{api}/projects/{project}'
    project_url_path = urlparse(project_url).path

    print('\tDownloading', project_url, '-->', project_fn)
    res = urllib.request.urlretrieve(project_url, project_fn)

    with open(project_fn) as project_f:
        project_versions_json = json.load(project_f)
        # print('\t', project_versions_json)

    #############################################################################
    #
    # Download each version of the project
    #
    #############################################################################

    project_versions = project_versions_json['versions']
    for version in project_versions:
        print('\tVersion:', version)
        branch = version['branch']
        revision = version['revision']
        wrap_fn = os.path.join(base_dir, 'projects', project, branch, f'{revision}', '-', 'get_wrap')
        os.makedirs(os.path.dirname(wrap_fn), exist_ok=True)
        wrap_url = f'https://wrapdb.mesonbuild.com/{api}/projects/{project}/{branch}/{revision}/get_wrap'
        wrap_url_path = urlparse(wrap_url).path
        print('\t\t', 'Downloading', wrap_url, '-->', wrap_fn)
        res = urllib.request.urlretrieve(wrap_url, wrap_fn)

        config = configparser.ConfigParser()
        config.read(wrap_fn, encoding='utf-8')

        patch_url = config.get('wrap-file', 'patch_url')
        patch_filename = config.get('wrap-file', 'patch_filename')
        patch_hash = config.get('wrap-file', 'patch_hash')

        # print('\t\tpatch_filename', patch_filename)
        # print('\t\tpatch_url', patch_url)

        # Create foo.wrap
        wrap_fn_alt = os.path.join(base_dir, 'projects', project, branch, f'{revision}', f'{project}.wrap')
        print('\t\t', 'Copying', wrap_fn, '-->', wrap_fn_alt)
        shutil.copy2(wrap_fn, wrap_fn_alt)

        # Create foo-1.2.3-1.wrap
        wrap_fn_alt2 = os.path.join(base_dir, 'projects', project, branch, f'{revision}', f'{project}-{branch}-{revision}.wrap')
        print('\t\t', 'Copying', wrap_fn, '-->', wrap_fn_alt2)
        shutil.copy2(wrap_fn, wrap_fn_alt2)

        zip_fn = os.path.join(base_dir, 'projects', project, branch, f'{revision}', '-', 'get_zip')
        os.makedirs(os.path.dirname(zip_fn), exist_ok=True)

        zip_url = f'https://wrapdb.mesonbuild.com/{api}/projects/{project}/{branch}/{revision}/get_zip'
        zip_url_http = f'http://wrapdb.mesonbuild.com/{api}/projects/{project}/{branch}/{revision}/get_zip'

        zip_url_path = urlparse(zip_url).path

        # Todo: replace it with the https version perhaps?
        if patch_url == zip_url_http:
            print('\t\t', 'WARNING: http zip url in wrap file', patch_filename, ':', patch_url)
        else:
            assert(zip_url == patch_url or api != 'v1')

        print('\t\t', 'Downloading', zip_url, '-->', patch_filename)
        res = urllib.request.urlretrieve(zip_url, zip_fn)

        # Create foo-1.2.3-1-wrap.zip
        zip_fn_alt = os.path.join(base_dir, 'projects', project, branch, f'{revision}', patch_filename)
        print('\t\t', 'Copying', zip_fn, '-->', zip_fn_alt)
        shutil.copy2(zip_fn, zip_fn_alt)
        
        with open(zip_fn,"rb") as zip_f:
            zip_bytes = zip_f.read() # read entire file as bytes
            zip_hash = hashlib.sha256(zip_bytes).hexdigest();
            if zip_hash != patch_hash:
                print('ERROR: Hash of', zip_fn, 'is', zip_hash, ', but expected', patch_hash)
                sys.exit(1)

    #############################################################################
    #
    # Download latest version of the project
    #
    #############################################################################

    if len(project_versions) > 0:
        # hyphen for file vs. dir
        get_latest_fn = os.path.join(base_dir, 'query', 'get_latest', '-', project)
        os.makedirs(os.path.dirname(get_latest_fn), exist_ok=True)

        get_latest_url = f'https://wrapdb.mesonbuild.com/{api}/query/get_latest/{project}'
        get_latest_url_path = urlparse(get_latest_url).path

        print('\tDownloading', get_latest_url, '-->', get_latest_fn)
        res = urllib.request.urlretrieve(get_latest_url, get_latest_fn)

print()
