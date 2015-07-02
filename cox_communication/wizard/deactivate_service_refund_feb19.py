# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class refund_customer_payment(osv.osv_memory):
    _inherit = "refund.customer.payment"
    _columns = {
    'diff_cc_refund': fields.boolean('Refund on Different CC/CC Expire'),
    'refund_cc_number' :fields.char('New CC',size=256,help="Credit Card Number"),
    'refund_cc_expiration_date' :fields.char('CC Exp Date [MMYYYY]',size=6,help="Credit Card Expiration Date"),
    }
    
    def refund_customer(self,cr,uid,ids,context={}):
        active_id = context.get('active_id',False)
        if active_id:
            authorize_obj = self.pool.get('authorize.net.config')
            config_ids = authorize_obj.search(cr,uid,[])
            return_object = self.pool.get('return.order')
            invoice_obj = self.pool.get('account.invoice')
            line_obj = self.pool.get('sale.order.line')
            if config_ids:
                context['linked_refund'] = True
                return_obj = return_object.browse(cr,uid,active_id)
                total= return_obj.amount_total
                wizard_obj = self.browse(cr, uid, ids[0])
                cc_number = wizard_obj.cc_number
                cust_profile_id = return_obj.linked_sale_order.partner_id.customer_profile_id
                cust_payment_profile_id = return_obj.linked_sale_order.customer_payment_profile_id
                auth_transaction_id = wizard_obj.auth_transaction_id
                cc_number = wizard_obj.cc_number
                if cc_number and len(cc_number)==4:
                    cc_number='XXXX'+''+str(cc_number)
                act_model = context.get('active_model',False)
                config_obj = authorize_obj.browse(cr,uid,config_ids[0])
                api_call,need_to_update_data = False,[]
                if act_model and cust_payment_profile_id:
#                    try:
                        transaction_status = authorize_obj.call(cr,uid,config_obj,'getTransactionDetailsRequest',auth_transaction_id)
    #                    print "transaction_status",transaction_status
                        if (transaction_status) and (transaction_status.get('transactionStatus') == 'settledSuccessfully'):
                            if wizard_obj.diff_cc_refund and wizard_obj.refund_cc_number:
                                cust_payment_profile_id = self.pool.get('custmer.payment.profile').create_payment_profile(cr,uid,return_obj.partner_id.id,return_obj.partner_invoice_id,return_obj.partner_shipping_id,cust_profile_id,wizard_obj.refund_cc_number,wizard_obj.refund_cc_expiration_date,context)
                                cc_number = wizard_obj.refund_cc_number[-4:]
                                cc_number='XXXX'+''+str(cc_number)
                                context['linked_refund'] = False
                            api_call =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',return_obj.id,'profileTransRefund',total,cust_profile_id,cust_payment_profile_id,auth_transaction_id,act_model,cc_number,context)
                        elif (transaction_status) and (transaction_status.get('transactionStatus') == 'expired'):
                            cr.execute("select id from account_invoice where (recurring=False or recurring is Null) and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple([return_obj.linked_sale_order.id]),))
                            invoice_id = cr.fetchone()
                            if invoice_id:
                                state =invoice_obj.browse(cr,uid,invoice_id[0]).state
                                if state =='draft':
                                    invoice_obj.action_cancel(cr,uid,[invoice_id[0]],context)
                        else:
                            amount = transaction_status.get('authAmount',0.0)
                            if float(amount) == float(total):
                                api_call =authorize_obj.call(cr,uid,config_obj,'VoidTransaction',cust_profile_id,cust_payment_profile_id,auth_transaction_id)
                            elif float(amount) ==0.01 and  float(total)==0.00 and transaction_status.get('transactionStatus',False)=='authorizedPendingCapture':
                                api_call =authorize_obj.call(cr,uid,config_obj,'VoidTransaction',cust_profile_id,cust_payment_profile_id,auth_transaction_id)
                            else:
                                raise osv.except_osv(_('Error !'),_('Refund Cannot Process now.Please Try Later'))
                        try:
                            if api_call:
                                    return_object.api_response(cr,uid,return_obj.id,api_call,cust_profile_id,cust_payment_profile_id,cc_number,context)
                                    cr.execute("select id from account_invoice where (recurring=False or recurring is Null) and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple([return_obj.linked_sale_order.id]),))
                                    invoice_id = cr.fetchone()
                                    if invoice_id:
                                            state =invoice_obj.browse(cr,uid,invoice_id[0]).state
                                            if state =='draft':
                                                invoice_obj.action_cancel(cr,uid,[invoice_id[0]],context)
                                            else:
                                                if not return_obj.invoice_ids:
                                                    journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
                                                    refund_invoice_id = invoice_obj.create(cr,uid,
                                                                {'partner_id':return_obj.partner_id.id,
#                                                                'address_invoice_id':return_obj.partner_invoice_id.id,
                                                                'currency_id':return_obj.pricelist_id.currency_id.id,
                                                                'account_id':return_obj.partner_id.property_account_receivable.id,
                                                                'name':return_obj.name,
#                                                                'address_contact_id':return_obj.partner_shipping_id.id,
                                                                'user_id':uid,
                                                                'journal_id':journal_id[0],
                                                                'type':'out_refund',
                                                                'return_id':return_obj.id,
                                                                'origin':return_obj.name,
                                                                'location_address_id': return_obj.linked_sale_order.location_id.partner_id.id,
                                                                'return_ref':return_obj.name+'/Credit_Return'
                                                    })
                                                    acc_invoice_line_obj = self.pool.get('account.invoice.line')
                                                    for each_order_line in return_obj.order_line:
                                                        if each_order_line.account_id:
                                                            account_id = each_order_line.account_id.id
                                                        else:
                                                            if each_order_line.product_id.property_account_income.id:
                                                                account_id = each_order_line.product_id.property_account_income.id
                                                            else:
                                                                account_id = each_order_line.product_id.categ_id.property_account_income_categ.id
                                                        account_invoice_line = acc_invoice_line_obj.create(cr,uid,
                                                        {'product_id':each_order_line.product_id.id,
                                                         'name':each_order_line.product_id.name,
                                                         'quantity':each_order_line.product_uom_qty,
                                                         'price_unit':each_order_line.price_unit,
                                                         'uos_id':each_order_line.product_uom.id,
                                                         'account_id':account_id,
                                                         'discount':each_order_line.discount,
                                                         'invoice_id':refund_invoice_id,
                                                         'origin': return_obj.name,
                                                        'invoice_line_tax_id': [(6, 0, [x.id for x in each_order_line.tax_id])],
                                                        'note': each_order_line.notes,
                                                        })
                                                        #insert into return_order_line_invoice_rel
                                                        cr.execute("insert into return_order_line_invoice_rel (order_line_id,invoice_id) values(%s,%s)",(each_order_line.id,account_invoice_line))
                                                        #insert into sale_order_line_invoice_rel
                                                        cr.execute("insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values(%s,%s)",(each_order_line.sale_line_id.id,account_invoice_line))
                                                    cr.execute("insert into return_order_invoice_rel (order_id,invoice_id) values(%s,%s)",(return_obj.id,refund_invoice_id))
                                                    netsvc.LocalService("workflow").trg_validate(uid, 'account.invoice', refund_invoice_id, 'invoice_open', cr)
                                                    invoice_obj.make_payment_of_invoice(cr, uid, [refund_invoice_id], context=context)
                                                    context['customer_profile_id'] = cust_profile_id
                                                    context['cc_number'] = cc_number
                                                    invoice_obj.api_response(cr,uid,refund_invoice_id,api_call,cust_payment_profile_id,'profileTransRefund',context)
                                                    #To write refund_generated as True in main Recurring invoice
                                                    cr.execute("update account_invoice set refund_generated=True where id=%s"%(invoice_id[0]))
                                    email_to = return_obj.partner_id.emailid
                                    self.pool.get('sale.order').email_to_customer(cr, uid, return_obj,'return.order','return_confirmation',email_to,context)
                            ###Code to Change Delivery Qty
                            cr.execute("select id from stock_picking where sale_id=%d and state != 'done'"%(return_obj.linked_sale_order.id))
                            picking_id=filter(None, map(lambda x:x[0], cr.fetchall()))
                            if picking_id:
                                return_object.change_delivery_qty(cr,uid,[return_obj.id],context)
                            return_lines=return_obj.order_line
                            for returns in return_lines:
                                if returns.sale_line_id:
                                    if returns.sale_line_id.product_id.id== returns.product_id.id and  returns.sale_line_id.product_uom_qty==returns.product_uom_qty and returns.product_id.type=='service':
                                        if returns.sale_line_id.sub_components:
                                            child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',returns.sale_line_id.id)])
                                            for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                                if (each_line.product_id.type == 'service') and (each_line.product_id.recurring_service):
                                                    need_to_update_data += return_object.deactivate_service(cr,uid,return_obj,each_line)
                                        else:
                                            need_to_update_data += return_object.deactivate_service(cr,uid,return_obj,returns.sale_line_id)
#                            if return_obj.receive:
                            state = 'done'
#                            else:
#                                state = 'progress'
                            return_object.write(cr,uid,[return_obj.id],{'manual_invoice_invisible': True,'state':state,'return_option':'refund'})
                            #will Update service as inactive on the magento site
                            if need_to_update_data:
                                attr_conn = return_obj.linked_sale_order.shop_id.referential_id.external_connection(True)
                                deactived_services = attr_conn.call('sales_order.recurring_services', ['update',need_to_update_data,''])
			    return {
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'res_id': return_obj.id,
                                    'res_model': 'return.order',
                                    'type': 'ir.actions.act_window',
                                    'context':context
                            } 	
                        except Exception, e:
                            print "Error in URLLIB",str(e)
                            return_object.write(cr,uid,[return_obj.id],{'note': str(e)})
        return {'type': 'ir.actions.act_window_close'}
refund_customer_payment()
