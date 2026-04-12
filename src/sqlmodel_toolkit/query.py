from typing import (
    TYPE_CHECKING,
    Generic,
    Any,
    List,
    Type,
    TypeVar,
    Union,
    cast,
)

from sqlalchemy import Engine
from sqlalchemy.orm import selectinload
from sqlmodel import inspect, not_, asc, desc
from sqlmodel import Session, func, select

if TYPE_CHECKING:
    from sqlmodel.sql._expression_select_gen import Select, SelectOfScalar
    from sqlmodel_toolkit.model import Model


ModelT = TypeVar("ModelT", bound="Model")


class Query(Generic[ModelT]):
    def __init__(self, model_class: Type[ModelT]):
        self.model_class = model_class
        self.engine: Engine = model_class.get_engine()
        self._statement: Union[Select, SelectOfScalar, None] = None  # defer

    @property
    def statement(self):
        # Lazily create the statement when first accessed
        if self._statement is None:
            self._statement = select(self.model_class)
        return self._statement

    @statement.setter
    def statement(self, value):
        self._statement = value

    def find(self, value: Any) -> ModelT | None:
        """
        Finds a record by its primary key (id only).

        Returns `None` if the record does not exist.

        ## Examples
        ```python
        user = User.find(1)
        ```
        """
        mapper = inspect(self.model_class)

        if mapper is None:
            raise ValueError(f"{self.model_class.__name__} is not a mapped model")

        pk_columns = mapper.primary_key

        if not pk_columns:
            raise ValueError(f"No primary key defined for {self.model_class.__name__}")

        if len(pk_columns) > 1:
            raise ValueError("Composite primary keys are not yet supported")

        pk_name = pk_columns[0].key  # just the string name
        model_attr = getattr(self.model_class, pk_name)  # proper InstrumentedAttribute
        return self.where(model_attr == value).first()

    def find_by(self, **kwargs) -> ModelT | None:
        """
        Finds the first record matching the provided conditions.

        Equivalent to calling `.query().where(...).first()`.

        ## Examples
        ```python
        User.find_by(name="Alice")
        User.find_by(email="alice@example.com", active=True)
        ```
        """
        if not kwargs:
            raise ValueError("At least one keyword argument must be provided.")
        return self.where(**kwargs).first()

    def where(self, *conditions, **kwargs) -> "Query[ModelT]":
        """
        Adds one or more filtering conditions to the query.

        Accepts both SQLAlchemy expressions (e.g. `User.age > 18`)
        and simple equality filters through keyword arguments.

        ## Examples
        ```python
        # Using SQLAlchemy expressions
        User.where(User.age > 18, User.active == True)

        # Using keyword arguments for equality
        User.where(name="Alice", active=True)

        # Equivalent: combines both styles
        User.where(User.age > 18, active=True)
        ```
        """
        for key, value in kwargs.items():
            column_ = getattr(self.model_class, key, None)
            if column_ is None:
                raise AttributeError(
                    f"{self.model_class.__name__} has no column '{key}'"
                )
            conditions += (column_ == value,)

        for condition in conditions:
            self.statement = self.statement.where(condition)
        return self

    def not_(self, *conditions, **kwargs) -> "Query[ModelT]":
        """
        Applies negation of one or more filtering conditions to the query.

        Accepts SQLAlchemy expressions directly, or simple equality conditions
        expressed as keyword arguments. Keyword arguments are interpreted as
        equality checks that will then be negated.

        Use this when you want to exclude records matching specific conditions.

        ## Examples
        ```python
        # Exclude a specific user by name
        User.not_(name="Alice").all()

        # Exclude inactive users (negating an expression)
        User.not_(User.active == False).all()

        # Mixed usage
        User.not_(User.age > 30, role="admin").all()
        ```
        """
        for key, value in kwargs.items():
            column_ = getattr(self.model_class, key, None)
            if column_ is None:
                raise AttributeError(
                    f"{self.model_class.__name__} has no column '{key}'"
                )
            conditions += (column_ == value,)

        for condition in conditions:
            self.statement = self.statement.where(not_(condition))
        return self

    def with_(self, *relationships: str) -> "Query[ModelT]":
        """
        Eagerly loads specified relationships for optimization.

        Use this when querying multiple records to avoid N+1 queries.
        For relationships configured with lazy="selectin", this combines
        the relationship loading into the main query instead of a separate one.

        ## Examples
        ```python
        # Loading a single record: with_() doesn't help much
        trigger = Trigger.find_by(name="Linus")  # Already loads trigger_words efficiently

        # Loading multiple records: with_() prevents N+1 queries
        # Without with_: 1 query for triggers + 1 query for all trigger_words = 2 queries
        triggers = Trigger.all()

        # With with_: 1 combined query = 1 query (more efficient)
        triggers = Trigger.with_("trigger_words").all()

        # Load multiple relationships at once
        User.with_("posts", "comments").where(User.active == True).all()
        ```
        """
        for relationship in relationships:
            relationship_attr = getattr(self.model_class, relationship, None)
            if relationship_attr is None:
                raise AttributeError(
                    f"{self.model_class.__name__} has no relationship '{relationship}'"
                )
            self.statement = self.statement.options(selectinload(relationship_attr))
        return self

    def order_by(self, *args, **kwargs) -> "Query[ModelT]":
        """
        Orders query results by one or more columns.

        Supports passing SQLAlchemy expressions directly,
        or using keyword arguments like `name="asc"` or `age="desc"`.

        ## Examples
        ```python
        User.order_by(User.name)
        User.order_by(User.created_at.desc())
        User.order_by(name="asc", age="desc")
        ```
        """
        for key, direction in kwargs.items():
            column_ = getattr(self.model_class, key, None)
            if column_ is None:
                raise AttributeError(
                    f"{self.model_class.__name__} has no column '{key}'"
                )

            if isinstance(direction, str):
                if direction.lower() == "asc":
                    args += (asc(column_),)
                elif direction.lower() == "desc":
                    args += (desc(column_),)
                else:
                    raise ValueError(
                        f"Order direction for '{key}' must be 'asc' or 'desc'"
                    )
            else:
                # Allow passing SQLAlchemy ordering objects directly
                args += (direction,)

        if args:
            self.statement = self.statement.order_by(*args)
        return self

    def limit(self, count: int) -> "Query[ModelT]":
        """
        Limits the number of results returned by the query.

        ## Examples
        ```python
        User.limit(10).all()
        ```
        """
        self.statement = self.statement.limit(count)
        return self

    def offset(self, count: int) -> "Query[ModelT]":
        """
        Skips a given number of records before returning results.

        Useful for pagination.

        ## Examples
        ```python
        User.offset(20).limit(10).all()
        ```
        """
        self.statement = self.statement.offset(count)
        return self

    def distinct(self) -> "Query[ModelT]":
        """
        Returns only distinct/unique records.

        Removes duplicate rows from the result set.

        ## Examples
        ```python
        # Get unique users
        User.distinct().all()

        # Get distinct active users
        User.where(User.active == True).distinct().all()

        # Combined with other query methods
        User.distinct().order_by(User.name).limit(10).all()
        ```
        """
        self.statement = self.statement.distinct()
        return self

    def all(self) -> List[ModelT]:
        """
        Executes the query and returns all matching records as a list.

        ## Examples
        ```python
        users = User.where(User.active == True).all()
        ```
        """
        with Session(self.engine, expire_on_commit=False) as session:
            return list(session.exec(self.statement).all())

    def first(self) -> ModelT | None:
        """
        Executes the query and returns the first matching record.

        Returns `None` if no result is found.

        ## Examples
        ```python
        user = User.where(User.name == "Alice").first()
        ```
        """
        with Session(self.engine, expire_on_commit=False) as session:
            return cast(ModelT | None, session.exec(self.statement).first())

    def one(self) -> ModelT:
        """
        Executes the query and returns exactly one result.

        Raises an exception if no result or multiple results are found.

        ## Examples
        ```python
        user = User.where(User.email == "alice@example.com").one()
        ```
        """
        with Session(self.engine, expire_on_commit=False) as session:
            return cast(ModelT, session.exec(self.statement).one())

    def count(self) -> int:
        """
        Returns the number of records matching the current query.

        ## Examples
        ```python
        total = User.where(User.active == True).count()
        ```
        """
        with Session(self.engine) as session:
            count_statement: SelectOfScalar[int] = select(func.count()).select_from(
                self.statement.subquery()
            )
            return session.exec(count_statement).one()
