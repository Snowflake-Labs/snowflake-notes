import boto3
import os
import json
import base64
from botocore.exceptions import ClientError
import os


class Credentials:
    def __init__(self, username, password, account, region):
        self._username = username
        self._password = password
        self._account = account
        self._region = region

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def account(self):
        return self._account

    @property
    def region(self):
        return self._region


def get_secret():
    secret_name = os.environ["SECRET_ARN"]
    region_name = os.environ["REGION"]
    session = boto3.session.Session()

    client = session.client(service_name="secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    except ClientError as e:
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            raise e
        elif e.response["Error"]["Code"] == "InternalServiceErrorException":
            raise e
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            raise e
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            raise e
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise e
    else:
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )

        return json.loads(secret)


creds_json = get_secret()

creds = Credentials(
    creds_json["uname"],
    creds_json["pass"],
    creds_json["account"],
    os.environ["REGION"],
)
