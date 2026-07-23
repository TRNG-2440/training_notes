# E-commerce Dataset Data Dictionary

## customers.csv

| Column | Raw type | Intended Silver type | Description |
|---|---|---|---|
| customer_id | string | string | Customer business key in `C######` format |
| first_name | string | string | Given name |
| last_name | string | string | Family name |
| email | string | string | Customer email |
| phone | string | string | Phone number with inconsistent formatting |
| date_of_birth | string | date | Customer birth date |
| gender | string | string | M/F/Male/Female/Other variations |
| address | string | string | Street address |
| city | string | string | City with casing and spacing issues |
| state | string | string | State or province |
| country | string | string | Country with synonyms |
| postal_code | string | string | Postal or ZIP code |
| signup_date | string | date | Registration date |
| loyalty_tier | string | string | Bronze, Silver, Gold, or Platinum |
| is_active | string | boolean | Y/N, Yes/No, 1/0, true/false |

## products.csv

| Column | Raw type | Intended Silver type | Description |
|---|---|---|---|
| product_id | string | string | Product key in `P#####` format |
| product_name | string | string | Product name |
| category | string | string | Main product category |
| subcategory | string | string | Product subcategory |
| brand | string | string | Brand |
| unit_price | string | decimal(18,2) | Selling price |
| cost_price | string | decimal(18,2) | Product cost |
| stock_quantity | string | int | Available stock |
| supplier_id | string | string | Supplier key |
| product_rating | string | decimal(4,1) | Rating from 0 to 5 |
| created_date | string | date | Product creation date |
| is_active | string | boolean | Product active flag |

## orders.csv

| Column | Raw type | Intended Silver type | Description |
|---|---|---|---|
| order_id | string | string | Order key in `O########` format |
| customer_id | string | string | Customer reference |
| order_date | string | timestamp | Order timestamp in multiple formats |
| order_status | string | string | Placed, Pending, Processing, Shipped, Delivered, Cancelled, Returned |
| channel | string | string | Web, Mobile, Marketplace, Store |
| currency | string | string | INR, USD, or EUR |
| subtotal | string | decimal(18,2) | Value before discount and tax |
| discount_amount | string | decimal(18,2) | Order discount |
| tax_amount | string | decimal(18,2) | Tax |
| shipping_cost | string | decimal(18,2) | Shipping fee |
| total_amount | string | decimal(18,2) | Final amount |
| promo_code | string | string | Promotion code |
| shipping_city | string | string | Delivery city |
| shipping_state | string | string | Delivery state |
| shipping_country | string | string | Delivery country |
| last_updated | string | timestamp | Last source update timestamp |

## order_items.csv

| Column | Raw type | Intended Silver type | Description |
|---|---|---|---|
| order_item_id | string | string | Line key in `OI#########` format |
| order_id | string | string | Order reference |
| product_id | string | string | Product reference |
| quantity | string | int | Ordered quantity |
| unit_price | string | decimal(18,2) | Item price at purchase |
| discount_pct | string | decimal(5,2) | Line discount percentage |
| line_total | string | decimal(18,2) | Quantity × price after line discount |

## payments.csv

| Column | Raw type | Intended Silver type | Description |
|---|---|---|---|
| payment_id | string | string | Payment key |
| order_id | string | string | Order reference |
| payment_date | string | timestamp | Payment timestamp |
| payment_method | string | string | Card, UPI, Net Banking, Wallet, COD |
| payment_status | string | string | Success, Failed, Pending, Refunded |
| amount | string | decimal(18,2) | Payment amount |
| transaction_id | string | string | External transaction reference |

## shipments.csv

| Column | Raw type | Intended Silver type | Description |
|---|---|---|---|
| shipment_id | string | string | Shipment key |
| order_id | string | string | Order reference |
| shipment_date | string | date | Ship date |
| delivery_date | string | date | Delivery date |
| carrier | string | string | Logistics provider |
| tracking_number | string | string | Tracking number |
| shipment_status | string | string | Processing, In Transit, Delivered |
| shipping_cost | string | decimal(18,2) | Shipment cost |

## returns.csv

| Column | Raw type | Intended Silver type | Description |
|---|---|---|---|
| return_id | string | string | Return key |
| order_id | string | string | Order reference |
| product_id | string | string | Returned product |
| return_date | string | date | Return date |
| return_reason | string | string | Return reason |
| return_status | string | string | Requested, Approved, Refunded, Rejected |
| refund_amount | string | decimal(18,2) | Refund amount |
