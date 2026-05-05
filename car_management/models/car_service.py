from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CarService(models.Model):
    _name = 'car.service'
    _description = 'Car Service Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, id desc'

    name = fields.Char(
        string='Service Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        readonly=True,
    )
    vehicle_id = fields.Many2one(
        'car.vehicle',
        string='Vehicle',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
    )
    brand_id = fields.Many2one(
        related='vehicle_id.brand_id', string='Brand', store=True, readonly=True
    )
    service_date = fields.Date(
        string='Service Date', required=True, default=fields.Date.today, tracking=True
    )
    service_type = fields.Selection(
        selection=[
            ('oil_change', 'Oil Change'),
            ('tire_rotation', 'Tire Rotation / Replacement'),
            ('brake_service', 'Brake Service'),
            ('battery', 'Battery Replacement'),
            ('transmission', 'Transmission Service'),
            ('engine', 'Engine Repair'),
            ('ac', 'A/C Service'),
            ('electrical', 'Electrical'),
            ('bodywork', 'Bodywork / Paint'),
            ('inspection', 'General Inspection'),
            ('other', 'Other'),
        ],
        string='Service Type',
        required=True,
        default='inspection',
        tracking=True,
    )
    mileage_at_service = fields.Float(
        string='Mileage at Service (km)', digits=(10, 2), tracking=True
    )
    technician = fields.Char(string='Technician / Garage')
    cost = fields.Float(string='Total Cost', digits=(12, 2), tracking=True)
    description = fields.Text(string='Description / Work Done')
    next_service_date = fields.Date(string='Next Service Date')
    next_service_mileage = fields.Float(
        string='Next Service Mileage (km)', digits=(10, 2)
    )
    state = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='scheduled',
        required=True,
        tracking=True,
    )
    part_ids = fields.One2many(
        'car.service.part', 'service_id', string='Parts Used'
    )
    parts_cost = fields.Float(
        string='Parts Cost', compute='_compute_parts_cost', store=True
    )

    # ── Invoice link ──────────────────────────────────────────────────
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        copy=False,
        readonly=True,
        tracking=True,
    )
    invoice_state = fields.Selection(
        related='invoice_id.payment_state',
        string='Payment Status',
        readonly=True,
        store=True,
    )
    invoice_count = fields.Integer(
        string='Invoices', compute='_compute_invoice_count'
    )

    # ── Computes ──────────────────────────────────────────────────────

    @api.depends('part_ids.subtotal')
    def _compute_parts_cost(self):
        for service in self:
            service.parts_cost = sum(service.part_ids.mapped('subtotal'))

    def _compute_invoice_count(self):
        for service in self:
            service.invoice_count = 1 if service.invoice_id else 0

    # ── ORM ───────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('car.service') or _('New')
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        for service in self:
            service.write({'state': 'done'})
            # Update vehicle mileage if higher
            if service.mileage_at_service and service.mileage_at_service > service.vehicle_id.mileage:
                service.vehicle_id.mileage = service.mileage_at_service

    def action_cancel(self):
        for service in self:
            if service.invoice_id and service.invoice_id.state == 'posted':
                raise UserError(_(
                    'Cannot cancel service "%s": a posted invoice already exists. '
                    'Please credit the invoice first.', service.name
                ))
        self.write({'state': 'cancelled'})

    def action_reset(self):
        self.write({'state': 'scheduled'})

    # ── Invoice creation ──────────────────────────────────────────────

    def action_create_invoice(self):
        """Create a draft customer invoice for the service and link it."""
        self.ensure_one()
        if self.invoice_id:
            return self.action_view_invoice()

        partner = self.vehicle_id.owner_id
        if not partner:
            raise UserError(_(
                'Please set an owner on vehicle "%s" before creating an invoice.',
                self.vehicle_id.name,
            ))

        service_type_label = dict(
            self._fields['service_type'].selection
        ).get(self.service_type, self.service_type)

        # Build invoice lines
        invoice_lines = []

        # One line for labour / service cost (cost minus parts)
        labour_cost = self.cost - self.parts_cost
        if labour_cost:
            invoice_lines.append((0, 0, {
                'name': _('%s – Labour (%s)', self.name, service_type_label),
                'quantity': 1.0,
                'price_unit': labour_cost,
            }))

        # One line per part
        for part in self.part_ids:
            invoice_lines.append((0, 0, {
                'name': part.name,
                'quantity': part.quantity,
                'price_unit': part.unit_price,
            }))

        # Fallback: if no labour and no parts, use total cost as single line
        if not invoice_lines:
            invoice_lines.append((0, 0, {
                'name': _('%s – %s', self.name, service_type_label),
                'quantity': 1.0,
                'price_unit': self.cost,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': self.service_date,
            'invoice_origin': self.name,
            'ref': self.name,
            'invoice_line_ids': invoice_lines,
        })

        self.invoice_id = invoice
        self.message_post(
            body=_('Invoice <a href="#" data-oe-model="account.move" data-oe-id="%d">%s</a> created.', invoice.id, invoice.name)
        )
        return self.action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_('No invoice linked to this service record.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
        }


class CarServicePart(models.Model):
    _name = 'car.service.part'
    _description = 'Service Part / Material'

    service_id = fields.Many2one(
        'car.service', string='Service', required=True, ondelete='cascade'
    )
    name = fields.Char(string='Part / Material', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price', digits=(12, 2))
    subtotal = fields.Float(
        string='Subtotal', compute='_compute_subtotal', store=True
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
