from moteino_sensors import validators


def test_dummy_that_sensor_validator_works():
  data = {
    'board_id': 'xyz',
    'sensor_type': 'some_sensor',
    'sensor_data': 'some_data',
  }
  validators.SensorDataSchema().deserialize(data)


def test_dummy_action_validator_works():
  data = {
    'action_interval': 1, #+
    'check_if_armed': { # +
      'default': 1,  # true/false
      'except': ['1', '2', '3'],
    },
    'action': [],
    'threshold': '123', #+
    'message_template': 'message template', #+
    'fail_count': 0, #+
    'fail_interval': 0, #+
    'priority': 10, #+
  }
  des = validators.ActionSchema().deserialize(data)
