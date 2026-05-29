# Sample Datasets for DataTrust AI

This folder contains curated CSV sample data for local testing and demoing the DataTrust AI audit pipeline.

Included datasets:

- `customer_master.csv` — customer records with duplicate keys, missing emails, and invalid revenue fields.
- `sales_transactions.csv` — sales orders with mixed date formats, duplicate rows, negative totals, and excessive discounts.
- `hr_employees.csv` — employee records with termination/hire mismatches, duplicate employee IDs, salary outliers, and department inconsistencies.

Use these files with the frontend upload UI or by sending a multipart POST request to `http://localhost:8000/audit`.
