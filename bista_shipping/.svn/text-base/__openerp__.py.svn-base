# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Shipping Service Integration',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse Management',
    'description': """
OpenERP Integration with USPS, UPS and Fedex
    """,
    'author': 'Bista Solutions Pvt. Ltd',
    'depends': ['sale','stock','delivery','product'],
    'init_xml': [],

    'update_xml': [
        "security/shipping_security.xml",
        "security/ir.model.access.csv",
        "wizard/generate_shipping_quotes.xml",
	"wizard/track_shipping_view.xml",
        'stock_view.xml',
        "shipping_view.xml",
        'canada_shipping.xml',
        "shipping_menu.xml",
        'sale_view.xml',
        'delivery_view.xml',
#        'product_view.xml',
        'shipping_data.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
}
