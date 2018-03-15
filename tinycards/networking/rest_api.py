import os

import requests

from . import json_converter
from .form_utils import generate_form_boundary,to_multipart_form


API_URL = 'https://tinycards.duolingo.com/api/1/'

DEFAULT_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://tinycards.duolingo.com/',
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4)' +
                   ' AppleWebKit/537.36 (KHTML, like Gecko)' +
                   ' Chrome/58.0.3029.94 Safari/537.36')
}


class RestApi(object):
    """Repository-like facade for the Tinycards API.

    Abstracts away all queries to the original Tinycards API and handles all
    JSON (un-)marshalling.
    """

    def __init__(self):
        """Initialize a new instance of the RestApi class."""
        self.session = requests.session()

    def login(self,
              identifier=None,
              password=None):
        """Log in an user with its Tinycards or Duolingo credentials.

        Args:
            identifier (str): The Tinycards identifier to use for logging in.
                For example, a user's email address.
                Will be taken from ENV if not specified:
                .. envvar:: TINYCARDS_IDENTIFIER
            password (str): The user's password to login to Tinycards.
                Will be taken from ENV if not specified.
                .. envvar:: TINYCARDS_PASSWORD
        """
        # Take credentials from ENV if not specified.
        identifier = identifier or os.environ.get('TINYCARDS_IDENTIFIER')
        password = password or os.environ.get('TINYCARDS_PASSWORD')

        request_payload = {
            'identifier': identifier,
            'password': password
        }
        r = self.session.post(url=API_URL + 'login',
                              json=request_payload)
        json_response = r.json()

        user_id = json_response['id']
        print("Logged in as '%s' (%s)"
              % (json_response['fullname'], json_response['email']))

        return user_id

    # --- Read user info.

    def get_user_info(self, user_id):
        """Get info data about the given user."""
        request_url = API_URL + 'users/' + str(user_id)
        r = self.session.get(url=request_url)

        if r.status_code != 200:
            raise ValueError(r.text)

        json_response = r.json()
        user_info = json_converter.json_to_user(json_response)

        return user_info

    # --- Get trends.

    def get_trends(self, types=None, limit=10, page=0, from_language='en'):
        """Get Tinycards trends for the current user.

        Args:
            types (list): What entity to search for. Can be DECK, DECK_GROUP
                and/or USER.
            limit (int): What number of results to should be returned.
            page (int): The page to return when returning more than limit
                results (zero-indexed).
            from_language: The language used for learning.

        Returns: A list of Trendable objects.

        """
        if not types:
            types = ['DECK', 'DECK_GROUP']

        request_url = API_URL + 'trendables'
        params = {'types': ','.join(types),
                  'limit': limit,
                  'page': page,
                  'fromLanguage': from_language}
        r = self.session.get(url=request_url, params=params)

        if r.status_code != 200:
            raise ValueError(r.text)

        json_response = r.json()
        json_trendables_list = json_response['trendables']
        trendables = [json_converter.json_to_trendable(trendable)
                      for trendable in json_trendables_list]

        return trendables

    # --- Subscriptions

    def subscribe(self, user_id):
        """Subscribe to the given user.

        Args:
            user_id: ID of the user to subscribe to.

        Returns: If successful, returns the ID of the user subscribed to.

        """
        request_url = API_URL + 'users/' + str(user_id) + '/subscriptions'
        r = self.session.post(url=request_url)

        json_response = r.json()
        added_subscription = json_response['addedSubscription']

        return added_subscription

    def unsubscribe(self, user_id):
        """Unsubscribe the given user.

        Args:
            user_id: ID of the user to unsubscribe.

        Returns: If successful, returns the ID of the unsubscribed user.

        """
        request_url = API_URL + 'users/' + str(user_id) + '/subscriptions'
        r = self.session.delete(url=request_url)

        json_response = r.json()
        removed_subscription = json_response['removedSubscription']

        return removed_subscription

    # --- Deck CRUD

    def get_decks(self, user_id):
        """Get all Decks for the currently logged in user.

        Returns:
            list: The list of retrieved decks.

        """
        request_url = API_URL + 'decks?userId=' + str(user_id)
        r = self.session.get(url=request_url)

        if r.status_code != 200:
            raise ValueError(r.text)

        json_response = r.json()
        decks = []
        for d in json_response['decks']:
            current_deck = json_converter.json_to_deck(d)
            decks.append(current_deck)

        return decks

    def get_deck(self, deck_id, user_id, include_cards=True):
        """Get the Deck with the given ID.

        Args:
            deck_id (str): The ID of the deck to retrieve.
            include_cards (bool): Only include the cards of the deck when set
                to True (as by default). Otherwise cards will be an empty list.

        Returns:
            Deck: The retrieved deck.

        """
        request_url = API_URL + 'decks/' + deck_id
        if include_cards:
            request_url += '?expand=true'
        r = self.session.get(url=request_url)
        json_response = r.json()

        deck = json_converter.json_to_deck(json_response)
        # Set additional properties.
        deck.id = deck_id
        deck.user_id = user_id

        return deck

    def create_deck(self, deck):
        """Create a new Deck for the currently logged in user.

        Args:
            deck (Deck): The Deck object to create.

        Returns:
            Deck: The created Deck object if creation was successful.

        """
        form_boundary = generate_form_boundary()

        # Clone headers to not modify the global variable.
        headers = dict(DEFAULT_HEADERS)
        # Explicitly set Content-Type to multipart/form-data.
        headers['Content-Type'] = ('multipart/form-data; boundary=%s'
                                   % form_boundary)

        request_payload = json_converter.deck_to_json(deck)
        request_payload = to_multipart_form(request_payload, form_boundary)
        r = self.session.post(url=API_URL + 'decks',
                              headers=headers,
                              data=request_payload)

        json_data = r.json()
        created_deck = json_converter.json_to_deck(json_data)

        return created_deck

    def update_deck(self, deck):
        """Update an existing deck.

        Args:
            deck (Deck): The Deck object to update.

        Returns:
            Deck: The updated Deck object if update was successful.

        """
        headers = DEFAULT_HEADERS
        request_payload = json_converter.deck_to_json(deck)

        r = self.session.patch(url=API_URL + 'decks/' + deck.id,
                               headers=headers,
                               json=request_payload)

        if not r.ok:
            raise Exception("Failure while sending updates to server")

        # The response from the PATCH request does not contain cards.
        # Therefore, we have to query the updated deck with an extra request.
        updated_deck = self.get_deck(deck.id, deck.user_id)

        return updated_deck

    def delete_deck(self, deck_id):
        """Delete an existing deck.

        Args:
            deck_id (str): The ID of the Deck to delete.

        Returns:
            Deck: The deleted Deck object if deletion was successful.

        """
        if type(deck_id) is not str:
            raise ValueError("'deck_id' parameter must be of type str")

        headers = DEFAULT_HEADERS

        r = self.session.delete(url=API_URL + 'decks/' + deck_id,
                                headers=headers)

        json_data = r.json()
        deleted_deck = json_converter.json_to_deck(json_data)

        return deleted_deck

    # --- Favorites CR(U)D

    def get_favorites(self, user_id):
        """Get all favorites for the given user.

        Args:
            user_id (int): ID of the user to get favorites for.

        Returns:
            list: The list of retrieved decks.

        """
        request_url = API_URL + 'users/%d/favorites' % user_id
        r = self.session.get(url=request_url)

        if r.status_code != 200:
            raise ValueError(r.text)

        json_response = r.json()
        decks = []
        try:
            for fav in json_response['favorites']:
                current_deck = json_converter.json_to_deck(fav['deck'])
                decks.append(current_deck)
        except KeyError as ke:
            raise Exception("Unexpected JSON format:\n%s" % ke)

        return decks
