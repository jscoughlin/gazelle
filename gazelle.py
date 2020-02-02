import pandas as pd
import argparse
import datetime

parser = argparse.ArgumentParser(description='a debt payoff calculator that uses either the avalanche or snowball method')
parser.add_argument('-a','--amount', help='total $$$ that can be put towards debt each month (including the monthly minimum payments)', type=int, required=True)
parser.add_argument('-d','--date', help='date (yyyymm) you want to start implementing this (default is the current month and year)',
					default=datetime.date.today(),type=lambda s: datetime.datetime.strptime(s, '%Y%m').date(), required=False)
parser.add_argument('-m','--method', help='either "avalanche" or "snowball" (default is avalanche)', required=False)
args = vars(parser.parse_args())

def load_debts(filename, method):
	debts = pd.read_csv(filename, encoding = "ISO-8859-1")
	debts["Adjusted Payment"] = 0
	debts["Monthly Interest Accumulated"] = 0
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
	for index, row in debts.iterrows():
		if(debt_exists(index)):
			daysinyear = 366 if (pd.Period("{}".format(date)).is_leap_year) else 365
			dailyrate = (debts.loc[index,"Rate"] / 100) / daysinyear
			days = pd.Period("{}".format(date)).days_in_month
			principal = (debts.loc[index,"Principal"])
			debts.loc[index, "Principal"] = (principal * (1+dailyrate) ** days)
			debts.loc[index,"Monthly Interest Accumulated"] = ((principal * (1+dailyrate) ** days)) - principal

def make_payment(totalfunds):
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
	data["Date"] = pd.date_range(start=(args['date']), periods=len(data), freq='MS')
	data["Date"] = data["Date"].shift(1) #skip the first row (the one with all of the debt names)
	data = data[["Date"] + [c for c in data if c not in ["Date"]]] #make the first column the date column
	print(data.to_string(index=False, header=False))
	return data
	
def update_schedule(totalfunds, date):
	output_payments=debts[["Name","Adjusted Payment"]].transpose()
	output_interest=debts[["Name","Monthly Interest Accumulated"]].transpose()
	output_principal=debts[["Name","Principal"]].transpose()

	while(you_got_debt()):
		if(insufficient_funds(totalfunds)):
			print("not enough for minimum monthly payments")
			break
		else:
			update_principal(date)
			make_payment(totalfunds)
			output_payments = output_payments.append(debts[["Adjusted Payment"]].transpose())
			output_principal = output_principal.append(debts[["Principal"]].transpose())
			output_interest = output_interest.append(debts[["Monthly Interest Accumulated"]].transpose())
		date = increment_date(date)
		#print(debts.to_string(index=False, header=True)) # uncomment for a fun visual representation

	data = add_date_column(output_payments)
	data.to_csv("payment_schedule.csv", index = False, header=False, encoding = "ISO-8859-1")

	data = add_date_column(output_principal)
	data.to_csv("principal.csv", index = False, header=False, encoding = "ISO-8859-1")

	data = add_date_column(output_interest)
	data.to_csv("interest.csv", index = False, header=False, encoding = "ISO-8859-1")

if __name__ == '__main__':

	filename = 'input.csv'
	method = (args['method'])
	totalfunds = (args['amount'])
	date = (args['date'])
	timetable = pd.DataFrame(columns = ["Date"])

	debts = load_debts(filename, method)
	update_schedule(totalfunds, date)
