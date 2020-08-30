import datetime
from pathlib import Path

import pandas as pd


def read_file(filename):
    """Load in the different debts from a csv."""

    debts = pd.read_csv(filename, encoding="utf-8", skiprows=4, index_col="Name")
    debts = debts.replace("[^.0-9]", "", regex=True).astype(float)
    debts["Adjusted Payment"] = 0
    debts["Interest"] = 0

    inputs = pd.read_csv(filename, encoding="utf-8", nrows=1)
    inputs[inputs.columns[:1]] = (
        inputs[inputs.columns[:1]].replace("[^.0-9]", "", regex=True).astype(float)
    )

    totalfunds = inputs.loc[0, "Monthly Payment"]
    try:
        date = datetime.datetime.strptime(
            str(inputs.loc[0, "Start Date (YYYY-MM)"]), "%Y-%m"
        )
    except ValueError:
        date = datetime.date.today()
        print(
            "Invalid date format entered for Start Date. Must be YYYY-MM format. Using today's date instead."
        )

    strategy = inputs.loc[0, "Strategy (Avalanche or Snowball)"].lower()

    if strategy == "snowball":
        debts = debts.sort_values("Principal", ascending=True)
    else:
        debts = debts.sort_values("Rate", ascending=False)

    return debts, totalfunds, date


def compound_daily(date, principal, rate):
    """Calculate the principal and interest using daily compounding."""

    daysinyear = 366 if (pd.Period(f"{date}").is_leap_year) else 365
    dailyrate = (rate / 100) / daysinyear
    days = pd.Period(f"{date}").days_in_month

    new_principal = principal * (1 + dailyrate) ** days
    interest = new_principal - principal

    return new_principal, interest


def pay_minimums(principal, payment):
    """Make the minimum payments first."""

    if principal - payment <= 0:
        payment = principal
    return principal - payment, payment


def pay_excess(principal, minimum, remainder):
    """Pay any excess remaining after making minimum payments."""

    excess = remainder

    if principal - excess <= 0:
        excess = principal
        remainder = remainder - principal
    else:
        remainder = 0
    return principal - excess, minimum + excess, remainder


def update_schedule():
    path = Path(__file__).parent / "input.csv"
    debts, totalfunds, date = read_file(path)

    initial_date = date
    payments = debts[["Adjusted Payment"]].transpose()
    interest = debts[["Interest"]].transpose()

    while debts["Principal"].sum() > 0:
        if debts["Minimum Payment"].sum() > totalfunds:
            print("not enough for minimum monthly payments")
            break
        else:

            # Update the principal and paid interest using daily compounding
            debts["Principal"], debts["Interest"] = zip(
                *debts.apply(
                    lambda x: compound_daily(date, x["Principal"], x["Rate"]), axis=1,
                )
            )

            # If principal balance is zero, set it's payment to zero.
            debts["Minimum Payment"] = debts.apply(
                lambda x: 0 if x["Principal"] <= 0 else x["Minimum Payment"], axis=1
            )

            # Make minimum payments
            debts["Principal"], debts["Adjusted Payment"] = zip(
                *debts.apply(
                    lambda x: pay_minimums(x["Principal"], x["Minimum Payment"]), axis=1
                )
            )

            remainder = totalfunds - debts["Minimum Payment"].sum()

            # Make excess payments and update the adjusted payment amount
            for debt in debts.index:
                if debts.loc[debt, "Principal"] > 0:
                    (
                        debts.loc[debt, "Principal"],
                        debts.loc[debt, "Adjusted Payment"],
                        remainder,
                    ) = pay_excess(
                        debts.loc[debt, "Principal"],
                        debts.loc[debt, "Minimum Payment"],
                        remainder,
                    )

            payments = payments.append(debts[["Adjusted Payment"]].transpose())
            interest = interest.append(debts[["Interest"]].transpose())

        date = date + pd.DateOffset(months=1)

    payments.index = pd.date_range(
        start=initial_date, periods=len(payments), freq="M", name="Date"
    )

    # The initial payment row is set to zero.
    # Shift up one and drop the last row before writing to csv.
    payments = payments.shift(-1).drop(payments.tail(1).index)
    path = Path(__file__).parent / "payment_schedule.csv"
    payments.to_csv(
        path, index=True, header=True, encoding="utf-8", float_format="%.2f"
    )

    print()
    print(f"Debt Free: {payments.index[-1].strftime('%B %Y')}")
    print()
    print(f"Total Payments: {payments.values.sum():,.2f}")
    print(f"Total Principal: {payments.values.sum()-interest.values.sum():,.2f}")
    print(f"Total Interest: {interest.values.sum():,.2f}")
    print()
    print("payment_schedule.csv generated!")


if __name__ == "__main__":
    update_schedule()
