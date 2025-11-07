from decimal import Decimal
import asyncio

from app import create_app
from app import crud
from app import batch_calc


def setup_accounts(session_factory, count=10):
    # disable email side-effects
    crud._dispatch_create_email = lambda account: None
    sess = session_factory()
    try:
        for i in range(1, count + 1):
            crud.create_account(sess, name=f"User{i}", number=f"U{i:03}", balance=Decimal(i * 10))
    finally:
        sess.close()


def test_total_balance_threaded():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    sf = app.session_factory
    setup_accounts(sf, count=7)  # balances 10,20,...,70 => total 280

    res = batch_calc.total_balance_in_batches_threaded(sf, batch_size=3, max_workers=3)
    assert isinstance(res, dict)
    assert abs(res["total"] - 280.0) < 1e-6
    assert res["batches"] == 3
    assert len(res["batch_sums"]) == 3


def test_total_balance_async():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    sf = app.session_factory
    setup_accounts(sf, count=5)  # 10+20+30+40+50 = 150

    res = asyncio.run(batch_calc.total_balance_in_batches_async(sf, batch_size=2, concurrency=2))
    assert isinstance(res, dict)
    assert abs(res["total"] - 150.0) < 1e-6
    assert res["batches"] == 3
    assert len(res["batch_sums"]) == 3