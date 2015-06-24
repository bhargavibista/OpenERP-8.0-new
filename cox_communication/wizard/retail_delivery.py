# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class retail_delivery(osv.osv_memory):
    _name='retail.delivery'
    _rec_name = 'so_line_ids'
    _columns={
    'stock_available':fields.boolean('Stock Available'),
    'so_line_ids': fields.text('Product_ids'),
    'procurement_ids':fields.char('procurement.order')  ##cox gen2
    }
    def default_get(self, cr, uid, fields, context={}):
        print "inside default getttttttttttttttttttttttttttt"
        if context is None: context = {}
        location_id = self.pool.get('stock.location')
        so_obj = self.pool.get('sale.order')
        so_line_obj = self.pool.get('sale.order.line')
        result = super(retail_delivery, self).default_get(cr, uid, fields, context=context)
        stock_available,sol_ids_available,sale_id = [],[],False
        if context and context.get('active_model') == 'sale.order':
            sale_id = context.get('active_id')
        else:
            sale_id = context.get('sale_id')
        if sale_id:
            if isinstance(sale_id,list):
                sale_id =  sale_id[0]
            sale_id_obj = so_obj.browse(cr,uid,sale_id)
            origin = sale_id_obj.name
#            pick_id = self.pool.get('stock.picking').search(cr,uid,[('sale_id','=',sale_id),('state','not in',('done','cancel'))])
            pick_id = self.pool.get('stock.picking').search(cr,uid,[('origin','=',origin),('state','not in',('done','cancel'))])
            if pick_id:
                ##cox gen2
#                cr.execute("select id from sale_order_line where id in (select sale_line_id from stock_move where picking_id=%d)"%(pick_id[0]))
#                cr.execute("select sale_line_id from stock_move where picking_id = %d and parent_stock_mv_id is null"%(pick_id[0]))
#                so_line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#                for each_line in so_line_obj.browse(cr,uid,so_line_ids):
#                    product_id = each_line.product_id.id
##                    _get_products
##                    available_qty = location_id._product_get(cr, uid, sale_id_obj.location_id.id, [product_id], context={})[product_id]
#                    available_qty = location_id._product_get(cr, uid, sale_id_obj.location_id.id, [product_id], context={})[product_id]
#                    print "available_qty",available_qty
                ###
                cr.execute("select procurement_id from stock_move where picking_id = %d and parent_stock_mv_id is null"%(pick_id[0]))
                procurement_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                
                print"procurement_ids",procurement_ids
                sale_line_ids = self.pool.get('procurement.order').browse(cr,uid,procurement_ids[0]).sale_line_id.id
                print"sale_line_ids",sale_line_ids
                cr.execute("select id from sale_order_line where parent_so_line_id='%s' and product_id in (select id from product_product where product_tmpl_id in (select id from product_template where type !='service'))"%(sale_line_ids))
                child_so_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
#                child_so_line_id =
                if child_so_line_id:
                    sale_line_ids =  child_so_line_id
                for each_line in so_line_obj.browse(cr,uid,sale_line_ids):
                    print"each_line.product_id",each_line.product_id
                    product_id = each_line.product_id.product_tmpl_id.id
                    print"product_id",product_id
#                    _get_products
#                    available_qty = location_id._product_get(cr, uid, sale_id_obj.location_id.id, [product_id], context={})[product_id]
                    available_qty = self.pool.get('product.template')._product_available(cr, uid,[product_id],'','')
                    print"available_qtyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",available_qty
                    if available_qty:
                       available_qty = available_qty[product_id]['qty_available']
#                    print "available_qty",available_qty[product_id]['qty_available']
                    if available_qty <= 0.0:
                        stock_available.append(False)
                    else:
                        stock_available.append(True)
                        sol_ids_available.append(str(each_line.id))
            if True not in stock_available:
                result.update({'stock_available':False})
            else:
                result.update({'stock_available':True})
            print"sol_ids_available",sol_ids_available
            if sol_ids_available:
                sol_ids_available = ','.join(sol_ids_available)
                result.update({'so_line_ids':sol_ids_available,'procurement_ids':procurement_ids})
                print"procurement_idsssssssss",type(procurement_ids)
                context={'procurement_id':procurement_ids}
        return result
    
    def delivery_later(self,cr,uid,ids,context={}):
        return {'type': 'ir.actions.act_window_close'}
    
    def barcode_scanning(self,cr,uid,ids,context):
        print"context barcode scanning",context
        sale_id = False
        if context and context.get('active_model') == 'sale.order':
            if context.get('active_id'):
                sale_id = context.get('active_id')
        else:
            sale_id = context.get('sale_id')
        if isinstance(sale_id,list):
            sale_id =  sale_id[0]
        if sale_id:
            name = self.pool.get('sale.order').browse(cr,uid,sale_id).name
        pick_id = self.pool.get('stock.picking').search(cr,uid,[('origin','=',name),('state','not in',('done','cancel'))])
        print "sale and pick idsssssssssssssssss",pick_id,sale_id
        procurement= []
        if pick_id:

            so_line_ids = self.browse(cr,uid,ids[0]).so_line_ids
            procurement_id = self.browse(cr,uid,ids[0]).procurement_ids
            print"procurement_id",procurement_id,type(procurement_id)
#            if len(procurement_id) > 1:
            context = dict(context, active_ids=pick_id, active_model='stock.picking',procurement_id=procurement_id,so_line_ids=so_line_ids,trigger='retail_store',sale_id=sale_id)
            print"context",context
            return {
                        'name':_("Bar Code Scanning"),
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'pre.picking.scanning',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'domain': '[]',
                        'context': context,
                    }

