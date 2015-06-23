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
#from django.http import HttpRequest




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
        
    def link_account(self, dict):
        print "inside bista playjammmmmmmmmmmmmmmmmm"
        print "dict-----------", dict
        partner_id=dict.get('CustomerId')
        print"*******", partner_id, type(partner_id)
        code= dict.get('ActivationCode')
        print "code-----------------", code
        request.cr.execute('select id from user_auth where code= %s', (str(code),))
        auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
        if auth_user_id == []:
            return {'body':{"code":False, "message":"No Such Device"}}
        request.cr.execute('select id from res_partner where id= %s', (int(partner_id),))
        pat_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
        print "patid-----------------",pat_id
        if pat_id == []:
            return {'body':{"code":False, "message":"Partner Not Present"}}
        if auth_user_id and partner_id:
            self.write(auth_user_id,{'partner_id':partner_id})
            auth_user_obj=self.pool.get('user.auth').browse(auth_user_id[0])
            pat_obj=self.pool.get('res.partner').browse(int(partner_id))
            accountPin= pat_obj.account_pin
            full_name=pat_obj.name
	        # print "pat_obj.name----------", pat_obj.name
            x=full_name.find(' ')
            full_name=full_name.replace(' ','')
            first_name=full_name[:x]
            last_name=full_name[x:]
            code=auth_user_obj.code
            name = first_name
            surname = last_name
            email = pat_obj.emailid
            dob = pat_obj.dob
            account_pin=pat_obj.account_pin
            payload={'name':name,'uid':partner_id, 'surname':surname,'email':email,'dob':dob,'accountPin':account_pin,'mode':'C','code':code,'active':True}
            res=self.account_playjam(payload)
            print"res-------------", res, type(res)
            dict_res=ast.literal_eval(res)
            if 'body' in dict_res and ('result' in dict_res.get('body')):
                if dict_res['body']['result']==4097:
                    pat_obj.write({'active':True,'playjam_exported':True})
                    request.cr.execute('select id from user_profile where playjam_exported = False partner_id= %s', (int(partner_id),))
                    profile_ids = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                    pro_obj=self.pool.get('user.profile').browse(profile_ids[0])
                    gender = pro_obj.gender
                    dob = pro_obj.dob
                    pin=pro_obj.pin
                    playerTag = pro_obj.player_tag
                    ageRating = pro_obj.age_rating
                    avatar_id=pro_obj.avatar_id
                    pc_params=pro_obj.pc_params
                    payload2={'mode':'C', 'uid':partner_id, 'gender':gender, 'dob':dob,'Pin':pin,'playerTag':playerTag,'ageRating':ageRating,'avatarId':avatar_id ,'pcParams':pc_params}
                    res2=self.profile_playjam(payload2)
                    dict_res2 = ast.literal_eval(res2)
                    if dict_res2.has_key('body') and (dict_res2.get('body')).has_key('result'):
                        if dict_res2['body']['result']==4097:
                            pro_obj.write({'playjam_exported':True})
                            return { "code":True, "message":"Success"}
            return {'body':{ "code":False, "message":"Partner Not Created At Playjam."}}

    def user_login(self, dict, context=None):
        print ''' Challenge Response algoooooooooooooooooo.'''
        result,auth_user_id = '',[]
        count = 0
	print "dict---------------",dict
        device_id,auth_reply = False,False
        if 'deviceId' in dict:
            device_id=dict.get('deviceId')
        if 'authReply' in dict:
            auth_reply=dict.get('authReply')
        if device_id:
            request.cr.execute('select id from user_auth where device_id = %s and is_registered = True', (device_id,))
            auth_user_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            print "app_unlink====",auth_user_id
        else:
            h=int('-0x0601', 16)
            return json.dumps({'body':{'result':'-0x0601'}})
        if auth_user_id==[]:
            print "auth_user_id$$$$$$$$$$$$$$$$$",auth_user_id
            h=int('-0x0012', 16)
            return json.dumps({'body':{'result':'-0x0012'}})
        print "authreply--------------",auth_reply
        if 'authReply' in dict:
            if auth_user_id:
                key=self.browse(auth_user_id[0]).key
                challenge=self.browse(auth_user_id[0]).challenge
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
                        self.write(auth_user_id[0],{'session_token':session_token,'insecure_token':insecure_token,'duration':duration,'token_exp_time':exp_time})
                        h=int('0x0011', 16)
                        return json.dumps({'body':{'result': '0x0011', 'sessionToken':session_token,'insecureToken':insecure_token,'duration':duration}})
                    else:
                        h=int('-0x0012', 16)
                        return json.dumps({'body':{'result':'-0x0012'}})
        else:
            if auth_user_id:
                print "enter22222222"
                challenge=hashlib.sha1(os.urandom(128)).hexdigest()
                print "chal--------------",challenge,type(challenge)
                challenge=challenge.replace('A', 'a').replace('F', 'f')
                print'chalengr=================',challenge

                request.cr.write(auth_user_id[0],{'challenge':str(challenge)})
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
                print "voucher====",voucher
                if voucher_code:
                    voucher_obj=self.pool.get('voucher.details').browse(voucher[0])
                    con=voucher_obj.consumed
                    type=voucher_obj.type
                    print "con============",con
                    print "typeeeeeeeeeeee",type
                if con== True or voucher_code==[]:
                    h=int('-0x0021', 16)
                    return {'result':hex(h)}
                if con== False and type=='facevalue':
                    user_id=auth_obj.name.id
                    value=voucher_obj.credit
                    print "value----------",value
                    self.wallet_playjam(user_id,context)
                    return {}
                if con==False and type=='rental':
                    user_id=auth_obj.name.id
                    apps_browse_list=voucher_obj.rental_apps
                    print "apps_browse_listapps_browse_list",apps_browse_list
                    app_id=apps_browse_list[0].id
                    duration=0.0
                    duration=voucher_obj.expiration
                    app_id=123 #get the product id
                    self.rental_playjam(user_id,app_id,duration,context)
            return result
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
        
    def wallet_playjam(self, cr, uid, user_id, quantity, context=None):
        url = "http://54.75.245.17/api/rest/flare/wallet/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}

        payload = {
                        "uid": 'FLARE1093',
                        "quantity":float(quantity),
                    }

        data=json.dumps(payload)
        print "data.......................",data
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+requ, headers=headers)
        print"response.content",response.content
        return response.content
    
    def device_playjam(self, dict, context=None):
        url = "http://54.172.158.69/api/rest/flare/device/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}


        data=json.dumps(dict)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        print "response.text----------",response.content

        return response.content
    
    
    def rental_playjam(self, user_id, appId, expiration, context=None):
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

        return response.content
    
    
class device_history(models.Model):
    '''Voucher related details'''
    _name = 'device.history'
    
    partner_id = fields.Many2one(comodel='res.partner',string='User Name')
    device_id = fields.Char()
    key = fields.Char()
    code = fields.Char()
    user_auth_id = fields.Many2one(comodel='user.auth',string='User Auth')

    
    def write(self,ids,vals,context=None):
        cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        res=super(device_history,self).write(cr,uid,ids,vals,context)
        return res

    
    def create(self,vals,context=None):
        cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        res=super(device_history,self).create(cr,uid,vals,context)
        return res
device_history()
