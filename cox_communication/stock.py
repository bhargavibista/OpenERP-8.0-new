# -*- coding: utf-8 -*-
#from encodings.iso2022_jp_2004 import decode
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import openerp.netsvc
import types
import socket
import xmlrpclib
from urllib import urlopen
class server_printer(osv.osv):
   '''
   This class store printer name and there server address with port number used in label printing in MO
   '''
   _name='server.printer'
   _columns={
           'name':fields.char('Printer Name',size=64),
           'ip':fields.char('IP Address',size=64),
           'port':fields.integer('Port No')
           }

server_printer()
#class stock_picking_out(osv.osv):
#    _inherit = "stock.picking.out"
#    _columns = {
#    'printed' : fields.boolean('Printed'),
#    'printer_id' : fields.many2one('server.printer','Printer'),
#    'print_label' : fields.boolean('Print Label'),
#    'no_of_prints' : fields.integer('Label Quantity',size = 32, help = 'Number of prints per label '),
#    'pick_up_back_office': fields.boolean('In Store Pick Up'),
#    'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=256),
#    'shipping_rate':fields.float('Shipping Rate'),
#    'ship_date':fields.char('Date',size=256),
#    'total_boxes':fields.integer('Total Boxes'),
#    'no_of_prdct_units':fields.integer('Total Product Units')
#    }
#    ##Function is inherited to show length,height and width of product
#    def create(self,cr,uid,vals,context={}):
#        if vals.get('move_lines'):
#            for each_move in vals.get('move_lines'):
#                if each_move[2].get('product_id',True):
#                    product_dimension = self.product_dimensions(cr,uid,each_move[2].get('product_id',False),{}) 
#                    vals.update(product_dimension)
#                    break
#        return super(stock_picking_out, self).create(cr, uid, vals, context)
#
#    def product_dimensions(self,cr,uid,prod_id,context={}):
#        prod_brw = self.pool.get('product.product').browse(cr,uid,prod_id)
#        data = {'pack_length': prod_brw.prod_length,
#        'pack_width': prod_brw.prod_width,
#        'pack_height': prod_brw.prod_height}
#        if context:
#            data.update({'weight_package': prod_brw.weight_net})
#        return data
#	
#    def action_process(self, cr, uid, ids, context=None):
#        if context is None: context = {}
#        if ids:
#            ids_obj =self.browse(cr,uid,ids[0])
#            context = dict(context, active_ids=ids, active_model='stock.picking')
#            if ids_obj.type == 'out':
#                if not context.get('action_process_original'):
#                    return {
#                            'name':_("Bar Code Scanning"),
#                            'view_mode': 'form',
#                            'view_type': 'form',
#                            'res_model': 'pre.picking.scanning',
#                            'type': 'ir.actions.act_window',
#                            'nodestroy': True,
#                            'target': 'new',
#                            'domain': '[]',
#                            'context': context,
#                        }
#            elif ids_obj.type == 'internal':
#                if not context.get('action_process_original'):
#                    return {
#                            'name':_("Shipping Process"),
#                            'view_mode': 'form',
#                            'view_type': 'form',
#                            'res_model': 'pre.shipping.process',
#                            'type': 'ir.actions.act_window',
#                            'nodestroy': True,
#                            'target': 'new',
#                            'domain': '[]',
#                            'context': context,
#                        }
##            cox gen2
#            return True
##            partial_id = self.pool.get("stock.partial.picking").create(cr, uid, {}, context=context)
##            return {
##                    'name':_("Products to Process"),
##                    'view_mode': 'form',
##                    'view_id': False,
##                    'view_type': 'form',
##                    'res_model': 'stock.partial.picking',
##                    'res_id': partial_id,
##                    'type': 'ir.actions.act_window',
##                    'nodestroy': True,
##                    'target': 'new',
##                    'domain': '[]',
##                    'context': context,
##                }	    
#    def in_store_pickup(self,cr,uid,ids,context):
#        context['active_ids']=ids
#        context['active_id']=ids[0]
#        return {
#                    'name':_("In Store Pick UP"),
#                    'view_mode': 'form',
#                    'view_id': False,
#                    'view_type': 'form',
#                    'res_model': 'in.store.pickup',
##                    'res_id': partial_id,
#                    'type': 'ir.actions.act_window',
#                    'nodestroy': True,
#                    'target': 'new',
#                    'domain': '[]',
#                    'context': context,
#                }
#stock_picking_out()

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    
    def _create_backorder(self, cr, uid, picking, backorder_moves=[], context=None):
        """ Move all non-done lines into a new backorder picking. If the key 'do_only_split' is given in the context, then move all lines not in context.get('split', []) instead of all non-done lines.
        """
        if not backorder_moves:
            backorder_moves = picking.move_lines
        backorder_move_ids = [x.id for x in backorder_moves if x.state not in ('done', 'cancel')]
        if 'do_only_split' in context and context['do_only_split']:
            backorder_move_ids = [x.id for x in backorder_moves if x.id not in context.get('split', [])]

        if backorder_move_ids:
            backorder_id = self.copy(cr, uid, picking.id, {
                'name': '/',
                'move_lines': [],
                'pack_operation_ids': [],
                'backorder_id': picking.id,
            })
            backorder = self.browse(cr, uid, backorder_id, context=context)
            self.message_post(cr, uid, picking.id, body=_("Back order <em>%s</em> <b>created</b>.") % (backorder.name), context=context)
            move_obj = self.pool.get("stock.move")
            move_obj.write(cr, uid, backorder_move_ids, {'picking_id': backorder_id}, context=context)
            self.write(cr, uid, [picking.id], {'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
            self.action_confirm(cr, uid, [backorder_id], context=context)
            return backorder_id
        return False

    ##Function is inherited to show length,height and width of product
    def create(self,cr,uid,vals,context={}):
        if vals.get('move_lines'):
            for each_move in vals.get('move_lines'):
                if each_move[2].get('product_id',True):
                    product_dimension = self.product_dimensions(cr,uid,each_move[2].get('product_id',False),{})
                    vals.update(product_dimension)
                    break
        return super(stock_picking, self).create(cr, uid, vals, context)

    def product_dimensions(self,cr,uid,prod_id,context={}):
        prod_brw = self.pool.get('product.product').browse(cr,uid,prod_id)
        data = {'pack_length': prod_brw.prod_length,
        'pack_width': prod_brw.prod_width,
        'pack_height': prod_brw.prod_height}
        if context:
            data.update({'weight_package': prod_brw.weight_net})
        return data
    
    def barcode_scanning_returns(self,cr,uid,ids,context={}):
        ids_brw = self.browse(cr,uid,ids[0])
        if ids_brw.return_id and ids_brw.picking_type_id.code == 'out' and ids_brw.state != 'done':
            context = dict(context, active_ids=ids, active_model='stock.picking',return_id= ids_brw.return_id.id)
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
        else:
            raise osv.except_osv(_('Error !'),_('You cannot do the Barcode Scanning')) 
   #Function is inherited because want to set to draft from cancel states
    def set_to_draft(self,cr,uid,ids,context={}):
        if not len(ids):
            return False
        cr.execute("select id from stock_move where picking_id IN %s and state=%s", (tuple(ids), 'cancel'))
        stock_moves = map(lambda x: x[0], cr.fetchall())
        self.write(cr, uid, ids, {'state': 'draft'})
        self.pool.get('stock.move').write(cr, uid, stock_moves, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for picking_id in ids:
            # Deleting the existing instance of workflow for picking
            wf_service.trg_delete(uid, 'stock.picking', picking_id, cr)
            wf_service.trg_create(uid, 'stock.picking', picking_id, cr)
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
#        for (id,name) in self.name_get(cr, uid, ids):
#            message = _("The Delivery Order '%s' has been set in draft state.") %(name,)
#            self.log(cr, uid, id, message)
        return True
    #Newly created function for creating partial shipments on the magento site
    def my_create_ext_partial_shipping(self, cr, uid, id, external_referential_id, stock_id_obj, mail_notification=True, context=None):
        if context is None: context = {}
        conn = context.get('conn_obj', False)
        item_qty = {}
        if stock_id_obj:
            magento_incrementid = stock_id_obj.sale_id.magento_so_id
            if magento_incrementid:
                for each_move in stock_id_obj.move_lines:
                    if not each_move.parent_stock_mv_id:
                        if each_move.product_id.magento_product_id:
                            item_qty[str(each_move.item_id)] = each_move.product_qty
            if item_qty:
              try:
                    ext_shipping_id = conn.call('sales_order_shipment.create', [magento_incrementid, item_qty, _("Shipping Created"), mail_notification, True])
              except Exception, e:
                    #print "error string",e
                    return False
              return ext_shipping_id
    #Function is inherited because wants to send tracking number after processing order i.e after creating
    #Shipping labels
    def export_shipment(self,cr,uid,ids,tracking_number,model,mag_shipmentid,context={}):
        model_id_obj = self.pool.get(model).browse(cr,uid,ids)
        delivery_carrier = self.pool.get('delivery.carrier')
        if model == 'stock.picking':
            sale_id = model_id_obj.sale_id
            if sale_id:
                 shop_id = sale_id.shop_id
                 if shop_id:
                    try:
                        conn = shop_id.referential_id.external_connection()
                        if conn:
                            context['conn_obj'] =  conn
                            magento_incrementid = sale_id.magento_so_id
                            external_referential_id = shop_id.referential_id.id
                            carrier_id = model_id_obj.carrier_id
                            if carrier_id:
                                context['model'] = model
                                delivery_carrier.check_ext_carrier_reference(cr, uid, carrier_id.id, magento_incrementid, context)
                            if not mag_shipmentid:
                                mag_shipmentid = self.my_create_ext_partial_shipping(cr, uid, model_id_obj, external_referential_id, model_id_obj,False,context)
                                if mag_shipmentid and carrier_id:
                                    carrier = delivery_carrier.read(cr, uid, carrier_id.id, ['magento_code', 'magento_tracking_title'], context)
                                    if tracking_number:
                                        carrier_code = carrier['magento_code'].split('_') ####bista code
                                        res= conn.call('sales_order_shipment.addTrack', [mag_shipmentid, carrier_code[0], carrier['magento_tracking_title'] or '', tracking_number or '']) ###bista code
                                    return mag_shipmentid
                    except Exception, e:
                        print "error string",e
                        
    #Function is inherited to show Bar Code Scanning instead of main Process Wizard
    
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        if context is None: context = {}
        if picking:
            ids_obj =self.browse(cr,uid,picking[0])
            context = dict(context, active_ids=picking, active_model='stock.picking')
            if ids_obj.picking_type_id.code == 'outgoing':
                if not context.get('action_process_original'):
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
            elif ids_obj.picking_type_id.code == 'internal':
                 if not context.get('action_process_original'):
                    return {
                            'name':_("Shipping Process"),
                            'view_mode': 'form',
                            'view_type': 'form',
                            'res_model': 'pre.shipping.process',
                            'type': 'ir.actions.act_window',
                            'nodestroy': True,
                            'target': 'new',
                            'domain': '[]',
                            'context': context,
                        }
            partial_id = self.pool.get('stock.transfer_details').create(cr, uid, {'picking_id':ids_obj.id}, context=context)
            return {
                    'name':_("Products to Process"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'stock.transfer_details',
                    'res_id': partial_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': context,
                }
                        
    ##cox gen2 
    '''def action_process(self, cr, uid, ids, context=None):
        if context is None: context = {}
        if ids:
            ids_obj =self.browse(cr,uid,ids[0])
            context = dict(context, active_ids=ids, active_model='stock.picking')
            if ids_obj.picking_type_id.code == 'outgoing':
                if not context.get('action_process_original'):
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
            elif ids_obj.picking_type_id.code == 'internal':
                if not context.get('action_process_original'):
                    return {
                            'name':_("Shipping Process"),
                            'view_mode': 'form',
                            'view_type': 'form',
                            'res_model': 'pre.shipping.process',
                            'type': 'ir.actions.act_window',
                            'nodestroy': True,
                            'target': 'new',
                            'domain': '[]',
                            'context': context,
                    }
#            cox gen2
#            return True
            partial_id = self.pool.get('stock.transfer_details').create(cr, uid, {'picking_id':ids_obj.id}, context=context)
            return {
                    'name':_("Products to Process"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'stock.transfer_details',
                    'res_id': partial_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': context,
                }'''
                
    def _state_get(self, cr, uid, ids, field_name, arg, context=None):
        print"state getttttttttttttt"
        '''The state of a picking depends on the state of its related stock.move
            draft: the picking has no line or any one of the lines is draft
            done, draft, cancel: all lines are done / draft / cancel
            confirmed, waiting, assigned, partially_available depends on move_type (all at once or partial)
        '''
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):
            if (not pick.move_lines) or any([x.state == 'draft' for x in pick.move_lines]):
                res[pick.id] = 'draft'
                continue
            if all([x.state == 'cancel' for x in pick.move_lines]):
                res[pick.id] = 'cancel'
                continue
            if all([x.state in ('cancel', 'done') for x in pick.move_lines]):
                res[pick.id] = 'done'
                continue

            order = {'confirmed': 0, 'waiting': 1, 'assigned': 2 , 'shipping':3}
            order_inv = {0: 'confirmed', 1: 'waiting', 2: 'assigned', 3:'shipping'}
            lst = [order[x.state] for x in pick.move_lines if x.state not in ('cancel', 'done')]
            if pick.move_type == 'one':
                res[pick.id] = order_inv[min(lst)]
            else:
                #we are in the case of partial delivery, so if all move are assigned, picking
                #should be assign too, else if one of the move is assigned, or partially available, picking should be
                #in partially available state, otherwise, picking is in waiting or confirmed state
                res[pick.id] = order_inv[max(lst)]
                if not all(x == 2 for x in lst):
                    if any(x == 2 for x in lst):
                        res[pick.id] = 'partially_available'
                    else:
                        #if all moves aren't assigned, check if we have one product partially available
                        for move in pick.move_lines:
                            if move.partially_available:
                                res[pick.id] = 'partially_available'
                                break
        return res

    def _get_pickings(self, cr, uid, ids, context=None):
        res = set()
        for move in self.browse(cr, uid, ids, context=context):
            if move.picking_id:
                res.add(move.picking_id.id)
        return list(res)
    
    def _get_sale_id(self, cr, uid, ids, name, args, context=None):
        sale_obj = self.pool.get("sale.order")
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = False
            if picking.group_id:
                sale_ids = sale_obj.search(cr, uid, [('procurement_group_id', '=', picking.group_id.id)], context=context)
                if sale_ids:
                    res[picking.id] = sale_ids[0]
        return res
    _columns = {
   'printed' : fields.boolean('Printed'),
   'printer_id' : fields.many2one('server.printer','Printer'),
   'print_label' : fields.boolean('Print Label'),
   'no_of_prints' : fields.integer('Label Quantity',size = 32, help = 'Number of prints per label '),
   'pick_up_back_office': fields.boolean('In Store Pick Up'),
   'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=256),
   'shipping_rate':fields.float('Shipping Rate'),
   'ship_date':fields.char('Date',size=256),
   'total_boxes':fields.integer('Total Boxes'),
   'no_of_prdct_units':fields.integer('Total Product Units'),
#   'state': fields.selection([
#       ('draft', 'Draft'),
#       ('cancel', 'Cancelled'),
#       ('auto', 'Waiting Another Operation'),
#       ('confirmed', 'Waiting Availability'),
#       ('assigned', 'Ready to Transfer'),
#       ('shipping','Shipped'),
#       ('done', 'Transferred'),
#       ], 'Status', readonly=True, select=True, track_visibility='onchange', help="""
#       * Draft: not confirmed yet and will not be scheduled until confirmed\n
#       * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
#       * Waiting Availability: still waiting for the availability of products\n
#       * Ready to Transfer: products reserved, simply waiting for confirmation.\n
#       * Transferred: has been processed, can't be modified or cancelled anymore\n
#       * Cancelled: has been cancelled, can't be confirmed anymore#"""
#    ),
    'state': fields.function(_state_get, type="selection", copy=False,
            store={
                'stock.picking': (lambda self, cr, uid, ids, ctx: ids, ['move_type'], 20),
                'stock.move': (_get_pickings, ['state', 'picking_id', 'partially_available'], 20)},
            selection=[
                ('draft', 'Draft'),
                ('cancel', 'Cancelled'),
                ('waiting', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('partially_available', 'Partially Available'),
                ('assigned', 'Ready to Transfer'),
                ('shipping','Shipped'),
                ('done', 'Transferred'),
                ], string='Status', readonly=True, select=True, track_visibility='onchange',
            help="""
                * Draft: not confirmed yet and will not be scheduled until confirmed\n
                * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                * Waiting Availability: still waiting for the availability of products\n
                * Partially Available: some products are available and reserved\n
                * Ready to Transfer: products reserved, simply waiting for confirmation.\n
                * Transferred: has been processed, can't be modified or cancelled anymore\n
                * Cancelled: has been cancelled, can't be confirmed anymore"""
        ),
        'sale_id': fields.function(_get_sale_id, type="many2one", relation="sale.order", string="Sale Order",store=True),
   }
    _defaults = {
        'shipping_type' : 'Fedex'
   }

    def shipment_receive(self, cr, uid, ids, context=None):
        context.update({'active_id':ids[0],'active_ids':ids,'active_model':'stock.picking'})
#        cox gen2
        partial_id = self.pool.get("stock.transfer_details").create(cr, uid, {'date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),'picking_id':ids[0]}, context=context)
        context.update({'partial_id':int(partial_id)})
        self.make_picking_done(cr,uid,ids,context)
        return True
    def make_picking_done(self, cr, uid, ids, context=None):
        status = self.browse(cr,uid,ids[0]).state
        if status == 'draft':
           draft_validate = self.action_confirm(cr, uid, ids, context=context)
#        context['action_process_original'] = True ##Extra Line of Code
#        function = self.action_process(cr, uid, ids, context=context)
        #self.pool.get('stock.picking').write(cr,uid,[pick.id],{'scan_uid':uid,'scan_date':time.strftime('%Y-%m-%d %H:%M:%S')})
#        res_id = function.get('res_id')
        res_id = context.get('partial_id')
        if res_id:
#            print"dsajkhfd"
#            cox gen2
            do_partial = self.pool.get("stock.transfer_details").do_detailed_transfer(cr,uid,[res_id],context=context)
stock_picking()


class stock_move(osv.osv):
    _inherit = "stock.move"
    def copy(self,cr,uid,id,default,context={}):
        default.update({'return_move_id':0})
        return super(stock_move, self).copy(cr, uid, id, default, context=context)
    def get_parent_stock_mv_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        so_line_obj = self.pool.get('sale.order.line')
        stock_move_obj = self.pool.get('stock.move')
        procurement_obj = self.pool.get('procurement.order')
        for each_move in self.browse(cr, uid, ids, context=context):
            if each_move.procurement_id.sale_line_id:
                search_child_so_line_id = so_line_obj.search(cr,uid,[('parent_so_line_id','=',each_move.procurement_id.sale_line_id.id)])
                if search_child_so_line_id:
                    for each_line in search_child_so_line_id:
                        search_stock_move = procurement_obj.search(cr,uid,[('sale_line_id','=',each_line)])
                        
                        if search_stock_move and len(search_stock_move) == 1:
                            result[search_stock_move[0]] = each_move.id
                            result[each_move.id] = False
            if each_move.return_move_id:
                    result[each_move.id] = each_move.return_move_id
        return result	
    
    def set_to_draft(self,cr,uid,ids,context):
        ids_obj = self.browse(cr,uid,ids[0])
        self.write(cr,uid,ids,{'state':'confirmed'})
        if ids_obj.picking_id:
            self.pool.get('stock.picking').write(cr,uid,ids_obj.picking_id.id,{'state':'confirmed'})
            if ids_obj.picking_id.sale_id:
                self.pool.get('sale.order').write(cr,uid,ids_obj.picking_id.sale_id.id,{'state':'progress'})
    #Function is inherited because to pass stock output account while generating incoming shipment for the Returns
    def _get_accounting_data_for_valuation(self, cr, uid, move, context=None):
        """
        Return the accounts and journal to use to post Journal Entries for the real-time
        valuation of the move.

        :param context: context dictionary that can explicitly mention the company to consider via the 'force_company' key
        :raise: osv.except_osv() is any mandatory account or journal is not defined.
        """
        product_obj=self.pool.get('product.product')
        accounts = product_obj.get_product_accounts(cr, uid, move.product_id.id, context)
        if move.location_id.valuation_out_account_id:
            acc_src = move.location_id.valuation_out_account_id.id
        ##Extra Code
        #starts here
        elif move.picking_id.type == 'in' and  move.picking_id.rma_return and move.picking_id.return_id.return_type=='car_return':
            acc_src = accounts['stock_account_output']
        #Ends here
        else:
            acc_src = accounts['stock_account_input']
        if move.location_dest_id.valuation_in_account_id:
            acc_dest = move.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts['stock_account_output']

        acc_valuation = accounts.get('property_stock_valuation_account_id', False)
        journal_id = accounts['stock_journal']

        if acc_dest == acc_valuation:
            raise osv.except_osv(_('Error!'),  _('Can not create Journal Entry, Output Account defined on this product and Valuation account on category of this product are same.'))

        if acc_src == acc_valuation:
            raise osv.except_osv(_('Error!'),  _('Can not create Journal Entry, Input Account defined on this product and Valuation account on category of this product are same.'))

        if not acc_src:
            raise osv.except_osv(_('Error!'),  _('There is no stock input account defined for this product or its category: "%s" (id: %d)') % \
                                    (move.product_id.name, move.product_id.id,))
        if not acc_dest:
            raise osv.except_osv(_('Error!'),  _('There is no stock output account defined for this product or its category: "%s" (id: %d)') % \
                                    (move.product_id.name, move.product_id.id,))
        if not journal_id:
            raise osv.except_osv(_('Error!'), _('There is no journal defined on the product category: "%s" (id: %d)') % \
                                    (move.product_id.categ_id.name, move.product_id.categ_id.id,))
        if not acc_valuation:
            raise osv.except_osv(_('Error!'), _('There is no inventory Valuation account defined on the product category: "%s" (id: %d)') % \
                                    (move.product_id.categ_id.name, move.product_id.categ_id.id,))
        return journal_id, acc_src, acc_dest, acc_valuation
    def create(self, cr, uid, vals, context=None):
        id=super(stock_move, self).create(cr, uid, vals, context)
        if vals.get('product_id',False) and vals.get('picking_id',False):
            picking_brw=self.pool.get('stock.picking').browse(cr,uid,vals.get('picking_id'))
            if picking_brw.picking_type_id.code =='internal':
                cr.execute("select comp_product_id from extra_prod_config where product_id=%s"%(vals.get('product_id')))
                sub_products=filter(None, map(lambda x:x[0], cr.fetchall()))
                if sub_products:
                    vals.update({'parent_stock_mv_id':id})
                    self.create_subproduct_move(cr, uid, vals, sub_products, context)
	    if picking_brw.picking_type_id.code== 'outgoing':
                if not (picking_brw.pack_length):
                    prod_brw = self.pool.get('product.product').browse(cr,uid,vals.get('product_id',False))
                    length = prod_brw.prod_length
                    width = prod_brw.prod_width
                    height = prod_brw.prod_height
                    cr.execute("update stock_picking set pack_length=%s,pack_width=%s,pack_height=%s where id=%s"%(length,width,height,picking_brw.id))
        return id
    def create_subproduct_move(self, cr, uid, vals, sub_products, context=None):
        for product in sub_products:
            vals.update({'product_id':product})
            self.create(cr, uid, vals, context)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        written=False
        if context is None:
            context = {}
        if ids:
            if type(ids) in [int, long]:
                ids = [ids]
            if not context.get('recursive',False):
                written=super(stock_move, self).write(cr, uid, ids, vals, context=context)
                picking_type=self.browse(cr,uid,ids[0]).picking_type_id.code
                if picking_type=='internal':
                    child_ids=self.search(cr,uid,[('parent_stock_mv_id','=',ids[0])])
                    if child_ids:
                        if 'product_id' in vals:
                            cr.execute("delete from stock_move where id in %s",(tuple(child_ids),))
                            context.update({'recursive': True})
                        else:
                            self.write(cr, uid, child_ids, vals, context)
                    else:
                        if 'product_id' in vals:
                            cr.execute("select comp_product_id from extra_prod_config where product_id=%s"%(vals.get('product_id')))
                            sub_products=filter(None, map(lambda x:x[0], cr.fetchall()))
                            if sub_products:
                                    vals1=self.read(cr,uid,ids[0],['product_uos_qty','date_expected','name',\
                                    'date','product_uom','product_packaging','location_dest_id','tracking_id',\
                                    'product_qty','product_uos','location_id','picking_id'],context)
                                    vals1.update({'parent_stock_mv_id':ids[0]})
                                    if vals1.get('product_uom',False):
                                        vals1.update({'product_uom':vals1.get('product_uom')[0]})
                                    if vals1.get('picking_id',False):
                                        vals1.update({'picking_id':vals1.get('picking_id')[0]})
                                    self.create_subproduct_move(cr, uid, vals1, sub_products, context)
        return written
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        if ids:
            child_ids=self.search(cr,uid,[('parent_stock_mv_id','=',ids)])
            if child_ids:
                cr.execute("delete from stock_move where id in %s",(tuple(child_ids),))
        return super(stock_move, self).unlink(cr, uid, ids, context=ctx)
    
    def _check_tracking_stock_prod_lots(self, cr, uid, ids, context=None):
        """ Checks if serial number is assigned to stock move or not.
        @return: True or False
        """
        for move in self.browse(cr, uid, ids, context=context):
            if not move.stock_prod_lots and \
               (move.state == 'done' and \
               ( \
                   (move.product_id.track_production and move.location_id.usage == 'production') or \
                   (move.product_id.track_production and move.location_dest_id.usage == 'production') or \
                   (move.product_id.track_incoming and move.location_id.usage == 'supplier') or \
                   (move.product_id.track_outgoing and move.location_dest_id.usage == 'customer') or \
                   (move.product_id.track_incoming and move.location_id.usage == 'inventory') \
               )):
                return False
        return True

    def _check_tracking(self, cr, uid, ids, context=None):
        """ Checks if serial number is assigned to stock move or not.
        @return: True or False
        """
        return True
    
    
    _columns = {
    'location_id': fields.many2one('stock.location', 'Source Location',select=True,states={'done': [('readonly', True)]}, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
    'location_dest_id': fields.many2one('stock.location', 'Destination Location',states={'done': [('readonly', True)]}, select=True, help="Location where the system will stock the finished products."),
#    'item_id':fields.related('sale_line_id', 'order_item_id', type="char",size=64,string="Item ID",store=True),
    'return_move_id': fields.integer('Return Move Id'),
    'parent_stock_mv_id': fields.function(get_parent_stock_mv_id, type='many2one', relation='stock.move', string='Parent Stock Move Id',store=True),
    } 
    
    _constraints = [
        (_check_tracking,
            'You must assign a serial number for this product.',
            ['prodlot_id']),
        (_check_tracking_stock_prod_lots,
            'You must assign a serial number for this product.',
            ['stock_prod_lots'])]
stock_move()


class shipping_response(osv.osv):
    _inherit = 'shipping.response'
    def generate_tracking_no(self, cr, uid, ids, context={}, error=True):
        res = super(shipping_response, self).generate_tracking_no(cr, uid, ids, context)
        id_obj = self.browse(cr,uid,ids[0])
        tracking_number = id_obj.picking_id.carrier_tracking_ref
        stock_obj = self.pool.get('stock.picking')
        mag_shipmentid = False
        try:
            if tracking_number:
                split_string = str(tracking_number).split(';')
                if split_string:
                    for each in split_string:
                            mag_shipmentid = stock_obj.export_shipment(cr,uid,id_obj.picking_id.id,each,'stock.picking',mag_shipmentid,{})
        except Exception, e:
            print "error string",e
        context['active_id'] = id_obj.picking_id.id
        context['active_ids'] = [id_obj.picking_id.id]
        context['active_model'] = 'stock.picking'
        return{
                    'name':_("Send Email"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'send.mail.manual',
                    'nodestroy': True,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'domain': '[]',
                    'context': context,}
        return res
shipping_response()

class stock_location(osv.osv):
    _inherit ="stock.location"
    _columns = {
    'return_location': fields.boolean('Return Location'),
    'tru':fields.boolean('TRU'),
    }
stock_location()
