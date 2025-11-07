import pytest
from decimal import Decimal

from app import create_app
from app import crud
from app.exceptions import NotFoundError, DuplicateError


@pytest.fixture
def app_instance():
    # use in-memory sqlite for isolated tests
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    return app


@pytest.fixture
def session_factory(app_instance):
    return app_instance.session_factory


def test_crud_lifecycle(session_factory):
    # avoid sending real emails during tests
    crud._dispatch_create_email = lambda account: None

    sess = session_factory()
    try:
        # create
        acct = crud.create_account(sess, name="Alice", number="A001", balance=100)
        assert acct.id is not None
        assert acct.name == "Alice"
        assert acct.number == "A001"
        assert float(acct.balance) == 100.0

        # get by id
        got = crud.get_account_by_id(sess, acct.id)
        assert got.id == acct.id and got.number == "A001"

        # get by number
        got2 = crud.get_account_by_number(sess, "A001")
        assert got2.id == acct.id

        # update
        updated = crud.update_account(sess, acct.id, {"name": "Alice B", "balance": Decimal("200")})
        assert updated.name == "Alice B"
        assert float(updated.balance) == 200.0

        # creating another and attempting to set duplicate number -> DuplicateError
        acct2 = crud.create_account(sess, name="Bob", number="B001", balance=50)
        with pytest.raises(DuplicateError):
            crud.update_account(sess, acct2.id, {"number": "A001"})

        # delete + ensure not found
        crud.delete_account(sess, acct.id)
        with pytest.raises(NotFoundError):
            crud.get_account_by_id(sess, acct.id)
    finally:
        sess.close()