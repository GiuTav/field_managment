from odoo import Command
from odoo.tests.common import TransactionCase


class TestDAFarmManagement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kg = cls.env.ref("uom.product_uom_kgm")
        cls.product = cls.env["product.product"].create({
            "name": "Test crop",
            "type": "consu",
            "is_storable": True,
            "tracking": "lot",
            "uom_id": cls.kg.id,
            "standard_price": 5.0,
            "da_gtin14": cls._gtin14("0801234567890"),
        })
        cls.field = cls.env["farm.field"].create({
            "name": "Test Field",
            "code": "TEST-FARM-01",
            "area_ha": 2.0,
            "cultivation_pattern": "mixed",
            "tenure_status": "rented",
        })
        cls.cycle = cls.env["farm.crop.cycle"].create({
            "name": "Test Cycle",
            "field_id": cls.field.id,
            "product_id": cls.product.id,
            "state": "done",
            "date_start": "2026-04-01",
        })

    @staticmethod
    def _gtin14(body):
        total = sum(int(digit) * (3 if index % 2 == 0 else 1) for index, digit in enumerate(reversed(body)))
        return body + str((10 - total % 10) % 10)

    def test_actual_cost_and_automatic_lot(self):
        employee = self.env["hr.employee"].create({"name": "Test Worker", "hourly_cost": 20.0})
        equipment = self.env["maintenance.equipment"].create({"name": "Test Tractor", "da_hourly_cost": 10.0})
        log = self.env["farm.field.log"].create({
            "field_id": self.field.id,
            "crop_cycle_id": self.cycle.id,
            "activity_type": "treatment",
            "product_id": self.product.id,
            "product_uom_id": self.kg.id,
            "quantity": 4.0,
            "labor_line_ids": [Command.create({"employee_id": employee.id, "hours": 2.0})],
            "machine_line_ids": [Command.create({
                "equipment_id": equipment.id,
                "usage_hours": 3.0,
                "hourly_cost": 10.0,
            })],
        })
        self.assertAlmostEqual(log.material_cost, 20.0)
        self.assertAlmostEqual(log.labor_cost, 40.0)
        self.assertAlmostEqual(log.machinery_cost, 30.0)
        self.assertAlmostEqual(log.da_actual_cost, 90.0)

        harvest = self.env["farm.harvest.lot"].create({
            "field_id": self.field.id,
            "crop_cycle_id": self.cycle.id,
            "quantity_kg": 100.0,
        })
        self.assertTrue(harvest.stock_lot_id)
        self.assertEqual(harvest.stock_lot_id.product_id, self.product)
        self.assertTrue(harvest.gs1_data.startswith("01"))
        self.assertIn("10", harvest.gs1_data)
        self.assertAlmostEqual(harvest.cost_per_kg, 0.9)

    def test_mixed_planting_and_sensor(self):
        line = self.env["da.farm.planting.line"].create({
            "crop_cycle_id": self.cycle.id,
            "product_id": self.product.id,
            "area_ha": 0.5,
            "plant_count": 2500,
        })
        self.assertEqual(line.density_plants_ha, 5000)
        reading = self.env["da.sensor.reading"].create({
            "field_id": self.field.id,
            "crop_cycle_id": self.cycle.id,
            "sensor_code": "SOIL-01",
            "soil_temperature": 21.5,
            "soil_moisture": 37.0,
        })
        self.assertEqual(reading.field_id, self.field)

    def test_vehicle_fuel_updates_odometer_and_plan(self):
        brand = self.env["fleet.vehicle.model.brand"].create({"name": "DA Test"})
        model = self.env["fleet.vehicle.model"].create({"name": "Tractor", "brand_id": brand.id})
        vehicle = self.env["fleet.vehicle"].create({"model_id": model.id, "license_plate": "TEST-FARM"})
        self.env["da.vehicle.fuel.log"].create({
            "vehicle_id": vehicle.id,
            "liters": 40.0,
            "total_cost": 72.0,
            "odometer_value": 1200.0,
        })
        plan = self.env["da.vehicle.maintenance.plan"].create({
            "name": "Oil change",
            "vehicle_id": vehicle.id,
            "interval_km": 1000.0,
            "last_service_odometer": 0.0,
            "interval_days": 0,
        })
        plan.invalidate_recordset(["current_odometer", "due_status"])
        self.assertEqual(plan.current_odometer, 1200.0)
        self.assertEqual(plan.due_status, "due")
