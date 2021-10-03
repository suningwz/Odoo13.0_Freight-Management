
from __future__ import division

import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)
try:
    from num2words import num2words
except ImportError:
    _logger.debug('Cannot `import num2words`.')

class orders(models.Model):
    _name = 'orders'
    _description = 'Ordes'
    _inherit = ['mail.thread', 'mail.activity.mixin','ir.sequence']
    _order = "id desc"
    name= fields.Char(string="Waybill Number ")
    sequence=fields.Char()
    description = fields.Text(string="Description")
    date_order = fields.Datetime(
        'Date', required=True,
        default=fields.Datetime.now)
    employee_id = fields.Many2one(
        'hr.employee', 'Driver', required=True ,
        domain=[('driver', '=', True)])
    driver_factor_ids = fields.One2many(
        'tms.factor', 'waybill_id',
        string='Travel Driver Payment Factors',
        domain=[('category', '=', 'driver'), ])
    notes = fields.Html()
    partner_id = fields.Many2one(
        'res.partner', required=True, change_default=True ,string="Customer",
        domain = [('customer', '=', True)])
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)
    partner_invoice_id = fields.Many2one(
        'res.partner', 'Invoice Address', required=True,
        help="Invoice address for current Waybill.")
    partner_order_id = fields.Many2one(
        'res.partner', 'Ordering Contact', required=True,
        help="The name and address of the contact who requested the "
             "order or quotation.")
    sender_phone = fields.Many2one(
        'res.partner', 'Phone', required=True,
        help="The name and address of the contact who requested the "
             "order or quotation.")
    Recevier_phone = fields.Many2one(
        'res.partner', 'Phone', required=True,
        help="The name and Recevier of the contact who requested the "
             "order or quotation.")
    departure_address_id = fields.Many2one(
        'res.partner', required=True,
        help="Departure address for current Waybill.", change_default=True)
    arrival_address_id = fields.Many2one(
        'res.partner', required=True,
        help="Arrival address for current Waybill.", change_default=True)
    upload_point = fields.Char(change_default=True)
    download_point = fields.Char(change_default=True)
    history = fields.Text()
    responsible_id = fields.Many2one('res.users',
                                     ondelete='set null', string="Salesman", index=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('in_stock', 'In Stock'),
        ('confirm', ' Confirm '),
        ('pending', ' Pending '),
        ('with_captain', ' with captain '),
        ('delivered', ' Delivered '),
        ('not_found', ' Not Found '),
        ('return', ' Return '),
        ('recived_money', 'Recived Money '),
        ('invoiced', ' Invoiced '),
        ('cancel', 'Cancel'),
    ], string='Order Status', readonly=True, copy=False, default='draft')

    @api.model
    def create(self, values):
        waybill = super(orders, self).create(values)
        waybill.sequence = waybill.next_by_id()
        return waybill
    def write(self, values):
        for rec in self:
            if 'partner_id' in values:
                for travel in rec.travel_ids:
                    travel.partner_ids = False
                    travel._compute_partner_ids()
            res = super(orders, self).write(values)
            return res
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.sender_phone:
            self.partner_phone = self.partner_id.sender_phone.id
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_order_id = self.partner_id.address_get(
                ['invoice', 'contact']).get('contact', False)
            self.partner_invoice_id = self.partner_id.address_get(
                ['invoice', 'contact']).get('invoice', False)
    def action_review(self):
        order_dreft = self.filtered(lambda s: s.state in ['draft'])
        return order_dreft.write({
            'state': 'review',
        })
    def action_in_stock(self):
        in_stock = self.filtered(lambda s: s.state in ['review'])
        return in_stock.write({
            'state': 'in_stock',
        })

    def action_confirm(self):
        confirm = self.filtered(lambda s: s.state in ['in_stock'])
        return confirm.write({
            'state': 'confirm',
        })

    def action_pending(self):
        pending = self.filtered(lambda s: s.state in ['in_stock'])
        return pending.write({
            'state': 'pending',
        })

    def action_new_date(self):
        new_date = self.filtered(lambda s: s.state in ['pending', 'not_found', 'return'])
        return new_date.write({
            'state': 'confirm',
        })

    def action_with_captain(self):
        with_captain = self.filtered(lambda s: s.state in ['confirm'])
        return with_captain.write({
            'state': 'with_captain',
        })

    def action_with_captain(self):
        with_captain = self.filtered(lambda s: s.state in ['confirm'])
        return with_captain.write({
            'state': 'with_captain',
        })

    def action_delivered(self):
        delivered = self.filtered(lambda s: s.state in ['with_captain'])
        return delivered.write({
            'state': 'delivered',
        })

    def action_not_found(self):
        not_found = self.filtered(lambda s: s.state in ['with_captain'])
        return not_found.write({
            'state': 'not_found',
        })

    def action_return(self):
        return_ = self.filtered(lambda s: s.state in ['with_captain'])
        return return_.write({
            'state': 'return',
        })

    def action_back(self):
        ordeer_back = self.filtered(lambda s: s.state in ['return'])
        return ordeer_back.write({
            'state': 'in_stock',
        })

    def action_recived_money(self):
        recived_money = self.filtered(lambda s: s.state in ['delivered'])
        return recived_money.write({
            'state': 'recived_money',
        })

    def action_invoiced(self):
        invoiced = self.filtered(lambda s: s.state in ['recived_money'])
        return invoiced.write({
            'state': 'invoiced',
        })

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_draft(self):
        courses = self.filtered(lambda s: s.state in ['cancel', 'draft'])
        return courses.write({
            'state': 'draft',
        })
