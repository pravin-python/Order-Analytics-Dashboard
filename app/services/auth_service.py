"""Authentication service for OMS API."""

import logging
import requests
from app.utils.cache import cache

logger = logging.getLogger(__name__)

TOKEN_CACHE_KEY = 'oms_auth_token'


class AuthService:
    """Handles OAuth token retrieval and caching for the OMS API."""

    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password

    def get_token(self, force_refresh=False):
        """
        Retrieve a valid OAuth token. Uses cache unless force_refresh is True.

        Returns:
            str: The access token.

        Raises:
            ConnectionError: If the API is unreachable.
            ValueError: If credentials are invalid.
        """
        if not force_refresh:
            cached_token = cache.get(TOKEN_CACHE_KEY)
            if cached_token:
                logger.debug('Using cached auth token.')
                return cached_token

        logger.info(f'Requesting new auth token from {self.base_url}')

        try:
            response = requests.get(
                f'{self.base_url}/oauth/token',
                params={
                    'grant_type': 'password',
                    'client_id': 'my-trusted-client',
                    'username': self.username,
                    'password': self.password
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token', '')
                expires_in = data.get('expires_in', 3500)

                if token:
                    cache.set(TOKEN_CACHE_KEY, token, ttl=int(expires_in) - 60)
                    logger.info('Auth token obtained and cached successfully.')
                    return token
                else:
                    raise ValueError('Token response missing access_token field.')

            elif response.status_code == 401:
                raise ValueError('Invalid credentials. Please check username and password.')
            else:
                raise ConnectionError(
                    f'Authentication failed with status {response.status_code}: {response.text}'
                )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f'Cannot connect to API at {self.base_url}. Please check the URL.')
        except requests.exceptions.Timeout:
            raise ConnectionError('API request timed out. Please try again.')

    def test_connection(self):
        """
        Test the API connection by attempting to get a token.

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            token = self.get_token(force_refresh=True)
            return {
                'success': True,
                'token': token,
                'message': f'Connection successful. Token received ({len(token)} chars).'
            }
        except (ConnectionError, ValueError) as e:
            return {
                'success': False,
                'message': str(e)
            }
