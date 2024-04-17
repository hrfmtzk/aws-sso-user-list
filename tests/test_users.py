import json
import os
import typing
from datetime import UTC, datetime

import pytest
from botocore.auth import SigV4Auth
from botocore.session import Session
from pytest_mock import MockerFixture
from requests import Response

from aws_sso_user_list.user import User, _fetch_users, fetch_all_users


class TestUser:
    @pytest.fixture
    def target(self) -> typing.Type[User]:
        return User

    def test_from_data(self, target: typing.Type[User]) -> None:
        data = {
            "Active": True,
            "Meta": {
                "CreatedAt": 948603360.0,
                "CreatedBy": "ABCDEFGHIJKLMNOPQRSTUVWXYZ:user@example.com",
                "UpdatedAt": 948603360.0,
                "UpdatedBy": "MIGRATION_V2",
            },
            "UserAttributes": {
                "emails": {
                    "ComplexListValue": [
                        {
                            "verificationStatus": {
                                "StringValue": "NOT_VERIFIED"
                            },
                            "type": {"StringValue": "work"},
                            "value": {"StringValue": "secondary@example.com"},
                            "primary": {"BooleanValue": False},
                        },
                        {
                            "verificationStatus": {"StringValue": "VERIFIED"},
                            "type": {"StringValue": "work"},
                            "value": {"StringValue": "primary@example.com"},
                            "primary": {"BooleanValue": True},
                        },
                    ]
                },
                "name": {
                    "ComplexValue": {
                        "givenName": {"StringValue": "John"},
                        "familyName": {"StringValue": "Doe"},
                    }
                },
                "addresses": {
                    "ComplexListValue": [{"type": {"StringValue": "work"}}]
                },
                "displayName": {"StringValue": "John Doe"},
            },
            "UserId": "01234567-89ab-cdef-0123-456789abcdef",
            "UserName": "user@example.com",
        }

        user = target.from_data(data)

        assert user.active is True
        assert (
            user.user_id == "01234567-89ab-cdef-0123-456789abcdef"
        )  # noqa: E501
        assert user.user_name == "user@example.com"
        assert user.email == "primary@example.com"
        assert user.email_verification_status == "VERIFIED"
        assert user.display_name == "John Doe"
        assert user.created_at == datetime(2000, 1, 23, 4, 56, tzinfo=UTC)
        assert user.updated_at == datetime(2000, 1, 23, 4, 56, tzinfo=UTC)


class TestFetchUsers:
    @pytest.fixture
    def target(self) -> typing.Callable[[SigV4Auth, str, str, str], dict]:
        return _fetch_users

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
            service_name="identitystore",
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
                "TotalUserCount": 1,
                "Users": [
                    {
                        "Active": True,
                        "Meta": {
                            "CreatedAt": 948603360.0,
                            "CreatedBy": "ABCDEFGHIJKLMNOPQRSTUVWXYZ:user@example.com",  # noqa: E501
                            "UpdatedAt": 948603360.0,
                            "UpdatedBy": "MIGRATION_V2",
                        },
                        "UserAttributes": {
                            "emails": {
                                "ComplexListValue": [
                                    {
                                        "verificationStatus": {
                                            "StringValue": "VERIFIED"
                                        },
                                        "type": {"StringValue": "work"},
                                        "value": {
                                            "StringValue": "primary@example.com"  # noqa: E501
                                        },
                                        "primary": {"BooleanValue": True},
                                    },
                                ]
                            },
                            "name": {
                                "ComplexValue": {
                                    "givenName": {"StringValue": "John"},
                                    "familyName": {"StringValue": "Doe"},
                                }
                            },
                            "addresses": {
                                "ComplexListValue": [
                                    {"type": {"StringValue": "work"}}
                                ]
                            },
                            "displayName": {"StringValue": "John Doe"},
                        },
                        "UserId": "01234567-89ab-cdef-0123-456789abcdef",  # noqa: E501
                        "UserName": "user@example.com",
                    }
                ],
            }
        ).encode()
        mocked_post = mocker.patch(
            "requests.post",
            return_value=response,
        )

        response = target(sigv4_auth, "d-1234567890", "us-east-1", "XXXXXXXX")

        mocked_post.assert_called_once()
        assert response["Users"][0]["UserName"] == "user@example.com"


class TestFetchAllUsers:
    @pytest.fixture
    def target(self) -> typing.Callable[[str, str], list[User]]:
        return fetch_all_users

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
        target: typing.Callable[[str, str], list[User]],
        credential_env: dict[str, str],
        mocker: MockerFixture,
    ) -> None:
        mocked_fetch_user = mocker.patch(
            "aws_sso_user_list.user._fetch_users",
            side_effect=[
                {
                    "TotalUserCount": 2,
                    "Users": [
                        {
                            "Active": True,
                            "Meta": {
                                "CreatedAt": 948603360.0,
                                "CreatedBy": "ABCDEFGHIJKLMNOPQRSTUVWXYZ:user@example.com",  # noqa: E501
                                "UpdatedAt": 948603360.0,
                                "UpdatedBy": "MIGRATION_V2",
                            },
                            "UserAttributes": {
                                "emails": {
                                    "ComplexListValue": [
                                        {
                                            "verificationStatus": {
                                                "StringValue": "VERIFIED"
                                            },
                                            "type": {"StringValue": "work"},
                                            "value": {
                                                "StringValue": "user1@example.com"  # noqa: E501
                                            },
                                            "primary": {"BooleanValue": True},
                                        },
                                    ]
                                },
                                "name": {
                                    "ComplexValue": {
                                        "givenName": {"StringValue": "John"},
                                        "familyName": {"StringValue": "Doe"},
                                    }
                                },
                                "addresses": {
                                    "ComplexListValue": [
                                        {"type": {"StringValue": "work"}}
                                    ]
                                },
                                "displayName": {"StringValue": "John Doe"},
                            },
                            "UserId": "01234567-89ab-cdef-0123-456789abcdef",  # noqa: E501
                            "UserName": "user1@example.com",
                        }
                    ],
                    "NextToken": "XXXXXXXX",
                },
                {
                    "TotalUserCount": 2,
                    "Users": [
                        {
                            "Active": True,
                            "Meta": {
                                "CreatedAt": 948603360.0,
                                "CreatedBy": "ABCDEFGHIJKLMNOPQRSTUVWXYZ:user@example.com",  # noqa: E501
                                "UpdatedAt": 948603360.0,
                                "UpdatedBy": "MIGRATION_V2",
                            },
                            "UserAttributes": {
                                "emails": {
                                    "ComplexListValue": [
                                        {
                                            "verificationStatus": {
                                                "StringValue": "VERIFIED"
                                            },
                                            "type": {"StringValue": "work"},
                                            "value": {
                                                "StringValue": "user2@example.com"  # noqa: E501
                                            },
                                            "primary": {"BooleanValue": True},
                                        },
                                    ]
                                },
                                "name": {
                                    "ComplexValue": {
                                        "givenName": {"StringValue": "John"},
                                        "familyName": {"StringValue": "Doe"},
                                    }
                                },
                                "addresses": {
                                    "ComplexListValue": [
                                        {"type": {"StringValue": "work"}}
                                    ]
                                },
                                "displayName": {"StringValue": "John Doe"},
                            },
                            "UserId": "01234567-89ab-cdef-0123-456789abcdef",  # noqa: E501
                            "UserName": "user2@example.com",
                        }
                    ],
                },
            ],
        )

        users = target("d-1234567890", "us-east-1")

        assert mocked_fetch_user.call_count == 2
        assert users[0].email == "user1@example.com"
        assert users[1].email == "user2@example.com"
