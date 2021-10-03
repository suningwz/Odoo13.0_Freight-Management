from odoo import fields, models

class partner_Freight(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
    customer = fields.Boolean("Customer", default=False)