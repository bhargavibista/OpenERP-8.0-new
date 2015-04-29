# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import openerp.netsvc as netsvc
from openerp.tools.translate import _

class sub_components(osv.osv):
    _name = 'sub.components'
    _rec_name = 'product_id'
    _columns = {
    'name':fields.char('Name',size=64),
     'qty_uom': fields.integer('Quantity', required=True),
     'uom_id': fields.many2one('product.uom', 'Product UoM', required=True),
     'product_id': fields.many2one('product.product', 'Product', required=True),
     'price':fields.float('Price',digits=(12,4)),
     'so_line_id': fields.many2one('sale.order.line', 'SO Line Id'),
     'product_type': fields.char('Product type')	
     }

sub_components()
class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
    'so_id': fields.many2one('sale.order', 'Sale Order ID'),
    'sub_components' : fields.one2many('sub.components', 'so_line_id', 'Order Lines'),
    'order_id': fields.many2one('sale.order', 'Order Reference', ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),# inherited to delete required=True
    'parent_so_line_id': fields.many2one('sale.order.line', 'Parent Sale Line ID')
}
#Function is get called when creating sale order line from the Add a new line button
    def product_change(self,cr,uid,ids,product_id,qty,uom,qty_uos,uos,packaging,flag,context):
        res = super(sale_order_line, self).product_change(cr, uid, ids, product_id,qty,uom,qty_uos,uos,packaging,flag, context)
        extra_prod_config = self.pool.get('extra.prod.config')
        
        if product_id:
            
            comps = []
            if ids:
                sub_comp_obj = self.pool.get('sub.components')
                search_previous_com = sub_comp_obj.search(cr,uid,[('so_line_id','in',ids)])
                if search_previous_com:
                    sub_comp_obj.unlink(cr,uid,search_previous_com)
            sub_components = extra_prod_config.search(cr,uid,[('product_id','=',product_id)])
            if sub_components:
                for each_comp in sub_components:
                    each_comp_obj = extra_prod_config.browse(cr,uid,each_comp)
		    comps.append((0, 0,{'product_type': each_comp_obj.comp_product_id.type,'qty_uom':each_comp_obj.qty,'name':each_comp_obj.name,'product_id':each_comp_obj.comp_product_id.id,'uom_id':(each_comp_obj.product_id.uom_id.id if each_comp_obj.product_id.uom_id else False),	
                    'price':each_comp_obj.price}))
            if res.get('value'):
                res['value']['sub_components'] = comps
        return res
#Function is called when creating sale orde line from create button
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product,qty,uom,qty_uos,uos,name,partner_id,lang,update_tax,date_order,packaging,fiscal_position,flag, context)
        print"context",context
        extra_prod_config = self.pool.get('extra.prod.config')
        product_obj = self.pool.get('product.product')
        if product:
            print"product",product
            product = product_obj.browse(cr,uid,product).product_tmpl_id.id
            print"product_id",product
            if ids:
                sub_comp_obj = self.pool.get('sub.components')
                search_previous_com = sub_comp_obj.search(cr,uid,[('so_line_id','in',ids)])
                if search_previous_com:
                    sub_comp_obj.unlink(cr,uid,search_previous_com)
            comps = []
            sub_components = extra_prod_config.search(cr,uid,[('product_id','=',product)])
            
            if sub_components:
                for each_comp in sub_components:
                    each_comp_obj = extra_prod_config.browse(cr,uid,each_comp)
                    com_qty = (each_comp_obj.qty) * qty
                    comp_price = each_comp_obj.price
		    comps.append((0,0,{'product_type': each_comp_obj.comp_product_id.type,'qty_uom':com_qty,'name':each_comp_obj.name,'product_id':each_comp_obj.comp_product_id.id,'uom_id':(each_comp_obj.product_id.uom_id.id if each_comp_obj.product_id.uom_id else False),
                    'price':comp_price,'recurring_price':each_comp_obj.recurring_price}))
            if context.get('bundle_configuration',False):
                product_obj = self.pool.get('product.product')
                for comp in context.get('bundle_configuration',False):  ##cox gen2
                    product_id = product_obj.search(cr, uid,[('magento_product_id', '=',comp.get('product_id',False))])
                    if product_id:
                        product_id_obj = product_obj.browse(cr,uid,product_id[0])
                        com_qty = comp.get('qty_ordered',0.0) * qty
                        comp_price = com_qty * comp.get('price_unit',0.0)
			comps.append((0,0,{'product_type': each_comp_obj.comp_product_id.type,'qty_uom':com_qty,'name':comp.get('name',''),'product_id':product_id[0],'uom_id':(product_id_obj.uom_id.id if product_id_obj.uom_id else False),
                        'price': comp_price}))
            if res.get('value'):
                res['value']['sub_components'] = comps
        return res
    
sale_order_line()

class sale_order(osv.osv):
    _inherit='sale.order'
    _columns={
    #Field to Create Hidden Sale order Lines for the sub components
    'so_line_comp': fields.one2many('sale.order.line', 'so_id', 'Order Lines'),
    }
    #Function is inherited to set hidden so_line_comp i.e sale_order_lines as False
#    def copy(self,cr,uid,ids,vals,context):
#        vals.update({'so_line_comp':[]})
#        return super(sale_order, self).copy(cr, uid, ids,vals,context=context)
        
    
    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Create the required procurements to supply sale order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sale order's requested location.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: sale order to which the order lines belong
        :param list(browse_record) order_lines: sale order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        sale_line_obj = self.pool.get('sale.order.line')
        proc_ids = []
        if order:
            cr.execute("select id from sale_order_line where so_id=%d"%(order.id))
            comp_so_line_ids=filter(None, map(lambda x:x[0], cr.fetchall()))
            if comp_so_line_ids:
                com_so_line_obj = sale_line_obj.browse(cr,uid,comp_so_line_ids)
                if order_lines:
                    order_lines = order_lines + com_so_line_obj
                else:
                    order_lines = com_so_line_obj
        for line in order_lines:
            if line.state == 'done':
                continue
            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
            if line.product_id:
                if line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                else:
                    # a service has no stock move
                    move_id = False
                if line.product_id.type != 'service':
                    proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
                    proc_ids.append(proc_id)
                    line.write({'procurement_id': proc_id})
                    self.ship_recreate(cr, uid, order, line, move_id, proc_id)
        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False
            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val)
        return True
    def sub_product_order_lines(self,cr,uid,id,parent_so_line_id,prod_id_brw,price,qty,partner_id,context):
        line_obj = self.pool.get('sale.order.line')
        so_line = {'product_id':prod_id_brw.id,
                                'name': prod_id_brw.name,
                                'so_id':id,
                                'product_uom_qty':qty,
                                'state':'draft',
                                'order_id':False,
#                                'type':prod_id_brw.procure_method,
                                'price_unit':price,
                                'delay':7,
                                'order_partner_id':partner_id,
                                'parent_so_line_id': parent_so_line_id,
                                'th_weight':prod_id_brw.weight }
        context['child_lines'] = True
        line_id = line_obj.create(cr,uid,so_line,context)
        line_brw = line_obj.browse(cr,uid,line_id)
        for each_com in line_brw.product_id.ext_prod_config:
            qty = float(each_com.qty) *  float(line_brw.product_uom_qty)
            price = float(each_com.price) *  float(line_brw.product_uom_qty)
            self.sub_product_order_lines(cr,uid,id,line_id,each_com.comp_product_id,price,qty,partner_id,context)

    def action_wait(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        res = super(sale_order, self).action_wait(cr, uid, ids,context)
        order = self.browse(cr,uid,ids[0])
        if order.order_line:
            so_line_obj = self.pool.get('sale.order.line')
            for each in order.order_line:
#                if each.product_id.ext_prod_config:
                if each.sub_components:
                    for each_com in each.sub_components:
                        qty = float(each_com.qty_uom)
                        price = float(each_com.price)
                        self.sub_product_order_lines(cr,uid,order.id,each.id,each_com.product_id,price,qty,order.partner_id.id,context)
            if order.so_line_comp:
                so_line_obj.button_confirm(cr, uid, [x.id for x in order.so_line_comp])
        return True
sale_order()
