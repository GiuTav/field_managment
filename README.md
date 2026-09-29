# Field Management for Odoo

Reusable Odoo module for farms and agri-food producers that need to manage fields, crop cycles, field logs, harvest lots and traceability from field to finished product.

## Main Features

- Field registry with area, soil, coordinates, responsible user and cultivation method.
- Crop cycles linked to fields and products/varieties.
- Field log for sowing, treatments, irrigation, fertilization, inspections, soil work and harvest notes.
- Withholding period calculation for treatments.
- Harvest lots with quantity, quality grade, destination and stock lot reference.
- Processing lots that connect harvested raw material to finished products.
- Chatter and activities on operational records.

## Demo Positioning

For Diana 2.0 or similar customers, the demo should tell the story of a controlled agri-food chain:

1. Create the field.
2. Start a crop cycle.
3. Register agronomic activities in the field log.
4. Record a hand harvest.
5. Transform the harvest lot into a finished product batch.
6. Show complete traceability from finished product back to field activities.

## Technical Notes

- Target Odoo version: 19.0.
- Addon path: `field_managment`.
- Core dependencies: `base`, `mail`, `product`, `stock`.
- Demo-specific customer data should stay outside the addon, in scripts or demo fixtures.
