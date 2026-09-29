from odoo import api, fields, models


class FarmCropCycle(models.Model):
    _name = "farm.crop.cycle"
    _description = "Crop Cycle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, name"

    name = fields.Char(required=True, tracking=True)
    field_id = fields.Many2one("farm.field", required=True, ondelete="cascade", tracking=True)
    product_id = fields.Many2one("product.product", string="Crop / Variety", required=True, tracking=True)
    variety = fields.Char()
    state = fields.Selection(
        [
            ("planned", "Planned"),
            ("active", "Active"),
            ("harvesting", "Harvesting"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="planned",
        tracking=True,
    )
    date_start = fields.Date(string="Sowing / Transplant Date", tracking=True)
    expected_harvest_date = fields.Date(tracking=True)
    date_end = fields.Date(string="End Date", tracking=True)
    target_qty_kg = fields.Float(string="Expected Yield (kg)")
    harvested_qty_kg = fields.Float(compute="_compute_harvested_qty", string="Harvested (kg)", store=True)
    yield_kg_ha = fields.Float(compute="_compute_harvested_qty", string="Yield (kg/ha)", store=True)
    log_ids = fields.One2many("farm.field.log", "crop_cycle_id", string="Field Logs")
    harvest_lot_ids = fields.One2many("farm.harvest.lot", "crop_cycle_id", string="Harvest Lots")
    sustainability_note = fields.Text()
    agronomic_note = fields.Text()

    @api.depends("harvest_lot_ids.quantity_kg", "field_id.area_ha")
    def _compute_harvested_qty(self):
        for cycle in self:
            cycle.harvested_qty_kg = sum(cycle.harvest_lot_ids.mapped("quantity_kg"))
            cycle.yield_kg_ha = cycle.harvested_qty_kg / cycle.field_id.area_ha if cycle.field_id.area_ha else 0.0

    def action_start(self):
        self.write({"state": "active"})

    def action_harvesting(self):
        self.write({"state": "harvesting"})

    def action_done(self):
        self.write({"state": "done"})
