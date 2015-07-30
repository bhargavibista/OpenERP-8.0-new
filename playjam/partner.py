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

#    _sql_constraints = [('username_uniq', 'unique(name)', 'A partner already exists with this User Name')]

    def get_wallet_update(self):
        url = "http://54.172.158.69/api/rest/flare/wallet/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded', 'content-length': 68}
        #                    payload = '{"uid": uid, "quantity":float(value)}'
        payload = '{"uid": "FLARE1124", "quantity":0}'
        request = urllib.quote(payload.encode('utf-8'))
        response = requests.post(
            url, data="request=" + request, headers=headers)

        resp = response.text
        res = ast.literal_eval(resp)
        if res and 'body' in res and ('quantity' in res.get('body')):
            qty = res['body']['quantity']
            if qty:
                self.write({'wal_bal': qty})
                return True
        self.write({'wal_bal': 'Error'})
        return True
    
    def push_transactions(self,dict,context=None):
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
                       
                       if not product_id:
                           if each.get('meta',False) and each.get('delta',False):
                               account_id=False
                               request.cr.execute('select id from account_account where name= %s', ('Service Revenue',))
                               account_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                               prod_vals={'name':each.get('meta'),'list_price':each.get('delta'),'app_id':each.get('appId'),'property_account_income':account_id[0],'product_type':'service','type':'service'}
                               product_id=self.pool.get('product.product').create(request.cr,uid,prod_vals)
			       request.cr.commit()
                               product_id=[product_id]
                       else:
                           pro_temp_obj=self.pool.get('product.product').browse(cr,uid,product_id[0]).product_tmpl_id
                           list_price=pro_temp_obj.list_price
                           if list_price!= each.get('delta'):
                               pro_temp_obj.write({'list_price':each.get('delta')})
                               cr.commit()
                       if product_id:
		           if self.pool.get('product.product').browse(cr,uid,product_id[0]).product_type!='service':
			       service_product=False
                           order_line.update({"line1":{"ProductId":product_id[0],"Qty":"1.0","Price":each.get('delta')}})
                       order_dict.update({'OrderLine':order_line})
                       if each.get('uid',False):
                           partner_id=each.get('uid',False)
                           if partner_id.isdigit():
                            partner_id=int(partner_id)
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
                            if product_id and order_dict and service_product and each.get('delta'):
 #                               order_res=self.pool.get('res.partner').create_order_magento(request.cr,SUPERUSER_ID,order_dict,{})
                                order_res=self.pool.get('res.partner').create_order_magento(order_dict)
                                order_res=str(order_res)
                                if 'true' in order_res:
                                    order_res=order_res.replace('true','True')
                                if 'false' in order_res:
                                    order_res=order_res.replace('false','False')

                                ord_res=ast.literal_eval(str(order_res))

                                #order_no='SO060'
                                if (ord_res.get('body')).has_key('OrderNo'):
                                    order_no=(ord_res.get('body')).get('OrderNo')
       return json.dumps({'body':{'result':123,'Message':'Success.'}})




    @api.one
    def account_deactivate(self):
        payload = dict(mode='U', uid=self.ids, active=False)
        res = self.pool.get('user.auth').account_playjam(payload)
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
        dict_res = ast.literal_eval(res)
        if 'body' in dict_res and ('result' in dict_res.get('body')):
            if dict_res['body']['result'] == 4097:
                res.write({'active': True})
                return True
        raise Warning(_('Reactivation Call to Playjam Failed. '))
    
    @api.one
    def quality_of_service(self,cr,uid,dict,context=None):

        if dict.has_key('UID'):
            cust_id=dict.get('UID')

            if cust_id:
                cust_id=int(cust_id)

                cr.execute('select id from res_partner where id= %s', (cust_id,))
                if_present = filter(None, map(lambda x:x[0], cr.fetchall()))
                if if_present!=[]:
                    game_id=dict.get('GameID',False)
                    s_date=dict.get('StartDate',False)
                    if s_date:
                        try:
                            date_object = datetime.datetime.strptime(s_date, '%d-%m-%Y')
                        except ValueError:
                            return json.dumps({"body":{"code":False,'message': "Incorrect date format, should be YYYY-MM-DD",}})
                        
                        start_date=date_object.strftime('%Y-%m-%d')
                    else:
                        start_date=""

                    e_date=dict.get('EndDate',False)
                    if e_date:
                        try:
                            date_object = datetime.datetime.strptime(e_date, '%d-%m-%Y')
                        except ValueError:
                            return json.dumps({"body":{"code":False,'message': "Incorrect date format, should be YYYY-MM-DD",}})
                        
                        end_date=date_object.strftime('%Y-%m-%d')
                    else:
                        end_date=""
                    session_id=dict.get('SessionId',False)
                    start_time=dict.get('StartTime',False)
                    end_time=dict.get('EndTime',False)
                    termination_reason=dict.get('TerminationReason',False)
                    start_bandwith=dict.get('StartBandwith',False)
                    end_bandwith=dict.get('EndBandwith',False)
                    packet_losses_count=dict.get('PacketLossesCount',False)
                    round_trip=dict.get('RoundTrip',False)
                    network_type=dict.get('NetworkType',False)
                    qos_avg_score=dict.get('QosAverageScore',False)
                    create_date=datetime.datetime.now()		
		
                    registry = openerp.modules.registry.Registry(str('QOS'))
                    with registry.cursor() as cr:
                        cr.execute('insert into quality_of_service (session_id,partner_id,game_id,start_date,start_time,end_date,end_time,termination_reason,start_bandwith,end_bandwith,packet_losses_count,round_trip,network_type,qos_avg_score,create_date,write_date,create_uid,write_uid) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (session_id,cust_id,game_id,start_date,start_time,end_date,end_time,termination_reason,start_bandwith,end_bandwith,packet_losses_count,round_trip,network_type,qos_avg_score,create_date,create_date,1,1))
                        return True

        return False
res_partner()