# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import requests
import urllib
import ast
import requests
import json
import ast
from passlib.hash import pbkdf2_sha256
from openerp import models, fields, api, _
from openerp.http import request
from openerp import SUPERUSER_ID


class res_partner(models.Model):
    """
        Voucher related details
    """
    _inherit = 'res.partner'
    wal_bal = fields.Char(string="Wallet Balance", size=32)
    user_auth_ids = fields.One2many(comodel_name="user.auth", inverse_name="partner_id", string="Auth User")
    user_profile_ids = fields.One2many(comodel_name="user.profile", inverse_name="partner_id", string="User Profile")
    playjam_exported = fields.Boolean()

    _sql_constraints = [('username_uniq', 'unique(name)', 'A partner already exists with this User Name')]

    def get_wallet_update(self):
        url = "http://54.172.158.69/api/rest/flare/wallet/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded', 'content-length': 68}
        #                    payload = '{"uid": uid, "quantity":float(value)}'
        payload = '{"uid": "FLARE1124", "quantity":0}'
        request = urllib.quote(payload.encode('utf-8'))
        print "request-----------------", request

        response = requests.post(
            url, data="request=" + request, headers=headers)

        print "response------------------", response.text
        resp = response.text
        res = ast.literal_eval(resp)
        print 'res----------------', type(res), res
        #        ero
        if res and 'body' in res and ('quantity' in res.get('body')):
            qty = res['body']['quantity']
            if qty:
                self.write({'wal_bal': qty})
                return True
        self.write({'wal_bal': 'Error'})
        return True
    
    def push_transactions(self,dict,context=None):
       print "dict------------------",dict
       if dict.get('transactions',False):
           for each in dict.get('transactions'):
	       service_product=True
               if each.get('productType')=='GAME' or each.get('productType')=='INGAME PRODUCT':
                   if each.get('productId',False):
                       app_id=each.get('appId',False)
		       product_id=each.get('productId')
                       request.cr.execute('select id from product_product where id= %s', (product_id,))
                       product_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                       order_line,order_dict={},{}
                       print "producttttttttttttttttiddddddddddddd",product_id
                       if not product_id:
                           if each.get('meta',False) and each.get('delta',False):
                               account_id=False
                               request.cr.execute('select id from account_account where name= %s', ('Service Revenue',))
                               account_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                               prod_vals={'name':each.get('meta'),'list_price':each.get('delta'),'app_id':each.get('appId'),'property_account_income':account_id[0],'product_type':'service','type':'service'}
                               product_id=self.pool.get('product.product').create(request.cr,uid,prod_vals)
			       request.cr.commit()
                               print "productid------------------",product_id
                               product_id=[product_id]
                       if product_id:
#		           if self.pool.get('product.product').browse(cr,uid,product_id[0]).product_type!='service':
#			       service_product=False
                           order_line.update({"line1":{"ProductId":product_id[0],"Qty":"1.0","Price":each.get('delta')}})
                       order_dict.update({'OrderLine':order_line})
                       if each.get('uid',False):
                           partner_id=each.get('uid',False)
                           partner_id=int(partner_id)
                           print "patner id/////////////////////",partner_id
                           pat_obj=self.browse(request.cr,SUPERUSER_ID,partner_id)
                           order_dict.update({"CustomerId":partner_id,"Email":pat_obj.emailid,})
                           billing_info={}
                           if pat_obj.street and pat_obj.city and pat_obj.state_id and pat_obj.zip:
                               bill_add={ "Street1": str(pat_obj.street),"Street2": str(pat_obj.street2 or ""),"City": str(pat_obj.city),"State": str(pat_obj.state_id.code),"Zip": str(pat_obj.zip),}
                               billing_info.update({'BillingAddress':bill_add})

                           order_dict.update({'BillingInfo':billing_info})
                           partner_addr = self.address_get(request.cr,SUPERUSER_ID, [int(partner_id)],['delivery',])
                           delivery_add=partner_addr.get('delivery')
                           default_add=partner_addr.get('default')
                           if delivery_add==default_add:
                               order_dict.update({'ShippingAddress':bill_add})
                           else:
                               delivery_obj=self.browse(request.cr,SUPERUSER_ID, delivery_add)
                               if delivery_obj.street and delivery_obj.city and delivery_obj.state_id and delivery_obj.zip:
                                   delivery_add={ "Street1": str(delivery_obj.street),"Street2": 'abc',"City": str(delivery_obj.city),"State": str(delivery_obj.state_id.code),"Zip": str(delivery_obj.zip),}
                                   order_dict.update({'ShippingAddress':delivery_add})
                           order_dict.update({'wallet_purchase':True})
                           print "1111111111111111111111------",order_dict
                           if product_id and order_dict and service_product:
#                               order_res=self.pool.get('res.partner').create_order_magento(request.cr,SUPERUSER_ID,order_dict,{})
                               order_res=self.pool.get('res.partner').create_order_magento(order_dict)
                               print"order_res-----------------",order_res
                               order_res=str(order_res)
                               if 'true' in order_res:
                                   order_res=order_res.replace('true','True')
                               if 'false' in order_res:
                                   order_res=order_res.replace('false','False')

                               ord_res=ast.literal_eval(str(order_res))
                               print "ord_res---111111111----------",ord_res

                               #order_no='SO060'
                               if (ord_res.get('body')).has_key('OrderNo'):
                                   order_no=(ord_res.get('body')).get('OrderNo')
                               print"(ord_res.get('body')=============----------++++",ord_res.get('body')
                               if (ord_res.get('body')).get('code')!=True:
                                   return json.dumps({'body':{"code":False, "message":"Order Not Created!!"}})
       return json.dumps({'body':{'result':123,'Message':'Success.'}})




    @api.one
    def account_deactivate(self):
        payload = dict(mode='U', uid=self.ids, active=False)
        res = self.pool.get('user.auth').account_playjam(payload)
        print "res-------------", res
        dict_res = ast.literal_eval(res)
        if 'body' in dict_res and ('result' in dict_res.get('body')):
            if dict_res['body']['result'] == 4097:
                res.write({'active': False,})
                return True
        raise Warning(_('Deactivation Call to Playjam Failed.'))

    @api.one
    def account_reactivate(self):
        payload = dict(mode= 'U', uid= self.ids, active=False)
        res = self.pool.get('user.auth').account_playjam(payload)
        print "res-------------",res
        dict_res = ast.literal_eval(res)
        if 'body' in dict_res and ('result' in dict_res.get('body')):
            if dict_res['body']['result'] == 4097:
                res.write({'active': True})
                return True
        raise Warning(_('Reactivation Call to Playjam Failed. '))
res_partner()
