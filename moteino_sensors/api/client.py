import logging

import requests


LOG = logging.getLogger(__name__)


class ApiClient(object):
  """Simple API client for JSON APIs"""

  def __init__(self, api_url):
    self.api_url = api_url

  def _get_url(self, path):
    if path.startswith('/'):
      path = path[1:]

    return '{api_url}/{path}'.format(
      api_url=self.api_url,
      path=path,
    )

  def request(self, path, method='GET', timeout=2, *args, **kwargs):
    url = self._get_url(path)
    try:
      resp = requests.request(method, url, timeout=timeout, *args, **kwargs)
      resp.raise_for_status()
      return resp.json()
    except (
      requests.HTTPError,
      requests.ConnectionError,
      requests.exceptions.Timeout
    ) as e:
      LOG.error('Fail to connect to url %s', e)
      return {}
    except (ValueError) as e:
      LOG.error('Failed to decode JSON response %s', e)
      return {}
