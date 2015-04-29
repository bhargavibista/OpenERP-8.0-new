# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import fields, osv
class custmer_payment_profile(osv.osv):
    _name = "custmer.payment.profile"
    _rec_name ="profile_id"
    def create_payment_profile(self,cr,uid,partner_id,billing_address,shipping_address,profile_id,cc_number,exp_date,context):
        authorize_net_config = self.pool.get('authorize.net.config')
        config_ids =authorize_net_config.search(cr,uid,[])
        numberstring = ''
        if config_ids:
            config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
            exp_date = exp_date[-4:] + '-' + exp_date[:2]
            if profile_id:
                cr.execute("select profile_id from custmer_payment_profile where credit_card_no='%s' and customer_profile_id='%s'"%(str(cc_number[-4:]),profile_id))
                numberstring = filter(None, map(lambda x:x[0], cr.fetchall()))
                if numberstring:
                    numberstring = numberstring[0]
                if not numberstring:
                    profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',profile_id)
                    print "profile_info",profile_info
                    if not profile_info.get('payment_profile'):
                      response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,partner_id,billing_address,shipping_address,profile_id,cc_number,exp_date,'return.order')
                      print"response CreateCustomerPaymentProfile bista authorize .net",response
                      hfdjfhg
                      numberstring = response.get('customerPaymentProfileId',False)
                    else:
                        profile_info = profile_info.get('payment_profile')
                        if cc_number[-4:] in profile_info.keys():
                            numberstring =  profile_info[cc_number[-4:]]
                        else:
                            response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,partner_id,billing_address,shipping_address,profile_id,cc_number,exp_date,'return.order')
                            numberstring = response.get('customerPaymentProfileId',False)
            if numberstring:
                payment_profile = {cc_number[-4:]: numberstring}
                self.pool.get('res.partner').cust_profile_payment(cr,uid,partner_id,profile_id,payment_profile,context)
                return numberstring
    _columns = {
        'profile_id' : fields.char('PaymentProfile ID',size=64),
        'customer_profile_id' : fields.char('Customer Profile ID',size=64),
        'credit_card_no' : fields.char('Credit Card No.',size=64),
        'active_payment_profile': fields.boolean('Active Payment Profile'),
    }
custmer_payment_profile()

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    def cust_profile_payment(self,cr,uid,ids,profile_id,payment_profile_data,context={}):
        print"payment_profile_data",payment_profile_data
        ids =int(ids)
        cr.execute("UPDATE res_partner SET customer_profile_id='%s' where id=%d"%(profile_id,ids))
        payment_obj = self.pool.get('custmer.payment.profile')
        active_payment_profile_id = []
        for cc_number in payment_profile_data.iterkeys():
            print"cc_number",cc_number
            dshfjd
            each_profile = payment_profile_data[cc_number]
            search_payment_profile = payment_obj.search(cr,uid,[('profile_id','=',each_profile),('credit_card_no','=',cc_number)])
            if not search_payment_profile:
                create_payment = payment_obj.create(cr,uid,{'active_payment_profile':True,'profile_id':each_profile,'credit_card_no':cc_number,'customer_profile_id':profile_id})
#                 active_payment_profile_id.append(create_payment)
                cr.execute('INSERT INTO partner_profile_ids \
                        (partner_id,profile_id) values (%s,%s)', (ids, create_payment))
            else:
                active_payment_profile_id.append(search_payment_profile[0])
        if active_payment_profile_id:
            payment_obj.write(cr,uid,active_payment_profile_id,{'active_payment_profile':True})
            cr.execute("select profile_id from partner_profile_ids where partner_id=%s and profile_id not in %s",(ids,tuple(active_payment_profile_id),))
            in_active_payment_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if in_active_payment_ids:
                payment_obj.write(cr,uid,in_active_payment_ids,{'active_payment_profile':False})
        return True
    _columns = {
    'customer_profile_id': fields.char('Customer Profile ID',size=64),
        'profile_ids': fields.many2many('custmer.payment.profile','partner_profile_ids', 'partner_id', 'profile_id','Customer Profiles'),
    }
res_partner()