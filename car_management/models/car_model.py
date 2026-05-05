from odoo import fields, models


class CarModel(models.Model):
    _name = 'car.model'
    _description = 'Car Model'
    _order = 'brand_id, name'

    name = fields.Char(string='Model Name', required=True, index=True)
    brand_id = fields.Many2one(
        'car.brand', string='Brand', required=True, ondelete='restrict', index=True
    )
    category = fields.Selection(
        selection=[
            ('sedan', 'Sedan'),
            ('suv', 'SUV'),
            ('hatchback', 'Hatchback'),
            ('coupe', 'Coupe'),
            ('convertible', 'Convertible'),
            ('wagon', 'Station Wagon'),
            ('van', 'Van / Minivan'),
            ('pickup', 'Pickup Truck'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('other', 'Other'),
        ],
        string='Body Type',
        required=True,
        default='sedan',
    )
    fuel_type = fields.Selection(
        selection=[
            ('gasoline', 'Gasoline'),
            ('diesel', 'Diesel'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('lpg', 'LPG'),
            ('hydrogen', 'Hydrogen'),
        ],
        string='Fuel Type',
        default='gasoline',
    )
    seats = fields.Integer(string='Seats', default=5)
    active = fields.Boolean(default=True)
    vehicle_ids = fields.One2many('car.vehicle', 'model_id', string='Vehicles')
    vehicle_count = fields.Integer(
        string='# Vehicles', compute='_compute_vehicle_count'
    )
    full_name = fields.Char(
        string='Full Name', compute='_compute_full_name', store=True
    )

    def _compute_vehicle_count(self):
        for model in self:
            model.vehicle_count = len(model.vehicle_ids)

    def _compute_full_name(self):
        for model in self:
            model.full_name = f"{model.brand_id.name} {model.name}" if model.brand_id else model.name

    def action_view_vehicles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicles',
            'res_model': 'car.vehicle',
            'view_mode': 'list,form',
            'domain': [('model_id', '=', self.id)],
            'context': {'default_model_id': self.id},
        }

    def name_get(self):
        return [(rec.id, f"{rec.brand_id.name} {rec.name}") for rec in self]
