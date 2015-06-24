# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import openerp.pooler as pooler
import ast
import urllib
from openerp.modules.registry import RegistryManager
from openerp import SUPERUSER_ID


class Playjam(http.Controller):

    @http.route('/flare/playjam/activate', type='http', auth="public")
    def activate(self,s_action=None,**kw):
        result={}
        t='true'
        f='false'
        want_code=False

        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                #string_con=urllib.unquote(string_con).decode('utf8')
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if t in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if f in string_con:
                string_con=string_con.replace(f, "False")

            print "str(request)------",string_con,type(string_con),requ

            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str({"body":{'result':-1537}})

            print "request---------",dict_req,type(dict_req)
            #a=dict_req.get('deviceId')
            a=dict_req.get('serialNumber')

            wc=dict_req.get('wantCode')
            dev_id=dict_req.get('deviceId')
            print "a-----",wc,dev_id
            print "wc-------",type(wc)
            if wc==u'True':
                want_code=True            
            registry = RegistryManager.get('test_odoo8_1')
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.get_key_code(dev_id, wc)

            print 'result---------------',result            
            return str(result)
        return str({"body":{'result':-1537}})

    @http.route('/flare/playjam/login', type='http', auth="public")
    def login(self,**kw):
        result={}
        t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
        want_code=False        

        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)

            if '%' in string_con:
                #string_con=urllib.unquote(string_con).decode('utf8')
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')

            print "str(request)------",string_con,type(string_con)

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return (str({"body":{'result':-1537}}))

            print "request---------",dict_req,type(dict_req)
            device_id=dict_req.get('deviceId')
            auth_reply=dict_req.get('authReply')
#            if auth_reply==None:
#                auth_reply=""
            print "a-----",device_id
            print "wc-------",type(auth_reply),auth_reply
            registry = RegistryManager.get('test_odoo8_1')
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.user_login(dict_req)
                            
            print 'result---------------',result            
            return (str(result))
        return str({"body":{'result':1537}})

    @http.route('/flare/playjam/topup', type='http', auth="public")
    def topup(self,**kw):
        result={}
        t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw,req
        want_code=False
        osv_pool = pooler.get_pool('playjam_test')
        user = osv_pool.get('user.auth')

        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)

            if '%' in string_con:
                #string_con=urllib.unquote(string_con).decode('utf8')
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')

            print "str(request)------",string_con,type(string_con)
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return (str({"body":{'result':-1537}}))


            print "request---------",dict_req,type(dict_req)
            session_token=dict_req.get('deviceId')
            auth_reply=dict_req.get('authReply')
            registry = RegistryManager.get('test_odoo8_1')
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.wallet_top_up(dict_req)            
            print 'result---------------',result            
            return (str(result))
        return str({"body":{'result':1537}})
    
    

class Playcast(http.Controller):
    
    @http.route('/flare/playjam/ValidateToken', type='http', auth="public")
    def ValidateToken(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
        want_code=False
        osv_pool = pooler.get_pool('test_odoo8_1')
#        user = osv_pool.get('user.auth')

        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)
            if '%' in string_con:
                #string_con=urllib.unquote(string_con).decode('utf8')
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if t in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if f in string_con:
                string_con=string_con.replace(f, "False")

            print "str(request)------",string_con,type(string_con),request
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return str({"body":{'result':-1537}})
            print "request---------",dict_req,type(dict_req)
	    token=dict_req.get('Token')
            
            registry = RegistryManager.get('test_odoo8_1')
            with registry.cursor() as cr:
                user = registry['user.auth']
                result=user.validate_insecure_token(token,{})

            print 'result---------------',result
            response={}
            if result:
                response={"body":{"code": 1, "message": "Success" }}
            else:
                response={"body":{"code": -1, "message": "Expired Token" }}

            return str(response)
        return str({"body":{'result':-1}})
    
    
    @http.route('/flare/playjam/QualityOfService', type='http', auth="public")
    def QualityOfService(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
        osv_pool = pooler.get_pool('test_odoo8_1')

        if 'request' in kw:
            
            response={"body":{"code": 1, "message": "Call Succesful" }}

            return str(response)
        return str({"body":{'result':-1, "message": "Call Failed" }})
