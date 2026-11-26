from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FarmFieldLog(models.Model):
    _inherit = "farm.field.log"

    registration_period = fields.Selection(
        [("daily", "Daily"), ("monthly", "Monthly summary")],
        default="daily",
        required=True,
        tracking=True,
    )
    period_start = fields.Date()
    period_end = fields.Date()
    product_uom_id = fields.Many2one("uom.uom", string="Product UoM")
    labor_line_ids = fields.One2many("da.field.log.labor", "field_log_id", string="Labor")
    machine_line_ids = fields.One2many("da.field.log.machine", "field_log_id", string="Machinery")
    sensor_reading_ids = fields.One2many("da.sensor.reading", "field_log_id", string="Sensor Readings")
    material_cost = fields.Monetary(compute="_compute_da_costs", currency_field="currency_id", store=True)
    labor_cost = fields.Monetary(compute="_compute_da_costs", currency_field="currency_id", store=True)
    machinery_cost = fields.Monetary(compute="_compute_da_costs", currency_field="currency_id", store=True)
    other_actual_cost = fields.Monetary(currency_field="currency_id")
    da_actual_cost = fields.Monetary(
        string="Actual Total Cost", compute="_compute_da_costs", currency_field="currency_id", store=True
    )

    @api.onchange("product_id")
    def _onchange_da_product_uom(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    @api.constrains("registration_period", "period_start", "period_end")
    def _check_period(self):
        for log in self:
            if log.period_start and log.period_end and log.period_end < log.period_start:
                raise ValidationError("The period end cannot precede the period start.")

    @api.depends(
        "product_id",
        "product_id.standard_price",
        "product_id.uom_id",
        "product_uom_id",
        "quantity",
        "labor_line_ids.total_cost",
        "machine_line_ids.total_cost",
        "other_actual_cost",
    )
    def _compute_da_costs(self):
        for log in self:
            quantity = log.quantity
            if log.product_id and log.product_uom_id:
                quantity = log.product_uom_id._compute_quantity(quantity, log.product_id.uom_id)
            log.material_cost = log.product_id.standard_price * quantity if log.product_id else 0.0
            log.labor_cost = sum(log.labor_line_ids.mapped("total_cost"))
            log.machinery_cost = sum(log.machine_line_ids.mapped("total_cost"))
            log.da_actual_cost = (
                log.material_cost + log.labor_cost + log.machinery_cost + log.other_actual_cost
            )


class DAFieldLogLabor(models.Model):
    _name = "da.field.log.labor"
    _description = "Field Log Labor Cost"
    _order = "id"

    field_log_id = fields.Many2one("farm.field.log", required=True, ondelete="cascade", index=True)
    employee_id = fields.Many2one("hr.employee", required=True)
    hours = fields.Float(required=True, default=1.0)
    hourly_cost = fields.Monetary(required=True, currency_field="currency_id")
    total_cost = fields.Monetary(compute="_compute_total", currency_field="currency_id", store=True)
    currency_id = fields.Many2one(related="field_log_id.currency_id", store=True)
    notes = fields.Char()

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        if self.employee_id:
            self.hourly_cost = self.employee_id.hourly_cost

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("employee_id") and not vals.get("hourly_cost"):
                vals["hourly_cost"] = self.env["hr.employee"].browse(vals["employee_id"]).hourly_cost
        return super().create(vals_list)

    @api.depends("hours", "hourly_cost")
    def _compute_total(self):
        for line in self:
            line.total_cost = line.hours * line.hourly_cost


class DAFieldLogMachine(models.Model):
    _name = "da.field.log.machine"
    _description = "Field Log Machinery Cost"
    _order = "id"

    field_log_id = fields.Many2one("farm.field.log", required=True, ondelete="cascade", index=True)
    equipment_id = fields.Many2one("maintenance.equipment")
    vehicle_id = fields.Many2one("fleet.vehicle")
    usage_hours = fields.Float(string="Hours")
    distance_km = fields.Float(string="Distance (km)")
    hourly_cost = fields.Monetary(currency_field="currency_id")
    cost_per_km = fields.Monetary(currency_field="currency_id")
    rental_cost = fields.Monetary(currency_field="currency_id")
    total_cost = fields.Monetary(compute="_compute_total", currency_field="currency_id", store=True)
    currency_id = fields.Many2one(related="field_log_id.currency_id", store=True)
    notes = fields.Char()

    @api.onchange("equipment_id", "vehicle_id")
    def _onchange_asset(self):
        if self.equipment_id:
            self.hourly_cost = self.equipment_id.da_hourly_cost
        elif self.vehicle_id:
            self.hourly_cost = self.vehicle_id.da_hourly_cost
            self.cost_per_km = self.vehicle_id.da_cost_per_km

    @api.constrains("equipment_id", "vehicle_id")
    def _check_asset(self):
        for line in self:
            if not line.equipment_id and not line.vehicle_id:
                raise ValidationError("Select either machinery or a vehicle.")
            if line.equipment_id and line.vehicle_id:
                raise ValidationError("Select only one asset per cost line.")

    @api.depends("usage_hours", "distance_km", "hourly_cost", "cost_per_km", "rental_cost")
    def _compute_total(self):
        for line in self:
            line.total_cost = (
                line.usage_hours * line.hourly_cost
                + line.distance_km * line.cost_per_km
                + line.rental_cost
            )


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    da_hourly_cost = fields.Monetary(string="Farm Hourly Cost", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
