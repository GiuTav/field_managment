from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    da_hourly_cost = fields.Monetary(string="Farm Hourly Cost", currency_field="currency_id")
    da_cost_per_km = fields.Monetary(string="Farm Cost per Km", currency_field="currency_id")


class DAVehicleFuelLog(models.Model):
    _name = "da.vehicle.fuel.log"
    _description = "Vehicle Fuel and Odometer Log"
    _order = "date desc, id desc"

    vehicle_id = fields.Many2one("fleet.vehicle", required=True, ondelete="cascade", index=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    liters = fields.Float(required=True)
    total_cost = fields.Monetary(currency_field="currency_id")
    cost_per_liter = fields.Monetary(compute="_compute_cost_per_liter", currency_field="currency_id", store=True)
    odometer_value = fields.Float(required=True, string="Odometer (km)")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    supplier_id = fields.Many2one("res.partner")
    notes = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            self.env["fleet.vehicle.odometer"].create({
                "vehicle_id": record.vehicle_id.id,
                "date": record.date,
                "value": record.odometer_value,
            })
        return records

    @api.depends("liters", "total_cost")
    def _compute_cost_per_liter(self):
        for log in self:
            log.cost_per_liter = log.total_cost / log.liters if log.liters else 0.0


class DAVehicleMaintenancePlan(models.Model):
    _name = "da.vehicle.maintenance.plan"
    _description = "Vehicle Preventive Maintenance Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "next_due_date, vehicle_id, id"

    name = fields.Char(required=True, tracking=True)
    vehicle_id = fields.Many2one("fleet.vehicle", required=True, ondelete="cascade", tracking=True)
    responsible_user_id = fields.Many2one(
        "res.users", string="Maintenance Owner", default=lambda self: self.env.user, required=True
    )
    interval_days = fields.Integer(default=365)
    interval_km = fields.Float(default=10000.0)
    last_service_date = fields.Date(default=fields.Date.context_today)
    last_service_odometer = fields.Float()
    next_due_date = fields.Date(compute="_compute_due", store=True)
    next_due_odometer = fields.Float(compute="_compute_due", store=True)
    current_odometer = fields.Float(compute="_compute_current_odometer")
    due_status = fields.Selection(
        [("ok", "OK"), ("due_soon", "Due Soon"), ("due", "Due")],
        compute="_compute_status",
    )
    active = fields.Boolean(default=True)
    notes = fields.Text()

    @api.depends("last_service_date", "interval_days", "last_service_odometer", "interval_km")
    def _compute_due(self):
        for plan in self:
            plan.next_due_date = (
                fields.Date.add(plan.last_service_date, days=plan.interval_days)
                if plan.last_service_date and plan.interval_days
                else False
            )
            plan.next_due_odometer = plan.last_service_odometer + plan.interval_km if plan.interval_km else 0.0

    @api.depends("vehicle_id")
    def _compute_current_odometer(self):
        Odometer = self.env["fleet.vehicle.odometer"]
        for plan in self:
            reading = Odometer.search([("vehicle_id", "=", plan.vehicle_id.id)], order="date desc, id desc", limit=1)
            plan.current_odometer = reading.value if reading else 0.0

    @api.depends("next_due_date", "next_due_odometer", "current_odometer")
    def _compute_status(self):
        today = fields.Date.today()
        for plan in self:
            due_date = plan.next_due_date and plan.next_due_date <= today
            soon_date = plan.next_due_date and plan.next_due_date <= fields.Date.add(today, days=30)
            due_km = plan.next_due_odometer and plan.current_odometer >= plan.next_due_odometer
            soon_km = plan.next_due_odometer and plan.current_odometer >= plan.next_due_odometer - 500
            plan.due_status = "due" if due_date or due_km else "due_soon" if soon_date or soon_km else "ok"

    def action_mark_serviced(self):
        for plan in self:
            plan.write({
                "last_service_date": fields.Date.today(),
                "last_service_odometer": plan.current_odometer,
            })
            plan.activity_ids.action_done()

    @api.model
    def _cron_create_due_activities(self):
        activity_type = self.env.ref("mail.mail_activity_data_todo")
        for plan in self.search([("active", "=", True)]).filtered(lambda item: item.due_status in ("due", "due_soon")):
            summary = f"Maintenance: {plan.name}"
            duplicate = plan.activity_ids.filtered(
                lambda activity: activity.activity_type_id == activity_type and activity.summary == summary
            )
            if not duplicate:
                plan.activity_schedule(
                    activity_type_id=activity_type.id,
                    user_id=plan.responsible_user_id.id,
                    date_deadline=plan.next_due_date or fields.Date.today(),
                    summary=summary,
                    note=f"Vehicle: {plan.vehicle_id.display_name}; status: {plan.due_status}",
                )
