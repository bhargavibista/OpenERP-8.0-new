# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Sales Returns',
    'version': '1.0',
    'category': 'Sales',
    'description': """
Allows the management of returns from customers. Gives ease of making Exchange and Credit return against a returned product.
    """,
    'author': 'Bista Solutions Pvt. Ltd',
    'depends': ['base','sale','stock','delivery','account','bista_authorize_net'],
    'init_xml': [],

    'update_xml': [
        'returns_view.xml',
        'wizard/refund_customer.xml',
        'wizard/receive_goods.xml',
        'stock_view.xml',
        'returns_sequence.xml',
        'sale_view.xml',
        'account_invoice_view.xml',
        'return_authorize_view.xml',
        'security/ir.model.access.csv',
#        'report_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
}
