# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.netsvc as netsvc

class refund_customer_payment(osv.osv_memory):
    _name = "refund.customer.payment"
    def default_get(self, cr, uid, fields, context=None):
        result = super(refund_customer_payment, self).default_get(cr, uid, fields, context=context)
        if context and context.get('auth_transaction_id'):
            result['auth_transaction_id'] = context.get('auth_transaction_id',False)
        if context and context.get('cc_number'):
            result['cc_number'] = context.get('cc_number',False)
        return result

    def refund_customer(self,cr,uid,ids,context={}):
        active_id = context.get('active_id',False)
        if active_id:
            authorize_obj = self.pool.get('authorize.net.config')
            config_ids = authorize_obj.search(cr,uid,[])
            return_object = self.pool.get('return.order')
            if config_ids:
                return_obj = return_object.browse(cr,uid,active_id)
                total= return_obj.amount_total
                wizard_obj = self.browse(cr, uid, ids[0])
                cust_profile_id = return_obj.linked_sale_order.partner_id.customer_profile_id
                cust_payment_profile_id = return_obj.linked_sale_order.customer_payment_profile_id
                auth_transaction_id = wizard_obj.auth_transaction_id
                cc_number = wizard_obj.cc_number
                if cc_number and len(cc_number)==4:
                    cc_number='XXXX'+''+str(cc_number)
                act_model = context.get('active_model',False)
                config_obj = authorize_obj.browse(cr,uid,config_ids[0])
                try:
                    transaction_status = authorize_obj.call(cr,uid,config_obj,'getTransactionDetailsRequest',auth_transaction_id)
                    print "transaction_status",transaction_status
                    if (transaction_status) and (transaction_status.get('transactionStatus') == 'settledSuccessfully'):
                        refund_tras_info =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',return_obj.id,'profileTransRefund',total,cust_profile_id,cust_payment_profile_id,auth_transaction_id,act_model,cc_number)
#                        refund_tras_info =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',return_obj.id,'profileTransRefund',total,'18120882','16964092','2192691900',act_model,'XXXX0027')
                        if refund_tras_info:
                            return_object.api_response(cr,uid,return_obj.id,refund_tras_info,cust_profile_id,cust_payment_profile_id,cc_number,context)
                            journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
                            account_refund = self.pool.get('account.invoice')
                            refund_invoice_id = account_refund.create(cr,uid,
                                        {'partner_id':return_obj.partner_id.id,
#                                        'address_invoice_id':return_obj.partner_id.id,
                                        'currency_id':return_obj.pricelist_id.currency_id.id,
                                        'account_id':return_obj.partner_id.property_account_receivable.id,
                                        'name':return_obj.name,
                                        'address_contact_id':return_obj.partner_shipping_id.id,
                                        'user_id':uid,
                                        'journal_id':journal_id[0],
                                        'type':'out_refund',
                                        'return_id':return_obj.id,
                                        'origin':return_obj.name,
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
                            cr.execute("insert into return_order_invoice_rel (order_id,invoice_id) values(%s,%s)",(return_obj.id,refund_invoice_id))
                            netsvc.LocalService("workflow").trg_validate(uid, 'account.invoice', refund_invoice_id, 'invoice_open', cr)
                            account_refund.make_payment_of_invoice(cr, uid, [refund_invoice_id], context=context)
#                            email_to = return_obj.partner_id.emailid
#                            email_to = return_obj.partner_id.email
#                            self.pool.get('sale.order').email_to_customer(cr, uid, return_obj,'return.order',email_to,context)
                    else:
                        trasaction_details =authorize_obj.call(cr,uid,config_obj,'VoidTransaction',cust_profile_id,cust_payment_profile_id,auth_transaction_id)
                        if trasaction_details:
                            return_object.api_response(cr,uid,return_obj.id,trasaction_details,cust_profile_id,cust_payment_profile_id,cc_number,context)
#                            email_to = return_obj.partner_id.email
#                            self.pool.get('sale.order').email_to_customer(cr, uid, return_obj,'return.order',email_to,context)
                    ###Code to Change Delivery Qty 
                    cr.execute("select id from stock_picking where sale_id=%d and state != 'done'"%(return_obj.linked_sale_order.id))
                    picking_id=filter(None, map(lambda x:x[0], cr.fetchall()))
                    if picking_id:
                        return_object.change_delivery_qty(cr,uid,[return_obj.id],context)
                except Exception, e:
#                    print "Error in URLLIB",str(e)
                    raise osv.except_osv(_('Error !'),_('%s')%(str(e)))
                if return_obj.receive:
                    state = 'done'
                else:
                    state = 'progress'
                return_object.write(cr,uid,[return_obj.id],{'manual_invoice_invisible': True,'state':state})
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
    'cc_number':fields.char('Credit Card Number',size=64,readonly=True),
    'transaction_type':fields.selection([('profileTransRefund','Refund')], 'Transaction Type',readonly=True),
    'auth_transaction_id' :fields.char('Transaction ID', size=40,readonly=True),
    }
    _defaults = {
        'transaction_type':'profileTransRefund',
        }
refund_customer_payment()
