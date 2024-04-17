import json
import os
import typing
from datetime import UTC, datetime

import pytest
from botocore.auth import SigV4Auth
from botocore.session import Session
from pytest_mock import MockerFixture
from requests import Response

from aws_sso_user_list.mfa_device import (
    MfaDevice,
    UserMfa,
    _fetch_mfa_devices,
    fetch_all_mfa_devices,
)


class TestMfaDevice:
    @pytest.fixture
    def target(self) -> typing.Type[MfaDevice]:
        return MfaDevice

    def test_from_data(self, target: typing.Type[MfaDevice]) -> None:
        data = {
            "deviceId": "m-0123456789abcdef_id",
            "deviceName": "m-0123456789abcdef_name",
            "displayName": "MFA Device",
            "mfaType": "WEBAUTHN",
            "registeredDate": 948603360.0,
        }

        mfa_device = target.from_data(data)

        assert mfa_device.device_id == "m-0123456789abcdef_id"
        assert mfa_device.device_name == "m-0123456789abcdef_name"
        assert mfa_device.display_name == "MFA Device"
        assert mfa_device.mfa_type == "WEBAUTHN"
        assert mfa_device.registered_date == datetime(
            2000, 1, 23, 4, 56, tzinfo=UTC
        )


class TestUserMfa:
    @pytest.fixture
    def target(self) -> typing.Type[UserMfa]:
        return UserMfa

    def test_from_data(
        self,
        target: typing.Type[UserMfa],
        mocker: MockerFixture,
    ) -> None:
        data = {
            "mfaDevices": [
                {
                    "deviceId": "m-0123456789abcdef_id1",
                    "deviceName": "m-0123456789abcdef_name1",
                    "displayName": "MFA Device1",
                    "mfaType": "WEBAUTHN",
                    "registeredDate": 948603360.0,
                },
                {
                    "deviceId": "m-0123456789abcdef_id2",
                    "deviceName": "m-0123456789abcdef_name2",
                    "displayName": "MFA Device2",
                    "mfaType": "TOTP",
                    "registeredDate": 948603360.0,
                },
            ],
            "user": {
                "directoryId": "d-0123456789",
                "userId": "01234567-89ab-cdef-0123-456789abcdef",
            },
        }

        mocked_mfa_device = mocker.patch(
            "aws_sso_user_list.mfa_device.MfaDevice"
        )
        mocked_mfa_device.from_data.side_effect = [
            MfaDevice(
                device_id="m-0123456789abcdef_id01",
                device_name="m-0123456789abcdef_name01",
                display_name="MFA Device01",
                mfa_type="WEBAUTHN",
                registered_date=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
            ),
            MfaDevice(
                device_id="m-0123456789abcdef_id02",
                device_name="m-0123456789abcdef_name02",
                display_name="MFA Device02",
                mfa_type="TOTP",
                registered_date=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
            ),
        ]
        user_mfa = target.from_data(data)

        assert mocked_mfa_device.from_data.call_count == 2
        assert user_mfa.user_id == "01234567-89ab-cdef-0123-456789abcdef"
        assert len(user_mfa.mfa_devices) == 2
        assert user_mfa.mfa_devices[0].device_id == "m-0123456789abcdef_id01"
        assert (
            user_mfa.mfa_devices[1].device_name == "m-0123456789abcdef_name02"
        )


class TestFetchMfaDevice:
    @pytest.fixture
    def target(
        self,
    ) -> typing.Callable[[SigV4Auth, str, str, list[str]], dict]:
        return _fetch_mfa_devices

    @pytest.fixture
    def credential_env(self) -> dict[str, str]:
        credentials = {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_SECURITY_TOKEN": "testing",
            "AWS_SESSION_TOKEN": "testing",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        for key, value in credentials.items():
            os.environ[key] = value

        return credentials

    @pytest.fixture
    def sigv4_auth(self, credential_env: dict) -> SigV4Auth:
        region = "us-east-1"

        return SigV4Auth(
            credentials=Session().get_credentials(),
            service_name="appsauth",
            region_name=region,
        )

    def test_call_success(
        self,
        target: typing.Callable[[SigV4Auth, str, str, str], dict],
        sigv4_auth: SigV4Auth,
        mocker: MockerFixture,
    ) -> None:
        response = Response()
        response._content = json.dumps(
            {
                "userMfaDevicesEntryList": [
                    {
                        "mfaDevices": [
                            {
                                "deviceId": "m-0123456789abcdef_id",
                                "deviceName": "m-0123456789abcdef_name",
                                "displayName": "MFA Device",
                                "mfaType": "WEBAUTHN",
                                "registeredDate": 948603360.0,
                            },
                        ],
                        "user": {
                            "directoryId": "d-0123456789",
                            "userId": "01234567-89ab-cdef-0123-456789abcdef",
                        },
                    },
                ],
            }
        ).encode()
        mocked_post = mocker.patch(
            "requests.post",
            return_value=response,
        )

        response = target(
            sigv4_auth,
            "d-1234567890",
            "us-east-1",
            ["01234567-89ab-cdef-0123-456789abcdef"],
        )

        mocked_post.assert_called_once()
        assert len(response["userMfaDevicesEntryList"]) == 1
        assert (
            response["userMfaDevicesEntryList"][0]["user"]["userId"]
            == "01234567-89ab-cdef-0123-456789abcdef"
        )
        assert (
            response["userMfaDevicesEntryList"][0]["mfaDevices"][0]["deviceId"]
            == "m-0123456789abcdef_id"
        )


class TestFetchAllMfaDevices:
    @pytest.fixture
    def target(self) -> typing.Callable[[str, str, list[str]], list[UserMfa]]:
        return fetch_all_mfa_devices

    @pytest.fixture
    def credential_env(self) -> dict[str, str]:
        credentials = {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_SECURITY_TOKEN": "testing",
            "AWS_SESSION_TOKEN": "testing",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        for key, value in credentials.items():
            os.environ[key] = value

        return credentials

    def test_call_success(
        self,
        target: typing.Callable[[str, str, list[str]], list[UserMfa]],
        credential_env: dict[str, str],
        mocker: MockerFixture,
    ) -> None:
        mocked_fetch_mfa_devices = mocker.patch(
            "aws_sso_user_list.mfa_device._fetch_mfa_devices",
            side_effect=[
                {
                    "userMfaDevicesEntryList": [
                        {
                            "mfaDevices": [
                                {
                                    "deviceId": "m-0123456789abcdef_id1",
                                    "deviceName": "m-0123456789abcdef_name1",
                                    "displayName": "MFA Device",
                                    "mfaType": "WEBAUTHN",
                                    "registeredDate": 948603360.0,
                                },
                            ],
                            "user": {
                                "directoryId": "d-0123456789",
                                "userId": "01234567-89ab-cdef-0123-456789abcde1",  # noqa: E501
                            },
                        },
                        {
                            "mfaDevices": [
                                {
                                    "deviceId": "m-0123456789abcdef_id2",
                                    "deviceName": "m-0123456789abcdef_name2",
                                    "displayName": "MFA Device",
                                    "mfaType": "TOTP",
                                    "registeredDate": 948603360.0,
                                },
                            ],
                            "user": {
                                "directoryId": "d-0123456789",
                                "userId": "01234567-89ab-cdef-0123-456789abcde2",  # noqa: E501
                            },
                        },
                    ],
                },
            ],
        )

        user_mfa_devices = target(
            "d-1234567890",
            "us-east-1",
            [
                "01234567-89ab-cdef-0123-456789abcde1",
                "01234567-89ab-cdef-0123-456789abcde2",
            ],
        )

        assert mocked_fetch_mfa_devices.call_count == 1
        assert (
            user_mfa_devices[0].user_id
            == "01234567-89ab-cdef-0123-456789abcde1"
        )
        assert (
            user_mfa_devices[0].mfa_devices[0].device_id
            == "m-0123456789abcdef_id1"  # noqa: E501
        )
        assert (
            user_mfa_devices[1].user_id
            == "01234567-89ab-cdef-0123-456789abcde2"
        )
        assert (
            user_mfa_devices[1].mfa_devices[0].device_id
            == "m-0123456789abcdef_id2"  # noqa: E501
        )
