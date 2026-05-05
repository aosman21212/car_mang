from odoo import fields, models


class CarBrand(models.Model):
    _name = 'car.brand'
    _description = 'Car Brand'
    _order = 'name'

    name = fields.Char(string='Brand Name', required=True, index=True)
    country_id = fields.Many2one('res.country', string='Country of Origin')
    logo = fields.Image(string='Logo', max_width=128, max_height=128)
    active = fields.Boolean(default=True)
    model_ids = fields.One2many('car.model', 'brand_id', string='Models')
    model_count = fields.Integer(
        string='Models Count', compute='_compute_model_count'
    )

    def _compute_model_count(self):
        for brand in self:
            brand.model_count = len(brand.model_ids)

    def action_view_models(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Models',
            'res_model': 'car.model',
            'view_mode': 'list,form',
            'domain': [('brand_id', '=', self.id)],
            'context': {'default_brand_id': self.id},
        }
