import datetime
import os

import pandas as pd


def read_file(filename):
    """Load in the different debts from a csv."""

    inputs = pd.read_csv("input.csv", encoding="utf-8", nrows=1)
    debts = pd.read_csv("input.csv", encoding="utf-8", skiprows=4)
    debts.set_index("Name", inplace=True)

    debts["Adjusted Payment"] = 0
    debts["Interest"] = 0
    if inputs.loc[0, "Strategy (Avalanche or Snowball)"].lower() == "snowball":
        debts = debts.sort_values("Principal", ascending=True)
    else:
        debts = debts.sort_values("Rate", ascending=False)
    return debts


def debt_exists(index):
    return 0 if debts.loc[index, "Principal"] == 0 else 1


def pay_minimums(principal, payment):
    """Make the minimum payments first."""

    if principal - payment <= 0:
        payment = principal
    return principal - payment, payment


def pay_excess(principal, pay, remainder):
    """Pay any excess remaining after making minimum payments."""

    payment = remainder

    if principal - payment <= 0:
        payment = principal
        remainder = remainder - principal
    else:
        remainder = 0
    return principal - payment, pay + payment, remainder


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

    payments = debts[["Adjusted Payment"]].transpose()
    interest = debts[["Interest"]].transpose()
    principal = debts[["Principal"]].transpose()
    principal.columns = [loan for loan in principal.columns]

    while debts["Principal"].sum() > 0:
        if debts["Payment"].sum() > totalfunds:
            print("not enough for minimum monthly payments")
            break
        else:
            update_principal(date)

            # set necessary payments to zero
            debts["Payment"] = debts.apply(
                lambda x: 0 if x["Principal"] <= 0 else x["Payment"], axis=1
            )
            debts["Adjusted Payment"] = debts.apply(
                lambda x: 0 if x["Principal"] <= 0 else x["Payment"], axis=1
            )

            # pay mins
            debts["Principal"], debts["Adjusted Payment"] = zip(
                *debts.apply(
                    lambda x: pay_minimums(x["Principal"], x["Payment"]), axis=1
                )
            )

            # calculate remainder
            remainder = totalfunds - debts["Payment"].sum()

            # pay excess and update the adjusted payment amount
            for loan in debts.index:
                if debts.loc[loan, "Principal"] > 0:
                    (
                        debts.loc[loan, "Principal"],
                        debts.loc[loan, "Adjusted Payment"],
                        remainder,
                    ) = pay_excess(
                        debts.loc[loan, "Principal"],
                        debts.loc[loan, "Payment"],
                        remainder,
                    )

            # append
            payments = payments.append(debts[["Adjusted Payment"]].transpose())
            principal = principal.append(debts[["Principal"]].transpose())
            interest = interest.append(debts[["Interest"]].transpose())
        date = increment_date(date)

    data = add_date_column(payments)
    data.to_csv("payment_schedule.csv", index=False, header=True, encoding="utf-8")

    data = add_date_column(principal)
    data.to_csv("principal.csv", index=False, header=True, encoding="utf-8")

    data = add_date_column(interest)
    data.to_csv("interest.csv", index=False, header=True, encoding="utf-8")


if __name__ == "__main__":

    filename = "input.csv"
    totalfunds = get_monthly_payment()
    date = get_initial_date()
    timetable = pd.DataFrame(columns=["Date"])

    debts = read_file(filename)
    update_schedule(totalfunds, date)
