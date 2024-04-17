import json
from dataclasses import dataclass
from datetime import UTC, datetime

import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import Session


@dataclass
class User:
    active: bool
    user_id: str
    user_name: str
    display_name: str
    email: str
    email_verification_status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_data(cls, data: dict) -> "User":
        primary_email = [
            email
            for email in data["UserAttributes"]["emails"]["ComplexListValue"]
            if email["primary"]["BooleanValue"] is True
        ][0]
        return cls(
            active=data["Active"],
            user_id=data["UserId"],
            user_name=data["UserName"],
            display_name=data["UserAttributes"]["displayName"]["StringValue"],
            email=primary_email["value"]["StringValue"],
            email_verification_status=primary_email["verificationStatus"][
                "StringValue"
            ],
            created_at=datetime.fromtimestamp(data["Meta"]["CreatedAt"], UTC),
            updated_at=datetime.fromtimestamp(data["Meta"]["UpdatedAt"], UTC),
        )


def _fetch_users(
    sigv4_auth: SigV4Auth,
    identity_store_id: str,
    region: str,
    next_token: str,
) -> dict:
    endpoint = f"https://up.sso.{region}.amazonaws.com/identitystore/"
    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSIdentityStoreService.SearchUsers",
    }
    data = json.dumps(
        {
            "IdentityStoreId": identity_store_id,
            "MaxResults": 100,
            "NextToken": next_token,
        }
    )
    request = AWSRequest(
        method="POST",
        url=endpoint,
        data=data,
        headers=headers,
    )
    sigv4_auth.add_auth(request)
    prepped = request.prepare()

    response = requests.post(
        prepped.url,
        headers=prepped.headers,
        data=data,
    )
    response_data = response.json()

    return response_data


def fetch_all_users(identity_store_id: str, region: str) -> list[User]:
    sigv4_auth = SigV4Auth(
        credentials=Session().get_credentials(),
        service_name="identitystore",
        region_name=region,
    )

    users: list[User] = []
    next_token = None
    while response := _fetch_users(
        sigv4_auth=sigv4_auth,
        identity_store_id=identity_store_id,
        region=region,
        next_token=next_token,
    ):
        users += [User.from_data(user) for user in response["Users"]]
        if not (next_token := response.get("NextToken")):
            break

    return users
