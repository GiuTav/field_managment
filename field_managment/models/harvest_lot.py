from odoo import api, fields, models


class FarmHarvestLot(models.Model):
    _name = "farm.harvest.lot"
    _description = "Harvest Lot"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, name"

    name = fields.Char(default="/", copy=False, readonly=True)
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    field_id = fields.Many2one("farm.field", required=True, ondelete="restrict", tracking=True)
    crop_cycle_id = fields.Many2one("farm.crop.cycle", required=True, ondelete="restrict", tracking=True)
    product_id = fields.Many2one(related="crop_cycle_id.product_id", store=True, readonly=True)
    quantity_kg = fields.Float(required=True, tracking=True)
    quality_grade = fields.Selection(
        [("a", "A"), ("b", "B"), ("processing", "Processing"), ("discard", "Discard")],
        default="processing",
        tracking=True,
    )
    destination = fields.Selection(
        [("fresh", "Fresh Sale"), ("processing", "Processing"), ("internal", "Internal Use")],
        default="processing",
        tracking=True,
    )
    operator_id = fields.Many2one("res.partner", string="Harvest Team / Operator")
    stock_lot_id = fields.Many2one("stock.lot", string="Stock Lot")
    traceability_url = fields.Char(compute="_compute_traceability_url")
    notes = fields.Text()
    processing_lot_ids = fields.Many2many(
        "farm.processing.lot",
        "farm_harvest_processing_rel",
        "harvest_lot_id",
        "processing_lot_id",
        string="Processing Lots",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("farm.harvest.lot") or "/"
        return super().create(vals_list)

    def _compute_traceability_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        for lot in self:
            lot.traceability_url = f"{base_url}/web#id={lot.id}&model=farm.harvest.lot&view_type=form" if lot.id else False
