# -*- encoding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import fields, osv

class receive_goods(osv.osv_memory):
    _name = "receive.goods"
    _columns = {
    }
    def no_receive_goods(self,cr,uid,ids,context):
        return {'type': 'ir.actions.act_window_close'}
    def create_parent_stock_mv(self,cr,uid,browse_id,model,picking_id_obj,serial_num,source_id,dest_id,context):
        model_id_obj = self.pool.get(model).browse(cr,uid,browse_id)
        obj_stock_move = self.pool.get('stock.move')
        sale_line_id = browse_id
        order_line_details = {
                            'product_id' : model_id_obj.product_id.id,
                            'location_id' : source_id,
                            'location_dest_id' : dest_id,
                            'product_qty' : model_id_obj.product_uom_qty,
                            'product_uom' : model_id_obj.product_uom.id,
                            'name' : model_id_obj.product_id.name,
                            'price_unit' : model_id_obj.price_unit,
                            'picking_id' : picking_id_obj.id,
                        }
        if context.get('delivery_order'):
            date_planned = datetime.strptime(time.strftime('%Y-%m-%d'), DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=7.0)
            date_planned = (date_planned - timedelta(days=picking_id_obj.company_id.security_lead)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            order_line_details['date_expected'] = date_planned
        return_move = obj_stock_move.create(cr, uid, order_line_details)
        # below code is used to specify the serial number in the returned incoming shipment
        serial_lot_id,todo_moves = False,[]
        if serial_num:
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
        todo_moves.append(return_move)
        if model == 'return.order.line':
            sale_line_id = model_id_obj.sale_line_id
        todo_moves += self.create_child_stock_mv(cr,uid,sale_line_id,model_id_obj.product_uom_qty,picking_id_obj.id,source_id,dest_id)
        return todo_moves

    def create_child_stock_mv(self,cr,uid,sale_line_id,qty,picking_exchange_in_id,source_id,dest_id):
        ##Code to create incoming stock move for the child product itself
        todo_moves = []
        obj_stock_move = self.pool.get('stock.move')
        cr.execute("select id from stock_move where parent_stock_mv_id in (select id from stock_move where sale_line_id = %d)"%(sale_line_id))
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
            }
                return_move = obj_stock_move.create(cr, uid, order_line_details)
                todo_moves.append(return_move)
        return todo_moves

    def receive_goods(self,cr,uid,ids,context):
        obj_picking = self.pool.get('stock.picking')
        obj_stock_move = self.pool.get('stock.move')
        return_obj = self.pool.get('return.order')
        location_obj = self.pool.get('stock.location')
        line_obj = self.pool.get('sale.order.line')
        if context.get('active_id'):
            obj_self = return_obj.browse(cr,uid,context.get('active_id'))
            if obj_self.linked_sale_order:
                search_return_rec = return_obj.search(cr, uid, [('linked_sale_order','=',obj_self.linked_sale_order.id),('receive','=',True),('return_type','=','exchange')])
                if search_return_rec:
                    self.log(cr,uid,ids[0],'Goods Are already Received')
                    return {'type': 'ir.actions.act_window_close'}
            if obj_self.receive:
                self.log(cr,uid,ids[0],'Goods Are already Received')
                return {'type': 'ir.actions.act_window_close'}
            if not obj_self.order_line:
                raise osv.except_osv(_('Error!'),  _('Please Insert Return Order lines'))
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
                source_picking = obj_picking.search(cr, uid, [('sale_id','=',obj_self.linked_sale_order.id)])
                if len(source_picking):
                    obj_stock_previous_move = obj_picking.browse(cr, uid, source_picking[0]).move_lines
                else:
                    raise osv.except_osv(_('Warning!'),_('No Delivery Order is Created for %s')%(obj_self.linked_sale_order.name))
                for each_move in obj_stock_previous_move:
                    source_id = each_move.location_dest_id.id
                    break
            # the code ends here for the source loation
            return_type = obj_self.return_type
            if not obj_self.linked_sale_order:
                origin = obj_self.name
            else:
                origin = obj_self.linked_sale_order.name
            order_details = {
                'origin' : origin,
                'type' : 'in',
                'address_id' : obj_self.partner_shipping_id.id,
                'return_id' : obj_self.id,
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
                context['default_type'] = 'in'#Very important line
                picking_exchange_in_id = obj_picking.create(cr, uid, order_details,context) # incoming shipment for the return sales order
                if picking_exchange_in_id:
                    pick=obj_picking.browse(cr,uid,picking_exchange_in_id)
                    for each_return_line in obj_self.order_line:
                        if (each_return_line.product_id) and each_return_line.product_id.type != 'service':
                            todo_moves += self.create_parent_stock_mv(cr,uid,each_return_line.id,'return.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
                        else:
                            child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',each_return_line.sale_line_id.id)])
                            for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                if (each_line.product_id.type != 'service'):
                                    todo_moves += self.create_parent_stock_mv(cr,uid,each_line.id,'sale.order.line',pick,obj_self.linked_serial_no,source_id,dest_id,context)
                    obj_stock_move.action_confirm(cr, uid, todo_moves)
                    obj_picking.draft_force_assign(cr,uid,[picking_exchange_in_id],context)
                    obj_picking.force_assign(cr,uid,[picking_exchange_in_id],context)
                    obj_picking.test_assigned(cr,uid,[picking_exchange_in_id])
                    pick.action_assign_wkf()
                    context['action_process_original'] = True ##Extra Line of Code
                    process = obj_picking.action_process(cr, uid, [pick.id], context=context)
                    context = process['context']
                    context['active_id']=ids[0]
                    partial_obj = self.pool.get('stock.partial.picking')
#                    res_id = process['res_id']
                    partial_picking_id = partial_obj.create(cr,uid,{},context)
#                    if res_id:
                    if partial_picking_id:
                        partial_obj.do_partial( cr, uid, [partial_picking_id], context)
                        pick.action_done()
                if obj_self.manual_invoice_invisible:
                    state = 'done'
                else:
                    state = 'progress'
                return_obj.write(cr, uid,obj_self.id, {'state': state,'receive':True})
                return {'type': 'ir.actions.act_window_close'}
receive_goods()