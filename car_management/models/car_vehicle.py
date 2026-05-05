from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CarVehicle(models.Model):
    _name = 'car.vehicle'
    _description = 'Car Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Vehicle Name', compute='_compute_name', store=True
    )
    vin = fields.Char(
        string='VIN (Chassis Number)',
        required=True,
        index=True,
        copy=False,
        help='17-character Vehicle Identification Number',
    )
    license_plate = fields.Char(
        string='License Plate',
        index=True,
        tracking=True,
    )
    model_id = fields.Many2one(
        'car.model',
        string='Model',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    brand_id = fields.Many2one(
        related='model_id.brand_id',
        string='Brand',
        store=True,
        readonly=True,
    )
    year = fields.Integer(
        string='Year', required=True, tracking=True,
        help='Manufacturing year'
    )
    color = fields.Char(string='Color', tracking=True)
    mileage = fields.Float(
        string='Current Mileage (km)', tracking=True, digits=(10, 2)
    )
    owner_id = fields.Many2one(
        'res.partner',
        string='Owner',
        tracking=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('in_use', 'In Use'),
            ('maintenance', 'Under Maintenance'),
            ('sold', 'Sold'),
            ('scrapped', 'Scrapped'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
    )
    purchase_date = fields.Date(string='Purchase Date')
    purchase_price = fields.Float(string='Purchase Price', digits=(12, 2))
    image = fields.Image(string='Vehicle Image', max_width=1024, max_height=1024)
    note = fields.Html(string='Notes')

    service_ids = fields.One2many('car.service', 'vehicle_id', string='Service Records')
    service_count = fields.Integer(
        string='Services', compute='_compute_service_count', aggregator='sum'
    )
    last_service_date = fields.Date(
        string='Last Service Date', compute='_compute_last_service_date', store=True
    )

    # ------------------------------------------------------------------ #
    # Computed fields                                                       #
    # ------------------------------------------------------------------ #

    @api.depends('model_id', 'year', 'license_plate')
    def _compute_name(self):
        for vehicle in self:
            parts = []
            if vehicle.model_id:
                parts.append(vehicle.model_id.full_name or str(vehicle.model_id.name))
            if vehicle.year:
                parts.append(str(vehicle.year))
            if vehicle.license_plate:
                parts.append(f"[{vehicle.license_plate}]")
            vehicle.name = ' '.join(parts) if parts else 'New Vehicle'

    def _compute_service_count(self):
        for vehicle in self:
            vehicle.service_count = len(vehicle.service_ids)

    @api.depends('service_ids.service_date')
    def _compute_last_service_date(self):
        for vehicle in self:
            services = vehicle.service_ids.filtered(lambda s: s.service_date)
            vehicle.last_service_date = max(services.mapped('service_date')) if services else False

    # ------------------------------------------------------------------ #
    # Constraints                                                           #
    # ------------------------------------------------------------------ #

    @api.constrains('vin')
    def _check_vin(self):
        for vehicle in self:
            if vehicle.vin and len(vehicle.vin.strip()) not in (0, 17):
                raise ValidationError(
                    _("VIN must be exactly 17 characters. Got %d for '%s'.")
                    % (len(vehicle.vin.strip()), vehicle.vin)
                )

    @api.constrains('year')
    def _check_year(self):
        for vehicle in self:
            if vehicle.year and (vehicle.year < 1886 or vehicle.year > 2100):
                raise ValidationError(
                    _("Year must be between 1886 and 2100.")
                )

    # ------------------------------------------------------------------ #
    # Actions                                                               #
    # ------------------------------------------------------------------ #

    def action_view_services(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service Records',
            'res_model': 'car.service',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_in_use(self):
        self.write({'state': 'in_use'})

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})

    def action_set_sold(self):
        self.write({'state': 'sold'})
