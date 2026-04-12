import pytest
from .conftest import User


def test_create__expects_record_persisted():
    user = User.create(name="Alice", email="alice@example.com")
    assert user.id is not None


def test_create__expects_attributes_set():
    user = User.create(name="Alice", email="alice@example.com", active=False)
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.active is False


def test_create__expects_returned_type_is_model():
    user = User.create(name="Alice", email="alice@example.com")
    assert isinstance(user, User)


def test_save__expects_record_persisted():
    user = User(name="Alice", email="alice@example.com")
    user.save()
    assert user.id is not None


def test_save__expects_returned_instance_is_same_type():
    user = User(name="Alice", email="alice@example.com")
    result = user.save()
    assert isinstance(result, User)


def test_update__expects_attributes_changed(user):
    user.update(name="Alice Smith")
    assert user.name == "Alice Smith"


def test_update__expects_changes_persisted(user):
    user.update(name="Alice Smith")
    reloaded = User.find(user.id)
    assert reloaded.name == "Alice Smith"


def test_update__expects_returned_instance_is_same_type(user):
    result = user.update(name="Alice Smith")
    assert isinstance(result, User)


def test_update__with_unknown_key__expects_no_error(user):
    user.update(nonexistent_field="value")


def test_delete__expects_record_removed(user):
    user_id = user.id
    user.delete()
    assert User.find(user_id) is None


def test_delete__expects_count_decremented(user):
    assert User.count() == 1
    user.delete()
    assert User.count() == 0


def test_reload__expects_unsaved_changes_discarded(user):
    user.name = "Changed"
    user.reload()
    assert user.name == "Alice"


def test_reload__expects_external_changes_reflected(user):
    User.find(user.id).update(name="Updated Externally")
    user.reload()
    assert user.name == "Updated Externally"


def test_reload__with_unsaved_instance__expects_value_error():
    unsaved = User(name="Ghost", email="ghost@example.com")
    with pytest.raises(ValueError):
        unsaved.reload()
