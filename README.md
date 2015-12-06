# mgw - Moteino Gateway
Originaly MGW was designed to handle metrics reported by
Moteino boards (http://lowpowerlab.com/moteino/).

Now MGW can handle metrics reported by any kind of software/hardware.
Main MGW task is to get metric from external stuff, write it to DB and perform
various action.

How to feed MGW:
* via serial port
* via HTTP API
* via MQTT

MGW except input in format:
* serial - [board_id][sensor_type:sensor_data]
* HTTP API - {"data": {"board_id": "board_id", "sensor_type": "sensor_type", "sensor_data": "sensor_data"}, "topic": "mgw/metric"}
* MQTT - '{"board_id": "board_id", "sensor_type": "sensor_type", "sensor_data": "sensor_data"}'

MGW contains a few sub services:
* Gateway - main daemon, resposible for saving metrics and executing actions
* SRL - serial daemon, responsible for reading metrics from serial and sending to gateway
* DBAQ - db asyncrhonous query, responsible for query DB
* API - JSON API to talk to other services via MQTT/query DB
* Fence - script which handle 'armed' status (it use external geofancing api to make a decision)

## Hardware:
* Moteino boards (+FTDI adapter to upload board code)
* Rassberry PI (or any other python compatible computer)

## What we use:
* python
* mqtt/paho/mosquitto
* sqlalchemy/sqlite
* bottle
* highcharts/highstock (graphs)
* handlebars (templates)
* twitter bootstrap

## Architecture
![MGW Arch](https://rawgit.com/bkupidura/mgw/master/docs/img/MGW_MQTT.svg)

## Instalation:

```
$ git clone https://github.com/bkupidura/mgw.git
$ cd mgw
$ pip install .
$ apt-get install mosquitto mosquitto-clients
```

Copy and modify configuration files:

```
$ cp global.config.json.example global.config.json
$ cp boards.config.json.example boards.config.json
$ cp sensors.config.json.example sensors.config.json
```

Run gateway and create DB (if not created before)

```
moteino-gateway --dir /dir/with/gateway/config --create-db
moteino-gateway --dir /dir/with/gateway/config --sync-db-desc
moteino-gateway --dir /dir/with/gateway/config
```

Start other MGW services (use supervisor if needed):

```
$ moteino-api --dir /dir/with/mgw/api/config
$ moteino-fence --dir /dir/with/mgw/fence/config
$ moteino-srl --dir /dir/with/mgw/srl/config
$ moteino-dbaq --dir /dir/with/mgw/dbaq/config
```

## Supervisor
> [program:moteino-gateway]

> command=/usr/local/bin/moteino-gateway --dir /root/mgw/main

> [program:moteino-api]

> command=/usr/local/bin/moteino-api --dir /root/mgw/main/api

> [program:moteino-fence]

> command=/usr/local/bin/moteino-fence --dir /root/mgw/main/fence

> [program:moteino-srl]

> command=/usr/local/bin/moteino-srl --dir /root/mgw/main/srl

> [program:moteino-dbaq]

> command=/usr/local/bin/moteino-dbaq --dir /root/mgw/main/dbaq

### Running tests
MGW has a bunch of tests that helps in development. Tests are run by `pytest` with
`tox` as automation tool.

First, install `tox`:

```
$ pip install tox
```

Then run `tox` (it will prepare virtual environment and install all requirements):

```
$ tox
```

### sensors.config.json
List of metrics you want to handle.
Fields:
* 'action' - list of actions (python functions) to execute in case of failure, it supports nested failback
* 'check_if_armed' - check if status['armed'] should be true, supports exceptions
* 'action_interval' - how offen perform action
* 'threshold' - check if value reported by board should trigger action (we use python lambda here)
* 'fail_count' - how many failures should occur before action
* 'fail_interval' - time window for fail_count, older values will be removed
* 'message_template' - format message for notify actions
* 'priority' - priority for given metric, lowest metrics will be handled first

### status
This is internal dict used to synchronize service status.

Every service can update status with MQTT topic 'mgmt/status'

Default value:
status = {
  'mgw': 1,
  'msd': 1,
  'srl': 1,
  'armed': 1,
  'fence': 1
}

All services use status (ex. status['mgw']) to check if service is enabled.

status dict can be used also to synchronize any kind of data, by default
MGW stores 'armed' status inside.

All updates to 'mgmt/status' should be send with retain=True, or by dedicated
function mqttThread.public_status().

### actions
Every action is simple python function which will do 'smth'.
Gateway execute actions with multiprocessing.Process().

List of actions can be found inside action/ directory.

Every action should have defined TIMEOUT and return proper exit code (0 sucess, >0 error).
Exitcode 255 is used by gateway for action which didn't finish before TIMEOUT.

### MQTT
MQTT based services subscribes to different topics based on own config.

If in config['mqtt']['topic'] 'service_name' is defined service will subscribe
automatically to:
* SERVICE_NAME/# - '#' is wildcard for all levels of hierarchy

Ex.
{
  "mqtt": {
    "server": "localhost",
    "topic": {
      "mgw": "mgw"
    }
}

MGW (gateway) service will subscribe to topic 'mgw/#'.

If in config['mqtt']['topic'] 'mgmt' is defined, service will subscribe
automatically to:
* 'mgmt/status'

This topic is used by all MGW services to sync 'status'

Ex.
{
  "mqtt": {
    "server": "localhost",
    "topic": {
      "mgw": "mgw",
      "mgmt": "mgmt",
    }
}

MGW (gateway) service will subscribe to topic 'mgw/#' and 'mgmt/status'.

### Moteino-srl
SRL expect on serial input in format:

[BOARD_ID][METRIC_NAME:METRIC_VALUE]

[10][voltage:3.3]

[board-10][voltage:3.3]

Moteino code compatible with MGW can be found at https://github.com/bkupidura/moteino

All metrics gathered by SRL will be send over MQTT to topic conf['mgw']+'/metric'

SRL will handle all data send to topic conf['srl']+'/write'.
Data from MQTT will be send to serial without any processing.

This can be used to ping gateway:

> mosquitto_pub -t 'srl/write' -m '1:1'

### Moteino-gateway
Gateway handle MQTT traffic on topics:
* conf['mgw']+'/metric' - put metric to DB and perform action
* conf['mgw']+'/action' - perform action

Gateway to handle metrics/actions use Queue with priorities.
Every sensor_type can have different priority.
Lowest priority will be handled first.

If priority is missing from sensors.config.json, default value is 500.

Gateway expect on MQTT input in format:
{"board_id": "BOARD_ID", "sensor_type": "SENSOR_TYPE", "sensor_data": "SENSOR_DATA"}

Ex.
{"board_id": "10", "sensor_type": "voltage", "sensor_data": "1"}

### Moteino-dbaq
Used to perform asynchronous db queries.
By default there is only one query defined 'msd' - Missing Sensor Detector.

When MSD find any missing board it send data over MQTT to topic conf['mgw']+'/action'.

### Moteino-fence
Based on external geofence API it will handle 'armed' status.

Set armed to 1 when:
* Armed == 0
* All conf['geo_devices'] leaves geofence area

OR

* geofence API not available

Set armed to 0 when
* Armed == 1
* At least 1 conf['geo_devices'] enters geofence area

Geofence API should return data in format:
{"DEVICE_ID":{"action":"ACTION","time":TIME}, "DEVICE_ID2":{"action":"ACTION","time":TIME}}

Ex.
{"AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE":{"action":"exited","time":1447746219}}

Updates to geofence API can be handled on iphone/android by:
* IFTTT - https://ifttt.com
* Geofancy - https://github.com/Geofancy

In example dir you can find geofencig API.
Geofencing API should be running on public available server.
Because of this please use SSL+strong password/long device id.

IFTTT recipe "If You enter or exit an area, then make a web request".
* if - "You enter or exit an area"
* then - "Make a web request"
* action url - http://example.com/geofence.php
* action method - POST
* action content-type - application/x-www-form-urlencoded
* action body - trigger={{EnteredOrExited}}&device=AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE

IFTTT web req dosen't support basic-auth, so you should set $ignore_auth_for_devices to 1.

geofence.php curl examples:

Get status:
> curl example.com/geofence.php -u user:pass

> {"AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE":{"action":"entered","time":1448045574}}

Update status:
> curl example.com/geofence.php --data 'device=AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE&trigger=entered'

> curl example.com/geofence.php --data 'device=AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE&trigger=exited'

### Moteino-API
API delivers static dashboard and way to communicate over MQTT.

All customization can be done inside api/static/mappings.js.

API endpoints:
* GET /api/action/status - get current MQTT status
* POST /api/action/status - set status and publish it to MQTT
* POST /api/action/mqtt - send message to MQTT
* GET/POST /api/action/node - get latests metrics (from DB) for all boards
* GET/POST /api/action/node/<board_id> - get latests metrics (from DB) for given board
* GET/POST /api/action/graph/<graph_type> - get metrics of given type (used by graphs)

Send data to MQTT via API:
> curl localhost:8080/api/action/mqtt -H "Content-Type: application/json" --data '{"data":{"asd": 10, "bsd": 20}, "topic":"xyz"}'

Screens can be found at [Dashboard screens](https://github.com/bkupidura/mgw/tree/master/docs/img/dashboard)

### Aggregate metric
In example dir you can find python script which can be used to aggregate data in DB.

Avarage environment can generate 300k records every week (15 boards, each board report 4 metrics every 120s).

Aggregate_metric parameters:
* db-string - sqlalchemy db connection string
* start - seconds since epoch, we are interested in data >= start
* end - seconds since epoch, we are interested in data <= end
* policy - for what time period store data, 1 record per hour/day/week/month
* execute - do real data aggregation, by default (without this argument) aggregate_metric don't change database

Examples:

Store 1 sensor_type+board_id pair per hour for range [2 weeks ago - 1 week ago]

> python aggregate_metric.py --db-string 'sqlite:////etc/mgw/mgw.db' --start $(date +%s -d '2 weeks ago') --end $(date +%s -d '1 weeks ago') --execute --policy hour

Store 1 sensor_type+board_id pair per day for range [1 month ago - 2 weeks ago]

> python aggregate_metric.py --db-string 'sqlite:////etc/mgw/mgw.db' --start $(date +%s -d '1 months ago') --end $(date +%s -d '2 weeks ago') --execute --policy day

Store 1 sensor_type+board_id pair per week for range [6 months ago - 1 month ago]

> python aggregate_metric.py --db-string 'sqlite:////etc/mgw/mgw.db' --start $(date +%s -d '6 months ago') --end $(date +%s -d '1 months ago') --execute --policy week

Store 1 sensor_type+board_id pair per month for range [1 year ago - 6 months ago]

> python aggregate_metric.py --db-string 'sqlite:////etc/mgw/mgw.db' --start $(date +%s -d '1 years ago') --end $(date +%s -d '6 months ago') --execute --policy month
