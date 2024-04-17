from dataclasses import asdict, dataclass
from datetime import datetime

from aws_sso_user_list.mfa_device import (
    MfaDevice,
    UserMfa,
    fetch_all_mfa_devices,
)
from aws_sso_user_list.user import User, fetch_all_users


@dataclass
class UserWithMfaDevice:
    active: bool
    user_id: str
    user_name: str
    display_name: str
    email: str
    email_verification_status: str
    created_at: datetime
    updated_at: datetime
    mfa_devices: list[MfaDevice]

    @classmethod
    def from_user_and_user_mfa(
        cls, user: User, user_mfa: UserMfa
    ) -> "UserWithMfaDevice":
        assert user.user_id == user_mfa.user_id
        return cls(
            mfa_devices=user_mfa.mfa_devices,
            **asdict(user),
        )


def combine_user_and_user_mfa(
    users: list[User], user_mfas: list[UserMfa]
) -> list[UserWithMfaDevice]:
    user_mfa_map = {user_mfa.user_id: user_mfa for user_mfa in user_mfas}
    user_with_mfa_device = [
        UserWithMfaDevice.from_user_and_user_mfa(
            user=user, user_mfa=user_mfa_map[user.user_id]
        )
        for user in users
    ]
    return user_with_mfa_device


def fetch_all_user_with_mfa_device(
    identity_store_id: str, region: str
) -> list[UserWithMfaDevice]:
    users = fetch_all_users(identity_store_id=identity_store_id, region=region)
    user_mfas = fetch_all_mfa_devices(
        identity_store_id=identity_store_id,
        region=region,
        user_ids=[user.user_id for user in users],
    )
    user_with_mfa_device = combine_user_and_user_mfa(
        users=users, user_mfas=user_mfas
    )

    return user_with_mfa_device
