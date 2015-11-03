import json

SENSORS = json.loads("""
{
  "voltage": {
    "action": [{"name": "send_sms", "failback": [{"name": "send_mail"}]}, {"name": "log"}],
    "check_if_armed": {"default": 0},
    "action_interval": 360,
    "threshold": "lambda x: float(x)<3.2",
    "fail_count": 2,
    "fail_interval": 300
  },
  "motion": {
    "action": [{"name": "send_sms", "failback": [{"name": "send_mail"}]}, {"name": "log"}],
    "check_if_armed": {"default": 1, "except": ["12"]},
    "action_interval": 360,
    "threshold": "lambda x: int(x)==1",
    "fail_count": 0,
    "fail_interval": 0
  }
}
""")

GLOBAL = json.loads("""
{
  "logging": {
    "level": 10
  },
  "serial": {
    "device": "/dev/ttys003",
    "speed": 115200,
    "timeout": 20
  },
  "msd": {
    "query": "SELECT <snap> FTIME('%s', 'now')-last_update>300",
    "action": [{"name": "send_sms", "failback": [{"name": "send_mail"}]}, {"name": "log"}],
    "action_interval": 86400,
    "loop_sleep": 60
  },
  "action_config": {
    "send_sms": {
      "endpoint": "https://bulksms.vsms.net/eapi/submission/send_sms/2/2.0",
      "user": "user",
      "password": "password",
      "recipient": ["+48000000000"],
      "enabled": 1
    },
    "send_mail": {
      "sender": "notify@example.com",
      "recipient": "root@example.com",
      "subject": "RPI notification",
      "host": "email-smtp.eu-west-1.amazonaws.com",
      "port": 587,
      "user": "user",
      "password": "password",
      "enabled": 1
    }
  },
  "loop_sleep": 10,
  "db_file": "/tmp/mgw.db",
  "mgmt_socket": "/tmp/mgw.sock",
  "gateway_ping_time": 120
}
""")

BOARDS = json.loads("""
{
  "1": "Gateway",
  "11": "Room 1",
  "10": "Room 2"
}

""")

####################
#
# ACTIONS
#
####################


# ???(prmtl): Pytaniem jest, jak bardzo sztywny ma byc interfejs akcji.
# Akcje powinny byc proste - czyli funkcje, a co bedzie w srodku to nas nie interesuje
# problemem jest tylko zaladowanie akcji - zgodnie ze sztuka, to entry-point i wszystko cacy
# ale to wszystko komplikuje, bo trzeba te entry pointy ladowac, szukac itp.
# Moim zdaniem akcje to powinny byc w pliku glownym (mgw.py) ewentualnie w 'actions.py'
# A zeby rozpoznac akcje i sie nie bawic w evale czy inne badziewia to zrobic dekorator,
# ktory nam to zarejestruje jako akcje (no bo zeby nagle sie nie okazalo, ze mamy w pliku 2 takie same
# akcje i jedna nadpisuje druga

# TODO(prmtl) jedynie bym w akcjach sprawdzal jakos czy dobre parametry funkcja lyka (jak pytest sprawdza fixtury?)

# Pytanie: czy chcemy miec jako akcje jakas funkcje lambda?
# w sumie mozna, bo jak nie znajdziemy akcji, to sprawdzamy, czy to lambda
# i wtedy straszny 'eval' leci


class _Action(object):

    def __init__(self, name, callback, config=None):
        self.name = name
        self.callback = callback

        config = config or _ActionConfig()
        if not isinstance(config, _ActionConfig):
            raise TypeError('Only _ActionConfig instance allowed as config')
        self.config = config

    @property
    def enabled(self):
        return self.config.enabled

    def load_config(self, raw_conf_dict):
        self.config = _ActionConfig(raw_conf_dict)

    def __repr__(self):
        return '<{}:{}>'.format(self.__class__.__name__, self.name)


class _ActionConfig(dict):

    @property
    def enabled(self):
        return self.get('enabled', True)


_ACTIONS = {
}


def is_action(func):
    action_name = func.__name__
    if action_name in _ACTIONS:
        raise Exception('Action {} already registered'.format(action_name))

    _ACTIONS[action_name] = _Action(name=action_name, callback=func)
    return func


@is_action
def send_sms(a, b, c):
    pass


@is_action
def send_mail(x, y, z):
    pass


@is_action
def log(x, y, z):
    pass


for action_name, action_config in GLOBAL['action_config'].iteritems():
    if action_name not in _ACTIONS:
        print('akcja {} nie istnieje'.format(action_name))
        continue

    action = _ACTIONS[action_name]
    action.load_config(action_config)


####################
#
# SENSORS
#
####################

class _SensorConfig(dict):
    pass


class _SensorAction(object):
    pass


class _Sensor(object):

    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.actions = []
        # mozna przesunac do osobnej funckji i wtedy _Sensor nie mialby zadnego
        # odwolania do "globalnych" zmiennych
        self.load_actions()

    def __repr__(self):
        return '<{}:{}>'.format(self.__class__.__name__, self.name)

    # failback moze miec failback, ktory moze miec failback itd., wiec lepiej nie parsowac nic dalej poza 'akcje'
    # minusem jes to, ze dopiero na etapie odpalnia kodu bedzie wiadomo, czy nie ma bledu w failbacku
    def load_actions(self):
        for raw_action in self.config['action']:
            action = _SensorAction()
            action.main_action = _ACTIONS.get(raw_action['name'])

            for raw_failback in raw_action.get('failback', []):
                action.failback_action = _ACTIONS.get(raw_failback['name'])

            self.actions.append(action)


_SENSORS = {}


for sensor_name, sensor_config in SENSORS.iteritems():
    config = _SensorConfig(sensor_config)
    _SENSORS[sensor_name] = _Sensor(sensor_name, config)


####################
#
# ActionStatus
#
####################

class _ActionStatus(dict):

    def can_be_run(self, reactor):
        return True


_ACTIONS_STATUS = _ActionStatus()


####################
#
# Reactor for data reads
#
####################

# na razie wyglda, ze jest niepotrzebny, bo nic ciekawego nie bedzie trzymal
class _Reactor(object):

    def __init__(self, sensor, data):
        self.sensor = sensor
        self.data = data

    def run(self):
        pass


class _IncomingData(dict):
    pass


INCOMING = _IncomingData({"board_id": 0, "sensor_type": "voltage", "sensor_data": "3.1"})

sensor = _SENSORS.get(INCOMING['sensor_type'])

reactor = _Reactor(sensor, INCOMING)

if _ACTIONS_STATUS.can_be_run(reactor):
    reactor.run()
