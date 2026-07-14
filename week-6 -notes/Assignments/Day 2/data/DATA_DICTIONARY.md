# Data Dictionary

## customers.csv

| Column | Type | Description |
|---|---|---|
| customer_id | string | Unique electricity customer ID |
| customer_name | string | Synthetic customer name |
| zone | string | Utility operating zone |
| connection_type | string | Residential, Commercial or Industrial |
| tariff_per_kwh | decimal | Billing rate per unit consumed |

## meter_readings.csv

| Column | Type | Description |
|---|---|---|
| reading_id | string | Unique meter-reading ID |
| reading_date | date string | Expected format: yyyy-MM-dd |
| customer_id | string | Customer reference |
| zone | string | Zone captured during reading |
| units_consumed | number | Electricity units consumed |
| meter_status | string | Meter condition |
| payment_status | string | PAID, PENDING or OVERDUE |

## outages.csv

| Column | Type | Description |
|---|---|---|
| outage_id | string | Unique outage ID |
| outage_date | date string | Expected format: yyyy-MM-dd |
| zone | string | Affected utility zone |
| duration_minutes | integer | Outage duration |
| affected_customers | integer | Estimated customers affected |
| cause | string | Outage cause |
| status | string | RESOLVED or IN_PROGRESS |
