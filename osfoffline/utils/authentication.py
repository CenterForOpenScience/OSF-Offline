import asyncio
import datetime
import json
import logging

import aiohttp
import furl
from sqlalchemy.exc import SQLAlchemyError

from osfoffline import settings
from osfoffline.database_manager.db import session
from osfoffline.database_manager.models import User
from osfoffline.database_manager.utils import save
from osfoffline.polling_osf_manager.remote_objects import RemoteUser
from osfoffline.exceptions import AuthError

class AuthClient(object):
    """Manages authorization flow """

    @asyncio.coroutine
    def _authenticate(self, username, password):
        """ Tries to use standard auth to authenticate and create a personal access token through APIv2

            :return: personal_access_token or raise AuthError
        """
        token_url = furl.furl(settings.API_BASE)
        token_url.path.add('/v2/tokens/')
        token_request_body = {
            'data': {
                'type': 'tokens',
                'attributes': {
                    'name': 'OSF-Offline - {}'.format(datetime.date.today()),
                    'scopes': settings.APPLICATION_SCOPES
                }
            }
        }
        headers = {'content-type': 'application/json'}

        try:
            resp = yield from aiohttp.request(method='POST', url=token_url.url, headers=headers, data=json.dumps(token_request_body), auth=(username, password))
        except (aiohttp.errors.ClientTimeoutError, aiohttp.errors.ClientConnectionError, aiohttp.errors.TimeoutError):
            # No internet connection
            raise AuthError('Unable to connect to server. Check your internet connection or try again later.')
        except Exception as e:
            # Invalid credentials probably, but it's difficult to tell
            # Regadless, will be prompted later with dialogbox later
            # TODO: narrow down possible exceptions here
            raise AuthError('Login failed')
        else:
            if resp.status == 401 or resp.status == 403:
                raise AuthError('Invalid credentials')
            elif not resp.status == 201:
                raise AuthError('Invalid authorization response')
            else:
                json_resp = yield from resp.json()
                return json_resp['data']['attributes']['token_id']

    @asyncio.coroutine
    def _create_user(self, username, password):
        """ Tries to authenticate and create user.

        :return: user or raise AuthError
        """
        logging.debug('User doesnt exist. Attempting to authenticate, then creating user.')
        personal_access_token = yield from self._authenticate(username, password)
        user = User(
            full_name='',
            osf_id='',
            osf_login=username,
            osf_local_folder_path='',
            oauth_token=personal_access_token,
        )
        return (yield from self.populate_user_data(user))

    @asyncio.coroutine
    def populate_user_data(self, user):
        """ Takes a user object, makes a request to ensure auth is working,
            and fills in any missing user data.

            :return: user or raise AuthError
        """
        me = furl.furl(settings.API_BASE)
        me.path.add('/v2/users/me/')
        header = {'Authorization': 'Bearer {}'.format(user.oauth_token)}
        try:
            resp = yield from aiohttp.request(method='GET', url=me.url, headers=header)
        except (aiohttp.errors.ClientTimeoutError, aiohttp.errors.ClientConnectionError, aiohttp.errors.TimeoutError):
            # No internet connection
            raise AuthError('Unable to connect to server. Check your internet connection or try again later')
        except Exception as e:
            raise AuthError('Login failed. Please log in again.')
        else:
            if resp.status != 200:
                raise AuthError('Invalid credentials. Please log in again.')
            json_resp = yield from resp.json()
            remote_user = RemoteUser(json_resp['data'])
            user.full_name = remote_user.name
            user.osf_id = remote_user.id

            return user

    @asyncio.coroutine
    def log_in(self, user=None, username=None, password=None):
        """ Takes standard auth credentials, returns authenticated user or raises AuthError.
        """
        if not username or not password:
            raise AuthError('Username and password required for login.')

        if user:
            user.oauth_token = yield from self._authenticate(username, password)
        else:
            user = yield from self._create_user(username, password)

        user.logged_in = True
        try:
            save(session, user)
        except SQLAlchemyError as e:
            raise AuthError('Unable to save user data. Please try again later')
        else:
            return user
