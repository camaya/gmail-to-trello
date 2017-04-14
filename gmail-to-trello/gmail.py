# -*- coding: utf-8 -*-

import base64
from email import message_from_string
from httplib2 import Http
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials


SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.modify'
]


def get_messages_matching_query(service, q=None):
    response = service.users().messages().list(userId='me', q=q).execute()

    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId='me', q=query,
                                                   pageToken=page_token).execute()
        messages.extend(response['messages'])

    return messages


def get_mime_messages(service, gmail_msgs):
    mime_msgs = {}

    for m in gmail_msgs:
        gmail_id = m['id']
        message = service.users().messages().get(userId='me', id=gmail_id,
                                                 format='raw').execute()
        msg_bytes = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        msg_str = str(msg_bytes, 'utf-8')
        mime_msg = message_from_string(msg_str)
        mime_msgs[gmail_id] = mime_msg

    return mime_msgs


def set_message_label(service, msg_id, label_name):
    labels = get_labels(service)
    label = next((l for l in labels if l['name'].upper() == label_name.upper()), None)

    if label is None:
        label_object = make_label_object(label_name)
        label = create_label(service, label_object)

    msg_labels = {'removeLabelIds': [], 'addLabelIds': [label['id']]}
    service.users().messages().modify(userId='me', id=msg_id,
                                      body=msg_labels).execute()


def get_labels(service):
    response = service.users().labels().list(userId='me').execute()
    return response['labels']


def create_label(service, label_object):
    label = service.users().labels().create(userId='me',
                                            body=label_object).execute()
    return label


def make_label_object(label_name, mlv='show', llv='labelShow'):
    label = {
        'name': label_name,
        'messageListVisibility': mlv,
        'labelListVisibility': llv
    }
    return label


def get_service(account, json_keyfile_path):
    credentials = _get_delegated_credentials(account, json_keyfile_path)
    http_auth = credentials.authorize(Http())
    service = discovery.build('gmail', 'v1', http=http_auth)
    return service


def _get_credentials(json_keyfile_path):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        json_keyfile_path, scopes=SCOPES)
    return credentials


def _get_delegated_credentials(email_to_impersonate, json_keyfile_path):
    credentials = _get_credentials(json_keyfile_path)
    delegated_credentials = credentials.create_delegated(email_to_impersonate)
    return delegated_credentials

