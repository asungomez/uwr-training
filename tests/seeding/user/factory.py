"""User factory. `build_user` returns an in-memory User (not persisted).

Mandatory fields are auto-filled with Faker; pass overrides only for what the test
story cares about, e.g. build_user(role="admin").
"""

from faker import Faker

from app.models import User, UserRole
from app.security import hash_password

fake = Faker()

# Known plaintext for built users, so tests can log in as them.
DEFAULT_PASSWORD = "Test1234!"


def build_user(
    *,
    password: str = DEFAULT_PASSWORD,
    role: UserRole | str = UserRole.member,
    **overrides: object,
) -> User:
    """Build an in-memory User with all mandatory fields filled."""
    if isinstance(role, str):
        role = UserRole(role)
    fields: dict[str, object] = {
        "email": fake.unique.email(),
        "hashed_password": hash_password(password),
        "role": role,
    }
    fields.update(overrides)
    return User(**fields)
