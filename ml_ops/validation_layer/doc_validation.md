# AI Documentation Validation

This module validates AI-generated code against the project's documentation.

## Guidelines
- Compare generated queries with `/docs/` schemas and business rules.
- Flag discrepancies (e.g., `JOIN pedidos ON cliente_id` instead of `customer_id`).
