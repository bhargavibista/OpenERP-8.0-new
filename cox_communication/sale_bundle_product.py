# -*- coding: utf-8 -*-
from openerp.addons.osv import osv, fields
class product_item_set_line(osv.osv):
    _inherit = "product.item.set.line"
    def get_sale_items_lines(self, cr, uid, ids, context=None):
        sale_item_line_obj = self.pool.get('sale.order.line.item.set')
        res=[]
        for item in self.browse(cr, uid, ids, context=context):
            context['item_set_line_obj'] = item
            res.append(sale_item_line_obj.get_create_items_lines(cr, uid, item.product_id.id, item.qty_uom, item.uom_id.id, context))
        return res
product_item_set_line()

class sale_order_line_item_set(osv.osv):
    _inherit = "sale.order.line.item.set"
    def get_create_items_lines(self, cr, uid, product_id, qty_uom, uom_id=False, context=False):
        '''this function will return the id of the configuration line if the line already exist, if not it will create the line automatically'''
        if not uom_id:
            uom_id = self.pool.get('product.product').read(cr, uid, product_id, ['uom_id'], context=context)['uom_id'][0]
#        sale_item_ids = self.search(cr, uid, [['product_id', '=', product_id], ['qty_uom', '=', qty_uom], ['uom_id', '=', uom_id]], context=context)
#        if sale_item_ids:
#            return sale_item_ids[0]
#        else:
        if context.get('item_set_line_obj'):
            item_set_line_obj = context.get('item_set_line_obj')
            selection_string = {'option_id':item_set_line_obj.item_set_id.sequence,'selection_id':item_set_line_obj.sequence,'qty':qty_uom}
        return self.create(cr, uid, {'product_id': product_id, 'qty_uom': qty_uom, 'uom_id': uom_id,'selection_string':selection_string}, context=context)

    _columns = {
        'selection_string': fields.text('Selection String')
    }
    _defaults = {
    }
sale_order_line_item_set()