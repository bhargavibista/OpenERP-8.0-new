# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from random import randint
import hashlib
import json
import ast
from openerp.http import request
import urllib
import requests
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
from openerp import SUPERUSER_ID
import datetime
import os
import logging
_logger = logging.getLogger(__name__)




class user_auth(models.Model):
    '''Authenticating the user'''
    _name = 'user.auth'
    _description = 'User Authentication'

    partner_id = fields.Many2one(comodel_name="res.partner", string="User Name", required=False, )
    # 'partner_id': fields.many2one('res.partner',"User Name"),
    device_id = fields.Char(required=False, )
    code = fields.Char(required=False, )
    key = fields.Char(required=False, )
    is_registered = fields.Boolean(string="Registered")
    challenge = fields.Char(required=False, )
    session_token = fields.Char(required=False, )
    insecure_token = fields.Char(required=False, )
    duration = fields.Char(required=False, )
    token_exp_time = fields.Datetime(required=False, )
    serial_no = fields.Many2one(comodel_name="stock.production.lot", required=False, )
    mac_address = fields.Char(required=False, )
    device_history_ids = fields.One2many('device.history','user_auth_id',string='History')
    is_tru = fields.Boolean(string='Tru')
    is_activated = fields.Boolean(string='Registered')
    is_attached = fields.Boolean(string='Attached')

    
    def get_key_code(self,device_id, want_code, context=None):
        ''' Returns the code '''
        code ,values,auth_user_id,hashed_key,note= '',{},[],'',''
        if (want_code is None) or (device_id is None):
            h=int('-0x0601', 16)
            values =json.dumps({'body':{'result':'-0x0601'}})
            return values
        random=randint(1,99999)
        key_random=randint(1,9999999999)
        _logger.info('policies---------------- %s,%s', device_id,want_code)
        dev_id=device_id
        if device_id and want_code==False:
            request.cr.execute('select id from user_auth where device_id = %s', (dev_id,))
            auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            if auth_user_id:
                brow_obj=self.browse(auth_user_id[0])
                active=brow_obj.is_registered
                if active:
                    key=brow_obj.key
                    hash_obj=hashlib.sha256(key)
                    hash_key=hash_obj.hexdigest()
                    h=int('0x0001', 16)
                    values=json.dumps({'body':{'result':'0x0001','key':hash_key}})
                    return values
                else:
                    h=int('-0x0001', 16)
                    values=json.dumps({'body':{'result': '-0x0001'}})
                    return values
        if device_id and want_code==True:
            request.cr.execute('select id from user_auth where device_id = %s',(dev_id,))
            auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            code=str(random)+device_id
            _logger.info('code---------------- %s', code)
            note="Enter the code on website to complete registration "
            key=str(key_random)+device_id
            hash_object = hashlib.md5(key)
            hashed_key=hash_object.hexdigest()
            hashed_key=hashed_key.replace('A', 'a').replace('F', 'f')
            if auth_user_id:
                self.write(request.cr,1,auth_user_id,{'code':code,'key':hashed_key,'device_id':device_id})
            else:
                self.create(request.cr,1,{'code':code,'key':hashed_key,'device_id':device_id})
            h=int('-0x0001', 16)
            values=json.dumps({'body':{'result':'-0x0001','code':str(code),'key':hashed_key}})
            return values
	    values= json.dumps({'body':{'result':'-0x0601'}})
        return values

    def register_user(self, code, context=None):
        # verifies user and associates the partner
        if code:
            request.cr.execute('select id from user_auth where code = %s', (code,))
            auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            if auth_user_id:
                self.write(request.cr,1,auth_user_id,{'is_registered':True})
                partner=self.browse(request.cr,1,auth_user_id[0]).partner_id
                if partner:
                    return json.dumps({'body':{"code":True, "message":"Success", "LinkedAccount":True, "OfferSKU":""}})
                else:
                    return json.dumps({'body':{"code":True, "message":"Success", "LinkedAccount":False, "OfferSKU":""}})
            else:
                return json.dumps({'body':{"code":False, "message":"No such Device"}})
        else:
            return json.dumps({'body':{"code":False, "message":"Please enter the Activation code"}})
    
    def link_account(self, dict, context=None):
        _logger.info('dict---------------- %s', dict)
        partner_id=dict.get('CustomerId')
        code= dict.get('ActivationCode')
        order_no=False
	product_id=False
        used = False
        request.cr.execute('select id from user_auth where code= %s', (str(code),))
        auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
        if auth_user_id==[]:
            return json.dumps({'body':{"code":False, "message":"No Such Device"}})
	request.cr.execute('select id from res_partner where id= %s', (int(partner_id),))
        pat_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
	if pat_id==[]:
	    return json.dumps({'body':{"code":False, "message":"Partner Not Present"}})
        #check if device belongs to TRU and create a SO if yes.

        pat_obj=self.pool.get('res.partner').browse(request.cr,SUPERUSER_ID,int(partner_id))
        auth_user_obj=self.pool.get('user.auth').browse(request.cr,SUPERUSER_ID,auth_user_id[0])
        email_id=pat_obj.emailid
        order_dict={"CustomerId":partner_id,"Email":str(email_id),}
        billing_info={}
        if pat_obj.profile_ids:
            _logger.info('profileids------------- %s', profile_ids)
            for each in pat_obj.profile_ids:
                if each.active_payment_profile==True:
                    if each.profile_id:
                        billing_info.update({'PaymentProfileId':str(each.profile_id)})
                    if each.credit_card_no :
                        cc_no=each.credit_card_no
                        billing_info.update({'CreditCard':{"CCNumber":str(each.credit_card_no),}})
            if billing_info=={}:
                return json.dumps({'body':{"code":False, "message":"Billing Info Missing!!"}})
        if pat_obj.street and pat_obj.city and pat_obj.state_id and pat_obj.zip:
            bill_add={ "Street1": str(pat_obj.street),"Street2": str(pat_obj.street2 or ""),"City": str(pat_obj.city),"State": str(pat_obj.state_id.code),"Zip": str(pat_obj.zip),}
            billing_info.update({'BillingAddress':bill_add})
        else:
            return json.dumps({'body':{"code":False, "message":"Incomplete Billing Address!!"}})
        order_dict.update({'BillingInfo':billing_info})
        partner_addr = self.pool.get('res.partner').address_get(request.cr,SUPERUSER_ID,[int(partner_id)],['delivery',])
        delivery_add=partner_addr.get('delivery')
        default_add=partner_addr.get('default')
        if delivery_add==default_add:
            order_dict.update({'ShippingAddress':bill_add})
        else:
            delivery_obj=self.browse(cr, uid, delivery_add)
            if delivery_obj.street and delivery_obj.city and delivery_obj.state_id and delivery_obj.zip:
                delivery_add={ "Street1": str(delivery_obj.street),"Street2": 'abc',"City": str(delivery_obj.city),"State": str(delivery_obj.state_id.code),"Zip": str(delivery_obj.zip),}
                order_dict.update({'ShippingAddress':delivery_add})
            else:
                return json.dumps({'body':{"code":False, "message":"Incomplete Shipping Address!!"}})
        serial_obj=auth_user_obj.serial_no
        tru_location=False
        if serial_obj:
            current_location_type=serial_obj.location_id.usage
            if current_location_type=='customer':
                move_ids = [move_id.id for move_id in serial_obj.move_prod_lot_ids]
	    	if move_ids: 
                    latest_move_id=max(move_ids)
                    selling_location_id=self.pool.get('stock.move').browse(request.cr,SUPERUSER_ID,latest_move_id).location_id
                    if selling_location_id.tru==True:
                        tru_location=selling_location_id.id
            elif current_location_type=='internal' and serial_obj.location_id.tru:
                tru_location=serial_obj.location_id.id
        if tru_location:
            if pat_obj.user_auth_ids:
                for each in pat_obj.user_auth_ids:
                    sno=each.serial_no.name
                    if each.is_tru==True and sno!= serial_obj.name:
                        return json.dumps({'body':{ "code":False, "message":"A Tru Device is already attached to this Account."}})
            used= serial_obj.used

        if tru_location and not used:
            cr.execute('select id from product_product where location_id= %s', (tru_location,))
            product_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            if product_id:
                prod_obj=self.pool.get('product.product').browse(request.cr,SUPERUSER_ID,product_id[0])
                prod_info={"ProductId":product_id[0],"Qty":"1.0","Price": prod_obj.product_tmpl_id.list_price,}
                order_dict.update({"OrderLine":{"line1":prod_info},"tru":True})
                _logger.info('order dict---------------- %s', order_dict)
		if not serial_obj.order_created:
                    order_res=self.pool.get('res.partner').create_order_magento(request.cr,SUPERUSER_ID,order_dict,{})
                    order_res=str(order_res)
                    if 'true' in order_res:
                        order_res=order_res.replace('true','True')
                    if 'false' in order_res:
                        order_res=order_res.replace('false','False')
                    ord_res=ast.literal_eval(str(order_res))
                    if (ord_res.get('body')).has_key('OrderNo'):
                        order_no=(ord_res.get('body')).get('OrderNo')
                    if (ord_res.get('body')).get('code')!=True:
                        return json.dumps({'body':{"code":False, "message":"Order Not Created!!"}})
                    else:
                        serial_obj.write({'order_created':True})
			cr.commit()
                        self.write(cr,uid,auth_user_id,{'is_tru':True})
        if auth_user_id and partner_id:
            self.write(request.cr,SUPERUSER_ID,auth_user_id,{'partner_id':partner_id})
            accountPin= pat_obj.account_pin
            full_name=pat_obj.name
            x=full_name.find(' ')
            full_name=full_name.replace(' ','')
            first_name=full_name[:x]
            last_name=full_name[x:]
            code=auth_user_obj.code
            name = first_name
            surname = last_name
            email = pat_obj.emailid
            dob = pat_obj.dob
	    p_exp=pat_obj.playjam_exported

	    if dob:
	        date_object = datetime.datetime.strptime(dob, '%Y-%m-%d')
                dob=date_object.strftime('%Y/%m/%d')
	    else:
		dob=""
            account_pin=pat_obj.account_pin
            payload={'name':name,'uid':partner_id, 'surname':surname,'email':email,'accountPin':account_pin,'dob':dob,'mode':'C','active':True}
            if not p_exp:
                res=self.account_playjam(payload)
                dict_res=ast.literal_eval(res)
                if dict_res.has_key('body') and (dict_res.get('body')).has_key('result'):
                    if dict_res['body']['result']==4097:
                        pat_obj.write({'active':True,'playjam_exported':True})
			cr.commit()
                    else:
                        r_string=dict_res['body']['resultString']
                        return json.dumps({'body':{ "code":False, "message":"Account Call to Playjam Failed."}})
		else:
		    return json.dumps({"body":{"code":False,"message":"Account Call To Playjam Failed."}})		    
	    if auth_user_obj.is_attached==False:
                device_payload={'uid':partner_id,'mode':'C','code':code,'alias':'abc'}
                device_res=self.device_playjam(device_payload)
                device_response=ast.literal_eval(device_res)
                if device_response.has_key('body') and (device_response.get('body')).has_key('result'):
                    if device_response['body']['result']==4241:
                        auth_user_obj.write({'is_attached':True})
                    else:
                        return json.dumps({'body':{ "code":False, "message":"Device call to Playjam Failed"}})
                else:
                     return json.dumps({'body':{ "code":False, "message":"Device Call To Playjam Failed."}})
            check_user_profiles=pat_obj.user_profile_ids
            if check_user_profiles==[]:
                return json.dumps({"body":{ "code":False, "message":"Profile Not Created Yet."}})
            request.cr.execute('select id from user_profile where playjam_exported = False and partner_id= %s', (int(partner_id),))
            profile_ids = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            if profile_ids:
                pro_obj=self.pool.get('user.profile').browse(request.cr,SUPERUSER_ID,profile_ids[0])
                gender = pro_obj.gender
                dob = pro_obj.dob
                if dob:
                    date_object = datetime.datetime.strptime(dob, '%Y-%m-%d')
                    dob=date_object.strftime('%Y/%m/%d')
		else:
                    dob = ''
                pin=pro_obj.pin
                playerTag = pro_obj.player_tag
                ageRating = pro_obj.age_rating
                avatar_id=pro_obj.avatar_id
                avatar_id=33
                payload2={'mode':'C', 'uid':partner_id, 'gender':gender,'Pin':pin,'playerTag':playerTag,'dob':dob,'ageRating':ageRating,'avatarId':avatar_id }
                res2=self.profile_playjam(cr,uid,payload2)
                dict_res2=ast.literal_eval(res2)
                if dict_res2.has_key('body') and (dict_res2.get('body')).has_key('result'):
                    if dict_res2['body']['result']==4225:
                        pro_obj.write({'playjam_exported':True})
                    else:
                        json.dumps({'body':{ "code":False, "message":"Profile Call Failed."}})
            app_id,sale_id,duration=False,False,False
            if product_id and order_no:
                product_obj=self.pool.get('product.product').browse(request.cr,SUPERUSER_ID,int(product_id[0]))
                for each in product_obj.ext_prod_config:
                   if each.comp_product_id.product_type=='service':
                       app_id=each.comp_product_id.app_id
                cr.execute('select id from sale_order where name = %s', (str(order_no),))
                order_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                sale_id=order_id[0]
                free_days=prod_obj.free_trail_days
                free_days=100
                if free_days:
                    mon_rel = relativedelta(months=free_days)
                    today = datetime.date.today()
                    end_free_trial=today + mon_rel
                    end_date=end_free_trial.strftime('%Y/%m/%d')
                    duration=time.mktime(datetime.datetime.strptime(end_date, "%Y/%m/%d").timetuple())
            else:
                request.cr.execute('select id from res_partner_policy where active_service = False and agmnt_partner = %s', (str(partner_id),))
                plociy_line_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                if len(plociy_line_id)>1:
                    return json.dumps({'body':{ "code":False, "message":"Multiple Inactive Service."}})
                elif plociy_line_id==[]:
                    if True:
			auth_user_obj.write({'is_activated':True})
                        return json.dumps({"body":{ "code":True, "message":"Success"}})
                    return json.dumps({'body':{ "code":False, "message":"No Service to Activate."}})
                policy_obj=self.pool.get('res.partner.policy').browse(request.cr,SUPERUSER_ID,plociy_line_id[0])
                app_id=policy_obj.product_id.app_id
                sale_id=policy_obj.sale_id
                free_days=100
                if free_days:
                    mon_rel = relativedelta(months=free_days)
                    todays_date = datetime.date.today()
                    end_free_trial=todays_date + mon_rel
                    end_date=end_free_trial.strftime('%Y/%m/%d')
                    duration=time.mktime(datetime.datetime.strptime(end_date, "%Y/%m/%d").timetuple())
            if app_id and sale_id and duration and not used:
                rental_resp=self.rental_playjam(partner_id,app_id,duration)
                rental_res=ast.literal_eval(rental_resp)
                _logger.info('rental response---------------- %s', rental_res)
                if rental_res.has_key('body') and (rental_res.get('body')).has_key('result'):
                    if rental_res['body']['result']==4113:
                        policy_active=self.pool.get('sale.order').write_selected_agreement([sale_id],{'update':True})
                        policy_active=True
                        if policy_active:
                            if tru_location:
                                serial_obj.write({'used':True})
			    auth_user_obj.write({'is_activated':True})
                            return json.dumps({"body":{ "code":True, "message":"Success"}})
        return json.dumps({'body':{ "code":False, "message":"Playjam Server Issue."}})
    
    
    def account_playjam(self,dict,context=None):
        playjam_config=self.pool.get('playjam.config.menu')
        config_ids = playjam_config.search(request.cr,SUPERUSER_ID,[])
        if config_ids:
            config_obj = playjam_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
            url=config_obj.account_playjam
#        url = "http://54.172.158.69/api/rest/flare/account/view.json"
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            data=json.dumps(dict)
            _logger.info('data for account playjam--------------- %s', data)
            request=urllib.quote(data.encode('utf-8'))
            response = requests.post(
                        url, data="request="+request, headers=headers)
            return response.content
        else:
            result={"body":{ 'code':'False', 'message':"Please Define Playjam Configuration!!"}}
            return json.dumps(result)


    def user_login(self, dict, context=None):
        result,auth_user_id = '',[]
        count = 0
        _logger.info('dict for user login--------------- %s', dict)
        device_id,auth_reply = False,False
        if 'deviceId' in dict:
            device_id=dict.get('deviceId')
        if 'authReply' in dict:
            auth_reply=dict.get('authReply')
        if device_id:
            request.cr.execute('select id from user_auth where device_id = %s and is_registered = True', (device_id,))
            auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
        else:
            h=int('-0x0601', 16)
            return json.dumps({'body':{'result':'-0x0601'}})
        if auth_user_id==[]:
            h=int('-0x0012', 16)
            return json.dumps({'body':{'result':'-0x0012'}})
        if 'authReply' in dict:
            if auth_user_id:
                key=self.browse(request.cr,SUPERUSER_ID,auth_user_id[0]).key
                challenge=self.browse(request.cr,SUPERUSER_ID,auth_user_id[0]).challenge
                if key and challenge:
                    chal_key=challenge+key
                    hash_obj=hashlib.sha256(chal_key)
                    encd_challenge=hash_obj.hexdigest()
                    if encd_challenge==auth_reply:
                        session_token=hashlib.sha1(os.urandom(256)).hexdigest()
                        insecure_token=hashlib.sha1(os.urandom(256)).hexdigest()
                        duration=5000000
                        now = datetime.datetime.now()
                        exp_time=now + datetime.timedelta(milliseconds=duration)
                        self.write(request.cr,SUPERUSER_ID,auth_user_id[0],{'session_token':session_token,'insecure_token':insecure_token,'duration':duration,'token_exp_time':exp_time})
                        h=int('0x0011', 16)
                        return json.dumps({'body':{'result': '0x0011', 'sessionToken':session_token,'insecureToken':insecure_token,'duration':duration}})
                    else:
                        h=int('-0x0012', 16)
                        return json.dumps({'body':{'result':'-0x0012'}})
        else:
            if auth_user_id:
                challenge=hashlib.sha1(os.urandom(128)).hexdigest()
                challenge=challenge.replace('A', 'a').replace('F', 'f')
                self.write(request.cr,SUPERUSER_ID,auth_user_id[0],{'challenge':str(challenge)})
                h=int('-0x0011', 16)
                return json.dumps({'body':{'result':'-0x0011','challenge':str(challenge)}})
        return result

    def voucher_validation(self, session_token, voucher_code, context=None):
        """
        Process to validate the voucher.
        :param session_token:
        :param voucher_code:
        :param context:
        :return:
        """
        result = ''
        count = 0
        auth_user_id=[]
        if session_token:
            self._cr.execute('select id from user_auth where session_token= %s', (session_token,))
            auth_user_id = filter(None, map(lambda x:x[0], self._cr.fetchall()))
            check=self.validate_token(session_token,context=None)
        if check==False:
            h=int('-0x0011', 16)
            return {'result':hex(h)}
        if auth_user_id:
            auth_obj=self.browse(auth_user_id[0])
        if check:
            if voucher_code:
                self._cr.execute('select id from voucher_details where  voucher_code= %s', (voucher_code,))
                voucher = filter(None, map(lambda x:x[0], self._cr.fetchall()))
                if voucher_code:
                    voucher_obj=self.pool.get('voucher.details').browse(voucher[0])
                    con=voucher_obj.consumed
                    type=voucher_obj.type
                if con== True or voucher_code==[]:
                    h=int('-0x0021', 16)
                    return {'result':hex(h)}
                if con== False and type=='facevalue':
                    user_id=auth_obj.name.id
                    value=voucher_obj.credit
                    self.wallet_playjam(user_id,context)
                    return {}
                if con==False and type=='rental':
                    user_id=auth_obj.name.id
                    apps_browse_list=voucher_obj.rental_apps
                    app_id=apps_browse_list[0].id
                    duration=0.0
                    duration=voucher_obj.expiration
                    app_id=123 #get the product id
                    self.rental_playjam(user_id,app_id,duration,context)
            return result
            json.dumps({'body':{ "code":False, "message":"Profile Call Failed."}})
            app_id,sale_id,duration=False,False,False
            if product_id and order_no:
                product_obj=self.pool.get('product.product').browse(cr,uid,int(product_id[0]))
                for each in product_obj.ext_prod_config:
                   if each.comp_product_id.product_type=='service':
                       app_id=each.comp_product_id.app_id
                cr.execute('select id from sale_order where name = %s', (str(order_no),))
                order_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                sale_id=order_id[0]
                free_days=prod_obj.free_trail_days
                free_days=100
                if free_days:
                    mon_rel = relativedelta(months=free_days)
                    today = datetime.date.today()
                    end_free_trial=today + mon_rel
                    end_date=end_free_trial.strftime('%Y/%m/%d')
                    duration=time.mktime(datetime.datetime.strptime(end_date, "%Y/%m/%d").timetuple())
            else:
                cr.execute('select id from res_partner_policy where active_service = False and agmnt_partner = %s', (str(partner_id),))
                plociy_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                if len(plociy_line_id)>1:
                    return json.dumps({'body':{ "code":False, "message":"Multiple Inactive Service."}})
                elif plociy_line_id==[]:
                    if True:
			auth_user_obj.write({'is_activated':True})
                        return json.dumps({"body":{ "code":True, "message":"Success"}})
                    return json.dumps({'body':{ "code":False, "message":"No Service to Activate."}})
                policy_obj=self.pool.get('res.partner.policy').browse(cr,uid,plociy_line_id[0])
                app_id=policy_obj.product_id.app_id
                sale_id=policy_obj.sale_id
                free_days=100
                if free_days:
                    mon_rel = relativedelta(months=free_days)
                    todays_date = datetime.date.today()
                    end_free_trial=todays_date + mon_rel
                    end_date=end_free_trial.strftime('%Y/%m/%d')
                    duration=time.mktime(datetime.datetime.strptime(end_date, "%Y/%m/%d").timetuple())
            if app_id and sale_id and duration and not used:
                rental_resp=self.rental_playjam(cr,uid,partner_id,app_id,duration)
                rental_res=ast.literal_eval(rental_resp)
                _logger.info('rental response--------------- %s', rental_res)
                if rental_res.has_key('body') and (rental_res.get('body')).has_key('result'):
                    if rental_res['body']['result']==4113:
                        policy_active=self.pool.get('sale.order').write_selected_agreement(cr,uid,[sale_id],{'update':True})
                        policy_active=True
                        if policy_active:
                            if tru_location:
                                serial_obj.write({'used':True})
			    auth_user_obj.write({'is_activated':True})
                            return json.dumps({"body":{ "code":True, "message":"Success"}})
        return json.dumps({'body':{ "code":False, "message":"Playjam Server Issue."}})
        
    def wallet_playjam(self, user_id, quantity, context=None):
        playjam_config=self.pool.get('playjam.config.menu')
        config_ids = playjam_config.search(request.cr,SUPERUSER_ID,[])
        if config_ids:
            config_obj = playjam_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
            url=config_obj.wallet_playjam
#        url = "http://54.75.245.17/api/rest/flare/wallet/view.json"
            headers = {'content-type': 'application/x-www-form-urlencoded'}

            payload = {
                            "uid": 'FLARE1093',
                            "quantity":float(quantity),
                        }

            data=json.dumps(payload)
            _logger.info('data for wallet--------------- %s', data)
            request=urllib.quote(data.encode('utf-8'))
            response = requests.post(
                        url, data="request="+request, headers=headers)
            _logger.info('response for wallet--------------- %s', response.content)
            return response.content
        else:
            result={"body":{ 'code':'False', 'message':"Please Define Playjam Configuration!!"}}
            return json.dumps(result)
    
    def device_playjam(self, dict, context=None):
        playjam_config=self.pool.get('playjam.config.menu')
        config_ids = playjam_config.search(request.cr,SUPERUSER_ID,[])
        if config_ids:
            config_obj = playjam_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
            url=config_obj.device_playjam
#        url = "http://54.172.158.69/api/rest/flare/device/view.json"
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            data=json.dumps(dict)
            request=urllib.quote(data.encode('utf-8'))
            response = requests.post(
                        url, data="request="+request, headers=headers)
            _logger.info('response for device playjam--------------- %s', response.content)
            return response.content
        else:
            result={"body":{ 'code':'False', 'message':"Please Define Playjam Configuration!!"}}
            return json.dumps(result)
    
    
    def rental_playjam(self, user_id, appId, expiration, context=None):
        playjam_config=self.pool.get('playjam.config.menu')
        config_ids = playjam_config.search(request.cr,SUPERUSER_ID,[])
        if config_ids:
            config_obj = playjam_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
            url=config_obj.rental_playjam
#            url = "http://54.172.158.69/api/rest/flare/rental/view.json"
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            _logger.info('App ID---------- %s', appId)
            expiration=int(expiration)
            _logger.info('Expiration---------- %s', expiration)
            payload = {
                "uid":long(user_id),
                "appId":long(appId),
                "expiration":(expiration)*1000,
                "charge":0.0
                }
            data=json.dumps(payload)
            request=urllib.quote(data.encode('utf-8'))
            response = requests.post(
                        url, data="request="+request, headers=headers)
            return response.content
        else:
            result={"body":{ 'code':'False', 'message':"Please Define Playjam Configuration!!"}}
            return json.dumps(result)

    def validate_insecure_token(self,session_token, context=None):
        request.cr.execute('select id from user_auth where insecure_token= %s', (session_token,))
        auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
        if auth_user_id==[]:
            return False
        if auth_user_id:
            cur_datetime = datetime.datetime.now()
            token_exp_time=self.browse(request.cr,SUPERUSER_ID,auth_user_id[0]).token_exp_time
            dt=datetime.datetime.strptime(token_exp_time, "%Y-%m-%d %H:%M:%S")
            if cur_datetime > dt:
                return False
        return True
    
    
class device_history(models.Model):
    '''Voucher related details'''
    _name = 'device.history'
    
    partner_id = fields.Many2one(comodel_name='res.partner',string='User Name')
    device_id = fields.Char()
    key = fields.Char()
    code = fields.Char()
    user_auth_id = fields.Many2one(comodel_name='user.auth',string='User Auth')

    
    def write(self,ids,vals,context=None):
        cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        res=super(device_history,self).write(cr,uid,ids,vals,context)
        return res

    
    def create(self,vals,context=None):
        cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        res=super(device_history,self).create(cr,uid,vals,context)
        return res
device_history()
