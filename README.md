# AWS SSO Uesr List CLI

Fetch users' information include email verification status and MFA devices.

## Requirements

- Python >= 3.12

## Installation

Create python virtualenv and activate.

```sh
$ python -m venv .venv
$ source .venv/bin/activate
```

Install packages

```sh
(.venv) $ pip install -e .
```

## Usage

```sh
(.venv) $ sso-user-list --identity-store-id={IdentityStoreId} --region={Region}
```
