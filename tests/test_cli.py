import json
import typing
from datetime import UTC, datetime

import pytest
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from aws_sso_user_list.cli import main
from aws_sso_user_list.mfa_device import MfaDevice
from aws_sso_user_list.utils import UserWithMfaDevice


class TestMain:
    @pytest.fixture
    def target(self) -> typing.Callable[[str, str, str], Result]:
        def wrapper(
            identity_store_id: str,
            region: str,
            format: str,
        ) -> Result:
            runner = CliRunner()
            result = runner.invoke(
                cli=main,
                args=[
                    f"--identity-store-id={identity_store_id}",
                    f"--region={region}",
                    f"--format={format}",
                ],
            )
            return result

        return wrapper

    def test_invoke_csv_format(
        self,
        target: typing.Callable[[str, str], Result],
        mocker: MockerFixture,
    ) -> None:
        mocked_fetch_all_user_with_mfa_device = mocker.patch(
            "aws_sso_user_list.cli.fetch_all_user_with_mfa_device",
            return_value=[
                UserWithMfaDevice(
                    active=True,
                    user_id="01234567-89ab-cdef-0123-456789abcdef",
                    user_name="user@example.com",
                    display_name="John Doe",
                    email="user@example.com",
                    email_verification_status="VERIFIED",
                    created_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                    updated_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                    mfa_devices=[
                        MfaDevice(
                            device_id="m-0123456789abcdef_id",
                            device_name="m-0123456789abcdef_name",
                            display_name="MFA Device",
                            mfa_type="WEBAUTHN",
                            registered_date=datetime(
                                2000, 1, 23, 4, 56, tzinfo=UTC
                            ),
                        ),
                    ],
                )
            ],
        )

        result = target("d-0123456789", "us-east-1", "csv")

        mocked_fetch_all_user_with_mfa_device.assert_called_once_with(
            identity_store_id="d-0123456789",
            region="us-east-1",
        )
        assert result.stdout == "\n".join(
            [
                ",".join(
                    [
                        "Active",
                        "UserId",
                        "UserName",
                        "DisplayName",
                        "Email",
                        "EmailVerificationStatus",
                        "MfaDeviceCount",
                        "CreatedAt",
                        "UpdatedAt",
                    ]
                ),
                ",".join(
                    [
                        "True",
                        "01234567-89ab-cdef-0123-456789abcdef",
                        "user@example.com",
                        "John Doe",
                        "user@example.com",
                        "VERIFIED",
                        "1",
                        "2000-01-23T04:56:00+00:00",
                        "2000-01-23T04:56:00+00:00",
                    ]
                ),
                "",
            ]
        )

    def test_invoke_json_format(
        self,
        target: typing.Callable[[str, str], Result],
        mocker: MockerFixture,
    ) -> None:
        mocked_fetch_all_user_with_mfa_device = mocker.patch(
            "aws_sso_user_list.cli.fetch_all_user_with_mfa_device",
            return_value=[
                UserWithMfaDevice(
                    active=True,
                    user_id="01234567-89ab-cdef-0123-456789abcdef",
                    user_name="user@example.com",
                    display_name="John Doe",
                    email="user@example.com",
                    email_verification_status="VERIFIED",
                    created_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                    updated_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                    mfa_devices=[
                        MfaDevice(
                            device_id="m-0123456789abcdef_id",
                            device_name="m-0123456789abcdef_name",
                            display_name="MFA Device",
                            mfa_type="WEBAUTHN",
                            registered_date=datetime(
                                2000, 1, 23, 4, 56, tzinfo=UTC
                            ),
                        ),
                    ],
                ),
            ],
        )

        result = target("d-0123456789", "us-east-1", "json")

        mocked_fetch_all_user_with_mfa_device.assert_called_once_with(
            identity_store_id="d-0123456789",
            region="us-east-1",
        )
        assert json.loads(result.stdout) == {
            "Users": [
                {
                    "active": True,
                    "user_id": "01234567-89ab-cdef-0123-456789abcdef",
                    "user_name": "user@example.com",
                    "display_name": "John Doe",
                    "email": "user@example.com",
                    "email_verification_status": "VERIFIED",
                    "created_at": "2000-01-23T04:56:00+00:00",
                    "updated_at": "2000-01-23T04:56:00+00:00",
                    "mfa_devices": [
                        {
                            "device_id": "m-0123456789abcdef_id",
                            "device_name": "m-0123456789abcdef_name",
                            "display_name": "MFA Device",
                            "mfa_type": "WEBAUTHN",
                            "registered_date": "2000-01-23T04:56:00+00:00",
                        },
                    ],
                },
            ],
        }
