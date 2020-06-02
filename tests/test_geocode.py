
#!/usr/bin/env python
# * coding: utf8 *
"""
testgeocode.py
A module that contains tests for the geocoding module.
"""

#pylint: disable=missing-function-docstring
#pylint: disable=protected-access

import csv
import os

import pytest

from agrcgeocoding import geocode


def test_cleanse_street():
    assert geocode._cleanse_street('main & state') == 'main and state'

@pytest.mark.parametrize(
    'street', ['  123 main street', '123      main street', '123 main street    ', '123 main$%# street']
)
def test_clean_street_spacing(street):
    assert geocode._cleanse_street(street) == '123 main street'

@pytest.mark.parametrize('zone', [84124, '84124   ', '   84124', '84124-1234'])
def test_clean_zone(zone):
    assert geocode._cleanse_zone(zone) == '84124'

    assert geocode._cleanse_zone('salt & lake city') == 'salt lake city'

def test_get_local_finds_version_from_src(tmpdir):
    src = str(tmpdir / 'src')
    os.makedirs(src)

    version = str(tmpdir / 'tool-version.json')

    with open(version, mode='w+') as version_file:
        version_file.write('{"VERSION_NUMBER": "1.0.0"}')

    current_file = os.path.join(src, 'geocode.py')

    assert geocode.get_local_version(current_file) == '1.0.0'

def test_get_local_finds_version_from_sibling(tmpdir):
    version = str(tmpdir / 'tool-version.json')

    with open(version, mode='w+') as version_file:
        version_file.write('{"VERSION_NUMBER": "1.0.0"}')

    current_file = str(tmpdir / 'geocode.py')

    assert geocode.get_local_version(current_file) == '1.0.0'

def test_get_local_returns_null_3_levels_up(tmpdir):
    version = str(tmpdir / 'tool-version.json')

    with open(version, mode='w+') as version_file:
        version_file.write('{"VERSION_NUMBER": "1.0.0"}')

    src = str(tmpdir / 'module-folder' / 'another-folder' / 'more-folders' / 'too-many-folders' / 'geocode.py')
    os.makedirs(src)

    assert geocode.get_local_version(src) is None

def test_get_remote_version(requests_mock):
    response = {'VERSION_NUMBER': '1.0.0'}
    requests_mock.get('https://raw.githubusercontent.com/agrc/geocoding-toolbox/py-2/tool-version.json', json=response)

    assert geocode.get_remote_version() == '1.0.0'

def test_invalid_API_key(tmpdir):
    with pytest.raises(geocode.InvalidAPIKeyException):
        geocode.execute('AGRC-99999999999999', [(1, '123 s main', '84114')], str(tmpdir))


def test_continuous_fail(tmpdir, requests_mock):
    response = {
        'status': 404,
        'message': 'No address candidates found with a score of 70 or better.'
    }
    street = 'badaddress'
    zone = 'badzone'
    requests_mock.get('/api/v1/geocode/{}/{}'.format(street, zone), json=response, status_code=404)

    def get_rows():
        count = 0
        while count < 30:
            yield (1, street, zone)
            count += 1

    with pytest.raises(geocode.ContinuousFailThresholdExceeded):
        geocode.execute('key', get_rows(), str(tmpdir))


def test_successful_run(tmpdir, requests_mock):
    response = {
        'status': 200,
        'result': {
            'location': {
                'x': 425046.4843,
                'y': 4514424.973
            },
            'score': 100,
            'locator': 'USPS Delivery Points',
            'matchAddress': 'UTAH STATE CAPITOL',
            'inputAddress': '123 S MAIN',
            'standardizedAddress': '123 south main',
            'addressGrid': 'SALT LAKE CITY'
        }
    }
    street = 'dummystreet'
    zone = 'dummyzone'
    requests_mock.get('/api/v1/geocode/{}/{}'.format(street, zone), json=response, status_code=200)

    def get_rows():
        count = 0
        while count < 30:
            yield (1, street, zone)
            count += 1

    table = geocode.execute('key', get_rows(), str(tmpdir))
    with open(table) as table_file:
        reader = csv.DictReader(table_file)

        first_row = next(reader)

        assert str(response['result']['score']) == first_row['score']


def test_bad_url(tmpdir, requests_mock):
    bad_request_response = 'not a json object because the api route was not matched since zone is empty'
    street = 'a'
    zone = 'fake'
    url = '/api/v1/geocode/{}/{}'.format(street, zone)
    requests_mock.get(url, text=bad_request_response, status_code=200)

    def get_rows():
        yield (1, street, zone)

    table = geocode.execute('key', get_rows(), str(tmpdir))
    with open(table) as results:
        reader = csv.DictReader(results)

        row = next(reader)

        assert row['message'].startswith('Missing required parameters for URL')


def test_generic_exception(tmpdir, requests_mock):
    exception_message = 'this is an exception'

    def raise_exception(request, context):
        raise Exception(exception_message)

    street = 'street'
    zone = '84124'
    url = '/api/v1/geocode/{}/{}'.format(street, zone)
    requests_mock.get(url, json=raise_exception)

    def get_rows():
        yield (1, street, zone)

    table = geocode.execute('key', get_rows(), str(tmpdir))
    with open(table) as results:
        reader = csv.DictReader(results)

        row = next(reader)
        assert exception_message == row['message']
