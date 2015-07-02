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
#        print 'shipment_name',shipment_name
        picking_ids = self.pool.get("stock.picking").search(cr,uid,[('name', '=', str(shipment_name[0]))]) 
#        print 'picking_ids',picking_ids
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
#            print 'picking_ids',picking_ids
            
            for picking_id in picking_ids:
                try:
#                    print 'picking_id',picking_id
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
            print name
            status = picking_obj.browse(cr,uid,picking_id).state

            if status == 'draft':
                 draft_validate = picking_obj.draft_validate(cr, uid, [picking_id], context=context)


            function = picking_obj.action_process(cr, uid, [picking_id], context=context)

            res_id = function['res_id']
            do_partial = self.pool.get("stock.partial.picking").do_partial(cr,uid,[res_id],context=context)
            return picking_id
            #print"do_partial",do_partial

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
#                print"function",function
#                saleid = self.browse(cr, uid, ids[0]).sale_id.id
#                cr.execute("select invoice_id from sale_order_invoice_rel where order_id=%s"%(saleid))
#                invoice_id = cr.fetchone()
#                if len(invoice_id):
#                    self.pool.get('account.invoice').button_reset_taxes(cr, uid, invoice_id)
#                    print"invoice_id", invoice_id
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

#        print 'voucher_data',voucher_data
        voucher_id = voucher_pool.create(cr,uid,voucher_data)
#        print 'voucher_id',voucher_id
        #break

        #Get all document Number in List
        #invoice_detail,invoice_number = {},[]
        #for payment_line_id in data[0]['payment_lines']:
        #    payment_details = payment_pool.browse(cr, uid, payment_line_id)
        #    invoice_number.append(payment_details.inv_id.number)
        #    invoice_detail[payment_details.inv_id.number] = payment_details.amount_paid

        #print 'invoice_detail',invoice_detail

        if voucher_id:
            #Get all the Documents for a Partner
            res = voucher_pool.onchange_partner_id(cr, uid, [voucher_id], inv.partner_id.id, bank_journal_ids[0], inv.amount_total, inv.currency_id.id, account_data['value']['type'], date, context=context)
    #        print 'res---------------------------',res

            #Loop through each document and Pay only selected documents and create a single receipt
            for line_data in res['value']['line_ids']:
#                print 'line_data--------------------',line_data
                #create one move line per voucher line where amount is not 0.0
                if not line_data['amount']:
                    continue

#                print 'inv.number',inv.number
#                print 'line.name',line_data['name']

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
#                print 'voucher_lines',voucher_lines
                voucher_line_id = self.pool.get('account.voucher.line').create(cr,uid,voucher_lines)
#                print 'voucher_line_id',voucher_line_id

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
#            print 'tax_id',tax_id
            return tax_id
        return False

    def button_dummy(self, cr, uid, ids, context=None):
        return True
    #inheriting do_partial function so that received quantity is reset

    '''def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, address_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        picking_obj = self.pool.get('stock.picking')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking,complete,too_many,too_few,move_product_qty,prodlot_ids,product_avail = None,[],[],[],{},{},{}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s'%(move.id), False)
                assert partial_data, _('Missing partial picking data for move #%s') % (move.id)
                product_qty = partial_data.get('product_qty',0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom',False)
                product_price = partial_data.get('product_price',0.0)
                product_currency = partial_data.get('product_currency',False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                if move.product_qty == product_qty:
                    complete.append(move)
                elif move.product_qty > product_qty:
                    too_few.append(move)
                else:
                    too_many.append(move)
                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
                    product = product_obj.browse(cr, uid, move.product_id.id)
                    move_currency_id = move.company_id.currency_id.id
                    context['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)
                    if product.id in product_avail:
                        product_avail[product.id] += qty
                    else:
                        product_avail[product.id] = product.qty_available
                    if qty > 0:
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                move_currency_id, product_price)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                product.uom_id.id)
                        if product.qty_available <= 0:
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.price_get('standard_price', context)[product.id]
                            new_std_price = ((amount_unit * product_avail[product.id])\
                                + (new_price * qty))/(product_avail[product.id] + qty)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})
                        # Record the values that were chosen in the wizard, so they can be
                        # used for inventory valuation if real-time valuation is enabled.
                        move_obj.write(cr, uid, [move.id],
                                {'price_unit': product_price,
                                 'price_currency_id': product_currency})
            for move in too_few:
                product_qty = move_product_qty[move.id]
                if not new_picking:
                    new_picking = picking_obj.copy(cr, uid, move.picking_id.id,{'move_lines':[], 'state':'draft'})
                    if new_picking:
            #            self.write(cr,uid,[new_picking],{'origin':(move.picking_id.sale_id.name if move.picking_id.sale_id else '')})
			self.write(cr,uid,[new_picking],{'origin':(move.picking_id.origin if move.picking_id.origin else move.picking_id.sale_id.name if move.picking_id.sale_id else '')})	
                if product_qty != 0:
                    defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty, #TODO: put correct uos_qty
                            'picking_id' : new_picking,
                            'state': 'assigned',
                            'move_dest_id': False,
                            'price_unit': move.price_unit,
                    }
                    #It will make received_qty as product_qty
                    if move.picking_id.skip_barcode == True:
                        defaults.update(received_qty=product_qty)
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)
                move_obj.write(cr, uid, [move.id],
                        {
                            'received_qty': 0,
                            'product_qty' : move.product_qty - product_qty,
                            'product_uos_qty':move.product_qty - product_qty, #TODO: put correct uos_qty
			    'lot_ids':[(6,0,[])],
                        })
                x = move.product_qty - product_qty
            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
                for move in complete:
                    if prodlot_ids.get(move.id):
                        move_obj.write(cr, uid, [move.id], {'prodlot_id': prodlot_ids[move.id],'received_qty':product_qty})
                    else:
                        move_obj.write(cr, uid, [move.id], {'received_qty':move.product_qty})
            else:
                for move in complete:
                    if move.picking_id.skip_barcode == True:
                        move_obj.write(cr, uid, [move.id], {'received_qty':product_qty})
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty' : product_qty,
                    'product_uos_qty': product_qty, #TODO: put correct uos_qty
                }
                #It will make received_qty as product_qty
                if move.picking_id.skip_barcode == True:
                    defaults.update(received_qty=product_qty)
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)
            # At first we confirm the new picking (if necessary)
            if new_picking:
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                # Then we finish the good picking
                self.write(cr, uid, [pick.id], {'backorder_id': new_picking,'shipping_process': 'backorder'})
                self.action_move(cr, uid, [new_picking])
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                delivered_pack_id = new_picking
            else:
                self.action_move(cr, uid, [pick.id])
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id
                self.write(cr, uid, [pick.id],
                                {'scan_uid':uid,
                                 'scan_date':time.strftime('%Y-%m-%d %H:%M:%S')})
            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}
        return res'''

#    def onchange_default_code_in(self, cr, uid, ids, default_code,quantity, context=None):
#        #bar code scanning
#        #print ids, default_code, quantity, context
#        #search the product in stock move
#        #search packaging and find out product and its quantity. Update stock move as per packaging details
#        product_ids = []
#        if len(ids):
#            this_id = ids[0]
#            packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
#            if len(packaging):
#                product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
#                product_ids.append(product_id)
#                product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty
#                print"packaging",packaging
#                print"product_id",product_id
#                print"qty",product_qty
#            #product_ids = self.pool.get('product.product').search(cr, uid, [('ean13', '=', default_code)])
#            if len(product_ids):
#                stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', this_id), ('product_id','=', product_ids[0])])
#                if len(stock_move_ids):
#                    prod_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).product_qty
#                    received_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).received_qty
#                    #received_qty += quantity
#                    received_qty += product_qty
#                    if received_qty <= prod_qty:
#                        self.pool.get('stock.move').write(cr, uid, stock_move_ids[0], {'received_qty':received_qty})
#                        #self.write(cr, uid, ids, {'bcquantity':1})
#                    else:
#                        raise osv.except_osv(_('Error !'), _('Quantity exceeds the requested one.'))
#
#        return {'value': {'default_code': False, 'bcquantity': 1}}

    # Onchange has changed to maintain new Incoming shipment also.
    '''def onchange_default_code_in(self, cr, uid, ids, default_code,quantity,dest_id,note,type,state,address_id, move_lines,context=None):
        #bar code scanning
        #print ids, default_code, quantity, context
        #search the product in stock move
        #search packaging and find out product and its quantity. Update stock move as per packaging details
        print"call for function onchange_default_code_in"
        print"ids",ids
        product_ids = []
        move_ids =[]
        increment = 0
        if dest_id:
            increment += 1
            print"increament",increment
            print"dest_id",dest_id
            print"move_lines",move_lines
            timedt = time.strftime('%Y-%m-%d')
            packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
            print"packing",packaging
            if len(packaging):
                product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
                product_ids.append(product_id)
                product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty
                if dest_id:
                    print"ids not",ids
                    print"Suppliers---",self.pool.get('stock.location').search(cr,uid,[('name', '=', 'Suppliers')])
                    #dest = order.location_id.id
                    datas = {
                        'name': 'AMEX' + ': ' +(self.pool.get('product.product').browse(cr,uid,product_id).name),
                        'product_id': product_id,
                        'product_qty': product_qty,
                        'received_qty':product_qty,
                        'product_uos_qty': product_qty,
                        'product_uom': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uom_id.id,
                        'product_uos': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uos_id.id,
                        'date': timedt,
                        'date_expected': timedt,
                        'location_id': self.pool.get('stock.location').search(cr,uid,[('name', '=', 'Suppliers')])[0],
                        'location_dest_id': dest_id,
                        'picking_id': ids[0],
                        #'move_dest_id': order_line.move_dest_id.id,
                        'state': 'draft',
                        #'purchase_line_id': order_line.id,
                        'company_id': self.pool.get('res.users').browse(cr,uid,uid).company_id.id,
                        'price_unit': self.pool.get('product.product').browse(cr,uid,product_id).lst_price
                    }
                    print"datas",datas
                    move = self.pool.get('stock.move').create(cr, uid,datas,context)

                    #print"move",move
                    #move_ids.append(move)
                    #print"move_ids===",move_ids
                else:
                    print"ids if**",ids
        return {'value': {'default_code': False, 'bcquantity': 1}}

#        if len(ids):
#            this_id = ids[0]
#            packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
#            if len(packaging):
#                product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
#                product_ids.append(product_id)
#                product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty
#                print"packaging",packaging
#                print"product_id",product_id
#                print"qty",product_qty
#            #product_ids = self.pool.get('product.product').search(cr, uid, [('ean13', '=', default_code)])
#            if len(product_ids):
#                stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', this_id), ('product_id','=', product_ids[0])])
#                if len(stock_move_ids):
#                    prod_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).product_qty
#                    received_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).received_qty
#                    #received_qty += quantity
#                    received_qty += product_qty
#                    if received_qty <= prod_qty:
#                        self.pool.get('stock.move').write(cr, uid, stock_move_ids[0], {'received_qty':received_qty})
#                        #self.write(cr, uid, ids, {'bcquantity':1})
#                    else:
#                        raise osv.except_osv(_('Error !'), _('Quantity exceeds the requested one.'))

        #return {'value': {'default_code': False, 'bcquantity': 1,'move_lines': move_ids}}'''

#####saziya
    '''def onchange_default_code_in(self, cr, uid, ids, default_code,quantity,dest_id,note,type,state,address_id, move_lines,context=None):
        #bar code scanning
        #print ids, default_code, quantity, context
        #search the product in stock move
        #search packaging and find out product and its quantity. Update stock move as per packaging details
       
        product_ids,move_ids = [],[]
        move_ids =[]
        timedt = time.strftime('%Y-%m-%d')
        packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
#        print"packing",packaging
        if len(packaging):
            product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
            product_ids.append(product_id)
            product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty
#            print"product_qty",product_qty
        if dest_id:
            if not move_lines:
                print"Suppliers---",self.pool.get('stock.location').search(cr,uid,[('name', '=', 'Suppliers')])
                datas = {
                    'name': 'AMEX' + ': ' +(self.pool.get('product.product').browse(cr,uid,product_id).name),
                    'product_id': product_id,
                    'product_qty': product_qty,
                    'received_qty':product_qty,
                    'product_uos_qty': product_qty,
                    'product_uom': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uom_id.id,
                    'product_uos': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uos_id.id,
                    'date': timedt,
                    'date_expected': timedt,
                    'location_id': self.pool.get('stock.location').search(cr,uid,[('name', '=', 'Suppliers')])[0],
                    'location_dest_id': dest_id,
                    'picking_id': ids[0],
                    'state': 'draft',
                    'company_id': self.pool.get('res.users').browse(cr,uid,uid).company_id.id,
                    'price_unit': self.pool.get('product.product').browse(cr,uid,product_id).lst_price
                }
#                print"datas",datas
                mov_id = self.pool.get('stock.move').create(cr, uid,datas,context)
            else:
#                print"ids if**",move_lines
                move = self.pool.get('stock.move').search(cr,uid,[('picking_id','=',ids[0]),('product_id','=',product_id)])
                if move:
                    stockobj = self.pool.get('stock.move').browse(cr,uid,move[0])
                    orderqty = stockobj.product_qty
                    receiveqty = stockobj.received_qty
                    orderqty += product_qty
                    receiveqty += product_qty
                    self.pool.get('stock.move').write(cr,uid,move[0],{'product_qty':orderqty,'received_qty':receiveqty,'product_uos_qty':receiveqty})
                else:
                    datas = {
                        'name': 'AMEX' + ': ' +(self.pool.get('product.product').browse(cr,uid,product_id).name),
                        'product_id': product_id,
                        'product_qty': product_qty,
                        'received_qty':product_qty,
                        'product_uos_qty': product_qty,
                        'product_uom': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uom_id.id,
                        'product_uos': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uos_id.id,
                        'date': timedt,
                        'date_expected': timedt,
                        'location_id': self.pool.get('stock.location').search(cr,uid,[('name', '=', 'Suppliers')])[0],
                        'location_dest_id': dest_id,
                        'picking_id': ids[0],
                        'state': 'draft',
                        'company_id': self.pool.get('res.users').browse(cr,uid,uid).company_id.id,
                        'price_unit': self.pool.get('product.product').browse(cr,uid,product_id).lst_price
                    }
                    #print"datas",datas
                    mov_id = self.pool.get('stock.move').create(cr, uid,datas,context)
        else:
            this_id = ids[0]
#                packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
#                if len(packaging):
#                    product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
#                    product_ids.append(product_id)
#                    product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty
#                    print"packaging",packaging
#                    print"product_id",product_id
#                    print"qty",product_qty
            #product_ids = self.pool.get('product.product').search(cr, uid, [('ean13', '=', default_code)])
            if len(product_ids):
                stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', this_id), ('product_id','=', product_ids[0])])
                if len(stock_move_ids):
                    prod_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).product_qty
                    received_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).received_qty
                    #received_qty += quantity
                    received_qty += product_qty
                    if received_qty <= prod_qty:
                        self.pool.get('stock.move').write(cr, uid, stock_move_ids[0], {'received_qty':received_qty})
                    else:
                        raise osv.except_osv(_('Error !'), _('Quantity exceeds the requested one.'))
        return {'value': {'default_code': False, 'bcquantity': 1}}'''
#######

    def onchange_default_code_out(self, cr, uid, ids, default_code,quantity, context=None):
        #bar code scanning
        #print ids, default_code, quantity, context
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

#    def heidler_output_file_creation(self, cr, uid, ids, context=None):
#        self.pool.get('heidler.info').create_heidler_file(cr, uid, ids, context)
#        return True
        #        heidler_output_file = "Record identification;Customer Number;Receiver-Name1;Receiver-Name2;Receiver-Name3;Receiver-street;Receiver-country;Receiver-zip code;Receiver Town;Receiver region/state;Train station receiver;Contact person receiver;Telephone number receiver;Fax number receiver;VAT No.Receiver;ILN No.Receiver;Mandator;Type of dispatch;Delivery information1;Delivery information2;Del.information additive 1;Del.information additive 2;Delivery note number;Order number;Purchase order number;Value of goods;Value of goods currency;Cash on delivery;Cash on delivery currency;Cash on delivery - paying condition;Cash on delivery - reason for payment;Insurance value;Insurance value currency;Terms of Trade-ID;Terms of payment;Terms of payment duty/tax;Carrier account number;Special service;Shipment content;Type of date delivery;Date of date delivery;Time of date/time delivery;Neutral sender-name1;Neutral sender-name2;Neutral sender name3;Neutral sender-street;Neutral sender-country;Neutral sender-zip code;Neutral sender-town;Invoice recipient-name1;Invoice recipient-name2;Invoice recipient-name3;Invoice recipeint-street;Invoice recipient-country;Invoice recipient-zip code;Invoice recipient-town;Routing code;ID delivery depot;Way bill number;Weight gross;Weight net;Number of packages; Package number;Package type;Length of Package;Width of package;Height of package;Packing place ID;Host Package ID;Package number;Tracking number;Print date;Dispatch date;Charge amount;Charge amount currency;Status;Manifest list number;Status;Error message;Dangerous goods status;Reference number;Broker name;Broker-phone number;Hold-At-Location;Hold-At-Location phone;Hold-at-location contact person;Number/Article;Additive line1;Additive line2;Free advice1;Free advice2;Status;Recevier email address;PaymentID\n"
#        #heidler_output_file += IMP;;;;;;;;;;;;;;;;;;;;;;{0};;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;L;;;;;;;;;;;;;;;;;;;;;;;;;"
#        #heidler file created should be placed in one of the location so that it can print the barcode label.
#        #compname = socket.gethostname()
#        for picking in self.browse(cr, uid, ids):
#            #the data needed by the file
#            delivery_number = picking.name
#            order_number = picking.sale_id.name
#            customer_number = (picking.address_id.partner_id.customer_seq or '')
#            receiver_name1 = picking.address_id.name + ' ' + (picking.address_id.lastname or ' ')
#            receiver_name3 = (picking.address_id.partner_id.name or ' ')
#            receiver_street = (picking.address_id.street or ' ') + (picking.address_id.street2 or ' ')
#            reciever_country = picking.address_id.country_id.code
#            receiver_zipcode = (picking.address_id.pobox or picking.zip)
#            receiver_town = (picking.address_id.town or '')
#            receiver_state = (picking.address_id.state_id.code or '')
#            receiver_telephone = (picking.address_id.phone or '')
#            fax_number_receiver = (picking.address_id.fax or '')
#            receiver_vat = (picking.address_id.partner_id.vat or '')
#            mandator = 1
#            type_of_dispatch = picking.carrier_id.name
#            delivery_note = picking.name
#            order_number = picking.sale_id.name
#            weight = int(picking.weight_net)
#
#            #For the undelivered address....take it based on the country you are delivering (check )
#            undelivered_address_brw = False
#            dynamic_header_ids = self.pool.get('dynamic.header').search(cr, uid, [('country_id.code', '=', reciever_country)])
#            if not len(dynamic_header_ids):
#                defdynamic_header_ids = self.pool.get('dynamic.header').search(cr, uid, [('type', '=', 'default')])
#                if len(defdynamic_header_ids):
#                    undelivered_address_brw = self.pool.get('dynamic.header').browse(cr, uid, defdynamic_header_ids[0]).res_partner_address_id
#            else:
#                undelivered_address_brw = self.pool.get('dynamic.header').browse(cr, uid, dynamic_header_ids[0]).res_partner_address_id
#            #type of dispatch:
#            '''
#            RM STD
#            RM RCD
#            RM Special
#            RM Tracked
#            DPD
#            DPD KP
#            DPD UK
#            DHL
#            D-POST
#            CORREOS
#            PostNL
#            PostNL Tracked
#            TOURLINE
#            Combined
#            '''
#            type_of_dispatch = False
#            if picking.carrier_id.name == 'DPD UK' or picking.carrier_id.name=='DPD KP':
#                type_of_dispatch = 'DPD'
#            elif picking.carrier_id.name == 'Royal Mail Tracked':
#                type_of_dispatch = 'RM TRACK'
#            elif picking.carrier_id.name == 'Royal Mail Standard':
#                type_of_dispatch = 'RM STD LTR'
#            else:
#                type_of_dispatch = picking.carrier_id.name
#            if undelivered_address_brw:
#                sender_name1 = 'Undelivered:'
#                sender_name3 = undelivered_address_brw.name or 'Vision Direct'
#                sender_street = (undelivered_address_brw.street or '') + ' '+ (undelivered_address_brw.street2 or '')
#                sender_country = undelivered_address_brw.country_id.code
#                sender_zipcode = (undelivered_address_brw.pobox or undelivered_address_brw.zip)
#                sender_town = undelivered_address_brw.town
#                #sender_state = (undelivered_address_brw.state_id.code or '')
#            else:
#                sender_name1 = 'Undelivered:'
#                sender_name3 = 'Vision Direct'
#                sender_street = 'PO BOX 351'
#                sender_country = 'GB'
#                sender_zipcode = 'MK41 9XZ'
#                sender_town = 'Bedford'
#                #sender_state = ''
#        #serverip = socket.gethostbyname(socket.gethostname())
#        #output:"IMP";"%custnumber";"%recename1";;%recnmae3;"%recstreet";"%reccountry";"%reccode";"%rec_town";"%rec_region/state";;"%recname1";"%telhone";%fax;"%vat";;%mand;"%type of distpath";;;;;"%delivernumber";"%ordernumber";;;;;;;;;;;;;;;;;;;"%underlivered";"%sendernm2";;"%posenderstreet";"%sendercountry";"%senderpost";"%sendertown";;;;;;;;;;;"%grossweight";"%netweight";1;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
#            heidler_output_file += '''%s;%s;%s;;%s;%s;%s;%s;%s;%s;;%s;%s;%s;%s;;%s;%s;;;;;%s;%s;;;;;;;;;;;;;;;;;;;%s;%s;;%s;%s;%s;%s;;;;;;;;;;;%s;%s;%s;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;'''%('IMP', customer_number,
#                                                    receiver_name1,
#                                                    receiver_name3,
#                                                    receiver_street,
#                                                    reciever_country,
#                                                    receiver_zipcode,
#                                                    receiver_town,
#                                                    receiver_state,
#                                                    receiver_name1,
#                                                    receiver_telephone,
#                                                    fax_number_receiver,
#                                                    receiver_vat,
#                                                    mandator,
#                                                    type_of_dispatch,
#                                                    delivery_number,
#                                                    order_number,
#                                                    sender_name1,
#                                                    sender_name3,
#                                                    sender_street,
#                                                    sender_country,
#                                                    sender_zipcode,
#                                                    sender_town,
#                                                    weight,
#                                                    weight,
#                                                    1
#
#                                                    )
#            #output the file to one a demo location:
#            import_folder = '/home/openerp/import/'
#            computer_name = socket.gethostname()
#            filename = delivery_number + '_PACK34_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.bak'
#            fileopen = open(import_folder+filename, 'w')
#            fileopen.write(heidler_output_file)
#            fileopen.close()
#
#        return True
stock_picking()

## cox gen2 commented the below class
'''class stock_picking_out(osv.osv):
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

stock_picking_out()'''

class stock_move(osv.osv):
    _name = "stock.move"
    _inherit = 'stock.move'
#    def get_image(self, cr, uid, ids, product_id, arg, context={}):
#        res = {}
#
#        for each in self.browse(cr, uid, ids):
#            product_id = each.product_id.id
#            packaging_ids = self.pool.get('product.packaging').search(cr, uid, [('product_id', '=', product_id),('no_bar','=',True)])
#            if len(packaging_ids):
#                res[each.id] = self.pool.get('product.packaging').browse(cr, uid, packaging_ids[0]).tr_barcode_id.image
#            else:
#                res[each.id] = '/9j/4AAQSkZJRgABAQEASABIAAD/4QCqRXhpZgAATU0AKgAAAAgABQEyAAIAAAAUAAAASlEQAAEA\nAAABAQAAAFERAAQAAAABAAALE1ESAAQAAAABAAALE4dpAAQAAAABAAAAXgAAAAAyMDA3OjA1OjA4\nIDIxOjU2OjI4AAABkoYABwAAADIAAABwAAAAAFVOSUNPREUAAEMAcgBlAGEAdABlAGQAIAB3AGkA\ndABoACAAVABoAGUAIABHAEkATQBQ/9sAQwACAQECAQECAgICAgICAgMFAwMDAwMGBAQDBQcGBwcH\nBgcHCAkLCQgICggHBwoNCgoLDAwMDAcJDg8NDA4LDAwM/9sAQwECAgIDAwMGAwMGDAgHCAwMDAwM\nDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwM/8AAEQgAGAAYAwEi\nAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQE\nAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2\nNzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Sl\npqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8B\nAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUh\nMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJ\nSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2\nt7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/aAAwDAQACEQMRAD8A/fyi\niigAooooAKKKKACiiigD/9k=\n'
#
#        return res

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
######

'''    def onchange_default_code_in(self, cr, uid, ids, default_code,quantity,dest_id,note,type,state,address_id, move_lines,context=None):
        #bar code scanning
        #print ids, default_code, quantity, context
        #search the product in stock move
        #search packaging and find out product and its quantity. Update stock move as per packaging details
#        print"call for function onchange_default_code_in"
#        print"ids",ids
        product_ids = []
        move_ids =[]
        timedt = time.strftime('%Y-%m-%d')
        packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
#        print"packing",packaging
        if len(packaging):
            product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
            product_ids.append(product_id)
            product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty

        if dest_id:
            if not move_lines:
#                print"increament",increment
#                print"dest_id",dest_id
#                print"move_lines",move_lines
                if dest_id:
#                    print"ids not",ids
#                    print"Suppliers---",self.pool.get('stock.location').search(cr,uid,[('name', '=', 'Suppliers')])
                    #dest = order.location_id.id
                    datas = {
                        'name': 'AMEX' + ': ' +(self.pool.get('product.product').browse(cr,uid,product_id).name),
                        'product_id': product_id,
                        'product_qty': product_qty,
                        'received_qty':product_qty,
                        'product_uos_qty': product_qty,
                        'product_uom': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uom_id.id,
                        'product_uos': self.pool.get('product.product').browse(cr,uid,product_id).product_tmpl_id.uos_id.id,
                        'date': timedt,
                        'date_expected': timedt,
                        'location_id': self.pool.get('stock.location').search(cr,uid,[('name', '=', 'Suppliers')])[0],
                        'location_dest_id': dest_id,
                        'picking_id': ids[0],
                        'state': 'draft',
                        'company_id': self.pool.get('res.users').browse(cr,uid,uid).company_id.id,
                        'price_unit': self.pool.get('product.product').browse(cr,uid,product_id).lst_price
                    }
#                    print"datas",datas
                    move = self.pool.get('stock.move').create(cr, uid,datas,context)
                else:
                    print"ids if**",ids
        else:
            this_id = ids[0]
#                packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
#                if len(packaging):
#                    product_id = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).product_id.id
#                    product_ids.append(product_id)
#                    product_qty = self.pool.get('product.packaging').browse(cr,uid,packaging[0]).qty
#                    print"packaging",packaging
#                    print"product_id",product_id
#                    print"qty",product_qty
            #product_ids = self.pool.get('product.product').search(cr, uid, [('ean13', '=', default_code)])
            if len(product_ids):
                stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', this_id), ('product_id','=', product_ids[0])])
                if len(stock_move_ids):
                    prod_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).product_qty
                    received_qty = self.pool.get('stock.move').browse(cr, uid, stock_move_ids[0]).received_qty
                    #received_qty += quantity
                    received_qty += product_qty
                    if received_qty <= prod_qty:
                        self.pool.get('stock.move').write(cr, uid, stock_move_ids[0], {'received_qty':received_qty})
                    else:
                        raise osv.except_osv(_('Error !'), _('Quantity exceeds the requested one.'))
        return {'value': {'default_code': False, 'bcquantity': 1}}'''
##############

#    def create(self, cr, uid, data):
#        result = super(stock_move, self).create(cr, uid, data)
#        print"result&&&&&&&&&&&&&&&&", result
#        stock_data = self.read(cr, uid, result, context=None)
#        print"stock_data", stock_data
#        if stock_data['product_packaging']:
#            product_barcode = self.pool.get('product.packaging').browse(cr, uid, stock_data['product_packaging']).name
#            tr_bar_ids = self.pool.get('tr.barcode').search(cr, uid,[('code','=',product_barcode)])
#            if tr_bar_ids:
#                image = self.pool.get('tr.barcode').browse(cr, uid, tr_bar_ids[0]).image
#                self.write(cr, uid, result,{"pack_nobar_image":image})
#        return result


stock_move()

class delivery_carrier(osv.osv):
    _inherit ="delivery.carrier"
    _columns ={
        'carrier_image': fields.binary('Delivery Method Image'),
        'is_scan_tracking': fields.boolean('Scan Tracking Reference', help="Scanning Tracking reference from a Barcode!")
    }
delivery_carrier()
