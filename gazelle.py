import datetime
import os

import pandas as pd


def read_file(filename):
    """Load in the different debts from a csv."""

    inputs = pd.read_csv("input.csv", encoding="utf-8", nrows=1)
    debts = pd.read_csv("input.csv", encoding="utf-8", skiprows=4)

    debts["Adjusted Payment"] = 0
    debts["Interest"] = 0
    if inputs.loc[0, "Strategy (Avalanche or Snowball)"].lower() == "snowball":
        debts = debts.sort_values("Principal", ascending=True)
    else:
        debts = debts.sort_values("Rate", ascending=False)
    return debts


def you_got_debt():
    return 0 if debts["Principal"].sum() == 0 else 1


def debt_exists(index):
    return 0 if debts.loc[index, "Principal"] == 0 else 1


def insufficient_funds(totalfunds):
    return 1 if (debts["Payment"].sum()) > totalfunds else 0


def pay_minimums(index):
    """Make the minimum payments first."""

    principal = debts.loc[index, "Principal"]
    payment = debts.loc[index, "Payment"]

    if principal - payment < 0:
        payment = principal

    debts.loc[index, "Adjusted Payment"] = payment
    debts.loc[index, "Principal"] = debts.loc[index, "Principal"] - payment


def pay_excess(index, remainder):
    """Pay any excess remaining after making minimum payments."""

    principal = debts.loc[index, "Principal"]
    payment = remainder

    if principal - payment < 0:
        payment = principal
        remainder = remainder - principal
    else:
        remainder = 0

    debts.loc[index, "Adjusted Payment"] = (
        debts.loc[index, "Adjusted Payment"] + payment
    )
    debts.loc[index, "Principal"] = debts.loc[index, "Principal"] - payment

    return remainder


def update_principal(date):
    """Calculate the principal and interest using daily compounding."""

    for index, row in debts.iterrows():
        if debt_exists(index):
            daysinyear = 366 if (pd.Period("{}".format(date)).is_leap_year) else 365
            dailyrate = (debts.loc[index, "Rate"] / 100) / daysinyear
            days = pd.Period("{}".format(date)).days_in_month
            principal = debts.loc[index, "Principal"]
            debts.loc[index, "Principal"] = principal * (1 + dailyrate) ** days
            debts.loc[index, "Interest"] = (
                (principal * (1 + dailyrate) ** days)
            ) - principal


def make_payment(totalfunds):
    """ Apply a payment to the loan(s)

	First pay the minimum balances required,
	then apply any extra to either the highest interest (avalanche),
	or the lowest principal (snowball).
	"""

    remainder = totalfunds

    for index, row in debts.iterrows():
        if debt_exists(index):
            remainder = remainder - debts.loc[index, "Payment"]

    for index, row in debts.iterrows():
        if debt_exists(index):
            pay_minimums(index)
        else:
            debts.loc[index, "Adjusted Payment"] = 0

    for index, row in debts.iterrows():
        if debt_exists(index):
            remainder = pay_excess(index, remainder)
        else:
            debts.loc[index, "Adjusted Payment"] = 0


def get_monthly_payment():
    inputs = pd.read_csv("input.csv", encoding="utf-8", nrows=1)
    return inputs.loc[0, "Monthly Payment"]


def get_initial_date():
    inputs = pd.read_csv("input.csv", encoding="utf-8", nrows=1)
    date = inputs.loc[0, "Balance Date (yyyymm)"]
    if pd.isnull(date):
        return datetime.date.today()
    else:
        return datetime.datetime.strptime(str(date), "%Y%m")


def increment_date(date):
    """Increment the date to the next month."""

    date = date + pd.DateOffset(months=1)
    date = date.date()
    return date


def add_date_column(data):
    """Adds a date column to the DataFrame
	
	Skip the first row (the one with all of the debt names)
	and make the first column the date column.
	"""

    data["Date"] = pd.date_range(
        start=(get_initial_date()), periods=len(data), freq="MS"
    )
    data["Date"] = data["Date"].shift(1)
    data = data[["Date"] + [c for c in data if c not in ["Date"]]]

    return data


def update_schedule(totalfunds, date):
    """Update the payment schedule after payments were made."""

    payments = debts[["Name", "Adjusted Payment"]].transpose()
    interest = debts[["Name", "Interest"]].transpose()
    principal = debts[["Name", "Principal"]].transpose()

    while you_got_debt():
        if insufficient_funds(totalfunds):
            print("not enough for minimum monthly payments")
            break
        else:
            update_principal(date)
            make_payment(totalfunds)
            payments = payments.append(debts[["Adjusted Payment"]].transpose())
            principal = principal.append(debts[["Principal"]].transpose())
            interest = interest.append(debts[["Interest"]].transpose())
        date = increment_date(date)

    data = add_date_column(payments)
    data.to_csv("payment_schedule.csv", index=False, header=False, encoding="utf-8")

    data = add_date_column(principal)
    data.to_csv("principal.csv", index=False, header=False, encoding="utf-8")

    data = add_date_column(interest)
    data.to_csv("interest.csv", index=False, header=False, encoding="utf-8")


if __name__ == "__main__":

    filename = "input.csv"
    totalfunds = get_monthly_payment()
    date = get_initial_date()
    timetable = pd.DataFrame(columns=["Date"])

    debts = read_file(filename)
    update_schedule(totalfunds, date)
