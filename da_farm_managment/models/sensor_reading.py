from odoo import fields, models


class DASensorReading(models.Model):
    _name = "da.sensor.reading"
    _description = "Agricultural Sensor Reading"
    _order = "measured_at desc, id desc"

    measured_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    field_id = fields.Many2one("farm.field", required=True, ondelete="cascade", index=True)
    crop_cycle_id = fields.Many2one("farm.crop.cycle", ondelete="set null", index=True)
    field_log_id = fields.Many2one("farm.field.log", ondelete="set null", index=True)
    sensor_code = fields.Char(required=True, index=True)
    source = fields.Selection(
        [("manual", "Manual"), ("api", "Sensor API"), ("import", "Import")],
        default="manual",
        required=True,
    )
    air_temperature = fields.Float(string="Air Temperature °C")
    soil_temperature = fields.Float(string="Soil Temperature °C")
    air_humidity = fields.Float(string="Air Humidity %")
    soil_moisture = fields.Float(string="Soil Moisture %")
    rainfall_mm = fields.Float(string="Rainfall (mm)")
    raw_payload = fields.Text(help="Optional raw payload retained for integration diagnostics.")
    notes = fields.Char()
