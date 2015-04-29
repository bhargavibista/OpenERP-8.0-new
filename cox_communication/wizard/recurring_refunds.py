# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import openerp.netsvc

class recurring_refunds(osv.osv_memory):
    _name = "recurring.refunds"
    _rec_name = 'invoice_ids'
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(recurring_refunds, self).default_get(cr, uid, fields, context=context)
        if context.get('active_model') == 'sale.order' and context.get('active_ids'):
            cr.execute("select id from account_invoice where recurring=True and refund_generated is null and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple(context.get('active_ids')),))
            invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if invoice_ids:
                res.update({'invoice_ids':invoice_ids})
        return res
    def recurring_refund(self,cr,uid,ids,context={}):
        if ids:
            id_obj = self.browse(cr,uid,ids[0])
            invoice_ids = id_obj.invoice_ids
            if invoice_ids:
                account_refund = self.pool.get('account.invoice')
                authorize_obj = self.pool.get('authorize.net.config')
                config_ids = authorize_obj.search(cr,uid,[])
                if config_ids:
                    config_obj = authorize_obj.browse(cr,uid,config_ids[0])
                    for each_inv in invoice_ids:
                        cc_number = ''
                        cr.execute("select customer_profile_id from custmer_payment_profile where profile_id = '%s'"%(each_inv.customer_payment_profile_id))
                        cust_profile_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                        if cust_profile_id:
                            context['linked_refund'] = True
                            if 'X' not in str(each_inv.cc_number):
                                cc_number = 'XXXX'+ str(each_inv.cc_number)
                            api_call =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',each_inv.id,'profileTransRefund',each_inv.amount_total,cust_profile_id[0],each_inv.customer_payment_profile_id,each_inv.auth_transaction_id,'account.invoice',cc_number,context)
                            journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
                            account_refund = self.pool.get('account.invoice')
                            refund_invoice_id = account_refund.create(cr,uid,
                                        {'partner_id':each_inv.partner_id.id,
#                                        'address_invoice_id':each_inv.partner_id.id,
                                        'currency_id':each_inv.currency_id.id,
                                        'account_id':each_inv.account_id.id,
                                        'name':each_inv.name,
#                                        'address_contact_id':each_inv.address_contact_id.id,
                                        'user_id':uid,
                                        'journal_id':journal_id[0],
                                        'type':'out_refund',
                                        'origin':each_inv.name,
                                        'location_address_id': each_inv.location_address_id.id,
                            })
                            acc_invoice_line_obj = self.pool.get('account.invoice.line')
                            for each_invoice_line in each_inv.invoice_line:
                                if each_invoice_line.account_id:
                                    account_id = each_invoice_line.account_id.id
                                else:
                                    if each_invoice_line.product_id.property_account_income.id:
                                        account_id = each_invoice_line.product_id.property_account_income.id
                                    else:
                                        account_id = each_invoice_line.product_id.categ_id.property_account_income_categ.id
                                account_invoice_line = acc_invoice_line_obj.create(cr,uid,
                                {'product_id':each_invoice_line.product_id.id,
                                 'name':each_invoice_line.product_id.name,
                                 'quantity':each_invoice_line.quantity,
                                 'price_unit':each_invoice_line.price_unit,
                                 'uos_id':each_invoice_line.uos_id.id,
                                 'account_id':account_id,
                                 'discount':each_invoice_line.discount,
                                 'invoice_id':refund_invoice_id,
                                 'origin': each_inv.name,
                                'invoice_line_tax_id': [(6, 0, [x.id for x in each_invoice_line.invoice_line_tax_id])],
                                })
                            netsvc.LocalService("workflow").trg_validate(uid, 'account.invoice', refund_invoice_id, 'invoice_open', cr)
                            account_refund.make_payment_of_invoice(cr, uid, [refund_invoice_id], context=context)
                            context['customer_profile_id'] = cust_profile_id
                            context['cc_number'] = cc_number
                            account_refund.api_response(cr,uid,refund_invoice_id,api_call,each_inv.customer_payment_profile_id,'profileTransRefund',context)
                            #To write refund_generated as True in main Recurring invoice
                            cr.execute("update account_invoice set refund_generated=True where id=%s"%(each_inv.id))
                        else:
                            raise osv.except_osv(_('Warning'), _('Customer Profile ID not found in Database'))
                else:
                    raise osv.except_osv(_('Warning'), _('Please Define Authorize.net Credentials'))
        return True
    _columns={
    'invoice_ids': fields.many2many('account.invoice', 'recurring_invoices', 'order_id', 'invoice_id', 'Invoices'),
    }
    
recurring_refunds()
