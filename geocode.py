#!/usr/bin/env python
# * coding: utf8 *
"""
Tools for geocoding addresses using AGRC's geocoding web service.

Arguments:
    api_key
    input_table
    id_field
    address_field
    zone_field
    output_directory

Optional Arguments:
    spatial_reference
    locator
"""

import csv
import random
import re
import time
from pathlib import Path
from string import Template

import requests

import arcpy

DEFAULT_SPATIAL_REFERENCE = 26912
DEFAULT_LOCATOR_NAME = 'Address points and road centerlines (default)'
HEADER = ('primary_key', 'input_address', 'input_zone', 'score', 'x', 'y', 'message')
SPACES = re.compile(r'(\s\d/\d\s)|/|(\s#.*)|%|(\.\s)|\?')
RATE_LIMIT_SECONDS = (0.015, 0.03)
HOST = 'api.mapserv.utah.gov'
HEADER = ('primary_key', 'input_address', 'input_zone', 'score', 'x', 'y', 'message')
UNIQUE_RUN = time.strftime('%Y%m%d%H%M%S')


def cleanse_address(data):
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


def cleanse_zone(data):
    """cleans up zone garbage
    """
    zone = SPACES.sub(' ', str(data)).strip()

    if len(zone) > 0 and zone[0] == '8':
        zone = zone.strip()[:5]

    return zone


def format_time(seconds):
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
    input_table,
    id_field,
    address_field,
    zone_field,
    output_directory,
    spatial_reference=DEFAULT_SPATIAL_REFERENCE,
    locator=DEFAULT_LOCATOR_NAME,
    add_message=print,
    ignore_failure=False
):
    """the main geocoding function
    """
    url_template = Template(f'https://{HOST}/api/v1/geocode/$street/$zone')
    sequential_fails = 0
    success = 0
    fail = 0
    score = 0
    total = 0

    def log_status():
        try:
            failure_rate = 100 * fail / total
        except ZeroDivisionError:
            failure_rate = 100
        try:
            average_score = round(score / success)
        except ZeroDivisionError:
            average_score = 'n/a'
        add_message(f'Total requests: {total}')
        add_message(f'Failure rate: {failure_rate}%')
        add_message(f'Average score: {average_score}')
        add_message(f'Time taken: {format_time(time.perf_counter() - start)}')

    #: convert strings to path objects
    input_table = Path(input_table)
    output_directory = Path(output_directory)

    add_message(f'executing geocode job on {input_table.name}')
    output_table = output_directory / f'geocoding_results_{UNIQUE_RUN}.csv'

    fields = [id_field, address_field, zone_field]
    with arcpy.da.SearchCursor(str(input_table), fields) as cursor, open(output_table, 'w', newline='') as result_file:
        writer = csv.writer(result_file)

        writer.writerow(HEADER)

        start = time.perf_counter()
        for primary_key, street, zone in cursor:
            # if options['--testing'].lower() == 'true' and total > 50:
            #     return 'result.csv'

            if not ignore_failure and sequential_fails > 25:
                add_message('passed continuous fail threshold. failing entire job.')

                return None

            url = url_template.substitute({'street': street, 'zone': zone})

            time.sleep(random.uniform(RATE_LIMIT_SECONDS[0], RATE_LIMIT_SECONDS[1]))

            try:
                request = requests.get(
                    url, timeout=5, params={
                        'apiKey': api_key,
                        'spatialReference': spatial_reference
                    }
                )

                response = request.json()

                if request.status_code != 200:
                    fail += 1
                    total += 1
                    sequential_fails += 1

                    writer.writerow((primary_key, street, zone, 0, 0, 0, response['message']))

                    continue

                match = response['result']
                match_score = match['score']
                location = match['location']
                match_x = location['x']
                match_y = location['y']

                sequential_fails = 0
                success += 1
                total += 1
                score += match_score

                writer.writerow((primary_key, street, zone, match_score, match_x, match_y, None))
            except Exception as ex:
                fail += 1
                total += 1

                writer.writerow((primary_key, street, zone, 0, 0, 0, str(ex)[:500]))

            if total % 10000 == 0:
                log_status()
                start = time.perf_counter()

        add_message('Job Completed')
        log_status()

    return output_table


if __name__ == '__main__':
    #: I'm purposefully not using something like docopt here since I don't want to make
    #: Pro users install any 3rd party modules.
    from sys import argv

    #: temporary fix for https://github.com/PyCQA/pylint/issues/2820
    execute(*argv[1:])  # pylint: disable=no-value-for-parameter
