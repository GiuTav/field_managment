from urllib.parse import quote

from odoo import api, fields, models


class FarmField(models.Model):
    _inherit = "farm.field"

    cultivation_pattern = fields.Selection(
        [("single", "Single crop"), ("mixed", "Mixed crops")],
        default="single",
        required=True,
        tracking=True,
    )
    tenure_status = fields.Selection(
        [
            ("owned", "Owned"),
            ("rented", "Rented"),
            ("managed", "Managed for third party"),
        ],
        default="owned",
        required=True,
        tracking=True,
    )
    landlord_id = fields.Many2one("res.partner", string="Owner / Landlord", tracking=True)
    lease_start = fields.Date(tracking=True)
    lease_end = fields.Date(tracking=True)
    annual_rent_cost = fields.Monetary(currency_field="currency_id", tracking=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    boundary_geojson = fields.Text(
        string="Boundary GeoJSON",
        help="GeoJSON polygon or multipolygon representing the field boundary.",
    )
    sensor_reading_ids = fields.One2many("da.sensor.reading", "field_id", string="Sensor Readings")
    total_harvested_kg = fields.Float(compute="_compute_history", store=True)
    average_yield_kg_ha = fields.Float(compute="_compute_history", store=True)
    completed_cycle_count = fields.Integer(compute="_compute_history", store=True)

    @api.depends(
        "crop_cycle_ids.state",
        "crop_cycle_ids.harvested_qty_kg",
        "crop_cycle_ids.yield_kg_ha",
    )
    def _compute_history(self):
        for field in self:
            completed = field.crop_cycle_ids.filtered(lambda cycle: cycle.state == "done")
            field.completed_cycle_count = len(completed)
            field.total_harvested_kg = sum(completed.mapped("harvested_qty_kg"))
            yields = completed.filtered(lambda cycle: cycle.yield_kg_ha).mapped("yield_kg_ha")
            field.average_yield_kg_ha = sum(yields) / len(yields) if yields else 0.0

    def action_open_da_map(self):
        self.ensure_one()
        if self.boundary_geojson:
            payload = quote(self.boundary_geojson, safe="")
            url = f"https://geojson.io/#data=data:application/json,{payload}"
        else:
            url = f"https://www.openstreetmap.org/?mlat={self.latitude}&mlon={self.longitude}#map=16/{self.latitude}/{self.longitude}"
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}


class FarmPlantingLine(models.Model):
    _name = "da.farm.planting.line"
    _description = "Farm Planting Line"
    _order = "crop_cycle_id, sequence, id"

    sequence = fields.Integer(default=10)
    crop_cycle_id = fields.Many2one("farm.crop.cycle", required=True, ondelete="cascade")
    field_id = fields.Many2one(related="crop_cycle_id.field_id", store=True)
    product_id = fields.Many2one("product.product", string="Crop", required=True)
    variety = fields.Char()
    area_ha = fields.Float(string="Allocated Area (ha)", digits=(12, 4))
    plant_count = fields.Integer()
    sowing_quantity_kg = fields.Float(string="Sowing Quantity (kg)")
    density_plants_ha = fields.Float(compute="_compute_density", store=True)
    notes = fields.Char()

    @api.depends("plant_count", "area_ha")
    def _compute_density(self):
        for line in self:
            line.density_plants_ha = line.plant_count / line.area_ha if line.area_ha else 0.0
