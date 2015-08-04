# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import base64

class tr_barcode(osv.osv):
    """ Barcode Class """
    _inherit = "tr.barcode"
    _description = "Barcode"
    _columns = {
        'product_id': fields.many2one('product.product','Product')
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id):
        res={}
        if not product_id:
            res = {'value': {'code': False}}
            return res
        default_code = self.pool.get('product.product').browse(cr,uid,product_id).default_code
#        print"default_code",default_code
        vals = {
               'code' : default_code,
               'barcode_type': 'Standard39',
           }
        return { 'value' : vals }
tr_barcode()
