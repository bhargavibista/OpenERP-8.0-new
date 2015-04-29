# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields, osv

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    _columns = {
        'address_checked' : fields.boolean('Address Checked',readonly=True),
        'invalid_addr': fields.boolean('Invalid Address',readonly=True),
    }

res_partner()