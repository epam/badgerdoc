from .conftest import User, Address
from src.enum_generator import (
    _get_model_fields,
    _exclude_fields,
    _get_table_name,
    _create_enum_model,
)


def test_get_model_fields():
    assert _get_model_fields(User) == ["id", "name", "address", "email"]
    assert _get_model_fields(Address) == ["id", "location", "owner"]


def test_exclude_fields():
    user_fields = _get_model_fields(User)
    address_fields = _get_model_fields(Address)
    assert _exclude_fields(user_fields, ["id", "address"]) == ["name", "email"]
    assert _exclude_fields(address_fields, ["id"]) == ["location", "owner"]


def test_get_table_name():
    assert _get_table_name(User) == "users_User"
    assert _get_table_name(Address) == "addresses_Address"


def test_create_enum_model():
    user_fields = _get_model_fields(User)
    user_table_name = _get_table_name(User)

    address_fields = _get_model_fields(Address)
    address_table_name = _get_table_name(Address)

    user_enum = _create_enum_model(user_table_name, user_fields)
    assert user_enum.ID.value == "id", user_enum.NAME.value == "name"
    assert user_enum.ADDRESS.value == "address", (
        user_enum.EMAIL.value == "email"
    )

    address_enum = _create_enum_model(address_table_name, address_fields)
    assert address_enum.ID.value == "id", (
        address_enum.LOCATION.value == "location"
    )
    assert address_enum.OWNER.value == "owner"
