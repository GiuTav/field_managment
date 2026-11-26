from odoo import api, fields, models


class FarmCropCycle(models.Model):
    _inherit = "farm.crop.cycle"

    log_frequency = fields.Selection(
        [("daily", "Daily"), ("monthly", "Monthly summary")],
        default="daily",
        required=True,
        tracking=True,
    )
    planting_line_ids = fields.One2many(
        "da.farm.planting.line", "crop_cycle_id", string="Crops / Planting"
    )
    campaign_year = fields.Integer(compute="_compute_campaign_year", store=True)
    actual_cost = fields.Monetary(compute="_compute_actual_cost", currency_field="currency_id", store=True)
    cost_per_kg = fields.Monetary(compute="_compute_actual_cost", currency_field="currency_id", store=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)

    @api.depends("date_start")
    def _compute_campaign_year(self):
        for cycle in self:
            cycle.campaign_year = cycle.date_start.year if cycle.date_start else 0

    @api.depends("log_ids.da_actual_cost", "harvested_qty_kg")
    def _compute_actual_cost(self):
        for cycle in self:
            cycle.actual_cost = sum(cycle.log_ids.mapped("da_actual_cost"))
            cycle.cost_per_kg = cycle.actual_cost / cycle.harvested_qty_kg if cycle.harvested_qty_kg else 0.0
