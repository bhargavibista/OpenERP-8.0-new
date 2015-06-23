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



class user_auth(osv.osv):
    '''Authenticating the user'''
    _name = 'user.auth'
    _description = 'User Authentication'
    def get_key_code(self,cr, uid,device_id,want_code, context=None):
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
        print "deviceid------------",device_id,type(device_id)
        dev_id=device_id
        if device_id and want_code==False:
            cr.execute('select id from user_auth where device_id = %s', (dev_id,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "auth_user_id",auth_user_id
            print "app_unlink====",auth_user_id
            if auth_user_id:
                brow_obj=self.browse(cr,uid,auth_user_id[0])
                print "enter-------"
                active=brow_obj.is_registered
                print "active-----------",active
                if active:
                    key=brow_obj.key
                    hash_obj=hashlib.sha256(key)
                    hash_key=hash_obj.hexdigest()

                    h=int('0x0001', 16)
                    values=json.dumps({'body':{'result':1,'key':hash_key}})
		    return values
                else:
                    h=int('-0x0001', 16)
                    values=json.dumps({'body':{'result': -1}})
                    return values
        if device_id and want_code==True:
	    cr.execute('select id from user_auth where device_id = %s', (dev_id,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            code=str(random)+device_id
            print "code------------",code,type(code)
            note="Enter the code on website to complete registration "
            key=str(key_random)+device_id
            hash_object = hashlib.md5(key)
            hashed_key=hash_object.hexdigest()
            hashed_key=hashed_key.replace('A', 'a').replace('F', 'f')
	    if auth_user_id:
                self.write(cr,uid,auth_user_id,{'code':code,'key':hashed_key,'device_id':device_id})
            else:
                self.create(cr,uid,{'code':code,'key':hashed_key,'device_id':device_id})
            #self.create(cr,uid,{'code':code,'key':hashed_key,'device_id':device_id})
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
            return json.dumps({'body':{'result':'-0x0601'}})
        if auth_user_id==[]:
            print "auth_user_id$$$$$$$$$$$$$$$$$",auth_user_id
            h=int('-0x0012', 16)
            return json.dumps({'body':{'result':'-0x0012'}})
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

                self.write(cr,uid,auth_user_id[0],{'challenge':str(challenge)})
                h=int('-0x0011', 16)
                return json.dumps({'body':{'result':'-0x0011','challenge':str(challenge)}})

        return result



    _columns={
        'partner_id': fields.many2one('res.partner',"User Name"),
        'device_id': fields.char('Device ID', size=32),
        'code': fields.char('Code', size=128),
        'key': fields.char('Key', size=128),
        'is_registered': fields.boolean('Registered'),
        'challenge':fields.char('Challenge', size=128),
        'session_token':fields.char('Session Token', size=128),
        'insecure_token':fields.char('Insecure Token', size=128),
        'duration':fields.char('Duration', size=128),
        'token_exp_time':fields.datetime('Token Exp Time'),
        'serial_no':fields.many2one('stock.production.lot','Serial Number'),
        'mac_address':fields.char('MAC Address',size=256),
        
        
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
        url = "http://54.75.245.17/api/rest/flare/account/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        


        data=json.dumps(dict)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text


    def profile_playjam(self,cr,uid,dict,context=None):
        url = "http://54.75.245.17/api/rest/flare/profile/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}


        data=json.dumps(dict)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text



    def link_account(self, cr, uid, dict, context=None):
        print "dict-----------",dict
        partner_id=dict.get('CustomerId')
	print"*******",partner_id,type(partner_id)
        code= dict.get('ActivationCode')
        print "code-----------------",code
        cr.execute('select id from user_auth where code= %s', (str(code),))
        auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if auth_user_id==[]:
            
            return {'body':{"code":False, "message":"No Such Device"}}

	cr.execute('select id from res_partner where id= %s', (int(partner_id),))
        pat_id = filter(None, map(lambda x:x[0], cr.fetchall()))
	print "patid-----------------",pat_id
	if pat_id==[]:
	    return {'body':{"code":False, "message":"Partner Not Present"}}

        if auth_user_id and partner_id:
            self.write(cr,uid,auth_user_id,{'partner_id':partner_id})
            auth_user_obj=self.pool.get('user.auth').browse(cr,uid,auth_user_id[0])
            pat_obj=self.pool.get('res.partner').browse(cr,uid,int(partner_id))
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
            account_pin=pat_obj.account_pin
 
            payload={'name':name,'uid':partner_id, 'surname':surname,'email':email,'dob':dob,'accountPin':account_pin,'mode':'C','code':code,'active':True}
#	    url= "http://54.75.245.17/api/rest/flare/account/view.json"
#	    headers = {'content-type': 'application/x-www-form-urlencoded'}
#            data=json.dumps(payload)
#            request=urllib.quote(data.encode('utf-8'))
#            response = requests.post(
#                        url, data="request="+request, headers=headers)

#            print "response---------------------",response.text
	    res=self.account_playjam(cr,uid,payload)
	    print"res-------------",res,type(res)
	    dict_res=ast.literal_eval(res)
	    if dict_res.has_key('body') and (dict_res.get('body')).has_key('result'):
	        if dict_res['body']['result']==4097:
                    pat_obj.write({'active':True,'playjam_exported':True})

                    cr.execute('select id from user_profile where playjam_exported = False partner_id= %s', (int(partner_id),))
                    profile_ids = filter(None, map(lambda x:x[0], cr.fetchall()))

                    pro_obj=self.pool.get('user.profile').browse(cr,uid,profile_ids[0])
                    gender = pro_obj.gender
                    dob = pro_obj.dob
                    pin=pro_obj.pin
                    playerTag = pro_obj.player_tag
                    ageRating = pro_obj.age_rating
                    avatar_id=pro_obj.avatar_id
                    pc_params=pro_obj.pc_params

                    payload2={'mode':'C', 'uid':partner_id, 'gender':gender, 'dob':dob,'Pin':pin,'playerTag':playerTag,'ageRating':ageRating,'avatarId':avatar_id ,'pcParams':pc_params}
                    res2=self.profile_playjam(cr,uid,payload2)
                    dict_res2=ast.literal_eval(res2)
                    if dict_res2.has_key('body') and (dict_res2.get('body')).has_key('result'):
                        if dict_res2['body']['result']==4097:
                            pro_obj.write({'playjam_exported':True})


                            return { "code":True, "message":"Success"}

        return {'body':{ "code":False, "message":"Partner Not Created At Playjam."}}



    '''def link_account(self, cr, uid, dict, context=None):
        print "dict-----------",dict
        partner_id=dict.get('CustomerId')
	print"*******",partner_id,type(partner_id)
        code= dict.get('ActivationCode')
        print "code-----------------",code
        cr.execute('select id from user_auth where code= %s', (str(code),))
        auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if auth_user_id==[]:
            
            return {'body':{ "code":False, "message":"Not A Valid Code."}}

	cr.execute('select id from res_partner where id= %s', (int(partner_id),))
        pat_id = filter(None, map(lambda x:x[0], cr.fetchall()))
	print "patid-----------------",pat_id
	if pat_id==[]:
	    return {'body':{ "code":False, "message":"Customer Not Present."}}

        if auth_user_id and partner_id:
            self.write(cr,uid,auth_user_id,{'partner_id':int(partner_id)})
	    auth_user_obj=self.pool.get('user.auth').browse(cr,uid,auth_user_id[0])
            pat_obj=self.pool.get('res.partner').browse(cr,uid,int(partner_id))
            accountPin= pat_obj.account_pin
            full_name=pat_obj.name
	    print "pat_obj.name----------",pat_obj.name
            x=full_name.find(' ')
            full_name=full_name.replace(' ','')
            first_name=full_name[:x]
            last_name=full_name[x:]
	    code=auth_user_obj.code
	    print "code-----------",code
            name = first_name
            surname = last_name
            gender = pat_obj.gender
            email = pat_obj.emailid
            dob = pat_obj.dob
            ageRating = pat_obj.age_rating
            playerTag = pat_obj.player_tag
           # payload={'name':name,'surname':surname,'gender':gender,'email':email,'dob':dob,'ageRating':ageRating,'playerTag':playerTag}
	    account_pin=pat_obj.account_pin
            payload={'name':name,'surname':surname,'gender':gender,'email':email,'dob':dob,'accountPin':account_pin,'mode':'C','code':code,'active':True}
	    url= "http://54.75.245.17/api/rest/flare/account/view.json"
	    headers = {'content-type': 'application/x-www-form-urlencoded'}
            data=json.dumps(payload)
            request=urllib.quote(data.encode('utf-8'))
            response = requests.post(
                        url, data="request="+request, headers=headers)

            print "response---------------------",response.text
	    res=response.text
	    print"res-------------",res,type(res)
	    dict_res=ast.literal_eval(res)
	    if dict_res.has_key('body') and (dict_res.get('body')).has_key('result'):
	        if dict_res['body']['result']==4097:
                    return {'body':{ "code":True, "message":"Success."}}

        return {'body':{ "code":False, "message":"Customer Not Created At Playjam End."}}'''

            

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

    def rental_playjam(self, cr, uid, user_id, appId, expiration, context=None):
        url = "http://54.75.245.17/api/rest/flare/rental/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        print "appid------------",appId
        print "expiration-------",expiration
        payload = {
            "uid":long(user_id),
            "appId":long(appId),
            "expiration":long(expiration)
            }


        data=json.dumps(payload)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text


    def wallet_playjam(self, cr, uid, user_id, quantity, context=None):
        url = "http://54.75.245.17/api/rest/flare/wallet/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}

        payload = {
                        "uid": user_id,
                        "quantity":float(quantity),
                    }


        data=json.dumps(payload)
        request=urllib.quote(data.encode('utf-8'))
        response = requests.post(
                    url, data="request="+request, headers=headers)

        return response.text




    def wallet_top_up(self, cr, uid, session_token, quantity, context=None):
        print"enterrrrrrrrrrrr",quantity
        option_list=[]
        top_optns_obj=self.pool.get('topup.options')
        if session_token:
            check=self.validate_token(cr,uid,session_token,context=None)

        if check==False:
            h=int('-0x0011', 16)
            return {'result':hex(h)}
        if check:
            if not quantity:
                cr.execute('select id from topup_options')
                top_up_options = filter(None, map(lambda x:x[0], cr.fetchall()))
                print "top_up_options-------------",top_up_options
                for each in top_up_options:
                    cdt=top_optns_obj.browse(cr,uid,each).credit
                    fb=top_optns_obj.browse(cr,uid,each).value
                    option_list.append({'credit':cdt,'value':fb})
                return option_list
                print "option_list=----------------",option_list
                return {}
            else:
                url = "http://54.172.158.69/api/rest/flare/wallet/view.json"
                headers = {'content-type': 'x-www-form-urlencoded'}
                payload = {
                    "uid": uid,
                    "quantity":float(quantity),

                }
                response = requests.post(
                    url, data=json.dumps(payload), headers=headers).json()

                print "response------------------",response

        return {}





user_auth()
