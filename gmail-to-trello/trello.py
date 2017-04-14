# -*- coding: utf-8 -*-

import requests


BASE_URL = 'https://api.trello.com/1/'
API_KEY = None
OAUTH_TOKEN = None


def create_card(name, description, list_id, labels_ids=None):
    endpoint = 'cards'
    query_string = {'name': name, 'desc': description, 'idList': list_id}

    if labels_ids:
        query_string['idLabels'] = ','.join(labels_ids)

    r = _post_api_response(endpoint, query_string)
    return r.json()


def _post_api_response(endpoint, query_string=None):
    url = BASE_URL + endpoint
    params = _get_params(query_string)
    r = requests.post(url, params)
    return r


def _get_params(query_string=None):
    params = {
        'key': API_KEY,
        'token': OAUTH_TOKEN
    }

    if query_string:
        params.update(query_string)

    return params
