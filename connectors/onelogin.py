
import base64
import logging
import xmltodict

from requests import ConnectionError, HTTPError
from lib.connector import UserConnector

logger = logging.getLogger(__name__)  # pylint:disable=invalid-name


class Connector(UserConnector):
    MappingName = 'OneLogin'
    Settings = {
        'url':              {'order': 1, 'default': "https://app.onelogin.com/api/v2/users.xml"},
        'api_token':        {'order': 2, 'example': "YOUR OneLogin API TOKEN"},
        'default_role':     {'order': 3, 'example': 25, 'type': int},
        'default_position': {'order': 4, 'example': 'Employee'},
    }

    FieldMappings = {
        'USER':           {'source': "username"},
        'FIRST_NAME':     {'source': "firstname"},
        'LAST_NAME':      {'source': "lastname"},
        'EMAIL':          {'source': "email"},
        'PHONE':          {'source': "phone"},
        'PERMISSIONS_ID': {'setting': "default_role"},
        'POSITION':       {'setting': "default_position"},
    }

    def __init__(self, settings):
        super(Connector, self).__init__(settings)
        self.url_template = "{0}?from_id=%s".format(self.settings['url'])

    def get_headers(self):
        return {
            'Authorization': "Basic %s" % base64.standard_b64encode(self.settings['api_token']+":x")
        }

    def test_connection(self, options):
        try:
            url = self.url_template % 1
            response = self.get(url)
            response.raise_for_status()
            return {'result': True, 'error': ''}
        except ConnectionError as exp:
            return {'result': False, 'error': 'Connection Failed: %s' % (exp.message)}
        except HTTPError as exp:
            return {'result': False, 'error': 'Connection Failed: %s' % (exp.message)}

    def _load_records(self, options):
        if 'datafile' in options:
            with open(options['datafile'], 'r') as datafile:
                response = xmltodict.parse(datafile.read())
                users = response['users']
                if isinstance(users['user'], dict):
                    # If the OneLogin API returns one result users won't
                    # be in a list, there will just be one OrderedDict
                    users = [users['user']]
                else:
                    users = users['user']
                for user in users:
                    if isinstance(user['phone'], dict) and '@nil' in user['phone']:
                        user['phone'] = None
#                    print repr(user)
                    yield user
            return

        # The OneLogin API returns 100 results at a time. We'll start at 0 and
        # set the from_id parameter to the max_id for each subsequent request.
        max_id = 0
        more_records = True
        while more_records:
            url = self.url_template % max_id
            response = self.get(url)
            response.raise_for_status()

            response = xmltodict.parse(response.text)
            if 'users' not in response:
                # The 'users' key doesn't exist.
                # We've likely gotten all the users we're going to get
                users = None
                more_records = False
            else:
                # FixMe: the logic below needs to be tests against the real API.
                users = response['users']
                if isinstance(users['user'], dict):
                    # If the OneLogin API returns one result users won't
                    # be in a list, there will just be one OrderedDict
                    users = [users['user']]
                else:
                    users = users['user']

                for user in users:
                    if isinstance(user['phone'], dict) and '@nil' in user['phone']:
                        user['phone'] = None
                    max_id = user['id']
                    yield user

