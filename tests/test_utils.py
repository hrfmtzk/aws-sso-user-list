import typing
from datetime import UTC, datetime

import pytest
from pytest_mock import MockerFixture

from aws_sso_user_list.mfa_device import MfaDevice, UserMfa
from aws_sso_user_list.user import User
from aws_sso_user_list.utils import (
    UserWithMfaDevice,
    combine_user_and_user_mfa,
    fetch_all_user_with_mfa_device,
)


class TestUserWithMfaDevice:
    @pytest.fixture
    def target(self) -> typing.Type[UserWithMfaDevice]:
        return UserWithMfaDevice

    def test_from_user_and_user_mfa(
        self, target: typing.Type[UserWithMfaDevice]
    ) -> None:
        user = User(
            active=True,
            user_id="01234567-89ab-cdef-0123-456789abcdef",
            user_name="user@example.com",
            display_name="John Doe",
            email="user@example.com",
            email_verification_status="VERIFIED",
            created_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
            updated_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
        )
        user_mfa = UserMfa(
            user_id="01234567-89ab-cdef-0123-456789abcdef",
            mfa_devices=[
                MfaDevice(
                    device_id="m-0123456789abcdef_id",
                    device_name="m-0123456789abcdef_name",
                    display_name="MFA Device",
                    mfa_type="WEBAUTHN",
                    registered_date=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                ),
            ],
        )

        user_with_mfa_device = target.from_user_and_user_mfa(
            user=user, user_mfa=user_mfa
        )

        assert user_with_mfa_device.active is True
        assert (
            user_with_mfa_device.user_id
            == "01234567-89ab-cdef-0123-456789abcdef"
        )
        assert user_with_mfa_device.user_name == "user@example.com"
        assert user_with_mfa_device.display_name == "John Doe"
        assert user_with_mfa_device.email == "user@example.com"
        assert user_with_mfa_device.email_verification_status == "VERIFIED"
        assert user_with_mfa_device.created_at == datetime(
            2000, 1, 23, 4, 56, tzinfo=UTC
        )
        assert user_with_mfa_device.updated_at == datetime(
            2000, 1, 23, 4, 56, tzinfo=UTC
        )
        assert len(user_with_mfa_device.mfa_devices) == 1
        assert (
            user_with_mfa_device.mfa_devices[0].device_id
            == "m-0123456789abcdef_id"
        )
        assert (
            user_with_mfa_device.mfa_devices[0].device_name
            == "m-0123456789abcdef_name"
        )
        assert user_with_mfa_device.mfa_devices[0].display_name == "MFA Device"
        assert user_with_mfa_device.mfa_devices[0].mfa_type == "WEBAUTHN"
        assert user_with_mfa_device.mfa_devices[0].registered_date == datetime(
            2000, 1, 23, 4, 56, tzinfo=UTC
        )


class TestCombineUserAndUserMfa:
    @pytest.fixture
    def target(
        self,
    ) -> typing.Callable[[list[User], list[UserMfa]], list[User]]:
        return combine_user_and_user_mfa

    def test_call_success(
        self,
        target: typing.Callable[
            [list[User], list[UserMfa]], list[UserWithMfaDevice]
        ],
    ) -> None:
        users = [
            User(
                active=True,
                user_id="01234567-89ab-cdef-0123-456789abcde1",
                user_name="user1@example.com",
                display_name="John Doe",
                email="user1@example.com",
                email_verification_status="VERIFIED",
                created_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                updated_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
            ),
            User(
                active=True,
                user_id="01234567-89ab-cdef-0123-456789abcde2",
                user_name="user2@example.com",
                display_name="Jane Doe",
                email="user2@example.com",
                email_verification_status="VERIFIED",
                created_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                updated_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
            ),
        ]
        user_mfas = [
            UserMfa(
                user_id="01234567-89ab-cdef-0123-456789abcde1",
                mfa_devices=[
                    MfaDevice(
                        device_id="m-0123456789abcdef_id1",
                        device_name="m-0123456789abcdef_name1",
                        display_name="MFA Device",
                        mfa_type="WEBAUTHN",
                        registered_date=datetime(
                            2000, 1, 23, 4, 56, tzinfo=UTC
                        ),
                    ),
                ],
            ),
            UserMfa(
                user_id="01234567-89ab-cdef-0123-456789abcde2",
                mfa_devices=[],
            ),
        ]

        user_with_mfa_device = target(users, user_mfas)

        assert len(user_with_mfa_device) == 2
        assert (
            user_with_mfa_device[0].user_id
            == "01234567-89ab-cdef-0123-456789abcde1"
        )
        assert len(user_with_mfa_device[0].mfa_devices) == 1
        assert (
            user_with_mfa_device[0].mfa_devices[0].device_id
            == "m-0123456789abcdef_id1"
        )
        assert (
            user_with_mfa_device[1].user_id
            == "01234567-89ab-cdef-0123-456789abcde2"
        )
        assert len(user_with_mfa_device[1].mfa_devices) == 0


class TestFetchAllUserWithMfaDevice:
    @pytest.fixture
    def target(self) -> typing.Callable[[str, str], list[UserWithMfaDevice]]:
        return fetch_all_user_with_mfa_device

    def test_call_success(
        self,
        target: typing.Callable[[str, str], list[UserWithMfaDevice]],
        mocker: MockerFixture,
    ) -> None:
        user = User(
            active=True,
            user_id="01234567-89ab-cdef-0123-456789abcdef",
            user_name="user@example.com",
            display_name="John Doe",
            email="user@example.com",
            email_verification_status="VERIFIED",
            created_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
            updated_at=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
        )
        user_mfa = UserMfa(
            user_id="01234567-89ab-cdef-0123-456789abcdef",
            mfa_devices=[
                MfaDevice(
                    device_id="m-0123456789abcdef_id",
                    device_name="m-0123456789abcdef_name",
                    display_name="MFA Device",
                    mfa_type="WEBAUTHN",
                    registered_date=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                ),
            ],
        )
        user_with_mfa_device = UserWithMfaDevice(
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
                    registered_date=datetime(2000, 1, 23, 4, 56, tzinfo=UTC),
                ),
            ],
        )
        mocked_fetch_all_users = mocker.patch(
            "aws_sso_user_list.utils.fetch_all_users",
            return_value=[user],
        )
        mocked_fetch_all_mfa_devices = mocker.patch(
            "aws_sso_user_list.utils.fetch_all_mfa_devices",
            return_value=[user_mfa],
        )
        mocked_combine_user_and_user_mfa = mocker.patch(
            "aws_sso_user_list.utils.combine_user_and_user_mfa",
            return_value=[user_with_mfa_device],
        )

        data = target("d-0123456789", "us-east-1")

        mocked_fetch_all_users.assert_called_once_with(
            identity_store_id="d-0123456789",
            region="us-east-1",
        )
        mocked_fetch_all_mfa_devices.assert_called_once_with(
            identity_store_id="d-0123456789",
            region="us-east-1",
            user_ids=["01234567-89ab-cdef-0123-456789abcdef"],
        )
        mocked_combine_user_and_user_mfa.assert_called_once_with(
            users=[user],
            user_mfas=[user_mfa],
        )
        assert data == [user_with_mfa_device]
