#!/usr/bin/env python
# * coding: utf8 *
"""
Tools for geocoding addresses using AGRC's geocoding web service.

CLI usage: `python geocode.py --help`.
"""

import csv
import random
import re
import time
from pathlib import Path
from string import Template

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_SPATIAL_REFERENCE = 26912
DEFAULT_LOCATOR_NAME = 'all'
HEADER = ('primary_key', 'input_address', 'input_zone', 'score', 'x', 'y', 'message')
SPACES = re.compile(r'(\s\d/\d\s)|/|(\s#.*)|%|(\.\s)|\?')
RATE_LIMIT_SECONDS = (0.015, 0.03)
HOST = 'api.mapserv.utah.gov'
HEADER = ('primary_key', 'input_address', 'input_zone', 'score', 'x', 'y', 'message')
UNIQUE_RUN = time.strftime('%Y%m%d%H%M%S')
HEALTH_PROB_COUNT = 25


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


def _get_retry_session():
    """create a requests session that has a retry built into it
    """
    retries = 3
    backoff_factor = 0.3
    status_forcelist = (500, 502, 504)

    session = requests.Session()
    session.headers.update({'x-client': 'geocoding-toolbox'})
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    return session


def execute(
    api_key,
    rows,
    output_directory,
    spatial_reference=DEFAULT_SPATIAL_REFERENCE,
    locators=DEFAULT_LOCATOR_NAME,
    add_message=print,
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
    url_template = Template(f'https://{HOST}/api/v1/geocode/$street/$zone')
    sequential_fails = 0
    success = 0
    fail = 0
    score = 0
    total = 0

    add_message(f'api_key: {api_key}')
    add_message(f'output_directory: {output_directory}')
    add_message(f'spatial_reference: {spatial_reference}')
    add_message(f'locators: {locators}')
    add_message(f'ignore_failures: {ignore_failures}')

    def log_status():
        try:
            failure_rate = round(100 * fail / total)
        except ZeroDivisionError:
            failure_rate = 100
        try:
            average_score = round(score / success)
        except ZeroDivisionError:
            average_score = 'n/a'

        add_message(f'Total requests: {total}')
        add_message(f'Failure rate: {failure_rate}%')
        add_message(f'Average score: {average_score}')
        add_message(f'Time taken: {_format_time(time.perf_counter() - start)}')

    #: convert strings to path objects
    output_directory = Path(output_directory)

    output_table = output_directory / f'geocoding_results_{UNIQUE_RUN}.csv'

    with open(output_table, 'w+', newline='') as result_file:
        writer = csv.writer(result_file)

        writer.writerow(HEADER)

        start = time.perf_counter()

        session = _get_retry_session()
        for primary_key, street, zone in rows:
            if not ignore_failures and total == HEALTH_PROB_COUNT and sequential_fails == HEALTH_PROB_COUNT:
                add_message('passed continuous fail threshold. failing entire job.')

                return None

            url = url_template.substitute({'street': _cleanse_street(street), 'zone': _cleanse_zone(zone)})

            time.sleep(random.uniform(RATE_LIMIT_SECONDS[0], RATE_LIMIT_SECONDS[1]))

            try:
                request = session.get(
                    url,
                    timeout=5,
                    params={
                        'apiKey': api_key,
                        'spatialReference': spatial_reference,
                        'locators': locators
                    }
                )

                response = request.json()

                if request.status_code == 400:
                    #: fail fast with api key auth
                    raise InvalidAPIKeyException(total, primary_key, response['message'])
                elif request.status_code != 200:
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
            except InvalidAPIKeyException as ex:
                raise ex
            except Exception as ex:
                fail += 1
                total += 1

                add_message(f'Failure on row: {primary_key} with {street}, {zone}')
                writer.writerow((primary_key, street, zone, 0, 0, 0, str(ex)[:500]))

            if total % 10000 == 0:
                log_status()
                start = time.perf_counter()

        add_message('Job Completed')
        log_status()

    return output_table


class InvalidAPIKeyException(Exception):
    """Custom exception for invalid API key returned from api
    """

    def __init__(self, total, primary_key, message):
        self.total = total
        self.primary_key = primary_key
        self.message = f'\n\nError returned for primary_key: {primary_key}\n' \
            f'API response message:{message}\nTotal rows processed: {total}'
        super().__init__(self.message)


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
