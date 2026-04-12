# sqlmodel-toolkit

A toolkit for cleaner SQLModel queries with fluent API, Model base class, and engine management.

`sqlmodel-toolkit` provides a system for working with SQLModel that simplifies database interactions through a
fluent query interface, removing boilerplate and making your data layer code more readable and maintainable.

## Features

- **Chainable Query API:** Chain query methods naturally: `.where().order_by().limit().all()`
- **Class-level Query Methods:** Call queries directly on your model: `User.find(1)`, `User.where(active=True).all()`
- **Simplified Engine Management:** Set once, use everywhere with `Model.set_engine()`
- **Eager Loading:** Prevent N+1 queries with `.with_()` relationship loading
- **Type-Safe:** Full type hints for excellent IDE support
- **Zero Dependencies Beyond SQLModel:** Minimal surface area

## Installation

```bash
pip install sqlmodel-toolkit
```

## Quick Start

### 1. Define your models

```python
from sqlmodel import Field, Relationship
from sqlmodel_toolkit import Model


class User(Model):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    active: bool = True
    posts: list["Post"] = Relationship(back_populates="author")


class Post(Model):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship(back_populates="posts")
```

### 2. Configure the engine

```python
from sqlmodel import create_engine
from sqlmodel_toolkit import Model

engine = create_engine("sqlite:///database.db")
Model.set_engine(engine)

# Create tables
SQLModel.create_all(engine)
```

### 3. Use your models

```python
# Create
user = User.create(name="Alice", email="alice@example.com")

# Find by primary key
user = User.find(1)

# Find with conditions
user = User.find_by(email="alice@example.com")

# Query with chainable methods
active_users = User.where(User.active == True).all()

# Order and limit
recent_users = User.order_by(User.id.desc()).limit(10).all()

# Combine conditions
admin_users = User.where(User.active == True).where(User.role == "admin").all()

# Or use keyword arguments for equality
active_admins = User.where(active=True, role="admin").all()

# Exclude records
inactive_users = User.not_(active=True).all()

# Avoid N+1 queries with eager loading
users_with_posts = User.with_("posts").all()

# Count results
total = User.where(active=True).count()

# Get exactly one result
user = User.where(email="alice@example.com").one()

# Update
user.update(name="Alice Smith", active=False)

# Reload from database
user.reload()

# Delete
user.delete()
```

## API Reference

### Query Methods

All query methods return `Query` for chaining, except terminal methods.

#### `where(*conditions, **kwargs) -> Query`

Add filtering conditions to the query.

```python
# Using SQLAlchemy expressions
User.where(User.age > 18, User.active == True)

# Using keyword arguments for equality
User.where(name="Alice", active=True)

# Mix both styles
User.where(User.age > 18, active=True)
```

#### `not_(*conditions, **kwargs) -> Query`

Negate filtering conditions (exclude records matching criteria).

```python
# Exclude inactive users
User.not_(active=False).all()

# Exclude specific users
User.not_(name="Alice").all()
```

#### `with_(*relationships) -> Query`

Eagerly load relationships to prevent N+1 queries.

```python
# Load single relationship
users = User.with_("posts").all()

# Load multiple relationships
users = User.with_("posts", "comments").all()
```

#### `order_by(*args, **kwargs) -> Query`

Order results by one or more columns.

```python
# Using SQLAlchemy expressions
User.order_by(User.name)
User.order_by(User.created_at.desc())

# Using keyword arguments
User.order_by(name="asc", age="desc")
```

#### `limit(count: int) -> Query`

Limit the number of results.

```python
User.limit(10).all()
```

#### `offset(count: int) -> Query`

Skip a given number of records (useful for pagination).

```python
User.offset(20).limit(10).all()  # Get items 21-30
```

#### `distinct() -> Query`

Return only unique records.

```python
User.distinct().all()
```

#### Terminal Methods

These execute the query and return results:

- **`all() -> List[T]`** — Return all matching records as a list
- **`first() -> T | None`** — Return the first matching record or None
- **`one() -> T`** — Return exactly one result (raises if not found)
- **`count() -> int`** — Return the count of matching records

### Model Methods

#### `find(value) -> T | None`

Find a record by its primary key.

```python
user = User.find(1)
```

#### `find_by(**kwargs) -> T | None`

Find the first record matching the provided conditions.

```python
user = User.find_by(email="alice@example.com")
user = User.find_by(name="Alice", active=True)
```

#### `create(**kwargs) -> T`

Create and save a new record.

```python
user = User.create(name="Alice", email="alice@example.com")
```

#### `query() -> Query`

Get a new query object for manual query building (rarely needed).

```python
User.query().where(User.active == True).all()
```

### Instance Methods

#### `save() -> Self`

Save the instance to the database.

```python
user = User(name="Alice")
user.save()
```

#### `update(**kwargs) -> Self`

Update attributes and save to the database.

```python
user.update(name="Alice Smith", active=False)
```

#### `reload() -> Self`

Reload the instance from the database, discarding unsaved changes.

```python
user.reload()
```

#### `delete() -> None`

Delete the record from the database.

```python
user.delete()
```

## Requirements

- Python 3.10+
- sqlmodel 0.0.38+

## License

This project is licensed under the terms
of [MIT license](https://github.com/Code-Society-Lab/sqlmodel-toolkit/blob/main/LICENSE).

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.