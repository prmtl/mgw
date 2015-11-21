import json
import logging
import socket
import threading
import time

import paho.mqtt.client as paho

from moteino_sensors import utils

LOG = logging.getLogger(__name__)


class MqttThread(threading.Thread):

  def __init__(self):
    super(MqttThread, self).__init__()

  def _on_mgmt_status(self, client, userdata, msg):
    self.status = utils.load_json(msg.payload)
    if self.name in self.status and hasattr(self, 'enabled'):
      if isinstance(self.enabled, threading._Event):
        self.enabled.set() if self.status[self.name] else self.enabled.clear()
      else:
        self.enabled = self.status[self.name]

  def _on_connect(self, client, userdata, flags, rc):
    if 'subscribe_to' in userdata:
      self.subscribe(userdata['subscribe_to'])

  def _on_disconnect(self, client, userdata, rc):
    if rc != 0:
      LOG.error('Connection to broker failed, reconnecting')
      while True:
        try:
          self.mqtt.reconnect()
        except(socket.error) as e:
          time.sleep(5)
        else:
          break

  def _connect(self, server='localhost', port=1883, keepalive=60, retries=-1, use_default_handlers=True):
    while retries != 0:
      try:
        self.mqtt.connect(server, port, keepalive)
      except (socket.error) as e:
        retries -= 1
        LOG.error('Fail to connect to broker, waiting..')
        time.sleep(5)
      else:
        if use_default_handlers:
          self.mqtt.on_connect = self._on_connect
          self.mqtt.on_disconnect = self._on_disconnect
        break

  def start_mqtt(self):
    if not hasattr(self, 'status'):
      self.status = {}

    topic = self.mqtt_config.get('topic', {})
    subscribe_to = []

    if self.name in topic:
      subscribe_to.append(topic[self.name]+'/#')
    if 'mgmt' in topic:
      subscribe_to.append(topic['mgmt']+'/status')

    userdata = {
      'subscribe_to': subscribe_to
    }
    self.mqtt = paho.Client(userdata=userdata)
    self._connect(self.mqtt_config['server'])

    if 'mgmt' in topic:
      self.mqtt.message_callback_add(topic['mgmt']+'/status', self._on_mgmt_status)

  def loop_start(self):
    self.mqtt.loop_start()
    self.mqtt._thread.setName(self.name+'-mqtt')

  def publish_status(self, status=None):
    topic = self.mqtt_config.get('topic', {})
    if hasattr(self, 'status') and 'mgmt' in topic:
      if status:
        self.status.update(status)
      self.publish(topic['mgmt']+'/status', self.status, retain=True)

  def subscribe(self, topic):
    if isinstance(topic, str) or isinstance(topic, unicode):
      self.mqtt.subscribe(str(topic))
    elif isinstance(topic, list):
      for t in topic:
        self.mqtt.subscribe(str(t))
    else:
      LOG.warning("Fail to subscribe to topic '%s', unknown type", topic)

  def publish(self, topic, payload, retain=False):
    payload = json.dumps(payload)
    if self.mqtt._host:
      if topic and payload:
        self.mqtt.publish(topic, payload=payload, retain=retain)
      else:
        LOG.warning('Topic or payload is empty')
    else:
      LOG.warning('Client is not connected to broker')