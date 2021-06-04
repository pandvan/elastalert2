import json

from unittest import mock
import pytest
from requests import RequestException

from elastalert.util import EAException
from elastalert.loaders import FileRulesLoader
from elastalert.alerters.thehive import HiveAlerter


def test_thehive_alerter():
    rule = {'alert': [],
            'alert_text': '',
            'alert_text_type': 'alert_text_only',
            'description': 'test',
            'hive_alert_config': {'customFields': [{'name': 'test',
                                                    'type': 'string',
                                                    'value': 'test.ip'}],
                                  'follow': True,
                                  'severity': 2,
                                  'source': 'elastalert',
                                  'status': 'New',
                                  'tags': ['test.port'],
                                  'tlp': 3,
                                  'type': 'external'},
            'hive_connection': {'hive_apikey': '',
                                'hive_host': 'https://localhost',
                                'hive_port': 9000},
            'hive_observable_data_mapping': [{'ip': 'test.ip'}],
            'name': 'test-thehive',
            'tags': ['a', 'b'],
            'type': 'any'}
    rules_loader = FileRulesLoader({})
    rules_loader.load_modules(rule)
    alert = HiveAlerter(rule)
    match = {
        "test": {
          "ip": "127.0.0.1",
          "port": 9876
        },
        "@timestamp": "2021-05-09T14:43:30",
    }
    with mock.patch('requests.post') as mock_post_request:
        alert.alert([match])

    expected_data = {
        "artifacts": [
            {
                "data": "127.0.0.1",
                "dataType": "ip",
                "message": None,
                "tags": [],
                "tlp": 2
            }
        ],
        "customFields": {
            "test": {
                "order": 0,
                "string": "127.0.0.1"
            }
        },
        "description": "\n\n",
        "follow": True,
        "severity": 2,
        "source": "elastalert",
        "status": "New",
        "tags": [
            "9876"
        ],
        "title": "test-thehive",
        "tlp": 3,
        "type": "external"
    }

    conn_config = rule['hive_connection']
    alert_url = f"{conn_config['hive_host']}:{conn_config['hive_port']}/api/alert"
    mock_post_request.assert_called_once_with(
        alert_url,
        data=mock.ANY,
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer '},
        verify=False,
        proxies={'http': '', 'https': ''}
    )

    actual_data = json.loads(mock_post_request.call_args_list[0][1]['data'])
    # The date and sourceRef are autogenerated, so we can't expect them to be a particular value
    del actual_data['date']
    del actual_data['sourceRef']

    assert expected_data == actual_data


def test_thehive_ea_exception():
    try:
        rule = {'alert': [],
                'alert_text': '',
                'alert_text_type': 'alert_text_only',
                'description': 'test',
                'hive_alert_config': {'customFields': [{'name': 'test',
                                                        'type': 'string',
                                                        'value': 'test.ip'}],
                                      'follow': True,
                                      'severity': 2,
                                      'source': 'elastalert',
                                      'status': 'New',
                                      'tags': ['test.ip'],
                                      'tlp': 3,
                                      'type': 'external'},
                'hive_connection': {'hive_apikey': '',
                                    'hive_host': 'https://localhost',
                                    'hive_port': 9000},
                'hive_observable_data_mapping': [{'ip': 'test.ip'}],
                'name': 'test-thehive',
                'tags': ['a', 'b'],
                'type': 'any'}
        rules_loader = FileRulesLoader({})
        rules_loader.load_modules(rule)
        alert = HiveAlerter(rule)
        match = {
            '@timestamp': '2021-01-01T00:00:00',
            'somefield': 'foobarbaz'
        }
        mock_run = mock.MagicMock(side_effect=RequestException)
        with mock.patch('requests.post', mock_run), pytest.raises(RequestException):
            alert.alert([match])
    except EAException:
        assert True


@pytest.mark.parametrize('hive_host, expect', [
    ('https://localhost', {'type': 'hivealerter', 'hive_host': 'https://localhost'}),
    ('', {'type': 'hivealerter', 'hive_host': ''})
])
def test_thehive_getinfo(hive_host, expect):
    rule = {'alert': [],
            'alert_text': '',
            'alert_text_type': 'alert_text_only',
            'description': 'test',
            'hive_alert_config': {'customFields': [{'name': 'test',
                                                    'type': 'string',
                                                    'value': 'test.ip'}],
                                  'follow': True,
                                  'severity': 2,
                                  'source': 'elastalert',
                                  'status': 'New',
                                  'tags': ['test.ip'],
                                  'tlp': 3,
                                  'type': 'external'},
            'hive_connection': {'hive_apikey': '',
                                'hive_host': hive_host,
                                'hive_port': 9000},
            'hive_observable_data_mapping': [{'ip': 'test.ip'}],
            'name': 'test-thehive',
            'tags': ['a', 'b'],
            'type': 'any'}
    rules_loader = FileRulesLoader({})
    rules_loader.load_modules(rule)
    alert = HiveAlerter(rule)

    expected_data = expect
    actual_data = alert.get_info()
    assert expected_data == actual_data
