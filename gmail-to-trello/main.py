# -*- coding: utf-8 -*-

import datetime
import os
import re

import gmail
import settings
import trello

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_DIR = os.path.join(PROJECT_DIR, 'assets')

PATTERNS = {
    'request_date': r'Fecha:.*\n.*<TD.*?>(.*)</TD>',
    'client_name': r'Cliente.*\n.*<TD.*>(.*)</TD>',
    'client_phone': r'fono.*\n.*<TD.*>(.*)</TD>',
    'client_email': r'E-mail:.*\n.*mailto:(.*)\"',
    'client_city': r'Ciudad:.*\n.*<TD.*?>(.*)</TD>',
    'check_in': r'Fecha de entrada:.*\n.*<TD.*?>(.*)</TD>',
    'check_out': r'Fecha de salida:.*\n.*<TD.*?>(.*)</TD>',
    'number_people': r'mero de personas:.*\n.*<TD.*?>(.*)</TD>',
    'product': r'Producto.*\n.*<TD.*>(.*)</TD>',
    'inquiry': r'Consulta:.*\n.*<TD.*?>(.*)</TD>'
}


def main():
    trello.API_KEY = settings.TRELLO['api_key']
    trello.OAUTH_TOKEN = settings.TRELLO['oauth_token']

    json_keyfile_path = os.path.join(ASSETS_DIR,
                                     settings.GMAIL['json_keyfile_name'])
    gmail_svc = gmail.get_service(settings.GMAIL['account'], json_keyfile_path)

    q = 'from: {} '.format(settings.GMAIL['from_account'])
    q += 'to: {} '.format(settings.GMAIL['to_account'])
    q += 'subject: {} '.format(settings.GMAIL['subject'])
    q += '-label: ' + settings.GMAIL['trello_label']
    q += 'after: ' + datetime.date.today().strftime('%Y/%m/%d')
    msgs = gmail.get_messages_matching_query(gmail_svc, q)

    if msgs:
        mime_msgs = gmail.get_mime_messages(gmail_svc, msgs)
        trello_card_template = load_template('card_template.txt')

        cards_created = 0
        for key, value in mime_msgs.items():
            msg_content = value.get_payload(decode=True).decode('utf-8')
            info = extract_card_info(msg_content)
            card = get_formatted_card(trello_card_template, info)
            trello.create_card(card['name'], card['description'],
                               settings.TRELLO['list_id'],
                               settings.TRELLO['labels_ids'])
            gmail.set_message_label(gmail_svc, key, settings.GMAIL['trello_label'])
            print('card {} successfully created.'.format(card['name']))
            cards_created += 1

        cards_label = 'cards' if cards_created > 1 else 'card'
        print('{} {} has been created.'.format(cards_created, cards_label))
    else:
        print('There are no new messages')


def extract_card_info(message_content):
    card_info = {}
    for key, value in PATTERNS.items():
        match = re.search(value, message_content)
        value = match.group(1) if match else ''

        if key == 'inquiry':
            value = value.replace('<BR>', '\n')

        card_info[key] = value

    return card_info


def get_formatted_card(template, card_info):
    card = {}
    card['name'] = '{0} - {1}'.format(card_info['client_name'],
                                      card_info['product'])
    card['description'] = (template
        .replace('#PHONE#', card_info['client_phone'])
        .replace('#EMAIL#', card_info['client_email'])
        .replace('#NUMBER_PEOPLE#', card_info['number_people'])
        .replace('#CHECK_IN#', card_info['check_in'])
        .replace('#CHECK_OUT#', card_info['check_out'])
        .replace('#INQUIRY#', card_info['inquiry']))
    return card


def load_template(name):
    path =  os.path.join(ASSETS_DIR, name)
    with open(path, 'r') as f:
        return f.read()


if __name__ == '__main__':
    main()

