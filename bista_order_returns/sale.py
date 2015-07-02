# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
        'sale_return_ids' : fields.one2many('return.order','linked_sale_order',readonly=True),
    }
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'sale_return_ids': []})
        return super(sale_order, self).copy(cr, uid, id, default, context=context)
sale_order()