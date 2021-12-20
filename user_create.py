import boto3
import json
from typing import List, Tuple
from datetime import datetime


def iam():
    return boto3.client('iam')


def get_users() -> List[dict]:
    return json.load(open('users.json'))


def create_user(username: str) -> dict:
    user = iam().create_user(UserName=username)
    return user


def create_access_key(username: str) -> Tuple[str, str]:
    key = iam().create_access_key(UserName=username)
    return key['AccessKey']['SecretAccessKey'], key['AccessKey']['AccessKeyId']


def add_user_to_group(username: str, group_name: str) -> dict:
    response = iam().add_user_to_group(
        UserName=username,
        GroupName=group_name
    )
    return response


def create_secret(username: str, secret_key: str, access_key, request_by: str) -> dict:
    client = boto3.client('secretsmanager')
    response = client.create_secret(
        Name=username,
        Description=f"Requested by {request_by} {datetime.now().strftime('%Y-%m-%d')}",
        SecretString=f'{{"secret_key":"{secret_key}", "access_key":"{access_key}"}}', )
    return response


def validate(user: dict) -> None:
    if 'username' not in user:
        raise Exception(f"Username is not provided. {user}")
    if 'user_group' not in user:
        raise Exception(f"User group is not provided. {user}")
    if 'requested_by' not in user:
        raise Exception(f"Requeste by is not provided. {user}")


def run() -> None:
    for user in get_users():
        validate(user)
        username = user['username']
        create_user(username)
        add_user_to_group(username, user['user_group'])
        secret_key, access_key = create_access_key(username)
        create_secret(username, secret_key, access_key, user['requested_by'])


if __name__ == '__main__':
    run()
