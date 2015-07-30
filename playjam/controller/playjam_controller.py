# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import openerp.pooler as pooler
import ast
import urllib
from openerp.modules.registry import RegistryManager
from openerp import SUPERUSER_ID
database = 'odoo_8_new'
import logging
_logger = logging.getLogger(__name__)

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
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if t in string_con:
                string_con=string_con.replace('true', "True")
            if f in string_con:
                string_con=string_con.replace(f, "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str({"body":{'result':-1537}})
            a=dict_req.get('serialNumber')
            wc=dict_req.get('wantCode')
            dev_id=dict_req.get('deviceId')
            if wc==u'True':
                want_code=True            
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.get_key_code(dev_id, wc)
            _logger.info('result for get key code------------ %s', result)
            return str(result)
        return str({"body":{'result':-1537}})

    @http.route('/flare/playjam/login', type='http', auth="public")
    def login(self,**kw):
        result={}
        t='true'
        f='false'
        want_code=False        
        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return (str({"body":{'result':-1537}}))
            device_id=dict_req.get('deviceId')
            auth_reply=dict_req.get('authReply')
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.user_login(dict_req)
            _logger.info('result for get user_login----- %s', result) 
            return (str(result))
        return str({"body":{'result':1537}})

    @http.route('/flare/playjam/topup', type='http', auth="public")
    def topup(self,**kw):
        result={}
        t='true'
        f='false'
        want_code=False
        user = osv_pool.get('user.auth')
        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return (str({"body":{'result':-1537}}))
            session_token=dict_req.get('deviceId')
            auth_reply=dict_req.get('authReply')
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.wallet_top_up(dict_req)            
            _logger.info('result for get wallet_top_up----- %s', result) 
            return (str(result))
        return str({"body":{'result':1537}})

class Playcast(http.Controller):
    
    @http.route('/flare/playjam/ValidateToken', type='http', auth="public")
    def ValidateToken(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        want_code=False
        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if t in string_con:
                string_con=string_con.replace('true', "True")
            if f in string_con:
                string_con=string_con.replace(f, "False")
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return str({"body":{'result':-1537}})
	    token=dict_req.get('Token')
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                user = registry['user.auth']
                result=user.validate_insecure_token(token,{})
            _logger.info('result for get validate_insecure_token----- %s', result) 
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
        osv_pool = pooler.get_pool('test_odoo8_1')
        if 'request' in kw:
            response={"body":{"code": 1, "message": "Call Succesful" }}
            return str(response)
        return str({"body":{'result':-1, "message": "Call Failed" }})
#        @openerpweb.httprequest


    @http.route('/flare/playjam/pushtransaction', type='http', auth="public")
    def pushtransaction(self,req,**kw):
        result={}
	t='true'
        f='false'
        want_code=False
        osv_pool = pooler.get_pool(database)
        user = osv_pool.get('res.partner')
        if kw.has_key('request'):
            request=kw.get('request')
            string_con=str(request)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if t in string_con:
                string_con=string_con.replace('true', "True")
            if f in string_con:
                string_con=string_con.replace(f, "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.push_transactions(dict_req)    
            _logger.info('result for  push_transactions----- %s', result) 
            return req.make_response(str(result), [('Content-Type', 'application/json; charset=UTF-8')])
        return str({"body":{'result':-1537}})
