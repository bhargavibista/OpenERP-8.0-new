# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import openerp.netsvc as netsvc

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
            'rma_return' : fields.char('Return Ref',size=64, readonly=True),
            'return_id' : fields.many2one('return.order','Return Id'),
        }
    
stock_picking()
#class stock_picking_in(osv.osv):
#   _inherit = 'stock.picking.in'
#   _columns = {
#           'rma_return' : fields.char('Return Ref',size=64, readonly=True),
#           'return_id' : fields.many2one('return.order','Return Id'),
#       }
#
#class stock_picking_out(osv.osv):
#   _inherit = 'stock.picking.out'
#   _columns = {
#           'rma_return' : fields.char('Return Ref',size=64, readonly=True),
#           'return_id' : fields.many2one('return.order','Return Id'),
#       }
class stock_move(osv.osv):
    _inherit = 'stock.move'

    # the below code is to automatically create an invoice for the Incoming shipments and delivery orders
    def validate_invoice(self,cr,uid,ids,picking_ids):
       wf_service = netsvc.LocalService("workflow")
       obj_picking = self.pool.get('stock.picking')
       obj_stock_invoice_shipping = self.pool.get('stock.invoice.onshipping')
       picking_ids_obj = obj_picking.browse(cr, uid, picking_ids)

       for each_pick in picking_ids_obj:
#           print"each_pick==========",each_pick
#           if each_pick.internal_type in ('input','output'):
#               continue
           current_pick_id = each_pick.id
#           print "state current",each_pick.invoice_state,current_pick_id
#           if each_pick.is_reverse:
#               continue
           wf_service.trg_write(uid, 'stock.picking', current_pick_id, cr)
           context = {
               'active_id' : current_pick_id,
               'active_ids' : [current_pick_id],
               'active_model' : 'stock.picking',
           }

           journal_id = obj_stock_invoice_shipping._get_journal(cr, uid, context)
#           print "journal id",journal_id
           stock_invoice_shipping_id = obj_stock_invoice_shipping.create(cr, uid, {
               'invoice_date' : False,
               'group' : False,
               'journal_id' : journal_id,

           },context)
#           print"stock_invoice_shipping_id**********",stock_invoice_shipping_id
           if stock_invoice_shipping_id:
                return_invoice_shipping = obj_stock_invoice_shipping.open_invoice(cr, uid, [stock_invoice_shipping_id], context)

       return True

#    def action_done(self, cr, uid, ids, context=None):
#        """ Makes the move done and if all moves are done, it will finish the picking.
#        @return:
#        """
#        print"ids*****************************",ids
#        if ids and ids[0]:
#            print"ids----------------------",ids
#            stock_move_obj = self.browse(cr,uid,ids[0])
#        else:
#            stock_move_obj= False
#        print"ids@@@ velodyne returns, context",ids,context
#        picking_ids = []
#        move_ids = []
#        wf_service = netsvc.LocalService("workflow")
#        print"context9999  action done velodyne returns",context
#        if context is None:
#            context = {}
#
#        todo = []
#        for move in self.browse(cr, uid, ids, context=context):
#            if move.state=="draft":
#                todo.append(move.id)
#        if todo:
#            self.action_confirm(cr, uid, todo, context=context)
#            todo = []
#
#        for move in self.browse(cr, uid, ids, context=context):
#            if move.state in ['done','cancel']:
#                continue
#            move_ids.append(move.id)
#            if move.picking_id:
#                if move.picking_id.id not in picking_ids: # condition added in velodyne for not allowing duplicate values to be added to the list
#                    picking_ids.append(move.picking_id.id)
#            if move.move_dest_id.id and (move.state != 'done'):
#                self.write(cr, uid, [move.id], {'move_history_ids': [(4, move.move_dest_id.id)]})
#                #cr.execute('insert into stock_move_history_ids (parent_id,child_id) values (%s,%s)', (move.id, move.move_dest_id.id))
#                if move.move_dest_id.state in ('waiting', 'confirmed'):
#                    self.force_assign(cr, uid, [move.move_dest_id.id], context=context)
#                    if move.move_dest_id.picking_id:
#                        wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
#                    if move.move_dest_id.auto_validate:
#                        self.action_done(cr, uid, [move.move_dest_id.id], context=context)
#
#            self._create_product_valuation_moves(cr, uid, move, context=context)
#
#            if move.state not in ('confirmed','done','assigned'):
#                todo.append(move.id)
#
#        if todo:
#            self.action_confirm(cr, uid, todo, context=context)
#
#        self.write(cr, uid, move_ids, {'state': 'done', 'date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
#        for id in move_ids:
#             wf_service.trg_trigger(uid, 'stock.move', id, cr)
#
#        for pick_id in picking_ids:
#            print"pick_id",pick_id
#            wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
#
#        # the below code is to automatically create an invoice for the Incoming shipments and delivery orders
##        print"sale_id",self.browse(cr,uid,ids[0]).picking_id.sale_idase_id
#
### code to make po line item read-only if no po qty is pending
#            purchase_line_id = move.purchase_line_id
#            print"purchase_line_id purchase_line_id:",purchase_line_id
##            if purchase_line_id.qty_due == 0.0 and purchase_line_id.ret_qty == 0.0:
##                self.pool.get('purchase.order.line').write(cr,uid,purchase_line_id.id,{'state':'done'})
##                print"yesss"
### code to make po line item read-only if no qty is pending Ends
#
#        if stock_move_obj and not stock_move_obj.picking_id.rma_return:
##TODO       added if condition to create invoice when invoice state is To be invoiced
#            if stock_move_obj.picking_id.invoice_state=='2binvoiced':
#                x = self.validate_invoice(cr,uid,ids,picking_ids)##calling the validate_invoice function to automate the creation of invoice on Validating.
#                print "x",x
#        # End
#
#        # velodyne code starts from here for confirming the incoming shipment and to create the delivery order
#        print "velodyne returns incoming"
#        obj_picking = self.pool.get('stock.picking')
#        obj_return = self.pool.get('return.order')
#        obj_stock_move = self.pool.get('stock.move')
#        obj_product = self.pool.get('product.product')
#        todo_moves= []
#        if picking_ids:
#           rma_return_id = obj_picking.browse(cr,uid,picking_ids[0]).return_id.id
#           print"rma_return_id*********",rma_return_id
##           do_both_move = obj_picking.browse(cr, uid, picking_ids[0]).return_id.do_both_move
#           do_both_move = obj_picking.browse(cr, uid, picking_ids[0]).return_id.ship_exchange_selection
#           type = obj_picking.browse(cr, uid, picking_ids[0]).type
#        else:
#           rma_return_id = False
#        print "rma return id",rma_return_id
#        if rma_return_id:
#            inv = True
#            deli = True
#            obj_return_sale = obj_return.browse(cr,uid,rma_return_id)
#            return_type = obj_return_sale.return_type
#            print"return type  *************",return_type
#            prev_sale_order_id = False
#            if obj_return_sale.linked_sale_order:
#                prev_sale_order_id = obj_return_sale.linked_sale_order.id
#                origin = obj_return_sale.linked_sale_order.name + ''
#            else:
#                origin = obj_return_sale.name
#
#            if return_type=='exchange' and do_both_move=='ship_after' and type=='in':
#                obj_incoming_pick = obj_picking.browse(cr, uid, pick_id)
#                cr.execute("update return_order set incoming_exchange=True where id=%s"%(rma_return_id))
#                # the above code is used to update the return order when the incoming shipment is done
#                # for the exchange return
#                print "address",obj_return_sale.name,obj_incoming_pick.move_lines
#
#                deliver_id = obj_picking.create(cr, uid, {
#                    'origin' : origin,
#                    'type' : 'out',
#                    'address_id' : obj_return_sale.partner_shipping_id.id,
#                    'return_id' : obj_return_sale.id,
#                    'rma_return' : obj_return_sale.name + "/Exchange",
#                })
#
#                for each_income_stock_move in obj_incoming_pick.move_lines:
#                    order_line_details = {
#                        'product_id' : each_income_stock_move.product_id.id,
#                        'location_id' : each_income_stock_move.location_dest_id.id,
#                        'location_dest_id' : each_income_stock_move.location_id.id,
#                        'product_qty' : each_income_stock_move.product_qty,
#                        'product_uom' : each_income_stock_move.product_uom.id,
#                        'name' : each_income_stock_move.product_id.name,
#                        'price_unit' : each_income_stock_move.price_unit,
#                        'picking_id' : deliver_id,
#
#                    }
#
#                    deliver_move = obj_stock_move.create(cr, uid, order_line_details)
#                    print "deliver move",deliver_id
#                    todo_moves.append(deliver_move)
#                obj_stock_move.action_confirm(cr, uid, todo_moves)
#                obj_stock_move.action_assign(cr, uid, todo_moves)
##                obj_stock_move.force_assign(cr, uid, todo_moves)
#                if deliver_id:
#                    obj_picking.draft_force_assign(cr,uid,[deliver_id],context)
#            elif return_type=='exchange' and type=='out':
#                # updates the return order when the new product is delivered for exchange
#                cr.execute("update return_order set outgoing_exchange=True where id=%s"%(rma_return_id))
#            elif return_type=='exchange' and type=='in':
#                # updates the return order when the exchange product is returned for exchange
#                cr.execute("update return_order set incoming_exchange=True where id=%s"%(rma_return_id))
#
#            if (return_type == 'car_return' or return_type == 'destroy') and type=='in':
#                print"pick ID *****************",pick_id
#                obj_incoming_pick = obj_picking.browse(cr, uid, pick_id)
#
#            print "return type",return_type
#
#            if (return_type == 'warranty' or return_type =='non-warranty')  and type == 'in':
#                obj_incoming_pick = obj_picking.browse(cr, uid, pick_id)
#                print "address",obj_return_sale.partner_shipping_id.id
#                if return_type == 'non-warranty':
#                    invoice_method = obj_return_sale.invoice_method
#                else:
#                    invoice_method = 'none'
#
#                invoice_id = obj_return_sale.partner_invoice_id.id
#                if prev_sale_order_id:
#                    prev_picking_id = obj_picking.search(cr,uid,[('sale_id','=',prev_sale_order_id)])
#                    print"prev_picking_id",prev_picking_id
#                    address_id = obj_picking.browse(cr,uid,prev_picking_id[0]).address_id.id
#                    partner_id = obj_picking.browse(cr,uid,prev_picking_id[0]).partner_id.id
#                    for each_move_line in obj_picking.browse(cr,uid,pick_id).move_lines:
#                        default_location_id = 12
#                        cust_location_id = 9
#                        if obj_return_sale.source_location:
#                           default_location_id = obj_return_sale.source_location.id
#                        elif each_move_line.product_id.default_location:
#                           default_location_id = each_move_line.product_id.default_location.id
#                        repair_dict = {}
#                        product_id = each_move_line.product_id.id
#                        product_obj = obj_product.browse(cr,uid,product_id)
#                        product_qty = each_move_line.product_qty
#                        prev_move_id = obj_stock_move.search(cr,uid,[('picking_id','=',prev_picking_id[0]),('product_id','=',product_id)])
#                        print"prev_move_id",prev_move_id
#                        move = obj_stock_move.browse(cr,uid,prev_move_id[0])
#                        limit = datetime.strptime(move.date_expected, '%Y-%m-%d %H:%M:%S') + relativedelta(months=int(product_obj.warranty))
#                        limitless = limit.strftime('%Y-%m-%d')
#                        return_order_lines = obj_return_sale.order_line
#                        for return_order_line in return_order_lines:
#                            print"return_order_line",return_order_line
#                            return_product_id = return_order_line.product_id.id
#                            if return_product_id==product_id:
#                                return_reason = return_order_line.description_reasons.id
#                                if return_order_line.guarantee_limit_ro:
#                                    limitless=return_order_line.guarantee_limit_ro
#                        print "previous move id",prev_move_id[0]
#                        if len(prev_move_id):
#			    print "product qty",product_qty
#                            for i in range(0,int(product_qty)):
#                                print"product_qty",product_qty
#                                print"i",i
#                                repair_dict['product_id'] = product_id
#                                repair_dict['move_id'] = prev_move_id[0]
#                                repair_dict['address_id'] = address_id
#                                repair_dict['partner_id'] = partner_id
#                                repair_dict['guarantee_limit'] = limitless
#                                repair_dict['location_id'] = default_location_id
#                                repair_dict['location_dest_id'] = cust_location_id
#                                repair_dict['sale_return_id'] = rma_return_id
#                                repair_dict['description_reason'] = return_reason
#                                repair_dict['invoice_method'] = invoice_method
#                                repair_dict['partner_invoice_id'] = invoice_id
#                                val_new = self.pool.get('mrp.repair').create(cr,uid,repair_dict)
#                                print"Val_new***********", val_new
#                    wf_service.trg_validate(uid, 'stock.picking', pick_id, 'button_confirm', cr)
#                else:
#
#                        for each_move_line in obj_picking.browse(cr,uid,pick_id).move_lines:
#                            default_location_id = 12
#                            cust_location_id = 9
#                            if each_move_line.product_id.default_location:
#                                default_location_id = each_move_line.product_id.default_location.id
#                            repair_dict = {}
#                            product_id = each_move_line.product_id.id
#                            product_obj = obj_product.browse(cr,uid,product_id)
#                            product_qty = each_move_line.product_qty
#                            limitless = time.strftime("%Y-%m-%d")
#                            return_order_lines = obj_return_sale.order_line
#                            for return_order_line in return_order_lines:
#
#                                return_product_id = return_order_line.product_id.id
#                                if return_product_id==product_id:
#                                    return_reason = return_order_line.description_reasons.id
#                                    if return_order_line.guarantee_limit_ro:
#                                        limitless=return_order_line.guarantee_limit_ro
#                            print "limitless",limitless
#                            for i in range(0,product_qty):
#                                print"product_qty",product_qty
#                                print"i",i
#                                repair_dict['product_id'] = product_id
##                                repair_dict['move_id'] = prev_move_id[0]
#                                repair_dict['address_id'] = obj_return_sale.partner_shipping_id.id
#                                repair_dict['partner_id'] = obj_return_sale.partner_id.id
#                                repair_dict['guarantee_limit'] = limitless
#                                repair_dict['location_id'] = default_location_id
#                                repair_dict['location_dest_id'] = cust_location_id
#                                repair_dict['sale_return_id'] = rma_return_id
#                                repair_dict['description_reason'] = return_reason
#                                repair_dict['invoice_method'] = invoice_method
#                                repair_dict['partner_invoice_id'] = invoice_id
#                                self.pool.get('mrp.repair').create(cr,uid,repair_dict)
#            elif (return_type == 'warranty' or return_type =='non-warranty')  and type == 'out':
#                cr.execute("select id from mrp_repair where picking_id=%s"%(pick_id))
#                res = cr.dictfetchone()
#                if res:
#                    cr.execute("update mrp_repair set state='2binvoiced' where id=%s"%(res['id']))
#
#            invoice_ids = obj_return_sale.invoice_ids
#            picking_ids = obj_return_sale.picking_ids
#            print"picking_ids",picking_ids
#            for invoice_id in invoice_ids:
#                print"invoice_id",invoice_id
#                if invoice_id.state!='paid':
#                    inv=False
#                    break
#            if inv:
#                for picking_id in picking_ids:
#                    if picking_id.state!='done':
#                        deli=False
#                        break
#                        print"picking_id",picking_id
#            if (return_type=='car_return' or return_type=='30_day') and not len(invoice_ids):
#                inv=False
#            if deli and inv:
#                obj_return_sale.write({'state':'done'})
###
#        return True

stock_move()
