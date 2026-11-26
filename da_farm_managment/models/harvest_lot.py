import re

from odoo import api, fields, models


def _gs1_lot_value(name):
    return re.sub(r"[^A-Za-z0-9._/-]", "", name or "")[:20]


class FarmHarvestLot(models.Model):
    _inherit = "farm.harvest.lot"

    allocated_cost = fields.Monetary(compute="_compute_da_cost", currency_field="currency_id", store=True)
    cost_per_kg = fields.Monetary(compute="_compute_da_cost", currency_field="currency_id", store=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    gs1_data = fields.Char(compute="_compute_gs1", store=True)
    gs1_human_readable = fields.Char(compute="_compute_gs1", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered(lambda lot: not lot.stock_lot_id):
            if record.product_id.tracking == "none":
                record.product_id.write({"tracking": "lot"})
            record.stock_lot_id = self.env["stock.lot"].create({
                "name": record.name,
                "product_id": record.product_id.id,
                "company_id": self.env.company.id,
            })
        return records

    @api.depends("crop_cycle_id.actual_cost", "crop_cycle_id.harvested_qty_kg", "quantity_kg")
    def _compute_da_cost(self):
        for lot in self:
            total_qty = lot.crop_cycle_id.harvested_qty_kg
            lot.cost_per_kg = lot.crop_cycle_id.actual_cost / total_qty if total_qty else 0.0
            lot.allocated_cost = lot.cost_per_kg * lot.quantity_kg

    @api.depends("name", "product_id.da_gtin14")
    def _compute_gs1(self):
        for lot in self:
            gtin, lot_value = lot.product_id.da_gtin14, _gs1_lot_value(lot.name)
            lot.gs1_data = f"01{gtin}10{lot_value}" if gtin and lot_value else False
            lot.gs1_human_readable = f"(01){gtin}(10){lot_value}" if gtin and lot_value else False


class FarmProcessingLot(models.Model):
    _inherit = "farm.processing.lot"

    stock_lot_id = fields.Many2one("stock.lot", string="Finished Stock Lot", copy=False)
    gs1_data = fields.Char(compute="_compute_gs1", store=True)
    gs1_human_readable = fields.Char(compute="_compute_gs1", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered(lambda lot: not lot.stock_lot_id):
            if record.product_id.tracking == "none":
                record.product_id.write({"tracking": "lot"})
            record.stock_lot_id = self.env["stock.lot"].create({
                "name": record.name,
                "product_id": record.product_id.id,
                "company_id": self.env.company.id,
            })
        return records

    @api.depends("name", "product_id.da_gtin14")
    def _compute_gs1(self):
        for lot in self:
            gtin, lot_value = lot.product_id.da_gtin14, _gs1_lot_value(lot.name)
            lot.gs1_data = f"01{gtin}10{lot_value}" if gtin and lot_value else False
            lot.gs1_human_readable = f"(01){gtin}(10){lot_value}" if gtin and lot_value else False
