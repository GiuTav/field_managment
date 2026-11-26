from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    da_gtin14 = fields.Char(
        string="GS1 GTIN-14",
        size=14,
        copy=False,
        help="Fourteen numeric digits, including the GS1 check digit.",
    )

    @api.constrains("da_gtin14")
    def _check_da_gtin14(self):
        for product in self.filtered("da_gtin14"):
            gtin = product.da_gtin14
            if len(gtin) != 14 or not gtin.isdigit():
                raise ValidationError("GTIN-14 must contain exactly 14 digits.")
            body, expected = gtin[:-1], int(gtin[-1])
            total = sum(int(digit) * (3 if index % 2 == 0 else 1) for index, digit in enumerate(reversed(body)))
            check = (10 - total % 10) % 10
            if check != expected:
                raise ValidationError("The GTIN-14 check digit is invalid.")
