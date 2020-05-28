#!/usr/bin/env python
# * coding: utf8 *
"""
Tools for geocoding addresses using AGRC's geocoding web service.

CLI usage: `python geocode.py --help`.
"""

import os
from __future__ import print_function

import csv
import json
import random
import re
import time
from string import Template

import requests
from requests.adapters import HTTPAdapter

DEFAULT_SPATIAL_REFERENCE = 26912
DEFAULT_LOCATOR_NAME = 'all'
SPACES = re.compile(r'(\s\d/\d\s)|/|(\s#.*)|%|(\.\s)|\?')
RATE_LIMIT_SECONDS = (0.015, 0.03)
HOST = 'api.mapserv.utah.gov'
HEADER = (
    'primary_key', 'input_street', 'input_zone', 'x', 'y', 'score', 'locator', 'matchAddress', 'standardizedAddress',
    'addressGrid', 'message'
)
UNIQUE_RUN = time.strftime('%Y%m%d%H%M%S')
HEALTH_PROBE_COUNT = 25


def _cleanse_street(data):
    """cleans up address garbage
    """
    replacement = ' '
    street = str(data).strip()

    street = SPACES.sub(replacement, street)

    for char in range(0, 31):
        street = street.replace(chr(char), replacement)
    for char in range(33, 37):
        street = street.replace(chr(char), replacement)

    street = street.replace(chr(38), 'and')

    for char in range(39, 47):
        street = street.replace(chr(char), replacement)
    for char in range(58, 64):
        street = street.replace(chr(char), replacement)
    for char in range(91, 96):
        street = street.replace(chr(char), replacement)
    for char in range(123, 255):
        street = street.replace(chr(char), replacement)

    return street.strip()


def _cleanse_zone(data):
    """cleans up zone garbage
    """
    zone = SPACES.sub(' ', str(data)).strip()

    if len(zone) > 0 and zone[0] == '8':
        zone = zone.strip()[:5]

    return zone


def _format_time(seconds):
    """seconds: number
    returns a human-friendly string describing the amount of time
    """
    minute = 60.00
    hour = 60.00 * minute

    if seconds < 30:
        return '{} ms'.format(int(seconds * 1000))

    if seconds < 90:
        return '{} seconds'.format(round(seconds, 2))

    if seconds < 90 * minute:
        return '{} minutes'.format(round(seconds / minute, 2))

    return '{} hours'.format(round(seconds / hour, 2))


def execute(
    api_key,
    rows,
    output_directory,
    spatial_reference=DEFAULT_SPATIAL_REFERENCE,
    locators=DEFAULT_LOCATOR_NAME,
    add_message=print_function,
    ignore_failures=False
):
    """Geocode an iterator of data.

    api_key           = string
    rows              = iterator of rows in this form: (primary_key, street, zone)
    output_directory  = path to directory that you would like the output csv created in
    spatial_reference = wkid for any Esri-supported spatial reference
    locator           = determines what locators are used ('all', 'roadCenterlines', or 'addressPoints')
    add_message       = the function that log messages are sent to
    ignore_failure    = used to ignore the short-circut on multiple subsequent failures at the beginning of the job
    """
    url_template = Template('https://{}/api/v1/geocode/$street/$zone'.format(HOST))
    sequential_fails = 0
    success = 0
    stats = {'fail': 0, 'total': 0}
    score = 0

    add_message('api_key: {}'.format(api_key))
    add_message('output_directory: {}'.format(output_directory))
    add_message('spatial_reference: {}'.format(spatial_reference))
    add_message('locators: {}'.format(locators))
    add_message('ignore_failures: {}'.format(ignore_failures))

    def log_status():
        try:
            failure_rate = round(100 * stats['fail'] / stats['total'])
        except ZeroDivisionError:
            failure_rate = 100
        try:
            average_score = round(score / success)
        except ZeroDivisionError:
            average_score = 'n/a'

        add_message('Total requests: {}'.format(stats['total']))
        add_message('Failure rate: {}%'.format(failure_rate))
        add_message('Average score: {}'.format(average_score))
        add_message('Time taken: {}'.format(_format_time(time.clock() - start)))

    output_table = os.path.join(output_directory, 'geocoding_results_{}.csv'.format(UNIQUE_RUN))

    with open(output_table, 'w+') as result_file:
        writer = csv.writer(result_file)

        writer.writerow(HEADER)

        start = time.clock()

        def write_error(primary_key, street, zone, error_message):
            writer.writerow((primary_key, street, zone, 0, 0, 0, None, None, None, None, error_message))

            stats['fail'] += 1
            stats['total'] += 1

            add_message('Failure on row: {} with {}, {}\n{}'.format(primary_key, street, zone, error_message))

        for primary_key, street, zone in rows:
            if not ignore_failures and stats['total'] == HEALTH_PROBE_COUNT and sequential_fails == HEALTH_PROBE_COUNT:
                add_message('Continuous fail threshold reached. Failing entire job.')

                return None

            url = url_template.substitute({'street': _cleanse_street(street), 'zone': _cleanse_zone(zone)})

            time.sleep(random.uniform(RATE_LIMIT_SECONDS[0], RATE_LIMIT_SECONDS[1]))

            try:
                request = requests.get(
                    url,
                    timeout=5,
                    params={
                        'apiKey': api_key,
                        'spatialReference': spatial_reference,
                        'locators': locators
                    },
                    headers={'x-client': 'geocoding-toolbox-py-2'}
                )

                try:
                    response = request.json()
                except ValueError as ex:
                    if ex.message == 'No JSON object could be decoded':
                        write_error(
                            primary_key, street, zone, 'Missing required parameters for URL: {}'.format(request.url)
                        )

                        continue

                    raise ex

                if request.status_code == 400:
                    #: fail fast with api key auth
                    raise InvalidAPIKeyException(stats['total'], primary_key, response['message'])
                elif request.status_code != 200:
                    sequential_fails += 1

                    write_error(primary_key, street, zone, response['message'])

                    continue

                match = response['result']
                match_score = match['score']
                location = match['location']
                match_address = match['matchAddress']
                standardized_address = match['standardizedAddress']
                address_grid = match['addressGrid']

                match_x = location['x']
                match_y = location['y']

                sequential_fails = 0
                success += 1
                stats['total'] += 1
                score += match_score

                writer.writerow((
                    primary_key, street, zone, match_score, match_address, standardized_address, address_grid, match_x,
                    match_y, None
                ))
            except InvalidAPIKeyException as ex:
                raise ex
            except Exception as ex:
                write_error(primary_key, street, zone, str(ex)[:500])

            if stats['total'] % 10000 == 0:
                log_status()
                start = time.clock()

        add_message('Job Completed')
        log_status()

    return output_table


class InvalidAPIKeyException(Exception):
    """Custom exception for invalid API key returned from api
    """

    def __init__(self, total, primary_key, message):
        self.total = total
        self.primary_key = primary_key
        self.message = '\n\nError returned for primary_key: {}\n'.format(
            primary_key
        ) + 'API response message: {}\nTotal rows processed: {}'.format(message, total)
        super(InvalidAPIKeyException, self).__init__(self.message)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Geocode a csv')

    parser.add_argument('key', type=str)
    parser.add_argument('csv', type=str)
    parser.add_argument('id', type=str)
    parser.add_argument('street', type=str)
    parser.add_argument('zone', type=str)
    parser.add_argument('output', type=str)
    parser.add_argument('--wkid', default=26912, type=int, action='store')
    parser.add_argument('--locators', default='all', type=str, action='store')
    parser.add_argument('--ignore-failures', action='store_true')

    args = parser.parse_args()

    def get_rows():
        """open csv and yield data for geocoding
        """
        with open(args.csv) as input_file:
            reader = csv.DictReader(input_file)
            for row in reader:
                yield (row[args.id], row[args.street], row[args.zone])

    execute(
        args.key,
        get_rows(),
        args.output,
        spatial_reference=args.wkid,
        locators=args.locators,
        add_message=print,
        ignore_failures=args.ignore_failures
    )
