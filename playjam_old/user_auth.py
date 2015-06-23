from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
import datetime
import hashlib
import md5
from datetime import timedelta
from datetime import date
import time
import requests
import json
import urllib
import ast
#from jsonrpc import ServiceProxy
from dateutil.relativedelta import relativedelta
import datetime




class user_auth(osv.osv):
    '''Authenticating the user'''
    _name = 'user.auth'
    _description = 'User Authentication'
    def get_key_code(self,cr, uid,serial_no,want_code,device_id, context=None):
        ''' Returns the code '''

        code ,values,auth_user_id,hashed_key,note= '',{},[],'',''
        print "wantcode-----------func-",want_code
        print "deviceid---------------func--",serial_no
        if (want_code is None) or (serial_no is None):
            h=int('-0x0601', 16)
            print "hhhhhhhhhh",h
            values =json.dumps({'body':{'result':-1537}})
            return values
        random=randint(1,99999)
        key_random=randint(1,9999999999)
        print "random---------------",random
        print "deviceid------------",serial_no,type(serial_no)
        cr.execute('select id from stock_production_lot where name = %s', (serial_no,))
        dev_id=filter(None, map(lambda x:x[0], cr.fetchall()))
	print "devid--------------",dev_id
        if dev_id == []:
            return json.dumps({'body':{'result':-1537}})
        if serial_no and want_code==False:
	    print "print serial_no-----------",serial_no
            cr.execute('select id from user_auth where serial_no = %s', (dev_id[0],))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "auth_user_id",auth_user_id
            print "app_unlink====",auth_user_id
            if auth_user_id:
                brow_obj=self.browse(cr,uid,auth_user_id[0])
                print "enter-------"
                active=brow_obj.is_registered
		acc_linked=brow_obj.partner_id
                print "active-----------",active
                if active and acc_linked:
                    key=brow_obj.key
                    hash_obj=hashlib.md5(key)
                    hash_key=hash_obj.hexdigest()

                    h=int('0x0001', 16)
                    values=json.dumps({'body':{'result':1,'hashKey':hash_key}})
		    return values
                else:
                    h=int('-0x0001', 16)
                    values=json.dumps({'body':{'result': -1}})
                    return values
	
#        Code to delete the device at playjam and maintain history
        if serial_no and want_code==True and device_id:
            print "innnnnnnn"
            cr.execute('select id from user_auth where serial_no = %s', (dev_id[0],))
            exist_auth_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            if exist_auth_id:
                auth_exist_obj=self.browse(cr,uid,exist_auth_id[0])
                existing_device_id=auth_exist_obj.device_id
                if existing_device_id != device_id:
                    existing_partner=auth_exist_obj.partner_id.id
                    existing_code=auth_exist_obj.code
                    existing_key=auth_exist_obj.key
                    
                    if existing_partner and existing_code:
                        device_del_dict={'mode':'D','uid':existing_partner,'code':existing_code}
                        del_res=self.device_playjam(cr,uid,device_del_dict,{})
                        device_response=ast.literal_eval(del_res)
                        print "deviceresponse-----------------",device_response
#                        print "type$$$$$$$$$$$$$$$$$$$$$$$$$$$",dict_res['body']['result'],type(dict_res['body']['result'])
                        if device_response.has_key('body') and (device_response.get('body')).has_key('result'):
                            if device_response['body']['result']!=4244:
                                return json.dumps({'body':{'result': -1}})
                            x=self.pool.get('device.history').create(cr,uid,{'partner_id':existing_partner,'device_id':existing_device_id,'key':existing_key,'code':existing_code,'user_auth_id':exist_auth_id[0],})
			    print "xxx---------------",x


        if serial_no and want_code==True and device_id:

	    cr.execute('select id from user_auth where serial_no = %s and device_id= %s', (dev_id[0],device_id))
            already_activated = filter(None, map(lambda x:x[0], cr.fetchall()))
	    print "alreadyactivated----------------------------------",already_activated
            if already_activated!=[]:
		attached_partner=self.browse(cr,uid,already_activated[0]).partner_id
		if attached_partner:
                    return json.dumps({'body':{'result': 1}})

	    print "serialno-----------",serial_no
	    cr.execute('select id from user_auth where serial_no = %s', (dev_id[0],))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            code=str(random)+serial_no
            print "code------------",code,type(code)
            note="Enter the code on website to complete registration "
            key=str(key_random)+serial_no
            hash_object = hashlib.md5(key)
            hashed_key=hash_object.hexdigest()
            hashed_key=hashed_key.replace('A', 'a').replace('F', 'f')
	    if auth_user_id:
                self.write(cr,uid,auth_user_id,{'code':code,'key':hashed_key,'serial_no':dev_id[0],'device_id':device_id, 'is_registered':False,'partner_id':False, 'is_attached':False})
            else:
                self.create(cr,uid,{'code':code,'key':hashed_key,'serial_no':dev_id[0],'device_id':device_id,'is_registered':False,'partner_id':False, 'is_attached':False})
            h=int('-0x0001', 16)
            values=json.dumps({'body':{'result':-1,'code':str(code),'key':hashed_key}})
            return values

	values= json.dumps({'body':{'result':-1537}})
        return values

    def register_user(self, cr, uid, code, context=None):
        ''' verifies user and associates the partner'''
        if code:
            cr.execute('select id from user_auth where code = %s', (code,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "app_unlink====",auth_user_id
            if auth_user_id:
		partner_id=self.browse(cr,uid,auth_user_id[0]).partner_id
		is_registered=self.browse(cr,uid,auth_user_id[0]).is_registered
		print "partneridddddddddddddddddddddddddddd",partner_id
		print "isregistereddddddddddddddddddddddddd",is_registered
		if partner_id and is_registered:
		    return json.dumps({'body':{"code":False, "message":"The Code has Already been Validated"}})
		self.write(cr,uid,auth_user_id,{'is_registered':True})
                partner=self.browse(cr,uid,auth_user_id[0]).partner_id
                if partner:
                    return json.dumps({'body':{"code":True, "message":"Success", "LinkedAccount":True, "OfferSKU":""}})
                else:
                    return json.dumps({'body':{"code":True, "message":"Success", "LinkedAccount":False, "OfferSKU":""}})
            else:
                return json.dumps({'body':{"code":False, "message":"No such Device"}})

        else:
            return json.dumps({'body':{"code":False, "message":"Please enter the Activation code"}})




    def user_login(self, cr, uid, dict, context=None):
        ''' Challenge Response algo.  '''
        result,auth_user_id = '',[]
        count = 0
	print "dict---------------",dict
        device_id,auth_reply = False,False
        if dict.has_key('deviceId'):
            device_id=dict.get('deviceId')
        if dict.has_key('authReply'):
            auth_reply=dict.get('authReply')
        if device_id:
            cr.execute('select id from user_auth where device_id = %s and is_registered = True', (device_id,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "app_unlink====",auth_user_id
        else:
            h=int('-0x0601', 16)
            return json.dumps({'body':{'result':-1537}})
        if auth_user_id==[]:
            print "auth_user_id$$$$$$$$$$$$$$$$$",auth_user_id
            h=int('-0x0012', 16)
            return json.dumps({'body':{'result':-18}})
        print "authreply--------------",auth_reply
        if dict.has_key('authReply'):
            if auth_user_id:
                key=self.browse(cr,uid,auth_user_id[0]).key
                challenge=self.browse(cr,uid,auth_user_id[0]).challenge
                if key and challenge:
                    chal_key=challenge+key
                    hash_obj=hashlib.sha256(chal_key)
                    encd_challenge=hash_obj.hexdigest()
                    print "encd_challenge------------",encd_challenge
                    if encd_challenge==auth_reply:
                        session_token=hashlib.sha1(os.urandom(256)).hexdigest()
                        insecure_token=hashlib.sha1(os.urandom(256)).hexdigest()
#                        duration=randint(1,99999)
                        duration=5000000
                        now = datetime.datetime.now()
                        print "now-------------------",now
                        exp_time=now + datetime.timedelta(milliseconds=duration)
                        print "now-----------------------",exp_time,type(exp_time)
                        self.write(cr,uid,auth_user_id[0],{'session_token':session_token,'insecure_token':insecure_token,'duration':duration,'token_exp_time':exp_time})
#                        h=-int('0x0011', 16)
                        return json.dumps({'body':{'result': 17, 'sessionToken':session_token,'insecureToken':insecure_token,'duration':duration}})
                    else:
                        h=int('-0x0012', 16)
                        return json.dumps({'body':{'result':-18}})

        else:
            if auth_user_id:
                print "enter22222222"
                challenge=hashlib.sha1(os.urandom(128)).hexdigest()
                print "chal--------------",challenge,type(challenge)
                challenge=challenge.replace('A', 'a').replace('F', 'f')
                print'chalengr=================',challenge

                self.write(cr,uid,auth_user_id[0],{'challenge':str(challenge)})
                h=int('-0x0011', 16)
                return json.dumps({'body':{'result':-17,'challenge':str(challenge)}})

        return result



    _columns={
        'partner_id': fields.many2one('res.partner',"User Name"),
        'serial_no':fields.many2one('stock.production.lot','Serial Number'),
        'device_id': fields.char('Device ID', size=128),
        'code': fields.char('Code', size=128),
        'key': fields.char('Key', size=128),
        'is_registered': fields.boolean('Registered'),
        'challenge':fields.char('Challenge', size=128),
        'session_token':fields.char('Session Token', size=128),
        'insecure_token':fields.char('Insecure Token', size=128),
        'duration':fields.char('Duration', size=128),
        'token_exp_time':fields.datetime('Token Exp Time'),
        'mac_address':fields.char('MAC Address',size=256),
	'device_history_ids' : fields.one2many('device.history','user_auth_id','History'),
	'is_tru': fields.boolean('Tru'),
        'is_activated': fields.boolean('Registered'),
	'is_attached': fields.boolean('Attached'),
    }
    _defaults={
    }





    def validate_token(self, cr, uid, session_token, context=None):

        cr.execute('select id from user_auth where session_token= %s', (session_token,))
        auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if auth_user_id==[]:
            return False
        if auth_user_id:
            cur_datetime = datetime.datetime.now()
            print "cur----------------",cur_datetime
            token_exp_time=self.browse(cr,uid,auth_user_id[0]).token_exp_time
            print "tok_exp_time-------------------------",token_exp_time
            dt=datetime.datetime.strptime(token_exp_time, "%Y-%m-%d %H:%M:%S.%f")
            print "dt-----------------------",dt
            if cur_datetime > dt:
                return False

        return True



    def obtaintransactions(self, cr, uid,user_id,start_time,end_time, context=None):

        if uid and start_time and end_time:
            url = "http://54.172.158.69/api/rest/flare/obtaintransactions/view.json"
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            payload = {
                "uid": uid,
                "startTime":long(start_time),
                "endTime":long(end_time),


            }

            data=json.dumps(payload)
            request=urllib.quote(data.encode('utf-8'))
            response = requests.post(
                        url, data="request="+request, headers=headers)

            return response.text

        return False


    def account_playjam(self,cr,uid,dict,context=None):
        url = "http://54.172.158.69/api/rest/flare/account/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}



        data=json.dumps(dict)
	print"account datat========",data
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text


    def profile_playjam(self,cr,uid,dict,context=None):
        url = "http://54.172.158.69/api/rest/flare/profile/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}


        data=json.dumps(dict)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text



    '''def link_account(self, cr, uid, dict, context=None):
        print "dict-----------",dict
        partner_id=dict.get('CustomerId')
	print"*******",partner_id,type(partner_id)
        code= dict.get('ActivationCode')
        print "code-----------------",code
        order_no=False
	product_id=False
        cr.execute('select id from user_auth where code= %s', (str(code),))
        auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if auth_user_id==[]:

            return json.dumps({'body':{"code":False, "message":"No Such Device"}})

	cr.execute('select id from res_partner where id= %s', (int(partner_id),))
        pat_id = filter(None, map(lambda x:x[0], cr.fetchall()))
	print "patid-----------------",pat_id
	if pat_id==[]:
	    return json.dumps({'body':{"code":False, "message":"Partner Not Present"}})

        #check if device belongs to TRU and create a SO if yes.

        pat_obj=self.pool.get('res.partner').browse(cr,uid,int(partner_id))
        auth_user_obj=self.pool.get('user.auth').browse(cr,uid,auth_user_id[0])
        email_id=pat_obj.emailid
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
        partner_addr = self.pool.get('res.partner').address_get(cr, uid, [int(partner_id)],['delivery',])
        delivery_add=partner_addr.get('delivery')
        default_add=partner_addr.get('default')
        if delivery_add==default_add:
            order_dict.update({'ShippingAddress':bill_add})
        else:
            delivery_obj=self.browse(cr, uid, delivery_add,{})
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
                move_ids = [move_id.id for move_id in serial_obj.move_ids]
                print "move_ids--------------",move_ids
                latest_move_id=max(move_ids)
                selling_location_id=self.pool.get('stock.move').browse(cr,uid,latest_move_id).location_id
                print "selling_location-------------",selling_location_id
                if selling_location_id.tru==True:
                    tru_location=selling_location_id.id
            elif current_location_type=='internal' and serial_obj.location_id.tru:
		print "innnnnnnnnnnnnnnnnnnnnn",serial_obj.location_id.tru
                tru_location=serial_obj.location_id.id


        if tru_location:
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
		


                order_res=self.pool.get('res.partner').create_order_magento(cr,uid,order_dict,{})
		print"order_res-----------------",order_res
		order_res=str(order_res)
		if 'true' in order_res:
		    order_res=order_res.replace('true','True')
		if 'false' in order_res:
                    order_res=order_res.replace('false','False')

                ord_res=ast.literal_eval(str(order_res))
		print "ord_res-------------",ord_res
		
		#order_no='SO060'
                if (ord_res.get('body')).has_key('OrderNo'):
                    order_no=(ord_res.get('body')).get('OrderNo')
		print"(ord_res.get('body')=============----------++++",ord_res.get('body')
                if (ord_res.get('body')).get('code')!=True:
                    return json.dumps({'body':{"code":False, "message":"Order Not Created!!"}})



#        ero
        if auth_user_id and partner_id:
            self.write(cr,uid,auth_user_id,{'partner_id':partner_id})


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
	    res=self.account_playjam(cr,uid,payload)
	    print"res----account---------",res,type(res)
	    dict_res=ast.literal_eval(res)
	    if dict_res.has_key('body') and (dict_res.get('body')).has_key('result'):
	        if dict_res['body']['result']==4097:
		#if dict_res['body']['result']==-4101:
                    pat_obj.write({'active':True,'playjam_exported':True})
                    #device_payload={'uid':12345601,'mode':'C','code':code,'alias':'abc'}
		    device_payload={'uid':partner_id,'mode':'C','code':code,'alias':'abc'}
                    device_res=self.device_playjam(cr,uid,device_payload)
                    device_response=ast.literal_eval(device_res)
		    print "deviceresponse-----------------",device_response
		    print "type$$$$$$$$$$$$$$$$$$$$$$$$$$$",dict_res['body']['result'],type(dict_res['body']['result'])
                    if device_response.has_key('body') and (device_response.get('body')).has_key('result'):
                        if device_response['body']['result']!=4241:
			#if device_response['body']['result']!=-4243:
                            return json.dumps({'body':{ "code":False, "message":"Device Call To Playjam Failed."}})

                    cr.execute('select id from user_profile where playjam_exported = False and partner_id= %s', (int(partner_id),))
                    profile_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
		    if profile_ids==[]:
			return json.dumps({"body":{ "code":False, "message":"Profile Not Created Yet."}})

                    pro_obj=self.pool.get('user.profile').browse(cr,uid,profile_ids[0])
                    gender = pro_obj.gender
                    dob = pro_obj.dob
		    if dob:
		    	date_object = datetime.datetime.strptime(dob, '%Y-%m-%d')
            	    	dob=date_object.strftime('%Y/%m/%d')
		    dob = ''
                    pin=pro_obj.pin
                    playerTag = pro_obj.player_tag
                    ageRating = pro_obj.age_rating
                    avatar_id=pro_obj.avatar_id
		    avatar_id=33
                    pc_params=pro_obj.pc_params

                    payload2={'mode':'C', 'uid':partner_id, 'gender':gender,'Pin':pin,'playerTag':playerTag,'ageRating':ageRating,'avatarId':avatar_id }
                    res2=self.profile_playjam(cr,uid,payload2)
		    print "res2222222222222222222222",res2
                    dict_res2=ast.literal_eval(res2)
                    if dict_res2.has_key('body') and (dict_res2.get('body')).has_key('result'):
                        if dict_res2['body']['result']==4225:
			#if dict_res2['body']['result']==-4230:
                            pro_obj.write({'playjam_exported':True})


                            app_id,sale_id,duration=False,False,False
			    print "product_id-------",product_id,order_no
                            if product_id and order_no:
				print "product_id-------",product_id,order_no
				#self.pool.get('product.product').browse(cr,uid,product_id[0]).
                                #app_id=product_id[0]
				app_id=109
                                cr.execute('select id from sale_order where name = %s', (str(order_no),))
                                order_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                                sale_id=order_id[0]
                                free_days=prod_obj.free_trail_days
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
				    print "222222222222222222"
                                    return json.dumps({'body':{ "code":False, "message":"No Service to Activate."}})
                                policy_obj=self.pool.get('res.partner.policy').browse(cr,uid,plociy_line_id[0])
                                app_id=policy_obj.product_id.id
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
                            if app_id and sale_id and duration:
                                rental_resp=self.rental_playjam(cr,uid,partner_id,app_id,duration)
                                rental_res=ast.literal_eval(rental_resp)
				print "rentalres---------------------",rental_res
                                if rental_res.has_key('body') and (rental_res.get('body')).has_key('result'):
                                    if rental_res['body']['result']==4113:
				    #if rental_res['body']['result']==-4230:
                                        policy_active=self.pool.get('sale.order').write_selected_agreement(cr,uid,[sale_id],{'update':True})
					policy_active=True
                                        if policy_active:
                                            return json.dumps({"body":{ "code":True, "message":"Success"}})
#	return json.dumps({"body":{ "code":True, "message":"Success"}})
        return json.dumps({'body':{ "code":False, "message":"Playjam Server Issue."}})'''

    




    def link_account(self, cr, uid, dict, context=None):
        print "dict-----------",dict
        partner_id=dict.get('CustomerId')
	print"*******",partner_id,type(partner_id)
        code= dict.get('ActivationCode')
        print "code-----------------",code
        order_no=False
	product_id=False
        used = False
        cr.execute('select id from user_auth where code= %s', (str(code),))
        auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if auth_user_id==[]:

            return json.dumps({'body':{"code":False, "message":"No Such Device"}})

	cr.execute('select id from res_partner where id= %s', (int(partner_id),))
        pat_id = filter(None, map(lambda x:x[0], cr.fetchall()))
	print "patid-----------------",pat_id
	if pat_id==[]:
	    return json.dumps({'body':{"code":False, "message":"Partner Not Present"}})

        #check if device belongs to TRU and create a SO if yes.

        pat_obj=self.pool.get('res.partner').browse(cr,uid,int(partner_id))
        auth_user_obj=self.pool.get('user.auth').browse(cr,uid,auth_user_id[0])
        email_id=pat_obj.emailid
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
        partner_addr = self.pool.get('res.partner').address_get(cr, uid, [int(partner_id)],['delivery',])
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
            self.write(cr,uid,auth_user_id,{'partner_id':partner_id})

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
                res=self.account_playjam(cr,uid,payload)
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
                device_res=self.device_playjam(cr,uid,device_payload)
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

                pro_obj=self.pool.get('user.profile').browse(cr,uid,profile_ids[0])
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
                res2=self.profile_playjam(cr,uid,payload2)
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






    def voucher_validation(self, cr, uid, session_token, voucher_code, context=None):
        ''' Process to validate the voucher.  '''
        result = ''
        count = 0
        auth_user_id=[]

        if session_token:
            cr.execute('select id from user_auth where session_token= %s', (session_token,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            check=self.validate_token(cr,uid,session_token,context=None)

        if check==False:
            h=int('-0x0011', 16)
            return {'result':hex(h)}
        if auth_user_id:
            auth_obj=self.browse(cr,uid,auth_user_id[0])

        if check:
            if voucher_code:
                cr.execute('select id from voucher_details where  voucher_code= %s', (voucher_code,))
                voucher = filter(None, map(lambda x:x[0], cr.fetchall()))
                print "voucher====",voucher
                if voucher_code:
                    voucher_obj=self.pool.get('voucher.details').browse(cr,uid,voucher[0])
                    con=voucher_obj.consumed
                    type=voucher_obj.type
                    print "con============",con
                    print "typeeeeeeeeeeee",type

                if con==True or voucher_code==[]:
#                    enter11
                    h=int('-0x0021', 16)
                    return {'result':hex(h)}

                if con==False and type=='facevalue':
                    user_id=auth_obj.name.id
                    value=voucher_obj.credit
                    print "value----------",value
                    self.wallet_playjam(cr,uid,user_id,context)

                    print "response------------------",response
                    return {}
                if con==False and type=='rental':
                    user_id=auth_obj.name.id
                    apps_browse_list=voucher_obj.rental_apps
                    print "apps_browse_listapps_browse_list",apps_browse_list
                    app_id=apps_browse_list[0].id
                    duration=0.0
                    duration=voucher_obj.expiration
                    app_id=123 #get the product id
                    self.rental_playjam(cr,uid,user_id,app_id,duration,context)

        return result




    def device_playjam(self, cr, uid, dict, context=None):
        url = "http://54.172.158.69/api/rest/flare/device/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}


        data=json.dumps(dict)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        print "response.text----------",response.text

        return response.text




    def rental_playjam(self, cr, uid, user_id, appId, expiration, context=None):
        url = "http://54.172.158.69/api/rest/flare/rental/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        print "appid------------",appId
	expiration=int(expiration)
        print "expiration-------",expiration
        payload = {
            "uid":long(user_id),
            "appId":long(appId),
            "expiration":(expiration)*1000,
	    "charge":0.0
            }
	print"payloaddddddddddddddddddddddddddddddddddddddddddddd",payload
#	payload = {
#           "uid":"FLARE1093",
#           "appId": 128,
#           "expiration": 0
#            }

        data=json.dumps(payload)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text


    def wallet_playjam(self, cr, uid, user_id, quantity, context=None):
        url = "http://54.172.158.69/api/rest/flare/wallet/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}

        payload = {
                        "uid": user_id,
                        "quantity":float(quantity),
                    }


        data=json.dumps(payload)
	print "data---------------------------",data
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text




    '''def wallet_top_up(self, cr, uid, dict, context=None):
        quantity=False
        session_token=dict.get('sessionToken')
        if dict.has_key('quantity'):
            quantity=dict.get('quantity')
        print"enterrrrrrrrrrrr",quantity
        option_list=[]
        top_optns_obj=self.pool.get('topup.options')
        check=False
        if session_token:
            check=self.validate_token(cr,uid,session_token,context=None)

        if check==False:
            h=int('-0x0011', 16)
            return json.dumps({'result':-17})
        if check:
            if not quantity:
                cr.execute('select id from topup_options')
                top_up_options = filter(None, map(lambda x:x[0], cr.fetchall()))
                print "top_up_options-------------",top_up_options
                for each in top_up_options:
                    cdt=top_optns_obj.browse(cr,uid,each).credit
                    fb=top_optns_obj.browse(cr,uid,each).value
                    option_list.append({'credit':cdt,'value':fb})
                print "option_list=----------------",option_list
                return json.dumps({'body':{'result': 50,'options':option_list}})

            else:
                cr.execute('select partner_id from user_auth where session_token=%s', (session_token,))
                partner_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                res=self.wallet_playjam(cr,uid,partner_id[0],quantity)

                print"res-------------",res,type(res)
                dict_res=ast.literal_eval(res)
                if dict_res.has_key('body') and (dict_res.get('body')).has_key('result'):
                    if dict_res['body']['result']==4129:
                        return json.dumps({'body':{'result':49}})

                return json.dumps({'body':{'result':-49}})'''


    def wallet_top_up(self, cr, uid, dict, context=None):
        quantity=False
        session_token=dict.get('sessionToken')
        if dict.has_key('quantity'):
            quantity=dict.get('quantity')
        print"enterrrrrrrrrrrr",quantity
        option_list=[]
        top_optns_obj=self.pool.get('topup.options')
        check=False
        if session_token:
            check=self.validate_token(cr,uid,session_token,context=None)

        if check==False:
            h=int('-0x0011', 16)
            return json.dumps({'result':-17})
        if check:
            if not quantity:
                cr.execute('select id from topup_options')
                top_up_options = filter(None, map(lambda x:x[0], cr.fetchall()))
                print "top_up_options-------------",top_up_options
                for each in top_up_options:
                    cdt=top_optns_obj.browse(cr,uid,each).credit
                    fb=top_optns_obj.browse(cr,uid,each).value
                    option_list.append({'credit':cdt,'value':fb})
                print "option_list=----------------",option_list
                return json.dumps({'body':{'result': 50,'options':option_list}})

            else:
                cr.execute('select partner_id from user_auth where session_token=%s', (session_token,))
                partner_id = filter(None, map(lambda x:x[0], cr.fetchall()))


                if partner_id==[]:
                    return json.dumps({'body':{'result':-49}})
                wallet_dict={}
                billing_info={}
                wallet_dict.update({'CustomerId':partner_id[0]})
                pat_obj=self.pool.get('res.partner').browse(cr,uid,partner_id[0])
                cust_pro_id=pat_obj.customer_profile_id
                print "custproofileid----------",cust_pro_id
                if not cust_pro_id:
                    return json.dumps({'body':{'result':-49}})
#                dict={'BillingInfo': {'PaymentProfileId': '29720861','BillingAddress': {'Street1': '581 Telegraph Canyon Rd', 'Street2': '', 'State': 'CA', 'Zip': '91910-6436', 'City': 'Chula Vista'}, 'CreditCard': {'CCNumber': '510510493671000', 'CCV': '123', 'ExpDate': '122020'}}, 'FillAmount': 10.0, 'ApiId': '123', 'PaymentType': 'CC', 'CustomerId': 6,'DBName': 'april_26th_final_test'}
                cr.execute('select profile_id from custmer_payment_profile where customer_profile_id=%s and active_payment_profile = True', (cust_pro_id,))
                cpp = filter(None, map(lambda x:x[0], cr.fetchall()))
                print "cpp------------------",cpp
                if cpp==[]:
                    return json.dumps({'body':{'result':-49}})
                billing_info.update({'PaymentProfileId':str(cpp[0])})
                wallet_dict.update({'PaymentType': 'CC'})
                partner_addr = self.pool.get('res.partner').address_get(cr, uid, [int(partner_id[0])],['default',])
                billing_add=partner_addr.get('default')
                if not billing_add:
                    return json.dumps({'body':{'result':-49}})
                if billing_add:
                    delivery_obj=self.pool.get('res.partner').browse(cr, uid, billing_add)
                    if delivery_obj.street and delivery_obj.city and delivery_obj.state_id and delivery_obj.zip:
                        billing_add={ "Street1": str(delivery_obj.street),"Street2": 'abc',"City": str(delivery_obj.city),"State": str(delivery_obj.state_id.code),"Zip": str(delivery_obj.zip),}
                        billing_info.update({'BillingAddress':billing_add})
                        billing_info.update({'CreditCard': {'CCNumber': '', 'CCV': '', 'ExpDate': ''}})
                wallet_dict.update({'BillingInfo':billing_info})
                wallet_dict.update({'FillAmount':quantity})
                print "wallet_dict------------",wallet_dict
                response=self.pool.get('res.partner').wallet_topup(cr,uid,wallet_dict,{})
                print "resp----------------------",response,type(response)
                
                if 'true' in response:
		    response=response.replace('true','True')
		if 'false' in response:
                    response=response.replace('false','False')
                    
                response=ast.literal_eval(str(response))
                
                if (response.get('body')).get('code')!=True:
                    return json.dumps({'body':{'result':-49}})
                else:
                    return json.dumps({'body':{'result':49}})





user_auth()


class device_history(osv.osv):
    '''Voucher related details'''
    _name = 'device.history'
    _columns={

        'partner_id':fields.many2one('res.partner',"User Name"),
        'device_id':fields.char('DeviceId'),
        'key':fields.char('Key'),
        'code':fields.char('Code'),
        'user_auth_id':fields.many2one('user.auth',"User Auth"),


    }
device_history()
