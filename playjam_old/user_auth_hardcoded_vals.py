from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os

import hashlib
import md5
#hash_object = hashlib.md5(b'Hello World')
#print(hash_object.hexdigest())


class user_auth(osv.osv):
    '''Authenticating the user'''
    _name = 'user.auth'
    _description = 'User Authentication'
    def get_code(self,cr, uid,device_id,want_code, context=None):
        ''' Returns the code '''
        code ,values,auth_user_id,hashed_key,note= '',{},[],'',''
        print "wantcode------------",want_code
        print "deviceid-----------------",device_id
        if (want_code is None) or (device_id is None):
            h=int('-0x0601', 16)
            print "hhhhhhhhhh",h
            return {'result':hex(h)}



#        want_code=True
        random=randint(1,99999)
        key_random=randint(1,9999999999)
        print "random---------------",random
        print "deviceid------------",device_id,type(device_id)
        dev_id=device_id
        if device_id==456:
            cr.execute('select id from user_auth where device_id = %s', (dev_id,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "app_unlink====",auth_user_id
            if auth_user_id:
                print "enter-------"
                active=self.browse(cr,uid,auth_user_id[0]).is_registered
                print "active-----------",active
                if active:
                    key=self.browse(cr,uid,auth_user_id[0]).key
                    hash_obj=hashlib.sha256(key)
                    hash_key=hash_obj.hexdigest()

                    h=int('0x0001', 16)
#                    return {'result':hex(h),'key':hash_key}
                    return {'result':hex(h),'key':'foo'}

        if device_id and want_code==True:
#            cr.execute('select id from user_auth where device_id = %s', (dev_id,))
#
#            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
#            print "app_unlink====",auth_user_id
#        if auth_user_id and want_code:
            code=str(random)+device_id
            print "code------------",code,type(code)
#            self.write(cr,uid,auth_user_id,{'code':code})
            note="Enter the code on website to complete registration "

            key=str(key_random)+device_id
            hash_object = hashlib.sha256(key)
            hashed_key=hash_object.hexdigest()
#            self.create(cr,uid,{'code':code,'key':hashed_key,'device_id':device_id})
            self.create(cr,uid,{'code':'foo','key':'bar','device_id':device_id})
#            self.write(cr,uid,auth_user_id,{'key':hashed_key})
#        if auth_user_id==[]:
#            note='Please enter a valid DeviceId'
#        if want_code:
            h=int('-0x0001', 16)
#            values={'result':hex(h),'code':code,'key':hashed_key,'note':note}
            values={'result':hex(h),'code':'foo','key':'bar','note':note}
            return values
        if want_code==False:
            h=int('-0x0001', 16)
            values={'result':hex(h)}
            return values


        print "vals-------123",values

        h=int('-0x0601', 16)
        print "hhhhhhhhhh",h
        values= {'result':hex(h)}
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
        #print "result..........",result
        return result


    def user_login(self, cr, uid, device_id, auth_reply, context=None):
        ''' Challenge Response algo.  '''
        result,auth_user_id = '',[]
        count = 0
        if device_id:
            cr.execute('select id from user_auth where device_id = %s', (device_id,))
            auth_user_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            print "app_unlink====",auth_user_id
        else:
            h=int('-0x0601', 16)
            return {'result':hex(h)}
#        hardcoded value
        if device_id!='456':
            h=int('-0x0012', 16)
            return {'result':hex(h),'note':'Unknown Device'}

        if auth_user_id==[]:
            h=int('-0x0012', 16)
            return {'result':hex(h),'note':'Unknown Device'}
        print "authreply--------------",auth_reply
        if auth_reply:
            print "enter111111111"
            if auth_user_id:
                print "enter3333333"
                key=self.browse(cr,uid,auth_user_id[0]).key
                challenge=self.browse(cr,uid,auth_user_id[0]).challenge
                if key and challenge:
                    print "enter44444444"
                    m = md5.new()
                    m.update(key)
                    m.update(challenge)
                    encd_challenge=m.hexdigest()
                    print "encd_challenge------------",encd_challenge
                    if encd_challenge==auth_reply:
                        session_token=hashlib.sha1(os.urandom(256)).hexdigest()
                        insecure_token=hashlib.sha1(os.urandom(256)).hexdigest()
                        duration=randint(1,99999)

#                        self.write(cr,uid,auth_user_id[0],{'session_token':session_token,'insecure_token':insecure_token,'duration':duration})

#                        hardcoded
                        self.write(cr,uid,auth_user_id[0],{'session_token':'foo','insecure_token':'bar','duration':789})
                        h=int('0x0011', 16)

#                        return {'result': hex(h), 'sessionToken':session_token,'insecureToken':insecure_token,'duration':duration}

#                        hardcoded
                        return {'result': hex(h), 'sessionToken': 'foo','insecureToken': 'bar','duration':789}
                    else:
                        h=int('-0x0012', 16)
                        return {'result':hex(h),'sessionToken':'','insecureToken':'','duration':0,'note':'The reply is incorrect'}

        else:
            print "enter"
            if auth_user_id:
                print "enter22222222"
                challenge=randint(1,99999)
                print "chal--------------",challenge

#                self.write(cr,uid,auth_user_id[0],{'challenge':str(challenge)})
#                        hardcoded
                self.write(cr,uid,auth_user_id[0],{'challenge':'abc'})
                h=int('-0x0011', 16)
#                return {'result':hex(h),'challenge':str(challenge)}
#                        hardcoded
                return {'result':hex(h),'challenge':'abc'}

        #print "result..........",result
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


    }
    _defaults={
    }





user_auth()
