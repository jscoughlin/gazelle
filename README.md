# Gazelle

Calculate how long it'll take to pay off your debt. See how much interest you'll pay using the [Avalanche or Snowball](https://www.investopedia.com/articles/personal-finance/080716/debt-avalanche-vs-debt-snowball-which-best-you.asp) method.

<img src="./docs/gazelle-banner.svg">

# Usage

First, edit `gazelle/input.csv` to have your debts, strategy, etc. Then navigate with a terminal to the directory containing `gazelle.py` and run:

```python gazelle.py```

That's it! Gazelle will generate `payment_schedule.csv` showing how much you should pay each month. The total payments, principal, and interest will also be calculated and displayed in your terminal.

```
Debt Free: July 2021

Total Payments: 25,778.62
Total Principal: 25,321.16
Total Interest: 457.46

payment_schedule.csv generated!
```

# FAQ
**What makes this different from the [NerdWallet](https://www.nerdwallet.com/article/finance/what-is-a-debt-avalanche) [calculators](https://www.nerdwallet.com/article/finance/debt-snowball-calculator)?**

Those are good options and something you could use to verify what gazelle calculates! I wanted a method to do this without entering data into a web app over and over. I found using CSV files made this a little easier. The [vertex42 calculator](https://www.vertex42.com/Calculators/debt-reduction-calculator.html?utm_source=debt-reduction-calculator&utm_campaign=templates&utm_content=browse) uses a spreadsheet - however, it's limited to 10 different debts (unless you pay for their extended version). You can use gazelle with unlimited debt (yay?) for free (yay!)

**What type of compounding interest does gazelle use?**

Daily.

**What's the difference between "Minimum Payment" and "Monthly Payment"?**

Minimum Payment = minimum that must be paid for that specific debt. Monthly Payment = maximum, overall, amount that you can put towards all debts.

**It's not working for me 💔 How do I make it do the thing?**

The biggest gotcha here is that `input.csv` must be named `input.csv` and the column names ("Monthly Payment", "Principal", etc.) must not be renamed. Gazelle is looking for that specific file with those column names. Also do not delete the blank row before the "Name" row 😬

# License

Copyright (c) 2020 James Coughlin. Licensed under the [MIT License](https://opensource.org/licenses/MIT).