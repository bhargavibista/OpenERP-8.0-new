# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class deliver_goods(osv.osv_memory):
    _name = "deliver.goods"
    _columns = {
    }
    def no_deliver_goods(self,cr,uid,ids,context={}):
        obj_picking = self.pool.get('stock.picking')
        picking_type = self.pool.get('stock.picking.type') ##cox gen2
        obj_stock_move = self.pool.get('stock.move')
        return_obj = self.pool.get('return.order')
        location_obj = self.pool.get('stock.location')
        receive_goods_obj = self.pool.get('receive.goods')
        line_obj = self.pool.get('sale.order.line')
        if context.get('active_id'):
            obj_self = return_obj.browse(cr,uid,context.get('active_id'))
            if not obj_self.order_line:
                raise osv.except_osv(_('Error!'),  _('Please Insert Return Order lines'))
            ##Destination Location
            dest_id = location_obj.search(cr, uid, [('usage','=','customer')])
            if dest_id:
                dest_id = dest_id[0]
            # below code is to find the destination location of one of the moves of the sales order
            # which has to be returned and use it as a source location for the sales return moves
            if obj_self.actual_linked_order:
                actual_sale_id = obj_self.actual_linked_order.id
                if actual_sale_id:
                    obj_self.write({'linked_sale_order':actual_sale_id})
            if obj_self.linked_sale_order:
                so_state = obj_self.linked_sale_order.state
                if so_state != 'done':
                    raise osv.except_osv(_('Warning!'),_('Products are not yet Shipped so you cannot do Delivery for Return'))
                ##Source Location
#                source_id = obj_self.linked_sale_order.shop_id.warehouse_id.lot_stock_id.id
                source_id = obj_self.linked_sale_order.warehouse_id.lot_stock_id.id
            # the code ends here for the source loation
            return_type = obj_self.return_type
            origin = obj_self.name
            if not origin:
                origin = obj_self.linked_sale_order.name
            picking_type_id = picking_type.search(cr,uid,[('code','=','outgoing'),('warehouse_id','=',obj_self.warehouse_id.id)])
            order_details = {
                'origin' : origin,
#                'type' : 'out',
                'picking_type_id' : picking_type_id[0],
                'partner_id' : obj_self.partner_shipping_id.id,
                'return_id' : obj_self.id,
                'sale_id': obj_self.linked_sale_order.id
            }
            todo_moves= []
            if return_type=='car_return' or return_type=='30_day' or return_type =='destroy' or return_type=='exchange':
                picking_exchange_in_id = False
                if return_type=='car_return':
                    order_details['rma_return'] = obj_self.name +'/Credit_Return'
                elif return_type=='exchange':
                    order_details['rma_return'] = obj_self.name +'/Exchange'
                elif return_type=='destroy':
                    order_details['rma_return'] = obj_self.name +'/Destroy'
                else:
                    order_details['rma_return'] = obj_self.name +'/'
                order_details['invoice_state'] = 'none'
                context['default_type'] = 'out'#Very important line
                context['delivery_order'] = True
                picking_exchange_in_id = self.pool.get('stock.picking').create(cr, uid, order_details,context) # incoming shipment for the return sales order
                pick=obj_picking.browse(cr,uid,picking_exchange_in_id)
                if picking_exchange_in_id:
                    for each_return_line in obj_self.order_line:
                        if (each_return_line.product_id) and each_return_line.product_id.type != 'service':
                            todo_moves += receive_goods_obj.create_parent_stock_mv(cr,uid,each_return_line.id,'return.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
                        else:
                            child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',each_return_line.sale_line_id.id)])
                            for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                if (each_line.product_id.type != 'service'):
                                    todo_moves += receive_goods_obj.create_parent_stock_mv(cr,uid,each_line.id,'sale.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
                    obj_stock_move.action_confirm(cr, uid, todo_moves)
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', picking_exchange_in_id, 'button_confirm', cr)
                    if obj_self.receive:
                        state = 'done'
                    else:
                        state = 'progress'
                    return_obj.write(cr, uid,obj_self.id, {'delivered':True,'state':state})
	    return {
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_id': obj_self.id,
                            'res_model': 'return.order',
                            'type': 'ir.actions.act_window',
                            'context':context
                            }		
        return {'type': 'ir.actions.act_window_close'}
    
    def deliver_goods(self,cr,uid,ids,context):
        obj_picking = self.pool.get('stock.picking')
        obj_picking_type = self.pool.get('stock.picking.type') ##cox gen2
        obj_stock_move = self.pool.get('stock.move')
        return_obj = self.pool.get('return.order')
        location_obj = self.pool.get('stock.location')
        receive_goods_obj = self.pool.get('receive.goods')
        line_obj = self.pool.get('sale.order.line')
        if context.get('active_id'):
            obj_self = return_obj.browse(cr,uid,context.get('active_id'))
            if not obj_self.order_line:
                raise osv.except_osv(_('Error!'),  _('Please Insert Return Order lines'))
            ##Destination Location
            dest_id = location_obj.search(cr, uid, [('usage','=','customer')])
            if dest_id:
                dest_id = dest_id[0]
            # below code is to find the destination location of one of the moves of the sales order
            # which has to be returned and use it as a source location for the sales return moves
            if obj_self.actual_linked_order:
                actual_sale_id = obj_self.actual_linked_order.id
                if actual_sale_id:
                    obj_self.write({'linked_sale_order':actual_sale_id})
            if obj_self.linked_sale_order:
                so_state = obj_self.linked_sale_order.state
                if so_state != 'done':
                    raise osv.except_osv(_('Warning!'),_('Products are not yet Shipped so you cannot do Delivery for Return'))
                ##Source Location
                source_id = obj_self.source_location.id
            # the code ends here for the source loation
            return_type = obj_self.return_type
            origin = obj_self.name
            if not origin:
                origin = obj_self.linked_sale_order.name
            picking_type_id = obj_picking_type.search(cr,uid,[('code','=','outgoing'),('warehouse_id','=',obj_self.warehouse_id.id)])
            order_details = {
                'origin' : origin,
#                'type' : 'out',  cox gen2
                'picking_type_id' : picking_type_id[0], #cox gen2
                'partner_id' : obj_self.partner_shipping_id.id,
                'return_id' : obj_self.id,
                'sale_id': obj_self.linked_sale_order.id
            }
            todo_moves= []
            if return_type=='car_return' or return_type=='30_day' or return_type =='destroy' or return_type=='exchange':
                picking_exchange_in_id = False
                if return_type=='car_return':
                    order_details['rma_return'] = obj_self.name +'/Credit_Return'
                elif return_type=='exchange':
                    order_details['rma_return'] = obj_self.name +'/Exchange'
                elif return_type=='destroy':
                    order_details['rma_return'] = obj_self.name +'/Destroy'
                else:
                    order_details['rma_return'] = obj_self.name +'/'
                order_details['invoice_state'] = 'none'
                context['default_type'] = 'out'#Very important line
                context['delivery_order'] = True
                picking_exchange_in_id = self.pool.get('stock.picking').create(cr, uid, order_details,context) # incoming shipment for the return sales order
                pick=obj_picking.browse(cr,uid,picking_exchange_in_id)
                if picking_exchange_in_id:
                    for each_return_line in obj_self.order_line:
                        if (each_return_line.product_id) and each_return_line.product_id.type != 'service':
                            todo_moves += receive_goods_obj.create_parent_stock_mv(cr,uid,each_return_line.id,'return.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
                        else:
                            child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',each_return_line.sale_line_id.id)])
                            for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                if (each_line.product_id.type != 'service'):
                                    todo_moves += receive_goods_obj.create_parent_stock_mv(cr,uid,each_line.id,'sale.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
                    obj_stock_move.action_confirm(cr, uid, todo_moves)
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', picking_exchange_in_id, 'button_confirm', cr)
#                    obj_picking.draft_force_assign(cr,uid,[picking_exchange_in_id],context)
#                    obj_picking.force_assign(cr,uid,[picking_exchange_in_id],context)
#                    obj_picking.test_assigned(cr,uid,[picking_exchange_in_id])
#                    pick.action_assign_wkf()
#                    context['action_process_original'] = True ##Extra Line of Code
#                    process = obj_picking.action_process(cr, uid, [pick.id], context=context)
#                    context = process.get('context')
#                    context['active_id']=ids[0]
#                    res_id = process.get('res_id')
#                    if res_id:
#                        self.pool.get('stock.partial.picking').do_partial( cr, uid, [process['res_id']], context)
#                        pick.action_done()
                    if obj_self.receive:
                        state = 'done'
                    else:
                        state = 'progress'
                    return_obj.write(cr, uid,obj_self.id, {'delivered':True,'state':state})
                    context = dict(context, active_ids=[picking_exchange_in_id], active_model='stock.picking',return_id= obj_self.id)
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
                return {'type': 'ir.actions.act_window_close'}
deliver_goods()
