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
                cr.execute("select procurement_id from stock_move where picking_id = %d and parent_stock_mv_id is null"%(pick_id[0]))
                procurement_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                sale_line_ids = self.pool.get('procurement.order').browse(cr,uid,procurement_ids[0]).sale_line_id.id
                cr.execute("select id from sale_order_line where parent_so_line_id='%s' and product_id in (select id from product_product where product_tmpl_id in (select id from product_template where type !='service'))"%(sale_line_ids))
                child_so_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                if child_so_line_id:
                    sale_line_ids =  child_so_line_id
                for each_line in so_line_obj.browse(cr,uid,sale_line_ids):
                    product_id = each_line.product_id.product_tmpl_id.id
                    available_qty = self.pool.get('product.template')._product_available(cr, uid,[product_id],'','')
                    if available_qty:
                       available_qty = available_qty[product_id]['qty_available']
                    if available_qty <= 0.0:
                        stock_available.append(False)
                    else:
                        stock_available.append(True)
                        sol_ids_available.append(str(each_line.id))
            if True not in stock_available:
                result.update({'stock_available':False})
            else:
                result.update({'stock_available':True})
            if sol_ids_available:
                sol_ids_available = ','.join(sol_ids_available)
                result.update({'so_line_ids':sol_ids_available,'procurement_ids':procurement_ids})
                context={'procurement_id':procurement_ids}
        return result
    
#    code to retrive to gen1 or gen2 OE page
    def view_document(self,cr,uid,ids,context=None):
        url="http://flareplay.com/salesorder.html"
        return {
        'type': 'ir.actions.act_url',
        'url':url,
        'target': 'self'
        }
    
    def delivery_later(self,cr,uid,ids,context={}): 
        res=self.view_document(cr,uid,ids,context=None)
        return res
#        warning =self.pool.get('warning').info(cr, uid, title='Delivery Message', message="Your Order will be processed by Warehouse")
#        return warning
    
    def barcode_scanning(self,cr,uid,ids,context):
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
        procurement= []
        if pick_id:

            so_line_ids = self.browse(cr,uid,ids[0]).so_line_ids
            procurement_id = self.browse(cr,uid,ids[0]).procurement_ids
            context = dict(context, active_ids=pick_id, active_model='stock.picking',procurement_id=procurement_id,so_line_ids=so_line_ids,trigger='retail_store',sale_id=sale_id)
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

