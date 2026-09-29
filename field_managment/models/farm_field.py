from odoo import api, fields, models


class FarmField(models.Model):
    _name = "farm.field"
    _description = "Agricultural Field"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Owner / Farm")
    responsible_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    area_ha = fields.Float(string="Area (ha)", digits=(12, 4), tracking=True)
    soil_type = fields.Selection(
        [
            ("sandy", "Sandy"),
            ("clay", "Clay"),
            ("loam", "Loam"),
            ("volcanic", "Volcanic"),
            ("mixed", "Mixed"),
        ],
        default="mixed",
        tracking=True,
    )
    cultivation_method = fields.Selection(
        [
            ("conventional", "Conventional"),
            ("integrated", "Integrated Pest Management"),
            ("organic", "Organic"),
            ("dry_farming", "Dry Farming"),
        ],
        default="integrated",
        tracking=True,
    )
    latitude = fields.Float(digits=(10, 7))
    longitude = fields.Float(digits=(10, 7))
    irrigation_available = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
    notes = fields.Text()
    crop_cycle_ids = fields.One2many("farm.crop.cycle", "field_id", string="Crop Cycles")
    current_crop_cycle_id = fields.Many2one(
        "farm.crop.cycle",
        compute="_compute_current_crop_cycle_id",
        string="Current Crop Cycle",
    )
    crop_cycle_count = fields.Integer(compute="_compute_counts")
    field_log_count = fields.Integer(compute="_compute_counts")
    harvest_lot_count = fields.Integer(compute="_compute_counts")

    _sql_constraints = [
        ("farm_field_code_unique", "unique(code)", "The field code must be unique."),
    ]

    @api.depends("crop_cycle_ids.state")
    def _compute_current_crop_cycle_id(self):
        for field in self:
            field.current_crop_cycle_id = field.crop_cycle_ids.filtered(
                lambda cycle: cycle.state in ("planned", "active", "harvesting")
            )[:1]

    def _compute_counts(self):
        CropCycle = self.env["farm.crop.cycle"]
        FieldLog = self.env["farm.field.log"]
        HarvestLot = self.env["farm.harvest.lot"]
        for field in self:
            field.crop_cycle_count = CropCycle.search_count([("field_id", "=", field.id)])
            field.field_log_count = FieldLog.search_count([("field_id", "=", field.id)])
            field.harvest_lot_count = HarvestLot.search_count([("field_id", "=", field.id)])
