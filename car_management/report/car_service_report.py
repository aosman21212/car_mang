from odoo import fields, models
from odoo.tools import SQL, drop_view_if_exists


class CarServiceReport(models.Model):
    _name = 'car.service.report'
    _description = 'Service Cost Analysis'
    _auto = False
    _order = 'service_date desc'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('car.vehicle', string='Vehicle', readonly=True)
    brand_id = fields.Many2one('car.brand', string='Brand', readonly=True)
    model_id = fields.Many2one('car.model', string='Model', readonly=True)
    service_date = fields.Date(string='Month', readonly=True)
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
        readonly=True,
    )
    service_count = fields.Integer(string='# Services', readonly=True, aggregator='sum')
    total_cost = fields.Float(string='Total Cost', digits=(12, 2), readonly=True)
    total_parts_cost = fields.Float(string='Parts Cost', digits=(12, 2), readonly=True)
    state = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        readonly=True,
    )

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(SQL(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER ()                                  AS id,
                    cs.vehicle_id                                         AS vehicle_id,
                    cv.brand_id                                           AS brand_id,
                    cv.model_id                                           AS model_id,
                    DATE_TRUNC('month', cs.service_date)::date            AS service_date,
                    cs.service_type                                       AS service_type,
                    cs.state                                              AS state,
                    COUNT(cs.id)                                          AS service_count,
                    SUM(cs.cost)                                          AS total_cost,
                    SUM(cs.parts_cost)                                    AS total_parts_cost
                FROM car_service cs
                JOIN car_vehicle cv ON cv.id = cs.vehicle_id
                GROUP BY
                    cs.vehicle_id,
                    cv.brand_id,
                    cv.model_id,
                    DATE_TRUNC('month', cs.service_date),
                    cs.service_type,
                    cs.state
            )
            """,
            SQL.identifier(self._table),
        ))
