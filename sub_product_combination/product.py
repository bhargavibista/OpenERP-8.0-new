# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
class extra_prod_config(osv.osv):
    _name = 'extra.prod.config'
    def onchange_product_id(self,cr,uid,ids,product_id,qty):
       res = {}
       if not qty:
           raise osv.except_osv(_('Warning !'),_('Qty should be greater than 0,0'))
       if product_id:
           product_id_obj = self.pool.get('product.product').browse(cr,uid,product_id)
           name = product_id_obj.name
           price = product_id_obj.list_price
           res['name'] =  name
           res['price'] =  price
       else:
           res['name'] =  ''
           res['price'] =  0.0
       return {'value':res}
    def create(self,cr,uid,vals,context={}):
        if vals.get('qty') == 0.0:
            raise osv.except_osv(_('Warning !'),_('Please Specify Quantity for %s in Extra Product Configuration')%(vals.get('name')))
        return super(extra_prod_config,self).create(cr,uid,vals,context)
    def write(self,cr,uid,ids,vals,context={}):
        if vals.get('qty') == 0.0:
            raise osv.except_osv(_('Warning !'),_('Please Specify Quantity for %s in Extra Product Configuration')%(vals.get('name')))
        return super(extra_prod_config,self).write(cr,uid,ids,vals,context)
    _columns = {
        'name':fields.char('Name',size=64),
        'price':fields.float('Price',digits=(12,4)),
        'qty':fields.float('Qty',digits=(12,4)),
        'comp_product_id':fields.many2one('product.product','Product ID'),
        'product_id':fields.many2one('product.product','Product ID'),
    }
    _defaults = {
    'qty':1.0}
extra_prod_config()

class product_template(osv.osv):
    _inherit="product.template"
    _columns={
    'ext_prod_config':fields.one2many('extra.prod.config','product_id','Extra Config'),
    }
product_template()