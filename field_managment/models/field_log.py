from odoo import api, fields, models


class FarmFieldLog(models.Model):
    _name = "farm.field.log"
    _description = "Field Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(default="/", copy=False, readonly=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True, tracking=True)
    field_id = fields.Many2one("farm.field", required=True, ondelete="cascade", tracking=True)
    crop_cycle_id = fields.Many2one("farm.crop.cycle", string="Crop Cycle", tracking=True)
    activity_type = fields.Selection(
        [
            ("sowing", "Sowing / Transplant"),
            ("treatment", "Treatment"),
            ("irrigation", "Irrigation"),
            ("fertilization", "Fertilization"),
            ("inspection", "Inspection"),
            ("weeding", "Weeding"),
            ("harvest", "Harvest"),
            ("soil_work", "Soil Work"),
            ("other", "Other"),
        ],
        required=True,
        default="inspection",
        tracking=True,
    )
    operator_id = fields.Many2one("res.partner", string="Operator")
    product_id = fields.Many2one("product.product", string="Input / Product")
    quantity = fields.Float()
    uom_name = fields.Char(string="Unit of Measure")
    weather = fields.Selection(
        [
            ("sunny", "Sunny"),
            ("cloudy", "Cloudy"),
            ("rain", "Rain"),
            ("wind", "Wind"),
            ("hot", "Hot"),
        ]
    )
    temperature = fields.Float(string="Temperature C")
    reason = fields.Char()
    withholding_days = fields.Integer(string="Withholding Period (days)")
    allowed_harvest_date = fields.Date(compute="_compute_allowed_harvest_date", store=True)
    is_natural_input = fields.Boolean(string="Natural / Low Impact Input")
    cost_estimate = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    notes = fields.Text()
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        default="draft",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("farm.field.log") or "/"
        return super().create(vals_list)

    @api.depends("date", "withholding_days")
    def _compute_allowed_harvest_date(self):
        for log in self:
            log.allowed_harvest_date = fields.Date.add(log.date.date(), days=log.withholding_days) if log.date else False

    def action_confirm(self):
        self.write({"state": "confirmed"})
