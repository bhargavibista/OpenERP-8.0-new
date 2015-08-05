# -*- coding: utf-8 -*-
import json
from openerp import http
from openerp.http import request
import openerp.pooler as pooler
import ast
import urllib
from openerp.modules.registry import RegistryManager
import logging
_logger = logging.getLogger(__name__)
database = 'odoo_8_new'

class Magento(http.Controller):

    @http.route('/flare/magento/LinkAccount', type='http', auth="none")
    def LinkAccount(self, **kw):
        result={}
        t='true'
        f='false'
        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception, e:
                return str(json.dumps({"body":{'result':-1537}}))
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            if api_id!= '123':
                return str(json.dumps({"body":{"result":"Authentication Error!!"}}))
            registry = RegistryManager.get(db_name)
            with registry.cursor() as cr:
                u = registry['user.auth']
                result= u.link_account(dict_req)
            _logger.info('result for link_account----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/ValidateActivationCode', type='http', auth="none")
    def ValidateActivationCode(self,s_action=None,**kw):
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
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str(json.dumps({"body":{"result":-1537}}))
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            act_code=dict_req.get('ActivationCode')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.register_user(act_code)
            _logger.info('result for register_user----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/UserLogin', type='http', auth="none")
    def UserLogin(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        want_code=False
        osv_pool = pooler.get_pool('odoo_8')
        user = osv_pool.get('res.partner')
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            u_name=dict_req.get('UserName')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
            ###odoo8 changes
#            registry = openerp.modules.registry.Registry(db_name)
#            with registry.cursor() as cr:
#                result=user.login_magento(cr,1,u_name,pwd,{})
#            obj=request.registry['res.partner']
#            result=obj.login_magento(u_name,pwd,{})
            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.login_magento(u_name,pwd)
            _logger.info('result for login_magento----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/CreateUpdateCustomer', type='http', auth="none")
    def CreateUpdateCustomer(self,s_action=None,**kw):
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
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            u_name=dict_req.get('UserName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
            ##odoo8 changes
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.create_update_customer(cr,1,dict_req,{})
            obj=request.registry['res.partner']
            result=obj.create_update_customer(dict_req,{})
            _logger.info('result for create_update_customer----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/CreateUpdateProfile', type='http', auth="none")
    def CreateUpdateProfile(self,s_action=None,**kw):
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
	    if 'null' in string_con:
                string_con=string_con.replace('null', "")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            u_name=dict_req.get('UserName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
            ###odoo8 changes
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.create_update_profile(cr,1,dict_req,{})
#            obj=request.registry['res.partner']
#            result=obj.create_update_profile(request.cr,1,dict_req,{})
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.create_update_profile(dict_req)
            _logger.info('result for create_update_profile----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    
    @http.route('/flare/magento/UpdateBillingInfo', type='http', auth="none")
    def UpdateBillingInfo(self,s_action=None,**kw):
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
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str({"body":{'result':-1537}})
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            u_name=dict_req.get('UserName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
            ##odoo8 changes
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.update_billing_info(cr,1,dict_req,{})
#            obj=request.registry['res.partner']
#            result=obj.update_billing_info(request.cr,1,dict_req,{})
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.update_billing_info(dict_req)
            _logger.info('result for update_billing_info----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    
    @http.route('/flare/magento/CreateOrder', type='http', auth="none")
    def CreateOrder(self,s_action=None,**kw):
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
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                _logger.info('Exception----------------- %s', e)
                return str({"body":{'result':-1537}})
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            u_name=dict_req.get('UserName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
            ###odoo8 changes
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.create_order_magento(cr,1,dict_req,{})
#            obj=request.registry['res.partner']
#            result=obj.create_order_magento(request.cr,1,dict_req,{})
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.create_order_magento(dict_req)
            _logger.info('result for create_order_magento----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/UpdateSubscription', type='http', auth="none")
    def UpdateSubscription(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str({"body":{'result':-1537}})
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            u_name=dict_req.get('UserName')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
            ##odoo8 changes
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.update_subscription(cr,1,dict_req,{})
            ###
            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.update_subscription(dict_req)
            _logger.info('result for update_subscription----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/GetPaymentHistory', type='http', auth="none")
    def GetPaymentHistory(self,s_action=None,**kw):
        result={}
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.get_transactions_magento(cr,1,dict_req,{})
#            obj=request.registry['res.partner']
#            result=obj.get_transactions_magento(request.cr,1,dict_req,{})
            registry = RegistryManager.get(database)
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.get_transactions_magento(dict_req)
            _logger.info('result for get_transactions_magento----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/GetProductInfo', type='http', auth="none")
    def GetProductInfo(self,s_action=None,**kw):
        result={}
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str({"body":{'result':-1537}})
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('product.product')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.get_product_info(cr,1,{})
#            obj=request.registry['product.product']
#            result=obj.get_product_info(request.cr,1,{})
            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['product.product']
                result = u.get_product_info({})
            _logger.info('result for get_product_info----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/UpdateProductInfo', type='http', auth="none")
    def UpdateProductInfo(self,s_action=None,**kw):
        result={}
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('product.product')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.update_product_info(cr,1,{})

#            obj=request.registry['product.product']
#            result=obj.update_product_info({})

            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['product.product']
                result = u.update_product_info({})
            _logger.info('result for update_product_info----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/AddWalletBalance', type='http', auth="none")
    def AddWalletBalance(self,s_action=None,**kw):
        result={}
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#		print"user====",user
#                result=user.wallet_topup(cr ,1,dict_req,{})
            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.wallet_topup(dict_req)
            _logger.info('result for wallet_topup----------------- %s', result)
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/RedeemGiftCard', type='http', auth="none")
    def RedeemGiftCard(self,s_action=None,**kw):
        result={}
        if 'request' in kw:
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            registry = RegistryManager.get(db_name)
            if api_id !='123':
                return str({"body":{"result":"Authentication Error!!"}})
            with registry.cursor() as cr:
                res_partner = registry['res.partner']
                result = res_partner.redeem_gift_card(dict_req)
            _logger.info('result for redeem_gift_card----------------- %s', result)       
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/GetAccountInfo', type='http', auth="none")
    def GetAccountInfo(self,s_action=None,**kw):
        result={}
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str({"body":{'result':-1537}})
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.get_account_info(cr ,1,dict_req,{})
#            obj=request.registry['res.partner']
#            result=obj.get_account_info(request.cr ,1,dict_req,{})
            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.get_account_info(dict_req,{})
            _logger.info('result for get_account_info----------------- %s', result)    
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/GetOrderInfo', type='http', auth="none")
    def GetOrderInfo(self,s_action=None,**kw):
        result={}
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                return str({"body":{'result':-1537}})
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.get_order_info(cr ,1,dict_req,{})

#            obj=request.registry['res.partner']
#            result=obj.get_order_info(request.cr ,1,dict_req,{})
            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.get_order_info(dict_req,{})
            _logger.info('result for get_order_info----------------- %s', result)   
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/some_url', type='json', auth="user")
    def some_url(self, **req):
        obj=request.registry['user.auth']
        dict=obj.get_key_code(request.cr,1,deviceId,wantCode,{})
        return dict

