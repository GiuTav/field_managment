from odoo import api, fields, models


class FarmProcessingLot(models.Model):
    _name = "farm.processing.lot"
    _description = "Processing Lot"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, name"

    name = fields.Char(default="/", copy=False, readonly=True)
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    product_id = fields.Many2one("product.product", string="Finished Product", required=True, tracking=True)
    harvest_lot_ids = fields.Many2many(
        "farm.harvest.lot",
        "farm_harvest_processing_rel",
        "processing_lot_id",
        "harvest_lot_id",
        string="Source Harvest Lots",
    )
    input_qty_kg = fields.Float(compute="_compute_quantities", string="Input (kg)", store=True)
    output_qty = fields.Float(string="Output Quantity", tracking=True)
    output_uom = fields.Char(string="Output UoM", default="pcs")
    state = fields.Selection(
        [("draft", "Draft"), ("processing", "Processing"), ("done", "Done")],
        default="draft",
        tracking=True,
    )
    batch_note = fields.Text()
    consumer_story = fields.Text(
        string="Consumer Story",
        help="Short traceability text suitable for a QR code landing page or label.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("farm.processing.lot") or "/"
        return super().create(vals_list)

    @api.depends("harvest_lot_ids.quantity_kg")
    def _compute_quantities(self):
        for lot in self:
            lot.input_qty_kg = sum(lot.harvest_lot_ids.mapped("quantity_kg"))

    def action_processing(self):
        self.write({"state": "processing"})

    def action_done(self):
        self.write({"state": "done"})
