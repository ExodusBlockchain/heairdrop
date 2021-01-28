import csv
import json
import sys
import time

from beem import Steem
from beem.account import Account
from beem.exceptions import AccountDoesNotExistsException
from beem.instance import set_shared_steem_instance

config = {}
user_list = []


def load_config():
    global config

    try:
        with open('config.json') as config_file:
            config = json.load(config_file)
    except:
        print("Unable to open configuration file")
        quit()


def load_users():
    global user_list

    if len(sys.argv) == 1:
        print("ERROR: Please specify airdrop file")
        quit()

    try:
        with open(sys.argv[1]) as user_file:
            reader = csv.reader(user_file)
            user_list = list(reader)
    except:
        print("Unable to open airdrop file")
        quit()


def build_payload(user, amount):
    data = {}
    data['contractName'] = 'tokens'
    data['contractAction'] = config['mode']

    data['contractPayload'] = {}
    data['contractPayload']['to'] = user
    data['contractPayload']['symbol'] = config['token'].upper()
    data['contractPayload']['quantity'] = f"{amount}"
    data['contractPayload']['memo'] = config['memo']

    return data


def send_tokens(stm, user, amount, retries=0):
    data = build_payload(user, amount)

    if not config['dry_run']:
        try:
            stm.custom_json('ssc-mainnet-hive', data,
                            required_auths=[config['account_name']])
        except:
            if retries < 3:
                send_tokens(stm, user, amount, retries=retries)
            else:
                print(f"Airdrop aborted at user: {user[0]}")
                quit()


def do_airdrop(stm):
    estimated_time = round((len(user_list) * config['delay']) / 60, 1)

    estimated_tokens = 0
    for user in user_list:
        estimated_tokens += float(user[1])

    print("Starting Airdrop")

    if config['dry_run']:
        print("DRY RUN! - Tokens will not be transfered.")
    print(f"Estimated Time: {estimated_time} minutes")
    print(f"Estimated Tokens Used: {estimated_tokens}")
    print("")

    for x in range(10, -1, -1):
        print(f"Starting in {x} seconds...", end='\r')
        time.sleep(1)
        sys.stdout.flush()

    for user in user_list:
        try:
            Account(user[0])
        except AccountDoesNotExistsException:
            print(f"Skipping user {user[0]} - Does not exist")
            continue

        print(f"Sending {user[1]} {config['token']} tokens to @{user[0]}")
        if not config['dry_run']:
            send_tokens(stm, user[0], user[1])

        time.sleep(config['delay'])


def main():
    load_config()
    load_users()

    stm = Steem(wif=config['wif'])
    set_shared_steem_instance(stm)

    do_airdrop(stm)


if __name__ == '__main__':
    main()
