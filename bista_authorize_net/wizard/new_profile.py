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

class customer_profile_payment(osv.osv_memory):
    _name = "customer.profile.payment"
    def onchange_cc_number(self,cr,uid,ids,cc_number,context={}):
        res,cc_number_filter = {},''
        if cc_number:
            cc_number_filter = cc_number.strip('%B')[:16]
            if cc_number_filter:
                res['auth_cc_number'] = cc_number_filter
            else:
                res['auth_cc_number'] = cc_number
#            if cc_number.find("?;")  != -1:
#                cc_number_filter = cc_number[cc_number.find(";")+1:cc_number.find("=")]
#            if cc_number_filter:
#                res['auth_cc_number'] = cc_number_filter
##            elif cc_number_filter_an:
##                res['auth_cc_number'] = cc_number_filter_an
#            else:
#                res['auth_cc_number'] = cc_number
        return {'value':res}

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        act_model = context.get('active_model',False)
        result = super(customer_profile_payment, self).default_get(cr, uid, fields, context=context)
        if act_model=='sale.order':
            active_id = context.get('sale_id',False)
            if active_id:
                customer_id = self.pool.get('sale.order').browse(cr,uid,active_id[0]).partner_id
                if customer_id:
                    result['partner_id'] = customer_id.id
        elif act_model == 'account.invoice':
            active_id = context.get('sale_id',False)
            if active_id:
                customer_id = self.pool.get('account.invoice').browse(cr,uid,active_id[0]).partner_id
                if customer_id:
                    result['partner_id'] = customer_id.id
        return result

    def charge_customer(self,cr,uid,ids,context={}):
        if context is None:
            context = {}
        active_id = context.get('sale_id',False)
        authorize_net_config = self.pool.get('authorize.net.config')
        wizard_obj = self.browse(cr, uid, ids[0])
        transaction_type = wizard_obj.transaction_type
        obj_all,transaction_details = False,''
        act_model = context.get('active_model',False)
        if act_model == 'sale.order':
            obj_all = self.pool.get('sale.order')
        elif act_model == 'account.invoice':
            obj_all = self.pool.get('account.invoice')
#            cr.execute("SELECT order_id from sale_order_invoice_rel WHERE invoice_id=%s",(active_id[0],))
#            id1 = cr.fetchone()
#            if id1:
#                cr.execute("SELECT auth_transaction_id,authorization_code,customer_payment_profile_id,auth_respmsg FROM sale_order WHERE id = %s",(id1,))
#                result = cr.fetchall()
#                if result:
#                    if result[0][1]:
#                        cr.execute("UPDATE account_invoice SET auth_transaction_id='%s', authorization_code='%s', customer_payment_profile_id='%s',auth_respmsg='%s' where id=%s"%(result[0][0],result[0][1],result[0][2],result[0][3],active_id[0],))
#                        cr.commit()
#                        raise osv.except_osv(_('Warning!'), _('This record has already been authorize !'))
        if active_id:
                id_obj = obj_all.browse(cr,uid,active_id[0])
                if id_obj:
                    customer_id = obj_all.browse(cr,uid,active_id[0]).partner_id
                    email = customer_id.emailid
                    cust_profile_Id,numberstring=False,False
                    current_obj = self.browse(cr,uid,ids[0])
                    ccn = current_obj.auth_cc_number
                    ccv = current_obj.auth_ccv_number ##ccv
                    exp_date = current_obj.auth_cc_expiration_date
        #            exp_date = exp_date[:4] + '-' + exp_date[4:]
                    exp_date = exp_date[-4:] + '-' + exp_date[:2]
                    config_ids =authorize_net_config.search(cr,uid,[])
                    if config_ids:
                        config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                        action_to_do = context.get('action_to_do',False)
                        if action_to_do == 'new_customer_profile':
                            response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileOnly',email)
                            print "response",response
                            if response:
                                cust_profile_Id = response.get('cust_profile_id')
                                if cust_profile_Id:
                                    if not response.get('success'):
                                        profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',cust_profile_Id)
                                        print "profile_info",profile_info
                                        if not profile_info.get('payment_profile'):
                                          response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                          numberstring = response.get('customerPaymentProfileId',False)
                                        else:
                                            profile_info = profile_info.get('payment_profile')
                                            if ccn[-4:] in profile_info.keys():
                                                numberstring =  profile_info[ccn[-4:]]
                                            else:
                                                response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                                numberstring = response.get('customerPaymentProfileId',False)
                                    else:
                                        response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                        print"response",response
                                        numberstring = response.get('customerPaymentProfileId',False)
                        else:
                             cust_profile_Id = customer_id.customer_profile_id
                             if cust_profile_Id:
                                cr.execute("select profile_id from custmer_payment_profile where credit_card_no='%s' and customer_profile_id='%s'"%(str(ccn[-4:]),cust_profile_Id))
                                numberstring = filter(None, map(lambda x:x[0], cr.fetchall()))
                                if numberstring:
                                    numberstring = numberstring[0]
                             if not numberstring:
                                profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',cust_profile_Id)
                                print "profile_info",profile_info
                                if not profile_info.get('payment_profile'):
                                  response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                  numberstring = response.get('customerPaymentProfileId',False)
                                else:
                                    profile_info = profile_info.get('payment_profile')
                                    if ccn[-4:] in profile_info.keys():
                                        numberstring =  profile_info[ccn[-4:]]
                                    else:
                                        response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                        numberstring = response.get('customerPaymentProfileId',False)
                             if not numberstring:
                                response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                numberstring = response.get('customerPaymentProfileId',False)
                        if cust_profile_Id and numberstring:
                            payment_profile_val = {ccn[-4:]: numberstring}
                            self.pool.get('res.partner').cust_profile_payment(cr,uid,customer_id.id,cust_profile_Id,payment_profile_val,context) ##ccv changes
                            amount =  obj_all.browse(cr,uid,active_id[0]).amount_total
                            print "amount at authorize side.............",amount
                            if amount>0.0:
                                transaction_res = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',active_id[0],transaction_type,amount,cust_profile_Id,numberstring,'',act_model,'',context)  ##ccv
                                if context.get('recurring_billing'):
                                    transaction_details = transaction_details.get('response','')
                                else:
                                    transaction_details = transaction_res
                                if transaction_res:
                                    if obj_all._name=='sale.order':
                                        obj_all.api_response(cr,uid,active_id[0],transaction_details,cust_profile_Id,numberstring,transaction_type,'XXXX'+ccn[-4:],context)
                                    elif obj_all._name=='account.invoice':
                                        context['cc_number'] ='XXXX'+ccn[-4:]
                                        context['customer_profile_id'] = cust_profile_Id
                                        obj_all.api_response(cr,uid,active_id[0],transaction_details,numberstring,transaction_type,context)
                                        if context.get('recurring_billing'):
                                            return transaction_res
#                                if transaction_res and obj_all._name=='sale.order':
#                                    wf_service = netsvc.LocalService("workflow")
#                                    wf_service.trg_validate(uid, 'sale.order', active_id[0], 'order_confirm', cr)
#                                    cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(active_id[0]))
#                                    invoice_id=cr.fetchone()
#                                    if invoice_id:
#                                        self.pool.get('account.invoice').capture_payment(cr,uid,[invoice_id[0]],context)
                    else:
                        raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
        return {'type': 'ir.actions.act_window_close'}
    _columns = {
    'partner_id': fields.many2one('res.partner','Partner ID'),
    'auth_cc_number' :fields.char('Credit Card Number',size=256,help="Credit Card Number",required=True),
    'auth_cc_expiration_date' :fields.char('CC Exp Date [MMYYYY]',size=6,help="Credit Card Expiration Date",required=True),
    'auth_ccv_number':fields.char('Credit Card Verification',size=256,required=True),
    'transaction_type':fields.selection([('profileTransAuthCapture','Authorize and Capture'),('profileTransAuthOnly','Authorize Only')], 'Transaction Type',readonly=True),
#    'transaction_type':fields.selection([('profileTransAuthOnly','Authorize Only')], 'Transaction Type',readonly=True),
    }
    _defaults = {
        'transaction_type':'profileTransAuthOnly',
        }
customer_profile_payment()
