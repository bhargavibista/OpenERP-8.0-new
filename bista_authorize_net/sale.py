# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import osv, fields
import time
from datetime import datetime, date
#try:
#    from quix.pay.gateway.authorizenet import AimGateway
#    from quix.pay.transaction import CreditCard
#except:
#    pass
class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
            'auth_transaction_type':fields.char('Transaction Type',size=256),
            'auth_transaction_id' :fields.char('Transaction ID', size=256,readonly=True),
            'customer_profile_id' :fields.char('Profile ID', size=256,readonly=True),
            'cc_number' :fields.char('Credit Card Number', size=256),
            'auth_respmsg' :fields.text('Response Message',readonly=True),
            'authorization_code': fields.char('Authorization Code',size=256,readonly=True),
            'customer_payment_profile_id': fields.char('Payment Profile ID',size=256,readonly=True),
            'cc_type': fields.char('Card Type',size=256,readonly=True)
	}
    def copy(self,cr,uid,ids,vals,context):
        vals.update({'auth_transaction_type':'','auth_transaction_id':'','cc_number':'',
        'auth_respmsg': '','authorization_code':'','customer_payment_profile_id':''})
        return super(sale_order, self).copy(cr, uid, ids, vals,context=context)
        
    def api_response(self,cr,uid,ids,response,customer_profile_id,payment_profile_id,transaction_type,cc_number,context={}):
        split = response.split(',')
        vals = {}
        if split:
            transaction_id = split[6]
            transaction_message = split[3]
            authorize_code = split[4]
            cc_type = split[51]
            if transaction_id and transaction_message:
                vals['auth_transaction_id'] = transaction_id
                vals['auth_respmsg'] = transaction_message
            if authorize_code:
                vals['authorization_code'] = authorize_code
            if payment_profile_id:
                vals['customer_payment_profile_id'] = payment_profile_id
            if transaction_type:
                vals['auth_transaction_type'] = transaction_type
            if customer_profile_id:
                vals['customer_profile_id'] = customer_profile_id
            if cc_number:
                vals['cc_number'] = cc_number
            if cc_type:
                if cc_type == 'Visa':
                    cc_type = 'VI'
                elif cc_type == 'MasterCard':
                    cc_type = 'MA'
                elif cc_type == 'American Express':
                    cc_type = 'AE'
                elif cc_type == 'Discover':
                    cc_type = 'DI'
                vals['cc_type'] = cc_type
            if vals:
                self.write(cr,uid,ids,vals)
            self.log(cr,uid,ids,transaction_message)
        return True

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals['auth_transaction_id'] = order.auth_transaction_id
        invoice_vals['authorization_code'] = order.authorization_code
        invoice_vals['customer_payment_profile_id'] = order.customer_payment_profile_id
        invoice_vals['auth_respmsg'] = order.auth_respmsg
        invoice_vals['cc_number'] = order.cc_number
        invoice_vals['customer_profile_id'] = order.customer_profile_id
        return invoice_vals
sale_order()

