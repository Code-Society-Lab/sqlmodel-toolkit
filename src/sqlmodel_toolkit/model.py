from typing import Type
from sqlalchemy import Engine
from sqlmodel import inspect
from sqlmodel.main import SQLModelMetaclass
from sqlmodel import Session, SQLModel

from sqlmodel_toolkit.query import Query, ModelT


class _ModelMeta(SQLModelMetaclass):
    """
    Metaclass that enables class-level query delegation for models.

    It allows calling query methods directly on the model class
    (e.g. `User.where(...)` instead of `User.query().where(...)`).

    ## Examples
    ```python
    User.where(User.active == True).all()
    User.order_by(User.created_at.desc()).limit(5).all()
    ```
    """

    def __new__(cls, name, bases, namespace, **kwargs):
        """
        Initializes a new instance of the model.

        This method behaves like a regular class constructor,
        but exists explicitly here to avoid conflicts with query delegation.
        """
        if name != "Model":
            if "table" not in kwargs:
                kwargs["table"] = True
        return super().__new__(cls, name, bases, namespace, **kwargs)

    def __getattr__(cls, name: str):
        """
        Delegates missing class attributes or methods to the model's query object.

        When a method such as `where`, `order_by`, or `count` is not found on the model,
        this metaclass automatically forwards it to a `Query` instance.

        This allows expressive query syntax directly on the model.

        ## Examples
        ```python
        # Equivalent to: User.query().where(User.name == "Alice").first()
        user = User.where(User.name == "Alice").first()

        # Equivalent to: User.query().count()
        total = User.count()
        ```
        """
        if cls.__name__ == "Model":
            raise AttributeError(f"{name} not found on base Model class")

        if name.startswith("_") or name in {"get_engine", "set_engine", "query"}:
            raise AttributeError(name)

        query_instance = cls.query()
        if hasattr(query_instance, name):
            attr = getattr(query_instance, name)
            if callable(attr):

                def wrapper(*args, **kwargs):
                    return attr(*args, **kwargs)

                return wrapper
            return attr

        raise AttributeError(f"{cls.__name__} has no attribute '{name}'")


class Model(SQLModel, metaclass=_ModelMeta):
    _engine: Engine | None = None

    @classmethod
    def set_engine(cls, engine: Engine) -> None:
        """
        Sets the database engine used by the model.

        Must be called before performing any queries.

        ## Examples
        ```python
        from sqlmodel import create_engine
        engine = create_engine("sqlite:///db.sqlite3")
        User.set_engine(engine)
        ```
        """
        cls._engine = engine

    @classmethod
    def get_engine(cls) -> Engine:
        """
        Returns the engine currently associated with this model.

        Raises a `RuntimeError` if no engine has been set.

        ## Examples
        ```python
        engine = User.get_engine()
        ```
        """
        if cls._engine is None:
            raise RuntimeError(
                f"No session set for {cls.__name__}. Call Model.set_engine() first."
            )
        return cls._engine

    @classmethod
    def query(cls: Type[ModelT]) -> Query[ModelT]:
        """
        Returns a new query object for the model.

        Enables chaining methods such as `where`, `order_by`, `limit`, etc.

        ## Examples
        ```python
        User.query().where(User.active == True).order_by(User.created_at).all()
        ```
        """
        if cls.__name__ == "Model":
            raise RuntimeError("Cannot query the base Model class")
        return Query(cls)

    @classmethod
    def create(cls: Type[ModelT], **kwargs) -> ModelT:
        """
        Creates and saves a new record with the given attributes.

        ## Examples
        ```python
        User.create(name="Alice", email="alice@example.com")
        ```
        """
        instance = cls(**kwargs)
        return instance.save()

    def save(self: ModelT) -> ModelT:
        """
        Saves the current model instance to the database.

        Commits changes immediately and refreshes the instance.

        ## Examples
        ```python
        user = User(name="Alice")
        user.save()
        ```
        """
        with Session(self.get_engine(), expire_on_commit=False) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self

    def delete(self) -> None:
        """
        Deletes the current record from the database.

        ## Examples
        ```python
        user = User.find(1)
        user.delete()
        ```
        """
        with Session(self.get_engine()) as session:
            # Merge the instance into the session if it's detached
            instance = session.merge(self)
            session.delete(instance)
            session.commit()

    def update(self: ModelT, **kwargs) -> ModelT:
        """
        Updates the current instance with the given attributes
        and saves the changes to the database.

        ## Examples
        ```python
        user = User.find(1)
        user.update(name="Alice Smith", active=False)
        ```
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self.save()

    def reload(self: ModelT) -> ModelT:
        """
        Reloads the instance from the database, discarding any unsaved changes.

        Similar to ActiveRecord's reload method.

        ## Examples
        ```python
        user = User.find(1)
        user.name = "Changed"
        user.reload()  # Discards the change
        ```
        """
        mapper = inspect(self.__class__)
        pk_columns = mapper.primary_key

        if not pk_columns:
            raise ValueError(
                f"Cannot reload: {self.__class__.__name__} has no primary key"
            )

        # Get the primary key value(s)
        pk_values = []
        for pk_column in pk_columns:
            pk_value = getattr(self, pk_column.key, None)
            if pk_value is None:
                raise ValueError(
                    "Cannot reload an unsaved record (primary key is None)"
                )
            pk_values.append(pk_value)

        # For composite keys, use tuple; for single key, use scalar
        pk_identity = tuple(pk_values) if len(pk_values) > 1 else pk_values[0]

        with Session(self.get_engine(), expire_on_commit=False) as session:
            fresh = session.get(self.__class__, pk_identity)
            if not fresh:
                raise ValueError(f"Record no longer exists in database")

            # Copy all attributes from fresh instance
            for column_ in mapper.columns:
                setattr(self, column_.key, getattr(fresh, column_.key))

            return self
