import pytest

from moteino_sensors import utils


@pytest.fixture(scope='function')
def metric():
  """Provides a default metric data"""
  return {
    'board_id': '10',
    'sensor_type': 'voltage',
    'sensor_data': '123'
  }


not_empty_string_test_data = (
  (
    'test',
    True
  ),
  (
    '',
    False
  ),
  (
    10,
    False
  ),
  (
    [],
    False
  ),
  (
    [1, ],
    False
  ),
  (
    {},
    False
  ),
  (
    {'test': 10},
    False
  ),
  (
    None,
    False
  ),
  (
    True,
    False
  ),
  (
    False,
    False
  ),
)


@pytest.mark.parametrize('board_id, expected', not_empty_string_test_data)
def test_board_id(metric, board_id, expected):
  metric['board_id'] = board_id

  ada = utils.validate_sensor_data(metric)

  assert ada == expected


@pytest.mark.parametrize('sensor_type, expected', not_empty_string_test_data)
def test_sensor_type(metric, sensor_type, expected):
  metric['sensor_type'] = sensor_type

  ada = utils.validate_sensor_data(metric)

  assert ada == expected


@pytest.mark.parametrize('sensor_data, expected', not_empty_string_test_data)
def test_sensor_data(metric, sensor_data, expected):
  metric['sensor_data'] = sensor_data

  ada = utils.validate_sensor_data(metric)

  assert ada == expected
