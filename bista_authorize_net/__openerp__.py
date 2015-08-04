# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
        "name" : "Authorize.Net",
        "version" : "0.1",
        "author" : "Bista Solutions Pvt. Ltd",
        "website" : "http://www.bistasolutions.com",
        "category" : "Payment Gateway",
        "description": """Charge Customers via Authorize.Net""",
        "depends" : ['base','sale','stock'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "data" : ['authorize_net.xml',
            'sale_view.xml',
            'invoice_view.xml',
            'partner_view.xml',
            'transaction_wizard.xml',
            'wizard/new_profile.xml',
            'wizard/customer_profile.xml',
            'wizard/charge_customer.xml'
        ],
        "installable": True
}