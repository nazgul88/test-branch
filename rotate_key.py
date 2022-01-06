import boto3
import json
from typing import List, Tuple
from datetime import datetime, timezone

ROTATE_AFTER = 90


def iam():
    return boto3.client('iam')


def secretsmanager():
    return boto3.client('secretsmanager')


def get_secrets() -> List[dict]:
    manager = secretsmanager()
    secrets = manager.list_secrets(MaxResults=100)['SecretList']
    for item in secrets:
        secret = manager.get_secret_value(SecretId=item['Name'])
        secret_pair = json.loads(secret['SecretString'])
        item['access_key_id'] = secret_pair['access_key']
    return secrets


def create_secret(username: str, secret_key: str, access_key: str) -> dict:
    secretsmanager().update_secret(
        SecretId=username,
        Description=f"Rotated at {datetime.now().strftime('%Y-%m-%d')}",
        SecretString=f'{{"secret_key":"{secret_key}", "access_key":"{access_key}"}}')


def deactivate_access_key(username: str, access_key_id: str) -> None:
    iam().update_access_key(
        UserName=username,
        AccessKeyId=access_key_id,
        Status='Inactive')

# def delete_access_key():
#     pass

def create_access_key(username: str) -> Tuple[str, str]:
    key = iam().create_access_key(UserName=username)
    return key['AccessKey']['SecretAccessKey'], key['AccessKey']['AccessKeyId']

def get_users_access_keys(username: str):
    iam().list_access_keys(
        UserName=username,
        MaxItems=100)



def rotate_keys() -> None:
    for secret in get_secrets():
        last_changed_at = secret['LastChangedDate']
        username = secret['Name']
        if (datetime.now(timezone.utc) - last_changed_at).days >= ROTATE_AFTER:
            deactivate_access_key(username, secret['access_key_id']) # TODO: delete rigth away. https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.list_access_keys
            secret_key, access_key = create_access_key(username) #boto3 does not give last changed/inactivated
            create_secret(username, secret_key, access_key)


if __name__ == '__main__':
    rotate_keys()
