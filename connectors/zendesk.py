
import base64
import logging

from requests import ConnectionError, HTTPError
from lib.connector import UserConnector

logger = logging.getLogger(__name__)  # pylint:disable=invalid-name

class Connector(UserConnector):
    MappingName = 'Zendesk'
    Settings = {
        'system_name':      {'order': 1, 'example': "oomnitza"},
        'api_token':        {'order': 2, 'example': "assTrGvyJ0hoXZRTIOCIJniwflkfDm5PHo0wCfyj"},
        'username':         {'order': 3, 'example': "person.name@example.com"},
        'default_role':     {'order': 4, 'example': 12, 'type': int},
        'default_position': {'order': 5, 'example': 'Employee'},
    }

    FieldMappings = {
        'USER':           {'source': "email"},
        'FIRST_NAME':     {'source': "name", 'converter': "first_from_full"},
        'LAST_NAME':      {'source': "name", 'converter': "last_from_full"},
        'EMAIL':          {'source': "email"},
        'PHONE':          {'source': "phone"},
        'PERMISSIONS_ID': {'setting': "default_role"},
        'POSITION':       {'setting': "default_position"},
    }

    def __init__(self, settings):
        super(Connector, self).__init__(settings)
        self.url_template = "https://%s.zendesk.com/api/{0}" % self.settings['system_name']

    def get_headers(self):
        auth_string = "{0}/token:{1}".format(self.settings['username'], self.settings['api_token'])
        return {
            'Accept': 'application/json',
            'Authorization': "Basic {0}".format(base64.b64encode(auth_string)),
        }

    def test_connection(self, options):
        try:
            url = self.url_template.format("v2/users.json") + "?per_page=1&page=1"
            response = self.get(url)
            response.raise_for_status()
            return {'result': True, 'error': ''}
        except HTTPError as exp:
            return {'result': False, 'error': 'Connection Failed: %s' % (exp.message)}


    def _load_records(self, options):
        url = self.url_template.format("v2/users.json")
        while url:
            response = self.get(url)
            response.raise_for_status()

            response = response.json()
            if 'users' not in response:
                # The 'users' key doesn't exist.
                # We've likely gotten all the users we're going to get
                users = None
                url = None
            else:
                for user in response['users']:
                    yield user
                url = response['next_page']

