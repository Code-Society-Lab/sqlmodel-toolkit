import pytest
from .conftest import User


def test_find__expects_record_returned(user):
    found = User.find(user.id)
    assert found is not None
    assert found.id == user.id


def test_find__with_missing_id__expects_none():
    found = User.find(999)
    assert found is None


def test_find__expects_correct_attributes(user):
    found = User.find(user.id)
    assert found.name == user.name
    assert found.email == user.email


def test_find_by__expects_record_returned(user):
    found = User.find_by(name="Alice")
    assert found is not None
    assert found.name == "Alice"


def test_find_by__with_missing_value__expects_none():
    found = User.find_by(name="Nobody")
    assert found is None


def test_find_by__with_multiple_kwargs__expects_record_returned(user):
    found = User.find_by(name="Alice", active=True)
    assert found is not None


def test_find_by__with_no_kwargs__expects_value_error():
    with pytest.raises(ValueError):
        User.find_by()


def test_where__expects_matching_records_returned(user, inactive_user):
    results = User.where(active=True).all()
    assert all(u.active for u in results)


def test_where__with_expression__expects_matching_records_returned(user, inactive_user):
    results = User.where(User.active == False).all()
    assert all(not u.active for u in results)


def test_where__with_no_match__expects_empty_list():
    results = User.where(name="Nobody").all()
    assert results == []


def test_where__with_multiple_conditions__expects_filtered_results(user, inactive_user):
    results = User.where(name="Alice", active=True).all()
    assert len(results) == 1
    assert results[0].name == "Alice"


def test_where__with_invalid_column__expects_attribute_error():
    with pytest.raises(AttributeError):
        User.where(nonexistent="value").all()


def test_not__expects_excluded_records_omitted(user, inactive_user):
    results = User.not_(active=False).all()
    assert all(u.active for u in results)


def test_not__with_expression__expects_excluded_records_omitted(user, inactive_user):
    results = User.not_(User.name == "Alice").all()
    assert all(u.name != "Alice" for u in results)


def test_not__with_invalid_column__expects_attribute_error():
    with pytest.raises(AttributeError):
        User.not_(nonexistent="value").all()


def test_all__expects_all_records_returned(user, inactive_user):
    results = User.all()
    assert len(results) == 2


def test_all__with_empty_table__expects_empty_list():
    results = User.all()
    assert results == []


def test_first__expects_record_returned(user):
    result = User.first()
    assert result is not None
    assert isinstance(result, User)


def test_first__with_empty_table__expects_none():
    result = User.first()
    assert result is None


def test_one__expects_record_returned(user):
    result = User.where(name="Alice").one()
    assert result.name == "Alice"


def test_one__with_no_match__expects_exception():
    with pytest.raises(Exception):
        User.where(name="Nobody").one()


def test_one__with_multiple_records__expects_exception(user, inactive_user):
    with pytest.raises(Exception):
        User.query().one()


def test_count__expects_correct_count(user, inactive_user):
    assert User.count() == 2


def test_count__with_where__expects_filtered_count(user, inactive_user):
    assert User.where(active=True).count() == 1


def test_count__with_empty_table__expects_zero():
    assert User.count() == 0


def test_order_by__with_asc__expects_ascending_order():
    User.create(name="Charlie", email="c@example.com")
    User.create(name="Alice", email="a@example.com")
    User.create(name="Bob", email="b@example.com")
    results = User.order_by(name="asc").all()
    names = [u.name for u in results]
    assert names == sorted(names)


def test_order_by__with_desc__expects_descending_order():
    User.create(name="Charlie", email="c@example.com")
    User.create(name="Alice", email="a@example.com")
    results = User.order_by(name="desc").all()
    names = [u.name for u in results]
    assert names == sorted(names, reverse=True)


def test_order_by__with_invalid_direction__expects_value_error():
    with pytest.raises(ValueError):
        User.order_by(name="sideways").all()


def test_order_by__with_invalid_column__expects_attribute_error():
    with pytest.raises(AttributeError):
        User.order_by(nonexistent="asc").all()


def test_limit__expects_capped_results():
    for i in range(5):
        User.create(name=f"User{i}", email=f"u{i}@example.com")
    results = User.limit(3).all()
    assert len(results) == 3


def test_offset__expects_skipped_results():
    for i in range(5):
        User.create(name=f"User{i}", email=f"u{i}@example.com")
    all_results = User.order_by(id="asc").all()
    offset_results = User.order_by(id="asc").offset(2).all()
    assert offset_results[0].id == all_results[2].id


def test_limit__with_offset__expects_paginated_results():
    for i in range(5):
        User.create(name=f"User{i}", email=f"u{i}@example.com")
    results = User.order_by(id="asc").offset(2).limit(2).all()
    assert len(results) == 2


def test_distinct__expects_no_duplicate_records(user):
    results = User.distinct().all()
    ids = [u.id for u in results]
    assert len(ids) == len(set(ids))


def test_chain__where_order_by_limit__expects_correct_results():
    User.create(name="Charlie", email="c@example.com", active=True)
    User.create(name="Alice", email="a@example.com", active=True)
    User.create(name="Bob", email="b@example.com", active=False)
    results = User.where(active=True).order_by(name="asc").limit(1).all()
    assert len(results) == 1
    assert results[0].name == "Alice"


def test_chain__not_order_by_offset__expects_correct_results():
    User.create(name="Charlie", email="c@example.com", active=True)
    User.create(name="Alice", email="a@example.com", active=True)
    User.create(name="Bob", email="b@example.com", active=False)
    results = User.not_(active=False).order_by(name="asc").offset(1).all()
    assert len(results) == 1
    assert results[0].name == "Charlie"
