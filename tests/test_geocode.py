
#!/usr/bin/env python
# * coding: utf8 *
'''
testgeocode.py
A module that contains tests for the geocoding module.
'''

import pytest
from pathlib import Path
from agrcgeocoding import geocode
import csv

def test_cleanse_street():
    assert geocode._cleanse_street('main & state') == 'main and state'

@pytest.mark.parametrize('street', ['  123 main street', '123      main street', '123 main street    ', '123 main$%# street'])
def test_clean_street_spacing(street):
    assert '123 main street' == geocode._cleanse_street(street)

@pytest.mark.parametrize('zone', [84124, '84124   ', '   84124', '84124-1234'])
def test_clean_zone(zone):
    assert '84124' == geocode._cleanse_zone(zone)

    assert 'salt lake city' == geocode._cleanse_zone('salt & lake city')

def test_get_local_finds_version_from_src(tmpdir):

    src = Path(tmpdir) / 'src'
    src.mkdir()
    version = Path(tmpdir) / 'tool-version.json'
    version.touch()

    with version.open(mode='w') as version_file:
        version_file.write('{"PRO_VERSION_NUMBER": "1.0.0"}')

    assert "1.0.0" == geocode.get_local_version(src / 'geocode.py')

def test_get_local_finds_version_from_sibling(tmpdir):
    parent = Path(tmpdir)
    version = parent / 'tool-version.json'
    version.touch()

    with version.open(mode='w') as version_file:
        version_file.write('{"PRO_VERSION_NUMBER": "1.0.0"}')

    assert "1.0.0" == geocode.get_local_version(parent / 'geocode.py')

def test_get_remote_version(requests_mock):
    response = {"PRO_VERSION_NUMBER": "1.0.0"}
    requests_mock.get('https://raw.githubusercontent.com/agrc/geocoding-toolbox/master/tool-version.json', json=response)

    assert "1.0.0" == geocode.get_remote_version()

def test_invalid_API_key(tmpdir):
    with pytest.raises(geocode.InvalidAPIKeyException):
        geocode.execute('AGRC-99999999999999', [(1, '123 s main', '84114')], tmpdir)


def test_continuous_fail(tmpdir, requests_mock):
    response = {
        'status': 404,
        'message': 'No address candidates found with a score of 70 or better.'
    }
    street = 'badaddress'
    zone = 'badzone'
    requests_mock.get(f'/api/v1/geocode/{street}/{zone}', json=response, status_code=404)

    def get_rows():
        count = 0
        while count < 30:
            yield (1, street, zone)
            count += 1

    with pytest.raises(geocode.ContinuousFailThresholdExceeded):
        geocode.execute('key', get_rows(), tmpdir)


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
    requests_mock.get(f'/api/v1/geocode/{street}/{zone}', json=response, status_code=200)

    def get_rows():
        count = 0
        while count < 30:
            yield (1, street, zone)
            count += 1

    table = Path(geocode.execute('key', get_rows(), tmpdir))
    with table.open() as table_file:
        reader = csv.DictReader(table_file)

        first_row = next(reader)

        assert str(response['result']['score']) == first_row['score']


def test_bad_url(tmpdir, requests_mock):
    bad_request_response = "not a json object because the api route was not matched since zone is empty"
    street = 'a'
    zone = 'fake'
    url = f'/api/v1/geocode/{street}/{zone}'
    requests_mock.get(url, text=bad_request_response, status_code=200)

    def get_rows():
        yield (1, street, zone)

    table = Path(geocode.execute('key', get_rows(), tmpdir))
    with table.open() as results:
        reader = csv.DictReader(results)

        row = next(reader)

        assert row['message'].startswith('Missing required parameters for URL')


def test_generic_exception(tmpdir, requests_mock):
    exception_message = 'this is an exception'
    def raise_exception(request, context):
        raise Exception(exception_message)

    street = 'street'
    zone = '84124'
    url = f'/api/v1/geocode/{street}/{zone}'
    requests_mock.get(url, json=raise_exception)

    def get_rows():
        yield (1, street, zone)

    table = Path(geocode.execute('key', get_rows(), tmpdir))
    with table.open() as results:
        reader = csv.DictReader(results)

        row = next(reader)
        assert exception_message == row['message']