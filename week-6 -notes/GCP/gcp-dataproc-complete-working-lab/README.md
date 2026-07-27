# GCP Dataproc Food-Delivery ETL Lab

This package contains:

- `gcp-dataproc-complete-step-by-step-tutorial.html` — interactive trainer notes
- `orders.csv` — 15-row input dataset
- `food_delivery_etl.py` — PySpark ETL program
- `commands-windows-cmd.txt` — complete verified command sequence
- `cleanup-resources.cmd` — cleanup helper; edit placeholder values before running

## Environment

The commands are written for **Windows Command Prompt (cmd.exe)**.

Do not paste Linux backslash line continuations into Command Prompt. Use a caret (`^`) for CMD continuation, or keep the command on one line.

## Expected Output

The input has 15 rows. The ETL keeps 11 completed, positive-value, nonblank-city, unique orders.

The city report should show:

- Mumbai: 2 orders, 2030.00
- Bengaluru: 3 orders, 1550.00
- Pune: 2 orders, 1450.00
- Hyderabad: 2 orders, 1120.00
- Chennai: 2 orders, 1090.00

## Cost Safety

Delete the cluster immediately after the job. The cluster command also contains `--delete-max-idle=30m` as a safety net.
