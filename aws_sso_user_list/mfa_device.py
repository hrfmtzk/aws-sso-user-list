import json
from dataclasses import dataclass
from datetime import UTC, datetime

import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import Session


@dataclass
class MfaDevice:
    device_id: str
    device_name: str
    display_name: str | None
    mfa_type: str
    registered_date: datetime

    @classmethod
    def from_data(cls, data: dict) -> "MfaDevice":
        return cls(
            device_id=data["deviceId"],
            device_name=data["deviceName"],
            display_name=data.get("displayName"),
            mfa_type=data["mfaType"],
            registered_date=datetime.fromtimestamp(
                data["registeredDate"],
                UTC,
            ),
        )


@dataclass
class UserMfa:
    user_id: str
    mfa_devices: list[MfaDevice]

    @classmethod
    def from_data(cls, data: dict) -> "UserMfa":
        return cls(
            user_id=data["user"]["userId"],
            mfa_devices=[
                MfaDevice.from_data(mfa_device)
                for mfa_device in data["mfaDevices"]
            ],
        )


def _fetch_mfa_devices(
    sigv4_auth: SigV4Auth,
    identity_store_id: str,
    region: str,
    user_ids: list[str],
) -> dict:
    endpoint = f"https://auth-control.{region}.prod.apps-auth.aws.a2z.com/"
    headers = {
        "Content-Type": "application/x-amz-json-1.0",
        "X-Amz-Target": "AppsAuthControlPlaneService.BatchListMfaDevicesForUser",  # noqa: E501
    }
    data = json.dumps(
        {
            "userList": [
                {"directoryId": identity_store_id, "userId": user_id}
                for user_id in user_ids
            ],
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


def fetch_all_mfa_devices(
    identity_store_id: str, region: str, user_ids: list[str]
) -> list[UserMfa]:
    sigv4_auth = SigV4Auth(
        credentials=Session().get_credentials(),
        service_name="appsauth",
        region_name=region,
    )

    user_mfa_devices: list[UserMfa] = []
    batch_size = 25
    for i in range(0, len(user_ids), batch_size):
        response = _fetch_mfa_devices(
            sigv4_auth=sigv4_auth,
            identity_store_id=identity_store_id,
            region=region,
            user_ids=user_ids[i : i + batch_size],  # noqa: E203
        )
        user_mfa_devices += [
            UserMfa.from_data(mfa)
            for mfa in response["userMfaDevicesEntryList"]
        ]

    return user_mfa_devices
