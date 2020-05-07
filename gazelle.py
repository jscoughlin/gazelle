import datetime

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


def pay_excess(principal, minimum, remainder):
    """Pay any excess remaining after making minimum payments."""

    excess = remainder

    if principal - excess <= 0:
        excess = principal
        remainder = remainder - principal
    else:
        remainder = 0
    return principal - excess, minimum + excess, remainder


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


def increment_date(date):
    """Increment the date to the next month."""

    return date + pd.DateOffset(months=1)


def update_schedule(totalfunds, date):
    """Update the payment schedule after payments were made."""

    payments = debts[["Adjusted Payment"]].transpose()
    interest = debts[["Interest"]].transpose()

    while debts["Principal"].sum() > 0:
        if debts["Minimum Payment"].sum() > totalfunds:
            print("not enough for minimum monthly payments")
            break
        else:
            update_principal(date)

            # If principal balance is zero, set it's payment to zero.
            debts["Minimum Payment"] = debts.apply(
                lambda x: 0 if x["Principal"] <= 0 else x["Minimum Payment"], axis=1
            )

            # pay mins
            debts["Principal"], debts["Adjusted Payment"] = zip(
                *debts.apply(
                    lambda x: pay_minimums(x["Principal"], x["Minimum Payment"]), axis=1
                )
            )

            # calculate remainder
            remainder = totalfunds - debts["Minimum Payment"].sum()

            # pay excess and update the adjusted payment amount
            for loan in debts.index:
                if debts.loc[loan, "Principal"] > 0:
                    (
                        debts.loc[loan, "Principal"],
                        debts.loc[loan, "Adjusted Payment"],
                        remainder,
                    ) = pay_excess(
                        debts.loc[loan, "Principal"],
                        debts.loc[loan, "Minimum Payment"],
                        remainder,
                    )

            payments = payments.append(debts[["Adjusted Payment"]].transpose())
            interest = interest.append(debts[["Interest"]].transpose())
        date = increment_date(date)

    payments.index = pd.date_range(
        start=(datetime.date.today()), periods=len(payments), freq="M", name="Date"
    )

    # The initial payment row is set to zero.
    # Shift up one and drop the last row before writing to csv.
    payments = payments.shift(-1).drop(payments.tail(1).index)
    payments.to_csv("payment_schedule.csv", index=True, header=True, encoding="utf-8")

    print()
    print(f"Total Time: {payments.index[-1]-payments.index[0]}")
    print(f"Total Payments: {payments.values.sum()}")
    print(f"Total Principal Payments: {payments.values.sum()-interest.values.sum()}")
    print(f"Total Interest Payments: {interest.values.sum()}")
    print()
    print("payment_schedule.csv generated!")


if __name__ == "__main__":

    filename = "input.csv"
    totalfunds = get_monthly_payment()
    date = datetime.date.today()
    timetable = pd.DataFrame(columns=["Date"])

    debts = read_file(filename)
    update_schedule(totalfunds, date)
