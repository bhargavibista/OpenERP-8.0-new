# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from dateutil.relativedelta import relativedelta
import time

class receive_goods(osv.osv_memory):
    _inherit = "receive.goods"
    _columns = {
    'received':fields.boolean('Received')
    }
    def no_receive_goods(self,cr,uid,ids,context):
        if context.get('active_id'):
            return_obj = self.pool.get('return.order')
            return_refund_cancel_obj = self.pool.get('return.refund.cancellation')
	    charge_termination_obj = self.pool.get('charge.termination.fee')	
            obj_self = return_obj.browse(cr,uid,context.get('active_id'))
            no_days_passed =  obj_self.no_days_passed
	    if not no_days_passed:
		no_days_passed = return_obj.no_days_passed(cr,uid,obj_self.linked_sale_order,context)	
            if obj_self.receive:
                raise osv.except_osv(_('Warning !'),_('Goods are already received'))
            if not obj_self.receive and obj_self.return_type == 'car_return':
                if obj_self.linked_sale_order.shipped:
                    if (no_days_passed >= 0) and (no_days_passed <= 90):
                        termination_fees = charge_termination_obj.get_termination_fees(cr,uid,context)
                        if termination_fees > 0.0:
                                return {
                                    'name':_("Charge Termination Fees"),
                                    'view_mode': 'form',
                                    'view_type': 'form',
                                    'res_model': 'charge.termination.fee',
                                    'type': 'ir.actions.act_window',
                                    'nodestroy': True,
                                    'target': 'new',
                                    'domain': '[]',
                                    'context': context,
                                }
                        else:
                            flag = return_obj.service_product_flag(cr,uid,obj_self,context)
                            if flag:
                                id = return_refund_cancel_obj.create(cr,uid,{'refund_cancel':'cancel','return_id':obj_self.id})
                                return {
                                'name':_("Service Cancellation"),
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_id': id,
                                'res_model': 'return.refund.cancellation',
                                'type': 'ir.actions.act_window',
                                'nodestroy': True,
                                'target': 'new',   }
                    else:
                        flag = return_obj.service_product_flag(cr,uid,obj_self,context)
                        if flag:
                            id = return_refund_cancel_obj.create(cr,uid,{'refund_cancel':'cancel','return_id':obj_self.id})
                            return {
                            'name':_("Service Cancellation"),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_id': id,
                            'res_model': 'return.refund.cancellation',
                            'type': 'ir.actions.act_window',
                            'nodestroy': True,
                            'target': 'new',
                                }
                else:
                    id = return_refund_cancel_obj.create(cr,uid,{'refund_cancel':'refund','return_id':obj_self.id})
		    if not obj_self.manual_invoice_invisible:
	        	    return {
        	        	    'name':_("Payment Finalization"),
	        	            'view_type': 'form',
        	        	    'view_mode': 'form',
		                    'res_id': id,
        		            'res_model': 'return.refund.cancellation',
		                    'type': 'ir.actions.act_window',
	       		            'nodestroy': True,
		                    'target': 'new',
        		            }
                return_obj.write(cr,uid,[obj_self.id],{'state':'done'})
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': obj_self.id,
                    'res_model': 'return.order',
                    'type': 'ir.actions.act_window',
                    'context':context
                }
 	    return {'type': 'ir.actions.act_window_close'}	       
    def create_parent_stock_mv(self,cr,uid,browse_id,model,picking_id_obj,serial_num,source_id,dest_id,context):
        if context is None: context = {}
        model_id_obj = self.pool.get(model).browse(cr,uid,browse_id)
        print"model_id_obj",model_id_obj
        obj_stock_move = self.pool.get('stock.move')
        sale_line_id = browse_id
        print"model_id_obj.product_uom_qty",model_id_obj.product_uom_qty
        order_line_details = {
            'product_id' : model_id_obj.product_id.id,
            'location_id' : source_id,
            'location_dest_id' : dest_id,
            ##cox gen2 start
#            'product_qty' : model_id_obj.product_uom_qty,
            'product_uom_qty' : model_id_obj.product_uom_qty,
            ##end
            'product_uom' : model_id_obj.product_uom.id,
            'name' : model_id_obj.product_id.name,
            'price_unit' : model_id_obj.price_unit,
            'picking_id' : picking_id_obj.id,
                        }
        if context and context.get('delivery_order'):
            date_planned = datetime.strptime(time.strftime('%Y-%m-%d'), DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=7.0)
            date_planned = (date_planned - timedelta(days=picking_id_obj.company_id.security_lead)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            order_line_details['date_expected'] = date_planned
        return_move = obj_stock_move.create(cr, uid, order_line_details)
        # below code is used to specify the serial number in the returned incoming shipment
        serial_lot_id,todo_moves = False,[]
        if picking_id_obj.picking_type_id.code =='incoming' and serial_num: ## cox gen2
            cr.execute("select id from stock_production_lot where name='%s'"%(serial_num))
            serial_lot_data = cr.dictfetchone()
            if serial_lot_data:
                serial_lot_id = serial_lot_data['id']
            else:
                serial_lot_id = self.pool.get('stock.production.lot').create(cr, uid, {
                    'name' : serial_num,
                    'product_id' : each_return_line.product_id.id,
                })
        if return_move and serial_lot_id:
            
            cr.execute('''
                insert into stock_move_lot values(%s,%s)
            '''%(return_move,serial_lot_id))
        context['parent_return_move_id'] = return_move
        todo_moves.append(return_move)
        if model == 'return.order.line':
            sale_line_id = model_id_obj.sale_line_id

        todo_moves += self.create_child_stock_mv(cr,uid,sale_line_id,model_id_obj.product_uom_qty,picking_id_obj.id,source_id,dest_id,context)
        return todo_moves
    
    def create_child_stock_mv(self,cr,uid,sale_line_id,qty,picking_exchange_in_id,source_id,dest_id,context):
        ##Code to create incoming stock move for the child product itself
        todo_moves = []
        obj_stock_move = self.pool.get('stock.move')
#        cr.execute("select id from stock_move where parent_stock_mv_id in (select id from stock_move where sale_line_id = %d)"%(sale_line_id))
        cr.execute("select id from stock_move where parent_stock_mv_id in (select id from stock_move where procurement_id in (select id from procurement_order where sale_line_id = %d))"%(sale_line_id))  #cox gen2
        stock_move = filter(None, map(lambda x:x[0], cr.fetchall()))
        if stock_move:
            for each in stock_move:
                stock_mv_id_obj = obj_stock_move.browse(cr,uid,each)
                order_line_details = {
                'product_id' : stock_mv_id_obj.product_id.id,
                'location_id' : source_id,
                'location_dest_id' : dest_id,
                'product_qty' : qty,
                'product_uom' : stock_mv_id_obj.product_uom.id,
                'name' : stock_mv_id_obj.product_id.name,
                'price_unit' : stock_mv_id_obj.price_unit,
                'picking_id' : picking_exchange_in_id,
                'return_move_id':context.get('parent_return_move_id',0)
            }
                return_move = obj_stock_move.create(cr, uid, order_line_details)
                todo_moves.append(return_move)
        return todo_moves
    def receive_goods(self,cr,uid,ids,context):
        if context and context.get('active_id',False):
            id = self.pool.get('return.shipment.label').create(cr,uid,{'return_id':context.get('active_id',False)})
            return {
                    'name':_("Shipment Needed ?"),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': id,
                    'res_model': 'return.shipment.label',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                        }
        
    def receive_goods_wizard(self,cr,uid,ids,context):
        obj_picking = self.pool.get('stock.picking')
        obj_stock_move = self.pool.get('stock.move')
        return_obj = self.pool.get('return.order')
        location_obj = self.pool.get('stock.location')
        line_obj = self.pool.get('sale.order.line')
        picking_type = self.pool.get('stock.picking.type')
        if context.get('active_id'):
            obj_self = return_obj.browse(cr,uid,context.get('active_id'))
            if not obj_self.order_line:
                raise osv.except_osv(_('Error!'),  _('Please Insert Return Order lines'))
            if not obj_self.receive:
                ##Source Location
                source_id = location_obj.search(cr, uid, [('usage','=','customer')])
                if source_id:
                    source_id = source_id[0]
                ##Destination Location
                source_location = obj_self.source_location
                dest_id = source_location.id
                search_return_location = location_obj.search(cr, uid, [('return_location','=',True)])
                if search_return_location:
                    dest_id = search_return_location[0]
                # below code is to find the destination location of one of the moves of the sales order
                # which has to be returned and use it as a source location for the sales return moves
                if obj_self.actual_linked_order:
                    actual_sale_id = obj_self.actual_linked_order.id
                    if actual_sale_id:
                        obj_self.write({'linked_sale_order':actual_sale_id})
                if obj_self.linked_sale_order:
                    so_state = obj_self.linked_sale_order.state
                    if so_state != 'done':
                        raise osv.except_osv(_('Warning!'),_('Products are not Shipped yet so you cannot do Incoming shipment'))
#                    source_picking = obj_picking.search(cr, uid, [('sale_id','=',obj_self.linked_sale_order.id)])
                    source_picking = obj_self.linked_sale_order.picking_ids
                    print"source_picking",source_picking
                    if len(source_picking):
                        obj_stock_previous_move = obj_picking.browse(cr, uid, source_picking.id).move_lines
                    else:
                        raise osv.except_osv(_('Warning!'),_('No Delivery Order is Created for %s')%(obj_self.linked_sale_order.name))
                    for each_move in obj_stock_previous_move:
                        source_id = each_move.location_dest_id.id
                        print"source_id",source_id
                        break
                # the code ends here for the source loation
                return_type = obj_self.return_type
                origin = obj_self.name
                if not origin:
                    origin = obj_self.linked_sale_order.name
                picking_type_id = picking_type.search(cr,uid,[('code','=','incoming'),('warehouse_id','=',obj_self.warehouse_id.id)])
                
                order_details = {
                    'origin' : origin,
#                    'type' : 'in',
                    'picking_type_id' : picking_type_id[0],
                    'partner_id' : obj_self.partner_shipping_id.id,
                    'return_id' : obj_self.id,
                }
                todo_moves,flag,picking_exchange_in_id= [],False,False
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
                    context['default_type'] = 'in'#Very important line
		    if context.get('picking_id_in',False):
			picking_exchange_in_id = context.get('picking_id_in',False)
			cr.execute("select id from stock_move where picking_id=%s"%(context.get('picking_id_in',False)))
			todo_moves = filter(None, map(lambda x:x[0], cr.fetchall()))		
		        flag = True
		    else:
	                    picking_exchange_in_id = self.pool.get('stock.picking').create(cr, uid, order_details,context) # incoming shipment for the return sales order
                    if picking_exchange_in_id:
			pick=obj_picking.browse(cr,uid,picking_exchange_in_id)
			if not flag:
#	                        pick=obj_picking.browse(cr,uid,picking_exchange_in_id)
        	                for each_return_line in obj_self.order_line:
                	            if (each_return_line.product_id) and each_return_line.product_id.type != 'service':
                        	        todo_moves += self.create_parent_stock_mv(cr,uid,each_return_line.id,'return.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
	                            else:
        	                        child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',each_return_line.sale_line_id.id)])
                	                for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                        	            if (each_line.product_id.type != 'service'):
                                	        todo_moves += self.create_parent_stock_mv(cr,uid,each_line.id,'sale.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
                        if not context.get('incoming_shipment',False):
                            obj_stock_move.action_confirm(cr, uid, todo_moves)
#                            obj_picking.draft_force_assign(cr,uid,[picking_exchange_in_id],context) cox gen2
                            obj_picking.force_assign(cr,uid,[picking_exchange_in_id],context)
#                            obj_picking.test_assigned(cr,uid,[picking_exchange_in_id]) cox gen2
#                            pick.action_assign_wkf()  cox gen2
                            context['action_process_original'] = True ##Extra Line of Code
#                            process = obj_picking.action_process(cr, uid, [pick.id], context=context)
                            process = obj_picking.do_enter_transfer_details(cr, uid, [pick.id], context=context)  ##cox gen2
                            context = process.get('context')
                            context['active_id']=ids[0]
                            res_id = process.get('res_id')
        #                    res_id = self.pool.get("stock.partial.picking").create(cr,uid,{},context)
                            if res_id:
#                                cox gen2
#                                self.pool.get('stock.partial.picking').do_partial( cr, uid, [process['res_id']], context)
                                self.pool.get('stock.transfer_details').do_detailed_transfer( cr, uid, [process['res_id']], context)
                                pick.action_done()
	                    if obj_self.manual_invoice_invisible:
	                        state = 'done'
	                    else:
	                        state = 'progress'
#                    #Extra Code to start
	                    data_to_write = {'state': state,'receive':True}
#                    onchange_val = return_obj.onchange_device_returned(cr,uid,[obj_self.id],True,obj_self.no_days_passed,{})
#                    if onchange_val and onchange_val.get('value',{}):
#                        data_to_write.update(onchange_val.get('value',{}))
	                    return_obj.write(cr, uid,obj_self.id, data_to_write)
            context['active_id'] = obj_self.id
            context['active_ids'] = [obj_self.id]
            return_data = {
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_id': obj_self.id,
                            'res_model': 'return.order',
                            'type': 'ir.actions.act_window',
                            'context':context
                        }
            no_days_passed =  obj_self.no_days_passed
	    if not no_days_passed:
		no_days_passed = return_obj.no_of_days_passed(cr,uid,obj_self.linked_sale_order,context)
            context['return_id'] = obj_self.id
            if obj_self.return_type == 'car_return':
	            return_data = return_obj.flow_option_based_on_days(cr,uid,no_days_passed,context)
	            if return_data:
        	        return return_data
	    else:
		return return_obj.deliver_confirm(cr,uid,[obj_self.id],context)		
receive_goods()

