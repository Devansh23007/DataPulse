
# Olist Source Table Catalog

## 1. Customers
- Source: olist_customers_dataset.csv
- Candidate primary key: customer_id
- Grain: One row per customer record.
- Relationships: Orders reference customer_id.

## 2. Orders
- Source: olist_orders_dataset.csv
- Candidate primary key: order_id
- Grain: One row per order.
- Relationships: References customers; connects to items,
  payments, and reviews through order_id.

## 3. Order Items
- Source: olist_order_items_dataset.csv
- Candidate composite key: order_id + order_item_id
- Grain: One row per item within an order.
- Relationships: References orders and products; includes seller_id.

## 4. Order Payments
- Source: olist_order_payments_dataset.csv
- Candidate composite key: order_id + payment_sequential
- Grain: One row per payment record within an order.
- Relationships: References orders.

## 5. Order Reviews
- Source: olist_order_reviews_dataset.csv
- Candidate key: To be validated.
- Grain: One row per review record.
- Relationships: References orders through order_id.

## 6. Products
- Source: olist_products_dataset.csv
- Candidate primary key: product_id
- Grain: One row per product.
- Relationships: Referenced by order items.

## 7. Sellers
- Source: olist_sellers_dataset.csv
- Candidate primary key: seller_id
- Grain: One row per seller.
- Relationships: Referenced by order items.

## 8. Geolocation
- Source: olist_geolocation_dataset.csv
- Candidate primary key: No assumed unique key.
- Grain: One row per recorded geolocation entry.
- Relationships: ZIP code prefixes can relate to customer
  and seller locations, but are not necessarily unique.

## 9. Product Category Translation
- Source: product_category_name_translation.csv
- Candidate primary key: product_category_name
- Grain: One row per translated category mapping.
- Relationships: Relates product categories to English names.

## Validation status
All keys and relationships must be verified against the
actual source files before database constraints are applied.
