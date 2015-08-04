# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import osv, fields
#import time
import authorize_osv
from openerp.tools.translate import _

class authorize_net_config(authorize_osv.authorize_osv):
    _name = "authorize.net.config"
    _rec_name = "api_username"
    def check_authorize_net(self,cr,uid,model_name,id,context):
        id_obj=self.pool.get(model_name).browse(cr,uid,id)
        authorize_net_config = self.pool.get('authorize.net.config')
        config_ids = authorize_net_config.search(cr,uid,[])
        config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
        transactions = self.call(cr,uid,config_obj,'getUnsettledTransactionListRequest')
        if transactions and transactions.has_key(id_obj.name):
            data = transactions.get(id_obj.name)	
            if id_obj.amount_total == float(data.get('amount')):
		vals = {}
                vals['auth_transaction_id'] = data.get('transid')
                vals['auth_respmsg'] = 'Transaction is approved'
                cr.execute("select profile_id from custmer_payment_profile where customer_profile_id='%s' and active_payment_profile=True"%(id_obj.partner_id.customer_profile_id))
                payment_profile_id = filter(None, map(lambda x:x[0], cr.fetchall()))
		if payment_profile_id:
	                vals['customer_payment_profile_id'] = payment_profile_id[0]
                vals['cc_number'] = data.get('cc_number')
                if model_name == 'credit.service':
                    vals['customer_profile'] = id_obj.partner_id.customer_profile_id
                else:
                    vals['customer_profile_id'] = id_obj.partner_id.customer_profile_id
                self.pool.get(model_name).write(cr,uid,[id_obj.id],vals)
		
                return ",,,'Transansaction is approved',,,%s"%(data.get('transid'))
            else:
                raise osv.except_osv(_('Warning !'),_('Transaction with these %s already exists on the Authorize.net'%(id_obj.name)))
        return False
	
    def get_customer_profile(self,cr,uid,ids,context={}):
        config_obj = self.browse(cr,uid,ids[0])
        email_ids = {}
        profile_ids_res = self.call(cr,uid,config_obj,'GetProfileIDS')
        if profile_ids_res.get('numericString',False):
           profile_ids = profile_ids_res.get('numericString',False)
           for each_id in profile_ids:
                profile_info = self.call(cr,uid,config_obj,'GetCustomerProfile',each_id)
                if profile_info.get('email',False):
                    email =profile_info.get('email',False)
                    email_ids[email] = {'customerProfileId':profile_info.get('customerProfileId',False),'payment_profile':profile_info.get('payment_profile',False)}
        return email_ids
                    
    def get_profile_ids(self,cr,uid,ids,context={}):
        config_obj = self.browse(cr,uid,ids[0])
        partner_obj = self.pool.get('res.partner')
        profile_ids_res = self.call(cr,uid,config_obj,'GetProfileIDS')
        if profile_ids_res.get('numericString',False):
           profile_ids = profile_ids_res.get('numericString',False)
#           customerPaymentProfileId = []
           for each_id in profile_ids:
                profile_ids = self.call(cr,uid,config_obj,'GetCustomerProfile',each_id)
                if profile_ids.get('email',False):
                    email = profile_ids.get('email',False)
#                    search_partner = partner_obj.search(cr,uid,[('emailid','=',email)])
                    search_partner = partner_obj.search(cr,uid,[('email','=',email)])
                    if search_partner:
                            if profile_ids.get('customerProfileId',False):
                                customerProfileId  = profile_ids.get('customerProfileId',False)
#                                customerPaymentProfileId  = profile_ids.get('customerPaymentProfileId',False)
                                customerPaymentProfile  = profile_ids.get('payment_profile',False)
                                if customerPaymentProfile:
#                                    cc_number = (customerPaymentProfile.keys()[0] if customerPaymentProfile.keys() else '')
#                                    customerPaymentProfileId = customerPaymentProfile.values()
                                    partner_obj.cust_profile_payment(cr,uid,search_partner[0],customerProfileId,customerPaymentProfile,exp_date,context)
                                    
        return True
    def onchange_test_production(self,cr,uid,ids,test_production,context):
        if test_production:
            res = {}
            if test_production == 'test':
                res['server_url'] = 'https://apitest.authorize.net/xml/v1/request.api'
            else:
                res['server_url'] = 'https://api.authorize.net/xml/v1/request.api'
            return {'value':res}
    _columns = {
	'api_username' : fields.char('API Login ID', size=100, required=True),
	'transaction_key' : fields.char('Transaction Key', size=100, required=True),
	'server_url': fields.char('Server Url', size=264),
         'test_production': fields.selection([
            ('test', 'Test'),
            ('production', 'Production')
            ], 'Test/Production'),
    }
authorize_net_config()
