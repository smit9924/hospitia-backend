# Reference data

Source files kept for reference. They are not loaded at runtime.

| File | Source | Content | Published |
|---|---|---|---|
| `iso_4217_currency_codes_list_one_by_www.six-group.com.xls` | [www.six-group.com](https://www.six-group.com/en/products-services/financial-information/market-reference-data/data-standards.html) (ISO 4217 Maintenance Agency) | ISO 4217 List One: current currency, fund and precious metal codes (entity, currency name, alphabetic code, numeric code, minor unit) | 2026-01-01 |

The `currency_units` seed migration takes its values from this file. Only a
subset of currencies is seeded; admins add any others through the app.
