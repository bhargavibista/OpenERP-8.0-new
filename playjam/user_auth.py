# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from random import randint
import hashlib
import json
from openerp.http import request




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

    
    def get_key_code(self,device_id, want_code, context=None):
        print"self",self
        print"device_id",device_id
        print"want_code",want_code
        ''' Returns the code '''
        code ,values,auth_user_id,hashed_key,note= '',{},[],'',''
        print "wantcode-----------func-",want_code
        print "deviceid---------------func--",device_id
        if (want_code is None) or (device_id is None):
            h=int('-0x0601', 16)
            print "hhhhhhhhhh",h
            values =json.dumps({'body':{'result':'-0x0601'}})
            return values
        random=randint(1,99999)
        key_random=randint(1,9999999999)
        print "random---------------",random
        print "deviceid------------++++++++",device_id,want_code
        dev_id=device_id
        if device_id and want_code==False:
            request.cr.execute('select id from user_auth where device_id = %s', (dev_id,))
            auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            print "auth_user_id",auth_user_id
            print "app_unlink====",auth_user_id
            if auth_user_id:
                brow_obj=self.browse(auth_user_id[0])
                print "enter-------"
                active=brow_obj.is_registered
                print "active-----------",active
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
            print"auth_user_id",auth_user_id
            request.cr.execute('select id from user_auth where device_id = %s',(dev_id,))
            auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            code=str(random)+device_id
            print "code------------",code,type(code)
            note="Enter the code on website to complete registration "
            key=str(key_random)+device_id
            hash_object = hashlib.md5(key)
            hashed_key=hash_object.hexdigest()
            hashed_key=hashed_key.replace('A', 'a').replace('F', 'f')
            if auth_user_id:
                self.write(request.cr,1,auth_user_id,{'code':code,'key':hashed_key,'device_id':device_id})
            else:
                self.create(request.cr,1,{'code':code,'key':hashed_key,'device_id':device_id})
            #self.create(cr,uid,{'code':code,'key':hashed_key,'device_id':device_id})
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
            print "app_unlink====",auth_user_id
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
        print "dict-----------",dict
        partner_id=dict.get('CustomerId')
	print"*******",partner_id,type(partner_id)
        code= dict.get('ActivationCode')
        print "code-----------------",code
        order_no=False
	product_id=False
        used = False
        request.cr.execute('select id from user_auth where code= %s', (str(code),))
        auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
        if auth_user_id==[]:

            return json.dumps({'body':{"code":False, "message":"No Such Device"}})

	request.cr.execute('select id from res_partner where id= %s', (int(partner_id),))
        pat_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
	print "patid-----------------",pat_id
	if pat_id==[]:
	    return json.dumps({'body':{"code":False, "message":"Partner Not Present"}})

        #check if device belongs to TRU and create a SO if yes.

        pat_obj=self.pool.get('res.partner').browse(request.cr,1,int(partner_id))
        print"pat_obj",pat_obj
        auth_user_obj=self.pool.get('user.auth').browse(request.cr,1,auth_user_id[0])
        email_id=pat_obj.emailid
        print"email_id",email_id
        order_dict={"CustomerId":partner_id,"Email":str(email_id),}

        billing_info={}
#        if pat_obj.customer_profile_id:
#            print "pat_obj.customer_profile_id----",pat_obj.customer_profile_id
#            billing_info.update({'PaymentProfileId':pat_obj.customer_profile_id})
        if pat_obj.profile_ids:
            print "profileids-------------",pat_obj.profile_ids
            for each in pat_obj.profile_ids:
                if each.active_payment_profile==True:
                    if each.profile_id:
                        billing_info.update({'PaymentProfileId':str(each.profile_id)})
                    if each.credit_card_no :
#                        and each.exp_date
                        cc_no=each.credit_card_no
#                        "ExpDate":each.exp_date,
                        billing_info.update({'CreditCard':{"CCNumber":str(each.credit_card_no),}})
            if billing_info=={}:
                return json.dumps({'body':{"code":False, "message":"Billing Info Missing!!"}})

        print "billing_infobilling_infobilling_info",billing_info

#      curl -X POST -d 'request=%7B%22ApiId%22%3A%22123%22%2C%22DBName%22%3A%22cox_db_12jan%22%2C%22CustomerId%22%3A%224545%22%2C%22ActivationCode%22%3A%2223456%22%2C%7D' http://localhost:8089/flare/magento/LinkAccount

        if pat_obj.street and pat_obj.city and pat_obj.state_id and pat_obj.zip:
            bill_add={ "Street1": str(pat_obj.street),"Street2": str(pat_obj.street2 or ""),"City": str(pat_obj.city),"State": str(pat_obj.state_id.code),"Zip": str(pat_obj.zip),}
            billing_info.update({'BillingAddress':bill_add})
        else:
            return json.dumps({'body':{"code":False, "message":"Incomplete Billing Address!!"}})

        order_dict.update({'BillingInfo':billing_info})
        partner_addr = self.pool.get('res.partner').address_get(request.cr, 1, [int(partner_id)],['delivery',])
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

        print "partner_addr",partner_addr
        print "order_dict------",json.dumps(order_dict)
        serial_obj=auth_user_obj.serial_no
        
	print "serial_obj----------------",serial_obj
        tru_location=False
        if serial_obj:
            current_location_type=serial_obj.location_id.usage
	    print "current_location_type",current_location_type
            if current_location_type=='customer':
		print "serilobj.moveids--------",serial_obj.move_prod_lot_ids
		
                move_ids = [move_id.id for move_id in serial_obj.move_prod_lot_ids]
                print "move_ids--------------",move_ids
		
	    	if move_ids: 
                    latest_move_id=max(move_ids)
                    selling_location_id=self.pool.get('stock.move').browse(cr,uid,latest_move_id).location_id
                    print "selling_location-------------",selling_location_id
                    if selling_location_id.tru==True:
                        tru_location=selling_location_id.id
	    
            elif current_location_type=='internal' and serial_obj.location_id.tru:
		print "innnnnnnnnnnnnnnnnnnnnn",serial_obj.location_id.tru
                tru_location=serial_obj.location_id.id
#        tru_already_attached=False
        if tru_location:
            if pat_obj.user_auth_ids:
                for each in pat_obj.user_auth_ids:
                    sno=each.serial_no.name

                    if each.is_tru==True and sno!= serial_obj.name:
                        return json.dumps({'body':{ "code":False, "message":"A Tru Device is already attached to this Account."}})

            used= serial_obj.used

        if tru_location and not used:
            print "tru_location-------",tru_location
            cr.execute('select id from product_product where location_id= %s', (tru_location,))
            product_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "product_id-------------",product_id
            if product_id:
                prod_obj=self.pool.get('product.product').browse(cr,uid,product_id[0])
                prod_info={"ProductId":product_id[0],"Qty":"1.0","Price": prod_obj.product_tmpl_id.list_price,}
                order_dict.update({"OrderLine":{"line1":prod_info},"tru":True})
                print "order_dict------------------",order_dict,type(order_dict)
#                result={"body":{ 'code':True, 'message':"Success",'OrderNo':so_name}}
		print "serial_obj.order_created--------------------------0",serial_obj.order_created
		if not serial_obj.order_created:
                    order_res=self.pool.get('res.partner').create_order_magento(cr,uid,order_dict,{})
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
                    else:
                        serial_obj.write({'order_created':True})
			cr.commit()
                        self.write(cr,uid,auth_user_id,{'is_tru':True})

#        ero
        if auth_user_id and partner_id:
            self.write(request.cr,1,auth_user_id,{'partner_id':partner_id})

            accountPin= pat_obj.account_pin
            full_name=pat_obj.name
	    print "pat_obj.name----------",pat_obj.name
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
		#return json.dumps({'body':{"code":False, "message":"DOB Is Required"}})
            account_pin=pat_obj.account_pin
            payload={'name':name,'uid':partner_id, 'surname':surname,'email':email,'accountPin':account_pin,'dob':dob,'mode':'C','active':True}
	    #payload={'name':name,'uid':12345601, 'surname':surname,'email':'abc@123.com','dob':dob,'accountPin':account_pin,'mode':'C','active':True}
	    print"account data create payload=-------====",payload
            if not p_exp:
                res=self.account_playjam(request.cr,1,payload)
                print"res----account---------",res,type(res)
                dict_res=ast.literal_eval(res)
                if dict_res.has_key('body') and (dict_res.get('body')).has_key('result'):
                    if dict_res['body']['result']==4097:
                    #if dict_res['body']['result']==-4101:
                        pat_obj.write({'active':True,'playjam_exported':True})
			cr.commit()
                    else:
                        r_string=dict_res['body']['resultString']
                        return json.dumps({'body':{ "code":False, "message":"Account Call to Playjam Failed."}})

		else:
		    return json.dumps({"body":{"code":False,"message":"Account Call To Playjam Failed."}})		    
	    if auth_user_obj.is_attached==False:
                device_payload={'uid':partner_id,'mode':'C','code':code,'alias':'abc'}
                device_res=self.device_playjam(request.cr,request.uid,device_payload)
                device_response=ast.literal_eval(device_res)
                print "deviceresponse-----------------",device_response
#                print "type$$$$$$$$$$$$$$$$$$$$$$$$$$$",dict_res['body']['result'],type(dict_res['body']['result'])
                if device_response.has_key('body') and (device_response.get('body')).has_key('result'):
                    if device_response['body']['result']==4241:
                        auth_user_obj.write({'is_attached':True})
                    else:
                        #r_string=dict_res['body']['resultString']
                        return json.dumps({'body':{ "code":False, "message":"Device call to Playjam Failed"}})
                else:
                     return json.dumps({'body':{ "code":False, "message":"Device Call To Playjam Failed."}})
            check_user_profiles=pat_obj.user_profile_ids
            if check_user_profiles==[]:
                return json.dumps({"body":{ "code":False, "message":"Profile Not Created Yet."}})
            cr.execute('select id from user_profile where playjam_exported = False and partner_id= %s', (int(partner_id),))
            profile_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
	    print "profile_ids---------------------------",profile_ids
            if profile_ids:
#                return json.dumps({"body":{ "code":False, "message":"Profile Not Created Yet."}})

                pro_obj=self.pool.get('user.profile').browse(request.cr,request.uid,profile_ids[0])
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
                pc_params=pro_obj.pc_params

                payload2={'mode':'C', 'uid':partner_id, 'gender':gender,'Pin':pin,'playerTag':playerTag,'dob':dob,'ageRating':ageRating,'avatarId':avatar_id }
		#payload2={'mode':'C', 'uid':partner_id, 'gender':gender,'Pin':pin,'playerTag':playerTag,'ageRating':ageRating,'avatarId':avatar_id ,'pcParams':pc_params}
                res2=self.profile_playjam(request.cr,request.uid,payload2)
                print "res2222222222222222222222",res2
                dict_res2=ast.literal_eval(res2)
                if dict_res2.has_key('body') and (dict_res2.get('body')).has_key('result'):
                    if dict_res2['body']['result']==4225:
                    #if dict_res2['body']['result']==-4230:
                        pro_obj.write({'playjam_exported':True})
                    else:
                        #r_string=dict_res2['body']['result']
                        json.dumps({'body':{ "code":False, "message":"Profile Call Failed."}})

            app_id,sale_id,duration=False,False,False
            print "product_id-------",product_id,order_no
            if product_id and order_no:
                print "product_id-------",product_id,order_no
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
                    print "enter free trialdats---------",free_days
                    mon_rel = relativedelta(months=free_days)
                    today = datetime.date.today()
                    end_free_trial=today + mon_rel
                    end_date=end_free_trial.strftime('%Y/%m/%d')
                    duration=time.mktime(datetime.datetime.strptime(end_date, "%Y/%m/%d").timetuple())
            else:
                cr.execute('select id from res_partner_policy where active_service = False and agmnt_partner = %s', (str(partner_id),))
                plociy_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                if len(plociy_line_id)>1:
                    print "11111111111111111111"
                    return json.dumps({'body':{ "code":False, "message":"Multiple Inactive Service."}})
                elif plociy_line_id==[]:
                    if True:
			auth_user_obj.write({'is_activated':True})
                        return json.dumps({"body":{ "code":True, "message":"Success"}})
                    print "222222222222222222"
                    return json.dumps({'body':{ "code":False, "message":"No Service to Activate."}})
                policy_obj=self.pool.get('res.partner.policy').browse(cr,uid,plociy_line_id[0])
                app_id=policy_obj.product_id.app_id
                sale_id=policy_obj.sale_id
                #sale_id=25
                #app_id=20
                free_days=100
                #free_days=policy_obj.free_trail_days
                #if free_days==0:
                    #free_days=1
                if free_days:
                    mon_rel = relativedelta(months=free_days)
                    todays_date = datetime.date.today()
                    #today=todays_date.date()
                    end_free_trial=todays_date + mon_rel
                    end_date=end_free_trial.strftime('%Y/%m/%d')
                    duration=time.mktime(datetime.datetime.strptime(end_date, "%Y/%m/%d").timetuple())

            print "Appid---------$$$$44444",app_id
            print "sale_id--------------123",sale_id
            print "duration!!!!!!!!!!!!!!!!!----------",duration
            if app_id and sale_id and duration and not used:
                rental_resp=self.rental_playjam(cr,uid,partner_id,app_id,duration)
                rental_res=ast.literal_eval(rental_resp)
                print "rentalres---------------------",rental_res
                if rental_res.has_key('body') and (rental_res.get('body')).has_key('result'):
                    if rental_res['body']['result']==4113:
                    #if rental_res['body']['result']==-4230:
                        policy_active=self.pool.get('sale.order').write_selected_agreement(cr,uid,[sale_id],{'update':True})
                        policy_active=True
                        if policy_active:
                            if tru_location:
                                serial_obj.write({'used':True})
			    auth_user_obj.write({'is_activated':True})
                            return json.dumps({"body":{ "code":True, "message":"Success"}})

        return json.dumps({'body':{ "code":False, "message":"Playjam Server Issue."}})

