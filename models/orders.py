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
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'date_order desc, id desc'
    order_sequence = fields.Char(string='waybill Number', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'))
    name = fields.Char(string="Reference ")
    description = fields.Text(string="Description")
    date_order = fields.Datetime(
        'Date', required=True,
        default=fields.Datetime.now)
    employee_id = fields.Many2one(
        'hr.employee', 'Driver', required=True,
        domain=[('driver', '=', True)])
    account_manger = fields.Many2one(
        'hr.employee', 'Account Manager', required=True,
        domain=[('account_manger', '=', True)])
    driver_factor_ids = fields.One2many(
        'tms.factor', 'waybill_id',
        string='Travel Driver Payment Factors',
        domain=[('category', '=', 'driver'), ])
    notes = fields.Html()
    partner_id = fields.Many2one(
        'res.partner', 'customer', required=True,
        domain=[('customer', '=', True)])
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)
    partner_order_id = fields.Many2one(
        'res.partner', 'Shipper', required=True,
        help="The name and address of the contact who requested the "
             "order or quotation.")
    sender_phone = fields.Char("Phone", required=True, change_default=True, readonly=True, copy=True)
    recevier_name = fields.Many2one(
        'res.partner', 'Recevier', required=True,
        help="Departure address for current Waybill.", change_default=True)
    recevier_phone = fields.Char(string="Phone", required=True, readonly=True, copy=True)
    upload_point = fields.Char(change_default=True)
    download_point = fields.Char(change_default=True)
    history = fields.Text()
    responsible_id = fields.Many2one('res.users',
                                     ondelete='set null', string="Data Entry", index=True,
                                     default=lambda self: self.env.user)
    def _get_default_require_signature(self):
        return self.env.company.portal_confirmation_sign
    signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True,
                             max_width=1024, max_height=1024)
    signed_by = fields.Char('Signed By', help='Name of the person that signed the SO.', copy=False)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    require_signature = fields.Boolean('Online Signature', default=_get_default_require_signature, readonly=True,
                                       states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
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
        ('invoiced', 'Invoiced'),
        ('sent', 'Sent'),
        ('cancel', 'Cancel'), ],
        string='Order Status', readonly=True, copy=False, default='draft')
    @api.model
    def create(self, vals):
        if vals.get('order_sequence', _('New')) == _('New'):
            vals['order_sequence'] = self.env['ir.sequence'].next_by_code('order.freights.sequence') or _('New')
            result = super(orders, self).create(vals)
            return result

    def has_to_be_signed(self, include_draft=False):
        return (self.state == 'sent' or (
                    self.state == 'draft' and include_draft)) and not self.is_expired and self.require_signature and not self.signature



    @api.onchange('partner_order_id')
    def onchange_partner_order_id(self):
        self.sender_phone = self.partner_order_id.phone

    @api.onchange('recevier_name')
    def onchange_recevier_name(self):
        self.recevier_phone = self.recevier_name.phone

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_order_id = self.partner_id.address_get(
                ['invoice', 'contact']).get('contact', False)

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
