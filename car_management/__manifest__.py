# -*- coding: utf-8 -*-
# =============================================================================
#  Car Management System
# -----------------------------------------------------------------------------
#  Location  : King Abdulaziz Branch Road, Riyadh, Saudi Arabia
#  Email     : sales@leapai.ai
#  Phone     : +966 53 553 3627
#  Website   : https://leapai.ai
#  Developer : Abdulkaraim Osman — Tech Manager | Backend Engineer | DevOps Engineer
#              at Bab International Corp For Specialized Services
#  LinkedIn  : https://www.linkedin.com/in/abdulkaraim-o-385b7a110/
# =============================================================================
{
    'name': 'Car Management System',
    'version': '19.0.1.0.0',
    'category': 'Fleet/Car Management',
    'summary': 'Manage cars, brands, models, owners, and service records',
    'description': """
Car Management System
=====================
A comprehensive module for managing:
- Car Brands & Models
- Vehicles (VIN, registration, color, year, mileage)
- Ownership records
- Service / Maintenance history
    """,
    'author': 'abdzoro89',
    'maintainer': 'Abdulkaraim Osman',
    'support': 'sales@leapai.ai',
    'website': 'https://apps.odoo.com',
    'price': 0.0,
    'currency': 'EUR',
    'images': ['static/description/banner.svg', 'static/description/icon.png'],
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/car_brand_views.xml',
        'views/car_model_views.xml',
        'views/car_vehicle_views.xml',
        'views/car_service_views.xml',
        'report/report_actions.xml',
        'report/report_car_vehicle_card_template.xml',
        'report/report_car_service_history_template.xml',
        'report/report_car_fleet_summary_template.xml',
        'views/menu_views.xml',
        'views/report_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
