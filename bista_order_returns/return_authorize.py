# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
import time
from datetime import datetime, date
#try:
#    from quix.pay.gateway.authorizenet import AimGateway
#    from quix.pay.transaction import CreditCard
#except:
#    pass
class return_order(osv.osv):
    _inherit = "return.order"
    _columns = {
            'cc_number':fields.char('CC Number',size=64,readonly=True),
            'auth_transaction_id' :fields.char('Transaction ID', size=40,readonly=True),
            'auth_respmsg' :fields.text('Response Message',readonly=True),
            'customer_profile': fields.char('Customer Profile',size=64,readonly=True),
            'customer_payment_profile_id': fields.char('Payment Profile ID',size=64,readonly=True)
	}

    def api_response(self,cr,uid,ids,response,customer_profile,payment_profile_id,cc_number,context={}):
        split = response.split(',')
        transaction_id = split[6]
        transaction_message = split[3]
        vals = {}
        if transaction_message:
            vals.update({'auth_respmsg':transaction_message})
        if transaction_id:
            vals.update({'auth_transaction_id':transaction_id})
        if customer_profile:
            vals.update({'customer_profile':customer_profile})
        if payment_profile_id:
            vals.update({'customer_payment_profile_id':payment_profile_id})
        if cc_number:
            vals.update({'cc_number':cc_number})
        if vals:
            self.write(cr,uid,ids,vals)# changed [ids] to ids---Preeti for RMA
        return True
return_order()
