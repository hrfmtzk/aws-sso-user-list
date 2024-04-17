import csv
import json
import typing
from dataclasses import asdict
from datetime import datetime
from enum import Enum

import click

from aws_sso_user_list.utils import (
    UserWithMfaDevice,
    fetch_all_user_with_mfa_device,
)

if typing.TYPE_CHECKING:
    from _typeshed import SupportsWrite


class Format(Enum):
    CSV = "csv"
    JSON = "json"


class BaseUserExporter:
    def __init__(self, users: list[UserWithMfaDevice]) -> None:
        self.users = users

    def export(self, output: "SupportsWrite") -> None:
        raise NotImplementedError()


class UserCsvExporter(BaseUserExporter):
    def export(self, output: "SupportsWrite") -> None:
        field_maps = [
            ("Active", lambda user: str(user.active)),
            ("UserId", lambda user: user.user_id),
            ("UserName", lambda user: user.user_name),
            ("DisplayName", lambda user: user.display_name),
            ("Email", lambda user: user.email),
            (
                "EmailVerificationStatus",
                lambda user: user.email_verification_status,
            ),
            ("MfaDeviceCount", lambda user: str(len(user.mfa_devices))),
            ("CreatedAt", lambda user: user.created_at.isoformat()),
            ("UpdatedAt", lambda user: user.updated_at.isoformat()),
        ]

        writer = csv.DictWriter(
            output, fieldnames=[fieldname for fieldname, _ in field_maps]
        )

        writer.writeheader()
        for user in self.users:
            row = {field: converter(user) for field, converter in field_maps}
            writer.writerow(row)


class UserJsonExporter(BaseUserExporter):
    def export(self, output: "SupportsWrite") -> None:
        data = {"Users": [asdict(user) for user in self.users]}

        def json_default(obj: typing.Any) -> typing.Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return str(obj)

        json.dump(
            data,
            output,
            indent=2,
            default=json_default,
            ensure_ascii=False,
        )


@click.command()
@click.option(
    "--identity-store-id",
    help="Identity store ID (e.g. d-0123456789)",
    prompt=True,
    required=True,
)
@click.option(
    "--region",
    help="region name (e.g. us-east-1)",
    prompt=True,
    required=True,
)
@click.option(
    "--format",
    type=click.Choice(
        choices=[format_.value for format_ in Format],
        case_sensitive=False,
    ),
    default=Format.JSON.name,
)
@click.option(
    "--output",
    type=click.File(mode="w", encoding="utf-8"),
    default="-",
)
def main(
    identity_store_id: str,
    region: str,
    format: str,
    output: "SupportsWrite",
) -> None:
    users = fetch_all_user_with_mfa_device(
        identity_store_id=identity_store_id,
        region=region,
    )
    exporter: BaseUserExporter = {
        Format.CSV: UserCsvExporter,
        Format.JSON: UserJsonExporter,
    }[Format(format)](users)

    exporter.export(output)
