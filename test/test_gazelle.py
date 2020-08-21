import datetime
from pathlib import Path

import pandas as pd
import pytest

from gazelle import gazelle

d = {
    "Date": [
        "2020-05-31",
        "2020-06-30",
        "2020-07-31",
        "2020-08-31",
        "2020-09-30",
        "2020-10-31",
        "2020-11-30",
    ],
    "Example Car Loan": [3089.03, 3089.03, 3089.03, 3089.03, 622.68, 0.00, 0.00],
    "Example Student Loan 1": [84.94, 84.94, 84.94, 84.94, 2551.29, 3953.56, 240.41],
    "Example Student Loan 2": [46.44, 46.44, 46.44, 46.44, 46.44, 46.44, 2037.01],
    "Example Student Loan 3": [779.59, 779.59, 779.59, 779.59, 422.92, 0.00, 0.00],
}

expected = pd.DataFrame(data=d)


def test_compound_daily():
    date = datetime.datetime(2020, 11, 20)
    assert gazelle.compound_daily(
        date=date, principal=10000, rate=4.5
    ) == pytest.approx((10036.95, 36.95), abs=0.1,)

    date = datetime.datetime(2021, 11, 20)
    assert gazelle.compound_daily(
        date=date, principal=10000, rate=4.5
    ) == pytest.approx((10037.05, 37.05), abs=0.1)


def test_pay_minimums():
    assert gazelle.pay_minimums(principal=12, payment=2) == (10, 2)
    assert gazelle.pay_minimums(principal=10, payment=10) == (0, 10)
    assert gazelle.pay_minimums(principal=10, payment=20) == (0, 10)


def test_pay_excess():
    assert gazelle.pay_excess(principal=10, minimum=2, remainder=4) == (6, 6, 0)
    assert gazelle.pay_excess(principal=10, minimum=2, remainder=10) == (0, 12, 0)
    assert gazelle.pay_excess(principal=10, minimum=2, remainder=12) == (0, 12, 2)


@pytest.mark.integtest
def test_update_schedule():
    date = datetime.date(2020, 5, 8)
    gazelle.update_schedule(date)
    path = Path.cwd() / "gazelle" / "payment_schedule.csv"
    output = pd.read_csv(path, encoding="utf-8")
    assert expected.equals(output) == True
    path.unlink()
