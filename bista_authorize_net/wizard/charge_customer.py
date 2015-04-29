# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.netsvc

class charge_customer(osv.osv_memory):
    _name = "charge.customer"
    def cust_profile_id(self, cr, uid, context={}):
        act_model = context.get('active_model', False)
        active_id = context.get('active_id',False)
        customer_id = False
        if active_id:
            if act_model == 'sale.order':
                obj_all = self.pool.get('sale.order').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            elif act_model == 'account.invoice':
                obj_all = self.pool.get('account.invoice').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            if customer_id:
                profile_id = customer_id.customer_profile_id
                res = [(profile_id, profile_id)]
        return res
    
    def customer_payment_id(self, cr, uid, context={}):
        act_model = context.get('active_model', False)
        res = []
        active_id = context.get('active_id',False)
        if active_id:
            if act_model == 'sale.order':
                obj_all = self.pool.get('sale.order').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            elif act_model == 'account.invoice':
                obj_all = self.pool.get('account.invoice').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            if customer_id:
                profile_ids = customer_id.profile_ids
                for each_profile in profile_ids:
                    if each_profile.active_payment_profile:
                        cc_number = each_profile.credit_card_no
                        profile_id = each_profile.profile_id
                        res.append((profile_id, cc_number))
        return res
    def charge_customer(self,cr,uid,ids,context={}):
        if context is None:
            context = {}
        act_model = context.get('active_model',False)
        active_id = context.get('active_id',False)
        customer_profile_id,cc_number,obj_all,transaction_id,transaction_response = False,'',False,'',''
        authorize_net_config = self.pool.get('authorize.net.config')
        current_obj = self.browse(cr,uid,ids[0])
        if active_id:
            if act_model == 'sale.order':
                obj = self.pool.get('sale.order')
                obj_all = obj.browse(cr,uid,active_id)
                customer_profile_id = obj_all.partner_id.customer_profile_id
                amount = obj_all.amount_total
            elif act_model == 'account.invoice':
                obj = self.pool.get('account.invoice')
                obj_all = obj.browse(cr,uid,active_id)
                customer_profile_id = obj_all.partner_id.customer_profile_id
                amount = obj_all.amount_total
#                cr.execute("SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id=%s",(active_id[0],))
#                id1 = cr.fetchone()
#                if id1:
#                    cr.execute("SELECT auth_transaction_id,authorization_code,customer_payment_profile_id,auth_respmsg FROM sale_order WHERE id = %s",(id1,))
#                    result = cr.fetchall()
#                    if result[0][1]:
#                        cr.execute("UPDATE account_invoice SET auth_transaction_id='%s', authorization_code='%s', customer_payment_profile_id='%s',auth_respmsg='%s' where id=%s"%(result[0][0],result[0][1],result[0][2],result[0][3],active_id[0],))
#                        cr.commit()
#                        raise osv.except_osv(_('Warning!'), _('This record has already been authorize !'))
#            if not obj_all.auth_transaction_id:
            config_ids = authorize_net_config.search(cr,uid,[])
            if config_ids and customer_profile_id:
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                cust_payment_profile_id = current_obj.cust_payment_profile_id
#                ccv = current_obj.ccv
                transaction_type = current_obj.transaction_type
                if obj_all.auth_transaction_id:
                    transaction_id = obj_all.auth_transaction_id
		if amount>0.0:
                    transaction_details =authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',active_id,transaction_type,amount,customer_profile_id,cust_payment_profile_id,transaction_id,act_model,'',context) 
                    cr.execute("select credit_card_no from custmer_payment_profile where profile_id='%s'"%(cust_payment_profile_id))
                    cc_number = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if cc_number:
                    	cc_number = cc_number[0]
                    if context.get('recurring_billing'):
                     	transaction_response = transaction_details.get('response','')
                    else:
                    	transaction_response = transaction_details
                    if transaction_details and obj._name=='sale.order':
                    	obj.api_response(cr,uid,active_id,transaction_response,customer_profile_id,cust_payment_profile_id,transaction_type,'XXXX'+cc_number,context)
                    if transaction_details and obj._name=='account.invoice':
                    	context['cc_number'] ='XXXX'+cc_number
                    	context['customer_profile_id'] = customer_profile_id
                    	obj.api_response(cr,uid,active_id,transaction_response,cust_payment_profile_id,transaction_type,context)
                    	if context.get('recurring_billing'):
                        	return transaction_details
#                        wf_service = netsvc.LocalService("workflow")
#                        wf_service.trg_validate(uid, 'sale.order', active_id[0], 'order_confirm', cr)
#                        cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(active_id[0]))
#                        invoice_id=cr.fetchone()
#                        if invoice_id:
#                            self.pool.get('account.invoice').capture_payment(cr,uid,[invoice_id[0]],context)
            else:
                raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
        return {'type': 'ir.actions.act_window_close'}
    _columns={
#        'cust_profile_id':fields.selection(cust_profile_id, 'Customer Profile ID', help="Gives the state of the order", select=True,required=True),
        'cust_payment_profile_id':fields.selection(customer_payment_id, 'Credit Card Number', help="Credit Card Numer", select=True,required=True),
        'transaction_type':fields.selection([('profileTransAuthCapture','Authorize and Capture'),('profileTransAuthOnly','Authorize Only')], 'Transaction Type',readonly=True),
#        'transaction_type':fields.selection([('profileTransAuthOnly','Authorize Only')], 'Transaction Type',readonly=True),
    }
    _defaults = {
        'transaction_type':'profileTransAuthOnly',
        }
charge_customer()
