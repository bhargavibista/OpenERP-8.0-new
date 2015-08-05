        # -*- encoding: utf-8 -*-
    ##############################################################################
    #
    #    OpenERP, Open Source Management Solution
    #    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
    #    $Id$
    #
    #    This program is free software: you can redistribute it and/or modify
    #    it under the terms of the GNU General Public License as published by
    #    the Free Software Foundation, either version 3 of the License, or
    #    (at your option) any later version.
    #
    #    This program is distributed in the hope that it will be useful,
    #    but WITHOUT ANY WARRANTY; without even the implied warranty of
    #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #    GNU General Public License for more details.
    #
    #    You should have received a copy of the GNU General Public License
    #    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    #
    ##############################################################################




from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
import openerp.addons.decimal_precision as dp
import logging
import socket

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _order = 'id desc'
    _columns = {
        'bcquantity': fields.integer('Quantity'),
#        'default_code': fields.char('Bar Code', size=13, help="Keep focus on this field and use bar code scanner to scan products"),
#        'default_code_out': fields.char('Bar Code', size=13, help="Keep focus on this field and use bar code scanner to scan products"),
        'skip_barcode': fields.boolean('Skip Barcode Scanning'),
        'dest_id': fields.many2one('stock.location', 'Destination Location', help="Location where the system will stock the finished products."),
        'scan_uid':fields.many2one('res.users','Scanned By',readonly=True),
        'scan_date':fields.datetime('Scanned Date',readonly=True),
        #'marked_packing': fields.boolean('Marked for Packing')
        'shipping_process': fields.selection([
                                ('backorder','Back Order'),
                                ('draft', 'Open'),
                                ('marked', 'Marked for Packing'),
                                ('partial', 'Awaiting Goods'),
                                ('wait', 'Order on Hold'),
                                ('printed', 'Packing List Printed'),
                                ('barcode', 'Waiting for Scanning'),
                                ('done', 'Done'),
                                ('approved', 'Backorder Allowed')
                                ], 'Shipping Process', readonly=True, select=True),
        'ship_date': fields.datetime('Shipped Date', help="Date of Completion"),
#        'must_buy_purchase': fields.boolean('check Must buy'),
        #'wait': fields.boolean('Wait', readonly=True, help="Order is hold until further notice from customer")
    }
    _defaults = {
        'bcquantity': lambda *a: 1,
        'shipping_process': lambda *a: 'draft',
#        'must_buy_purchase': False,
        'skip_barcode' : True,
    }

    def make_available(self, cr, uid, ids, context=None):
        ship_state = self.browse(cr,uid,ids[0]).shipping_process
        if ship_state == 'partial' or ship_state == 'backorder':
            self.write(cr, uid, ids, {'shipping_process': 'approved'})
        if ship_state == 'backorder':
            self.write(cr, uid, ids, {'carrier_id': '','carrier_tracking_ref':''})
        return True
    
    def split_delivery(self, cr, uid, ids, context={}):
        #Function splits the delivery order into two, one with products available in stock and the other with those not available in stock.
        #Line items stock availability  = stock.move --> state = confirmed => "Stock Not Available" and --> state = assigned => "Available"
        try:
            self.action_assign(cr, uid, ids)
        except:
            pass
        for picking in self.browse(cr, uid, ids):
            origin = picking.origin
            move_lines = picking.move_lines
            not_in_stock_moveid = []
            for moves in move_lines:
                if moves.state == 'confirmed':
                    not_in_stock_moveid.append(moves.id)
            if len(not_in_stock_moveid) and len(move_lines) > 1:
                parent_picking_id = picking.id
                new_picking_id = self.copy(cr, uid, parent_picking_id, default={'origin': origin}, context=context)
                self.write(cr, uid, [new_picking_id], {'origin': origin, 'shipping_process': 'draft'})
                #update not in stock => movelines to be attached to the new picking, and delete new picking move lines
                cr.execute('delete from stock_move where picking_id=%s'% (new_picking_id)) 
                for nis_moveid in not_in_stock_moveid:
                    cr.execute('update stock_move set picking_id=%s where id=%s'%(new_picking_id, nis_moveid))
                #validate the picking
                self.draft_validate(cr, uid, [new_picking_id])
                try:
                    self.action_assign(cr, uid, [new_picking_id])
                except:
                    pass
                
        return True
	
    def get_shipping_label(self, cr, uid, shipment_name, context=None):
        import os
        picking_ids = self.pool.get("stock.picking").search(cr,uid,[('name', '=', str(shipment_name[0]))]) 
        if len(picking_ids):
            service = netsvc.LocalService("report.stock.print.label");
            (result, format) = service.create(cr, uid, [picking_ids[0]], {}, context)
            mountpath = "/opt/openerp_export/shipping_labels/"
            if not os.path.exists(mountpath):
                os.makedirs(mountpath)
                os.chmod(mountpath,0o777)
            f_name = mountpath+str(shipment_name[0])+"."+format
            open(f_name,'wb').write(result)
            os.chmod(mountpath,0o777)
            return picking_ids[0]
        return 1
		
    def xmlrpc_validate_order(self, cr, uid, picking_names={}, context={}):
        if len(picking_names) ==0:
            return 1
        
        for picking_name in picking_names:
            #picking_id = 15595
            #this is run so that the availability of stock is checked
            picking_obj = self.pool.get('stock.picking')
            picking_ids = picking_obj.search(cr,uid,[('name','=',str(picking_name))])
            
            for picking_id in picking_ids:
                try:
                    picking_obj.action_assign(cr, uid, [picking_id])
                except:
                    pass
                    #try except to avoid any kind of message
            #Make the skip scanning active to skip the scanning for now
            
            picking_obj.write(cr, uid, [picking_id], {'skip_barcode': True})
            #need to provide the back order logic here
            context['active_model']='ir.ui.menu'
            context['active_ids']= [picking_id]
            context['active_id']=picking_id
            picking_brw = picking_obj.browse(cr,uid,picking_id)
            name = picking_brw.name
            status = picking_obj.browse(cr,uid,picking_id).state

            if status == 'draft':
#                 draft_validate = picking_obj.draft_validate(cr, uid, [picking_id], context=context) ##odoo8 changes
                draft_validate = picking_obj.action_confirm(cr, uid, [pick.id], context=context)

#            function = picking_obj.action_process(cr, uid, [picking_id], context=context)
#
#            res_id = function['res_id']
#            do_partial = self.pool.get("stock.partial.picking").do_partial(cr,uid,[res_id],context=context)
            function = picking_obj.do_enter_transfer_details(cr, uid, [pick.id], context=context)
                
                #self.pool.get('stock.picking').write(cr,uid,[pick.id],{'scan_uid':uid,'scan_date':time.strftime('%Y-%m-%d %H:%M:%S')})
            res_id = function.get('res_id')
            if res_id:
#                    cox gen2
                do_partial = self.pool.get("stock.transfer_details").do_detailed_transfer(cr,uid,[res_id],context=context)
            return picking_id

        return 1
    
    def xmlrpc_process(self, cr, uid, ids, context=None):
 #       logger.notifyChannel('init', netsvc.LOG_WARNING, ' starting date time test________%s' %(time.strftime('%Y-%m-%d %H:%M:%S'),))
        obj_data = ids[0]
        partial_datas = {
            'delivery_date' : time.strftime('%Y-%m-%d %H:%M:%S')
        }
        pick_obj = self.pool.get('stock.picking')
        lot_object = self.pool.get('stock.picking').browse(cr, uid, obj_data)
        for pick in pick_obj.browse(cr, uid, ids, context=context):
            need_product_cost = (pick.type == 'in')
            p_moves = {}

            for move in lot_object.move_lines:
                p_moves[move.id] = move
                partial_datas['move%s' % (move.id)] = {
                    'product_id' : p_moves[move.id].product_id.id,
                    'product_qty' : p_moves[move.id].product_qty,
                    'product_uom' : p_moves[move.id].product_uom.id,
                    'prodlot_id' : p_moves[move.id].prodlot_id.id,
                }
                if (move.picking_id.type == 'in') and (move.product_id.cost_method == 'average'):
                    partial_datas['move%s' % (move.id)].update({
                                                    'product_price' : p_moves[move.id].cost,
                                                    'product_currency': p_moves[move.id].currency.id,
                                                    })
        pick_obj.do_partial(cr, uid, ids, partial_datas, context=context)
#        logger.notifyChannel('init', netsvc.LOG_WARNING, 'END date time________%s' %(time.strftime('%Y-%m-%d %H:%M:%S'),))
        return True
    #inherit def action_done(self, cr, uid, ids, context=None): to complete the shipping process
#    def action_done(self, cr, uid, ids, context=None):
#        super(stock_picking, self).action_done(cr, uid, ids, context=None)
#        type = False
#        sale_id = False
#        for picking in self.browse(cr, uid, ids):
#            shipdate = picking.ship_date
#            if shipdate != False:
#                self.write(cr, uid, ids, {'date_done': shipdate})
#            type = picking.type
#            if type == 'out':
#                customer_reference = picking.sale_id.client_order_ref
#                sale_id = picking.sale_id.id
#                if sale_id:
#                    shop_id = picking.sale_id.shop_id.id
#                    mysql_conf_ids = self.pool.get('mysql.db').search(cr, uid, [('shop_id','=',shop_id)])
#                    if len(mysql_conf_ids):
#                        push_back_status = False
#                        push_back_status = self.pool.get('mysql.db').browse(cr, uid, mysql_conf_ids[0]).push_back_order_status
#                        if push_back_status:
#                                jshopconnectobj = self.pool.get('mysql.db').connect(cr, uid, mysql_conf_ids)
#                                self.pool.get('mysql.db').update_shipping_for_order(cr, uid, ids, jshopconnectobj, sale_id,customer_reference)
#                            
#        for thisobj in self.browse(cr, uid, ids, context):
#            picking_type = thisobj.type
#            #updating the scanned by user and
#            scan_date = time.strftime('%Y-%m-%d %H:%M:%S')
#
#            #self.write(cr, uid, ids, {})
#            picking_dict = {'scan_uid': uid, 'scan_date': scan_date}
#            if picking_type == 'out':
#                picking_dict.update({'shipping_process': 'done'})
#                #self.write(cr, uid, ids, {'shipping_process': 'done'})
#
#                #adding the Heidler output file creation code here
#                #try to create...or it will need manual intervention
#                try:
#                    self.heidler_output_file_creation(cr, uid, ids, context)
#                except:
#                    note = self.browse(cr, uid, ids[0]).note
#                    if note:
#                        note += '\n Heidler file not created! Please rerun the Heidler Output Process!'
#                    else:
#                        note = '\n Heidler file not created! Please rerun the Heidler Output Process!'
#                    picking_dict.update({'note': note})
#            self.write(cr, uid, ids, picking_dict)
#        
#        #adding the Heidler output file creation code here
#        #try to create...or it will need manual intervention
#        if type == 'out' and sale_id:
#            try:
#                self.heidler_output_file_creation(cr, uid, ids, context)
#            except:
#                note = self.browse(cr, uid, ids[0]).note
#                if note:
#                    note += '\n Heidler file not created! Please rerun the Heidler Output Process!'
#                else:
#                    note = '\n Heidler file not created! Please rerun the Heidler Output Process!'
#                self.write(cr, uid, ids, {'note': note})
#            if self.browse(cr, uid, ids[0]).sale_id.shop_id.is_wholesale == False:
#                journal_pool = self.pool.get('account.voucher')
#                wf_service = netsvc.LocalService("workflow")
#                shop_id = self.browse(cr, uid, ids[0]).sale_id.shop_id.id
#                date = self.browse(cr, uid, ids[0]).ship_date
#                if date != False:
#                    self.write(cr, uid, ids, {'date_done': date})
#                else:
#                    date == self.browse(cr, uid, ids[0]).date_done
#                get_mysql_conf = self.pool.get('mysql.db').search(cr, uid, [('shop_id', '=', shop_id)])
#                sale_journal_ids = []
#                if len(get_mysql_conf):
#                    sale_journal_ids = [self.pool.get('mysql.db').browse(cr, uid, get_mysql_conf[0]).sale_journal_id.id]
#                else:
#                    sale_journal_ids = journal_pool.search(cr, uid, [('name', '=', 'Current')])
#                #account_data = self.get_accounts(cr,uid,custid,bank_journal_ids[0])
#                context={'lang': u'en_US', 'search_default_available': 1, 'tz': False, 'active_model': 'stock.picking', 'contact_display': 'partner_address', 'active_ids': ids , 'active_id':ids[0], 'retail_shop':True, 'journal_id':sale_journal_ids[0], 'invoice_date':date}
#                function = self.pool.get('stock.invoice.onshipping').open_invoice(cr, uid, ids, context=context)
#                saleid = self.browse(cr, uid, ids[0]).sale_id.id
#                cr.execute("select invoice_id from sale_order_invoice_rel where order_id=%s"%(saleid))
#                invoice_id = cr.fetchone()
#                if len(invoice_id):
#                    self.pool.get('account.invoice').button_reset_taxes(cr, uid, invoice_id)
#                    wf_service.trg_validate(uid, 'account.invoice', invoice_id[0], 'invoice_open', cr)
#                    self.make_payment_of_invoice(cr, uid, ids, invoice_id[0])
#
#
#            return True

    def make_payment_of_invoice(self, cr, uid, ids, invoice_id):

        voucher_id = False
        inv_pool = self.pool.get('account.invoice')
        payment_pool = self.pool.get('payment.lines.wizard')

        voucher_pool = self.pool.get('account.voucher')
        inv = inv_pool.browse(cr, uid, invoice_id)

        partner_pool = self.pool.get('res.partner')


        shop_id = self.browse(cr, uid, ids[0]).sale_id.shop_id.id
        get_mysql_conf = self.pool.get('mysql.db').search(cr, uid, [('shop_id', '=', shop_id)])
        bank_journal_ids = []
        if len(get_mysql_conf):
            bank_journal_ids = [self.pool.get('mysql.db').browse(cr, uid, get_mysql_conf[0]).bank_journal_id.id]
        else:
            bank_journal_ids = journal_pool.search(cr, uid, [('name', '=', 'Current')])
        if not len(bank_journal_ids):
            return True
        context = {}
        context.update({
                'default_partner_id': inv.partner_id.id,
                'default_amount': inv.residual,
                'default_name':inv.name,
                'close_after_process': True,
                'invoice_type':inv.type,
                'invoice_id':inv.id,
                'journal_id':bank_journal_ids[0],
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
        })
        tax_id = self._get_tax(cr, uid, context)

        account_data = self.get_accounts(cr,uid,inv.partner_id.id,bank_journal_ids[0])
        date = time.strftime('%Y-%m-%d')

        voucher_data = {
                'period_id': inv.period_id.id,
                'account_id': account_data['value']['account_id'],
                'partner_id': inv.partner_id.id,
                'journal_id':bank_journal_ids[0],
                'currency_id': inv.currency_id.id,
                'reference': inv.reference,
                #'narration': data[0]['narration'],
                #'amount': inv.amount_total,
                'amount': 0.000,
                'type':account_data['value']['type'],
                'state': 'draft',
                'pay_now': 'pay_later',
                'name': '',
                'date': time.strftime('%Y-%m-%d'),
                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher',context=None),
                'tax_id': tax_id,
                'payment_option': 'without_writeoff',
                'comment': _('Write-Off'),
            }

        voucher_id = voucher_pool.create(cr,uid,voucher_data)
        #break

        #Get all document Number in List
        #invoice_detail,invoice_number = {},[]
        #for payment_line_id in data[0]['payment_lines']:
        #    payment_details = payment_pool.browse(cr, uid, payment_line_id)
        #    invoice_number.append(payment_details.inv_id.number)
        #    invoice_detail[payment_details.inv_id.number] = payment_details.amount_paid


        if voucher_id:
            #Get all the Documents for a Partner
            res = voucher_pool.onchange_partner_id(cr, uid, [voucher_id], inv.partner_id.id, bank_journal_ids[0], inv.amount_total, inv.currency_id.id, account_data['value']['type'], date, context=context)

            #Loop through each document and Pay only selected documents and create a single receipt
            for line_data in res['value']['line_ids']:
                #create one move line per voucher line where amount is not 0.0
                if not line_data['amount']:
                    continue


                #if line_data['name'] in invoice_number:
                voucher_lines = {
                    'move_line_id': line_data['move_line_id'],
                    'amount': inv.amount_total,
                    'name': line_data['name'],
                    'amount_unreconciled': line_data['amount_unreconciled'],
                    'type': line_data['type'],
                    'amount_original': line_data['amount_original'],
                    'account_id': line_data['account_id'],
                    'voucher_id': voucher_id,
                }
                voucher_line_id = self.pool.get('account.voucher.line').create(cr,uid,voucher_lines)

            #Add Journal Entries
            voucher_pool.action_move_line_create(cr,uid,[voucher_id])
            #self.write(cr, uid, ids, {'state':'done'}, context)
            message = "Receipt ' "+str(voucher_data['reference'])+" ' Created"
            voucher_pool.log(cr, uid, voucher_id, message)

        return True
    def get_accounts(self, cr, uid, partner_id=False, journal_id=False, context=None):
        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        default = {
            'value':{},
        }

        if not partner_id or not journal_id:
            return default

        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
        tr_type = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
            tr_type = 'sale'
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
            tr_type = 'purchase'
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            tr_type = 'receipt'

        default['value']['account_id'] = account_id
        default['value']['type'] = tr_type

        return default
    
    def _get_tax(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if not journal_id:
            ttype = context.get('type', 'bank')
            res = journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)
            if not res:
                return False
            journal_id = res[0]

        if not journal_id:
            return False
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id
            return tax_id
        return False

    def button_dummy(self, cr, uid, ids, context=None):
        return True
    #inheriting do_partial function so that received quantity is reset

    def onchange_default_code_out(self, cr, uid, ids, default_code,quantity, context=None):
        #bar code scanning
        #search the product in stock move
        #search packaging and find out product and its quantity. Update stock move as per packaging details
        product_ids=[]
        if len(ids):
            this_id = ids[0]
            packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
            if len(packaging):
                product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
                product_ids.append(product_id)
                product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty
            #product_ids = self.pool.get('product.product').search(cr, uid, [('ean13', '=', default_code)])
            if len(product_ids):
                stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', this_id), ('product_id','=', product_ids[0])])
                if len(stock_move_ids):
                    prod_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).product_id.qty_available
                    qty_req = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).product_qty
                    received_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).received_qty
                    #received_qty += quantity
                    received_qty += product_qty
                    if received_qty <= prod_qty and received_qty <= qty_req:
                        self.pool.get('stock.move').write(cr, uid, stock_move_ids[0], {'received_qty':received_qty})
                        #self.write(cr, uid, ids, {'bcquantity':1})
                    elif received_qty > qty_req:
                        raise osv.except_osv(_('Error !'), _('Quantity exceeds the requested one.'))
                    else:
                        raise osv.except_osv(_('Error !'), _('Quantity scanned greater than the stock availability.'))

        return {'value': {'default_code': False, 'bcquantity': 1}}

stock_picking()

class stock_move(osv.osv):
    _name = "stock.move"
    _inherit = 'stock.move'

    def _check_tracking_stock_prod_lots(self, cr, uid, ids, context=None):
        """ Checks if serial number is assigned to stock move or not.
        @return: True or False
        """
        for move in self.browse(cr, uid, ids, context=context):
            if not move.stock_prod_lots and (move.picking_id.skip_barcode==False and \
               (move.state == 'done' and \
               ( \
                   (move.product_id.track_production and move.location_id.usage == 'production') or \
                   (move.product_id.track_production and move.location_dest_id.usage == 'production') or \
                   (move.product_id.track_incoming and move.location_id.usage == 'supplier') or \
                   (move.product_id.track_outgoing and move.location_dest_id.usage == 'customer') or \
                   (move.product_id.track_incoming and move.location_id.usage == 'inventory') \
               ))):
                return False
        return True

    def check_tracking(self, cr, uid, ids,lot_id, context=None):
        """ Checks if serial number is assigned to stock move or not.
        @return: True or False
        """
        return True

    _columns = {
        'received_qty': fields.integer('Received Quantity'),
#        'pack_nobar_image': fields.function(get_image, string="Image", type="binary", method=True),#binary("Image"),
        'status':fields.selection([
            ('draft','Not Scanned'),
            ('done','Scanned')],'Status', select=True, readonly=True),
        'note': fields.text('Notes'),
        'reference': fields.related('picking_id', 'name', type="text", string="Reference", store=True),
        'premerge_purchase_id': fields.many2one('purchase.order', 'Pre-Merge Purchase Order Reference'),
        'stock_prod_lots': fields.many2many('stock.production.lot', 'stock_move_lot', 'stock_move_id','production_lot','Serial numbers',readonly=True)
    }
    _defaults = {
        'received_qty': lambda *a: 0,
        'status': 'draft',
    }
    _constraints = [
        (_check_tracking_stock_prod_lots,
            'You must assign a serial number for this product.',
            ['stock_prod_lots'])]
######


stock_move()

class delivery_carrier(osv.osv):
    _inherit ="delivery.carrier"
    _columns ={
        'carrier_image': fields.binary('Delivery Method Image'),
        'is_scan_tracking': fields.boolean('Scan Tracking Reference', help="Scanning Tracking reference from a Barcode!")
    }
delivery_carrier()
