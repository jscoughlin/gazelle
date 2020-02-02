import pandas as pd
import argparse
import datetime
import matplotlib.pyplot as plt
from matplotlib import style
import os

parser = argparse.ArgumentParser(
	description="a debt payoff calculator"
)
parser.add_argument('-a','--amount', 
	help="monthly amount that can be put towards debt",
 	type=int, required=True
)
parser.add_argument('-d','--date', 
	help="start date in yyyymm, " 
	"(default is the current month and year)",
	default=datetime.date.today(),
	type=lambda s: datetime.datetime.strptime(s, '%Y%m').date(), 
	required=False
)
parser.add_argument('-m','--method', 
	help="either 'avalanche' or 'snowball', " 
	"(default is avalanche)", type = str.lower, required=False
)
args = vars(parser.parse_args())


def load_debts(filename, method):
	debts = pd.read_csv(filename, encoding = "ISO-8859-1")
	debts["Adjusted Payment"] = 0
	debts["Interest"] = 0
	if method == "snowball":
		debts = debts.sort_values("Principal",ascending=True)
	else:
		debts = debts.sort_values("Rate",ascending=False)
	return debts


def you_got_debt():
	return 0 if debts["Principal"].sum() == 0 else 1


def debt_exists(index):
	return 0 if debts.loc[index, "Principal"] == 0 else 1


def insufficient_funds(totalfunds):
	return 1 if (debts["Payment"].sum()) > totalfunds else 0


def pay_minimums(index):
	principal = (debts.loc[index,"Principal"])
	payment = (debts.loc[index,"Payment"])
	
	if(principal - payment < 0):
		payment = principal

	debts.loc[index,"Adjusted Payment"] = payment
	debts.loc[index, "Principal"] = debts.loc[index, "Principal"] - payment


def pay_excess(index, remainder):
	principal = (debts.loc[index,"Principal"])
	payment = remainder
	
	if(principal - payment < 0):
		payment = principal
		remainder = remainder - principal
	else:
		remainder = 0

	debts.loc[index,"Adjusted Payment"] = debts.loc[index,"Adjusted Payment"] + payment
	debts.loc[index, "Principal"] = debts.loc[index, "Principal"] - payment

	return remainder


def update_principal(date):
	# Calculate the updated principal and interest paid
	# using daily interest compounding.
	for index, row in debts.iterrows():
		if(debt_exists(index)):
			daysinyear = 366 if (pd.Period("{}".format(date)).is_leap_year) else 365
			dailyrate = (debts.loc[index,"Rate"] / 100) / daysinyear
			days = pd.Period("{}".format(date)).days_in_month
			principal = (debts.loc[index,"Principal"])
			debts.loc[index, "Principal"] = (principal * (1+dailyrate) ** days)
			debts.loc[index,"Interest"] = ((principal * (1+dailyrate) ** days)) - principal


def make_payment(totalfunds):
	# First pay the minimum balances required,
	# then apply any extra to either the highest interest (avalanche),
	# or the lowest principal (snowball).
	remainder = totalfunds

	for index, row in debts.iterrows():
		if(debt_exists(index)):
			remainder = remainder - debts.loc[index,"Payment"]

	for index, row in debts.iterrows():
		if(debt_exists(index)):
			pay_minimums(index)
		else:
			debts.loc[index,"Adjusted Payment"] = 0

	for index, row in debts.iterrows():
		if(debt_exists(index)):
			remainder = pay_excess(index, remainder)
		else:
			debts.loc[index,"Adjusted Payment"] = 0


def increment_date(date):
	date = date + pd.DateOffset(months=1)
	date = date.date()
	return date


def add_date_column(data):
	# Skip the first row (the one with all of the debt names)
	# and make the first column the date column.
	data["Date"] = pd.date_range(start=(args['date']), 
								periods=len(data), freq='MS')
	data["Date"] = data["Date"].shift(1)
	data = data[["Date"] + [c for c in data if c not in ["Date"]]]
	
	return data
	

def update_schedule(totalfunds, date):
	payments=debts[["Name","Adjusted Payment"]].transpose()
	interest=debts[["Name","Interest"]].transpose()
	principal=debts[["Name","Principal"]].transpose()

	while(you_got_debt()):
		if(insufficient_funds(totalfunds)):
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
	data.to_csv("payment_schedule.csv", index = False, 
				header=False, encoding = "ISO-8859-1")

	data = add_date_column(principal)
	data.to_csv("principal.csv", index = False, 
				header=False, encoding = "ISO-8859-1")

	data = add_date_column(interest)
	data.to_csv("interest.csv", index = False, 
				header=False, encoding = "ISO-8859-1")


def show_results(method):
	principal = pd.read_csv("principal.csv", parse_dates=[0], 
							index_col=0, encoding = "ISO-8859-1")
	interest = pd.read_csv("interest.csv", parse_dates=[0], 
							index_col=0, encoding = "ISO-8859-1")
	payments = pd.read_csv("payment_schedule.csv", parse_dates=[0], 
							index_col=0, encoding = "ISO-8859-1")

	style.use('ggplot')

	if(method == "snowball"):
		ax = principal.plot(figsize=(8.0, 5.0),
			title="Individual Principal vs. Time (Snowball)")
	else:
		ax = principal.plot(figsize=(8.0, 5.0),
			title="Individual Principal vs. Time (Avalanche)")
	ax.set_xlabel('Time (Years)')
	ax.set_ylabel('Principal')
	ax.get_legend().remove()

	plt.savefig('principal-vs-time.png')

	if(method == "snowball"):
		ax = interest.plot(figsize=(8.0, 5.0), 
			title="Individual Interest vs. Time (Snowball)")
	else:
		ax = interest.plot(figsize=(8.0, 5.0),
			title="Individual Interest vs. Time (Avalanche)")
	ax.set_xlabel('Time (Years)')
	ax.set_ylabel('Interest')
	ax.get_legend().remove()

	plt.savefig('interest-vs-time.png')

	for index, row in payments.iterrows():
		interest.loc[index,'Sum'] = interest.loc[index].sum(axis=0)
		payments.loc[index,'Sum'] = payments.loc[index].sum(axis=0) - interest.loc[index,'Sum']
	start = interest.index[0]
	end = index

	ax = interest.plot(y='Sum')

	if(method == "snowball"):
		payments.plot(figsize=(8.0, 5.0),
			y='Sum',title="Payments vs. Time (Snowball)", ax=ax)
	else:
		payments.plot(figsize=(8.0, 5.0),
			y='Sum',title="Payments vs. Time (Avalanche)", ax=ax)
	ax.legend(["Interest", "Principal"]);
	ax.set_xlabel('Time (Years)')
	ax.set_ylabel('Payment')

	plt.savefig('payments-vs-time.png')

	print("Total Time: {}".format(end-start))
	print("Total Interest Payments: {}".format(interest['Sum'].sum()))
	print("Total Principal Payments: {}".format(payments['Sum'].sum()))
	print("Total Payments: {}".format(interest['Sum'].sum()+payments['Sum'].sum()))

	os.remove('principal.csv')
	os.remove('interest.csv')


if __name__ == '__main__':

	filename = 'input.csv'
	method = (args['method'])
	totalfunds = (args['amount'])
	date = (args['date'])
	timetable = pd.DataFrame(columns = ["Date"])

	debts = load_debts(filename, method)
	update_schedule(totalfunds, date)
	show_results(method)
