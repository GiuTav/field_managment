"""Create demo data for the Field Management Diana 2.0 scenario.

Run from an Odoo shell:
    exec(open("scripts/setup_diana_demo.py", encoding="utf-8").read())
"""

from datetime import timedelta

from odoo import fields

today = fields.Date.context_today(env["res.users"].browse(env.uid))

Product = env["product.product"]
Partner = env["res.partner"]
Field = env["farm.field"]
Cycle = env["farm.crop.cycle"]
Log = env["farm.field.log"]
Harvest = env["farm.harvest.lot"]
Processing = env["farm.processing.lot"]

farm = Partner.search([("name", "=", "Diana 2.0")], limit=1)
if not farm:
    farm = Partner.create({"name": "Diana 2.0", "company_type": "company"})

datterino = Product.search([("name", "=", "Datterino arancione")], limit=1)
if not datterino:
    datterino = Product.create({"name": "Datterino arancione"})

passata = Product.search([("name", "=", "Passata di datterino arancione")], limit=1)
if not passata:
    passata = Product.create({"name": "Passata di datterino arancione"})

field = Field.search([("code", "=", "DIA-VL-01")], limit=1)
if not field:
    field = Field.create(
        {
            "name": "Campo Villa Literno - Datterino",
            "code": "DIA-VL-01",
            "partner_id": farm.id,
            "area_ha": 1.8,
            "soil_type": "sandy",
            "cultivation_method": "integrated",
            "irrigation_available": True,
            "notes": "Campo demo per raccontare tracciabilita, raccolta manuale e trasformazione entro poche ore.",
        }
    )

cycle = Cycle.search([("name", "=", "Datterino arancione 2026"), ("field_id", "=", field.id)], limit=1)
if not cycle:
    cycle = Cycle.create(
        {
            "name": "Datterino arancione 2026",
            "field_id": field.id,
            "product_id": datterino.id,
            "variety": "Datterino arancione",
            "state": "harvesting",
            "date_start": today - timedelta(days=95),
            "expected_harvest_date": today - timedelta(days=3),
            "target_qty_kg": 4200,
            "agronomic_note": "Ciclo demo con monitoraggio manuale, input a basso impatto e raccolta selettiva.",
            "sustainability_note": "Scenario pensato per valorizzare lotta integrata, uso consapevole dell'acqua e filiera corta.",
        }
    )

for vals in [
    {
        "activity_type": "sowing",
        "date": fields.Datetime.now() - timedelta(days=95),
        "reason": "Trapianto piantine selezionate",
        "notes": "Avvio ciclo colturale.",
    },
    {
        "activity_type": "inspection",
        "date": fields.Datetime.now() - timedelta(days=22),
        "weather": "sunny",
        "temperature": 29,
        "reason": "Controllo allegagione e stato vegetativo",
        "notes": "Piante uniformi, nessuna criticita rilevante.",
    },
    {
        "activity_type": "treatment",
        "date": fields.Datetime.now() - timedelta(days=10),
        "quantity": 3.5,
        "uom_name": "l",
        "is_natural_input": True,
        "withholding_days": 0,
        "reason": "Trattamento naturale preventivo",
        "notes": "Intervento compatibile con racconto di basso impatto.",
    },
    {
        "activity_type": "irrigation",
        "date": fields.Datetime.now() - timedelta(days=6),
        "quantity": 18,
        "uom_name": "mc",
        "reason": "Supporto idrico mirato",
        "notes": "Irrigazione localizzata.",
    },
]:
    existing = Log.search(
        [
            ("field_id", "=", field.id),
            ("crop_cycle_id", "=", cycle.id),
            ("activity_type", "=", vals["activity_type"]),
            ("reason", "=", vals["reason"]),
        ],
        limit=1,
    )
    if not existing:
        vals.update({"field_id": field.id, "crop_cycle_id": cycle.id, "state": "confirmed"})
        Log.create(vals)

harvest = Harvest.search([("name", "=", "DIA-HAR-2026-001")], limit=1)
if not harvest:
    harvest = Harvest.create(
        {
            "name": "DIA-HAR-2026-001",
            "date": today,
            "field_id": field.id,
            "crop_cycle_id": cycle.id,
            "quantity_kg": 380,
            "quality_grade": "processing",
            "destination": "processing",
            "notes": "Raccolta manuale demo destinata alla trasformazione entro poche ore.",
        }
    )

processing = Processing.search([("name", "=", "DIA-PRD-2026-001")], limit=1)
if not processing:
    Processing.create(
        {
            "name": "DIA-PRD-2026-001",
            "date": today,
            "product_id": passata.id,
            "harvest_lot_ids": [(6, 0, [harvest.id])],
            "output_qty": 720,
            "output_uom": "jars",
            "state": "done",
            "consumer_story": "Datterino arancione raccolto a mano e trasformato entro poche ore in una filiera tracciata dal campo al prodotto finito.",
            "batch_note": "Lotto demo per presentazione Diana 2.0.",
        }
    )

env.cr.commit()
print("Field Management Diana 2.0 demo data ready.")
