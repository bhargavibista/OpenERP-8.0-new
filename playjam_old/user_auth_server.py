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


class user_auth(osv.osv):
    '''Authenticating the user'''
    _name = 'user.auth'
    _description = 'User Authentication'
    _rec_name = "device_id"
    def get_key_code(self,cr, uid,device_id,want_code, context=None):
        ''' Returns the code '''
        code ,values,auth_user_id,hashed_key,note= '',{},[],'',''
        print "wantcode------------",want_code
        print "deviceid-----------------",device_id
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
                    values=json.dumps({'body':{'result':'0x0001','key':hash_key}})
		    return values
                else:
                    h=int('-0x0001', 16)
                    values=json.dumps({'body':{'result': '-0x0001'}})
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
            h=int('-0x0001', 16)
            values=json.dumps({'body':{'result':'-0x0001','code':str(code),'key':hashed_key}})
            return values
        
	values= json.dumps({'body':{'result':'-0x0601'}})
        return values

    def register_user(self, cr, uid, values, context=None):
        ''' verifies user and associates the partner'''
        print "code----",values
        
        code=values.get('code')
        print "code----1-22-",code
        all_values = dict(values)
        del values['code']
        print"values--------------",values
        if code:
            cr.execute('select id from user_auth where code = %s', (code,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "app_unlink====",auth_user_id
            if auth_user_id:
                patner_id=self.pool.get('res.partner').create(cr,uid,values)
                print "partnerid---------------",patner_id
                self.write(cr,uid,auth_user_id,{'is_registered':True,'name':patner_id})

                url = "http://54.75.245.17/api/rest/flare/account/view.json"
                headers = {'content-type': 'x-www-form-urlencoded'}

                payload = {
                        "uid":123,
                        "accountPin":456,
                        "name ":'abc',
                        "surname ":'pqr',
                        "gender":'M',
                        "email":'abc@test.com',
                        "dob":'1990/03/30',
                        "ageRating":15,
                        "playerTag":'tag1',
                        "code":code,
                        "active":True,

                        }

                request=urllib.quote(str(payload).encode('utf-8'))
                print "request-----------------",request

                response = requests.post(
                    url, data="request="+request, headers=headers)

                print "response------------------",response.text

            else:
                return "Incorrect Code"
        
        return True

    def check_registration(self, cr, uid, device_id, context=None):
        ''' Informs wether the user is registered or not.  '''
        result = ''
        count = 0
        if device_id:
            cr.execute('select id from user_auth where device_id = %s', (device_id,))

            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "app_unlink====",auth_user_id
            if auth_user_id:
                check=self.browse(cr,uid,auth_user_id[0]).is_registered
                if check==True:
                    result='The User is now Registered.'
                    return result
                else:
                    result='The User is Not Registered yet.Please enter the code on website.'
                    return result
            else:
                result="The device was not recognized."
        return result


    def user_login(self, cr, uid, device_id, auth_reply, context=None):
        ''' Challenge Response algo.  '''
        result,auth_user_id = '',[]
        count = 0
        if device_id:
            cr.execute('select id from user_auth where device_id = %s and is_registered = True', (device_id,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "app_unlink====",auth_user_id
        else:
            h=int('-0x0601', 16)
            return {'body':{'result':'-0x0601'}}
        if auth_user_id==[]:
            print "auth_user_id$$$$$$$$$$$$$$$$$",auth_user_id
            h=int('-0x0012', 16)
            return {'body':{'result':'-0x0012'}}
        print "authreply--------------",auth_reply
        if auth_reply:
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
                        return {'body':{'result': '0x0011', 'sessionToken':session_token,'insecureToken':insecure_token,'duration':duration}}
                    else:
                        h=int('-0x0012', 16)
                        return {'body':{'result':'-0x0012'}}

        else:
            if auth_user_id:
                print "enter22222222"
                challenge=hashlib.sha1(os.urandom(128)).hexdigest()
                print "chal--------------",challenge,type(challenge)
                challenge=challenge.replace('A', 'a').replace('F', 'f')
                print'chalengr=================',challenge

                self.write(cr,uid,auth_user_id[0],{'challenge':str(challenge)})
                h=int('-0x0011', 16)
                return {'body':{'result':'-0x0011','challenge':str(challenge)}}

        return result


    _columns={
        'name': fields.many2one('res.partner',"User Name"),
        'device_id': fields.char('Device ID', size=32),
        'code': fields.char('Code', size=128),
        'key': fields.char('Key', size=128),
        'is_registered': fields.boolean('Registered'),
        'challenge':fields.char('Challenge', size=128),
        'session_token':fields.char('Session Token', size=128),
        'insecure_token':fields.char('Insecure Token', size=128),
        'duration':fields.char('Duration', size=128),
        'token_exp_time':fields.datetime('Token Exp Time'),
        
        
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
                    value=voucher_obj.credit
                    print "value----------",value
                    url = "http://54.172.158.69/api/rest/flare/wallet/view.json"
		    headers = {'content-type': 'application/x-www-form-urlencoded','content-length' : 68}
		    payload = '{"uid": "FLARE1124", "quantity":0}'
                    request=urllib.quote(payload.encode('utf-8'))
                    print "request-----------------",request

                    response = requests.post(
                        url, data="request="+request, headers=headers)

                    print "response------------------",response.text

                    return {}
                if con==False and type=='rental':

                    apps_browse_list=voucher_obj.rental_apps
                    print "apps_browse_listapps_browse_list",apps_browse_list
                    app_id=apps_browse_list[0].id
                    duration=0.0
                    duration=voucher_obj.expiration
                    url = "http://54.172.158.69/api/rest/flare/rental/view.json"
#                    url = "http://54.75.245.17/api/rest/flare/rental/view.json"
                    headers = {'content-type': 'application/x-www-form-urlencoded'}

                    print "appid------------",app_id
                    print "expiration-------",duration

                    req='{"uid":123,"appId":456,"expiration":1415976070000}'


                    request=urllib.quote(req.encode('utf-8'))
                    print "request-----------------",request
                    response = requests.post(
                        url, data="request="+request, headers=headers)

                    print "response------------------",response.text

                    return {}
        #print "result..........",result
        return result



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
#                erooo
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
