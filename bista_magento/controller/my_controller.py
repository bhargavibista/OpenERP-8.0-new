# -*- coding: utf-8 -*-
import json
from openerp import http
from openerp.http import request
import openerp.pooler as pooler
import ast
import urllib
from openerp.modules.registry import RegistryManager
database = 'odoo8_stable_2july'

class Magento(http.Controller):

#
#    def session_info(self):
#        request.session.ensure_valid()
#        return {
#            "session_id": request.session_id,
#            "uid": request.session.uid,
#            "user_context": request.session.get_context() if request.session.uid else {},
#            "db": request.session.db,
#            "username": request.session.login,
#            "company_id": request.env.user.company_id.id if request.session.uid else None,
#        }
#
#    @http.route('/web/session/get_session_info1', type='json', auth="none")
#    def get_session_info(self):
#
#        request.uid = request.session.uid
#        request.disable_db = False
#        return self.session_info()

    @http.route('/flare/magento/LinkAccount', type='http', auth="none")
    def LinkAccount(self, **kw):
        result={}
        t='true'
        f='false'
        print "aaaaaaaaaa------",kw
#        want_code=False
        if 'request' in kw:
            request=kw.get('request')
            string_con=str(request)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con
            if "false" in string_con:
                string_con=string_con.replace('false', "False")
            print "str(request)------",string_con,type(string_con),request
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception, e:
                return str(json.dumps({"body":{'result':-1537}}))
            print "request---------",dict_req,type(dict_req)
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            if api_id!= '123':
                return str(json.dumps({"body":{"result":"Authentication Error!!"}}))
            registry = RegistryManager.get(db_name)
            with registry.cursor() as cr:
                u = registry['user.auth']
                result= u.link_account(dict_req)
            print 'result---------------',result
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/ValidateActivationCode', type='http', auth="none")
    def ValidateActivationCode(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
        want_code=False
#        osv_pool = pooler.get_pool('odoo_8')
#        user = osv_pool.get('user.auth')

        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                #string_con=urllib.unquote(string_con).decode('utf8')
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")

            print "str(request)------",string_con,type(string_con),requ
            try:
                dict_req = ast.literal_eval(str(string_con))
            except Exception ,e:
                
                return str(json.dumps({"body":{"result":-1537}}))
            
            print "request---------",dict_req,type(dict_req)
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            act_code=dict_req.get('ActivationCode')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            print "a-----",a
#            print "wc-------",type(wc)
#            if wc==u'True':
#                want_code=True
#            registry = openerp.modules.registry.Registry(db_name)
#            with registry.cursor() as cr:
#                result=user.register_user()

#            obj=request.registry.get('user.auth')
#            result=obj.register_user(request.cr,1,act_code,{})
            registry = RegistryManager.get('odoo8_stable_2july')
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.register_user(act_code)
            print 'result---------------',result
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/UserLogin', type='http', auth="none")
    def UserLogin(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
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
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])

            print "request---------",dict_req,type(dict_req)
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
           
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/CreateUpdateCustomer', type='http', auth="none")
    def CreateUpdateCustomer(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
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
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])

            
            print "request---------",dict_req,type(dict_req)
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
            print 'result---------------',result
    #        user = osv_pool.get('res.users')
            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/CreateUpdateProfile', type='http', auth="none")
    def CreateUpdateProfile(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
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
                print "string--------------",string_con

            if f in string_con:
                string_con=string_con.replace(f, "False")

	    if 'null' in string_con:
                string_con=string_con.replace('null', "")


            print "str(request)------",string_con,type(string_con),requ

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])

            print "request---------",dict_req,type(dict_req)
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

            registry = RegistryManager.get('odoo8_stable_2july')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.create_update_profile(dict_req)
            print 'result---------------',result
    #        user = osv_pool.get('res.users')
            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    
    @http.route('/flare/magento/UpdateBillingInfo', type='http', auth="none")
    def UpdateBillingInfo(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
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
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ
            
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return str({"body":{'result':-1537}})
            
            print "request---------",dict_req,type(dict_req)
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

            registry = RegistryManager.get('odoo8_stable_2july')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.update_billing_info(dict_req)
            print 'result---------------',result
    #        user = osv_pool.get('res.users')
            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    
    @http.route('/flare/magento/CreateOrder', type='http', auth="none")
    def CreateOrder(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
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
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ

            try:
                dict_req = ast.literal_eval(str(string_con))
                print"dict_req",dict_req
            except Exception ,e:
                print"e",e
                return str({"body":{'result':-1537}})
            
            print "request---------",dict_req,type(dict_req)
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

            registry = RegistryManager.get('odoo_8')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.create_order_magento(dict_req)
            print 'result---------------',result
    #        user = osv_pool.get('res.users')
            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/UpdateSubscription', type='http', auth="none")
    def UpdateSubscription(self,s_action=None,**kw):
        result={}
	t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw
#        want_code=False


        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')

            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return str({"body":{'result':-1537}})
            
            print "request---------",dict_req,type(dict_req)
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
            u_name=dict_req.get('UserName')
#            osv_pool = pooler.get_pool(str(db_name))
#            user = osv_pool.get('res.partner')
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
            print 'resulttttt---------------',result
    #        user = osv_pool.get('res.users')
#            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/GetPaymentHistory', type='http', auth="none")
    def GetPaymentHistory(self,s_action=None,**kw):
        result={}
        print "aaaaaaaaaa------",self,kw
#        want_code=False


        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')

            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            
            print "request---------",dict_req,type(dict_req)
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            pwd=dict_req.get('Password')
#            u_name=dict_req.get('UserName')
            osv_pool = pooler.get_pool(str(db_name))
            user = osv_pool.get('res.partner')
            if not api_id=='123':
                return str({"body":{"result":"Authentication Error!!"}})
#            registry = openerp.modules.registry.Registry(str(db_name))
#            with registry.cursor() as cr:
#                result=user.get_transactions_magento(cr,1,dict_req,{})
#            obj=request.registry['res.partner']
#            result=obj.get_transactions_magento(request.cr,1,dict_req,{})

            registry = RegistryManager.get('odoo8_stable_2july')
            with registry.cursor() as cr:
                u = registry['res.partner']
                result = u.get_transactions_magento(dict_req)
            print 'result---------------',result
    #        user = osv_pool.get('res.users')
            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/GetProductInfo', type='http', auth="none")
    def GetProductInfo(self,s_action=None,**kw):
        result={}
        print "aaaaaaaaaa------",self,kw
#        want_code=False


        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')

            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return str({"body":{'result':-1537}})
            
            print "request---------",dict_req,type(dict_req)
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
#            pwd=dict_req.get('Password')
#            u_name=dict_req.get('UserName')
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
            print 'result---------------',result
    #        user = osv_pool.get('res.users')
            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/UpdateProductInfo', type='http', auth="none")
    def UpdateProductInfo(self,s_action=None,**kw):
        result={}
        print "aaaaaaaaaa------",self,kw
#        want_code=False


        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')


            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")


            print "str(request)------",string_con,type(string_con),requ

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])

            
            print "request---------",dict_req,type(dict_req)
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
#            pwd=dict_req.get('Password')
#            u_name=dict_req.get('UserName')
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
            print 'result---------------',result
    #        user = osv_pool.get('res.users')
            print "user--------------------",user
    #        ero
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})

    @http.route('/flare/magento/AddWalletBalance', type='http', auth="none")
    def AddWalletBalance(self,s_action=None,**kw):
        result={}
        print "aaaaaaaaaa------",self,kw
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            print "str(request)------",string_con,type(string_con),requ

            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            
            print "request---------",dict_req,type(dict_req)
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
            print 'result---------------',result
#            obj=request.registry['res.partner']
#            result=obj.wallet_topup(request.cr ,1,dict_req,{})
#            print 'result---------------',result
            print "user--------------------",user
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/RedeemGiftCard', type='http', auth="none")
    def RedeemGiftCard(self,s_action=None,**kw):
        result={}
        print "aaaaaaaaaa------",self,kw
        if 'request' in kw:
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')

            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")
                
            print "str(request)------",string_con,type(string_con),requ
            
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return req.make_response(str({"body":{'result':-1537}}), [('Content-Type', 'application/json; charset=UTF-8')])
            
            print "request---------",dict_req,type(dict_req)
            api_id=dict_req.get('ApiId')
            db_name=dict_req.get('DBName')
            registry = RegistryManager.get(db_name)
            if api_id !='123':
                return str({"body":{"result":"Authentication Error!!"}})
            with registry.cursor() as cr:
                res_partner = registry['res.partner']
                result = res_partner.redeem_gift_card(dict_req)

            print 'result---------------',result            
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/GetAccountInfo', type='http', auth="none")
    def GetAccountInfo(self,s_action=None,**kw):
        result={}
        print "aaaaaaaaaa------",self,kw
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')

            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")

            print "str(request)------",string_con,type(string_con),requ
            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return str({"body":{'result':-1537}})
            
            print "request---------",dict_req,type(dict_req)
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
            print 'result---------------',result
            print "user--------------------",user
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/flare/magento/GetOrderInfo', type='http', auth="none")
    def GetOrderInfo(self,s_action=None,**kw):
        result={}
        print "aaaaaaaaaa------",self,kw
        if kw.has_key('request'):
            requ=kw.get('request')
            string_con=str(requ)
            if '%' in string_con:
                if '+' in string_con:
                    string_con=string_con.replace('+','')
                    string_con=urllib.unquote(string_con).decode('utf8')
            print "str(request)------",string_con,type(string_con),requ

            if "true" in string_con:
                string_con=string_con.replace('true', "True")
                print "string--------------",string_con

            if "false" in string_con:
                string_con=string_con.replace('false', "False")

            try:
                dict_req = ast.literal_eval(str(string_con))

            except Exception ,e:
                return str({"body":{'result':-1537}})
            
            print "request---------",dict_req,type(dict_req)
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
            print 'result---------------',result
            print "user--------------------",user
            return str(result)
        return str({"body":{"result":"SERVER ERROR INVALID SYNTAX"}})
    
    @http.route('/some_url', type='json', auth="user")
    def some_url(self, **req):
#        osv_pool = pooler.get_pool('odoo_demo')
#        user = osv_pool.get('res.users')
#        ero
        print "fields-------------",req
#        deviceId=req.get('deviceId')
#        wantCode =req.get('wantCode')

        obj=request.registry['user.auth']
        print "user----------",obj
        dict=obj.get_key_code(request.cr,1,deviceId,wantCode,{})
        
#        rec=http.request.env['user']
        print "rec---------",dict
#        params = dict(map(operator.itemgetter('name', 'value'), fields))
#        print "params--------------",params
##        print "users+++++++++++++++",cert_type
#        user = osv_pool.get('res.users')
#        print "users------------",user
##        return "<h1>This is a test</h1>"
        return dict



#    @http.route('/registration', type='json', auth="public")
#    def registration(self, **req):
##        osv_pool = pooler.get_pool('odoo_demo')
##        user = osv_pool.get('res.users')
#        print "fields-------------",req
#        obj=request.registry['user.auth']
#        print "user----------",obj
#        dict=obj.register_user(request.cr,1,req,{})
#        print "rec---------",dict
#        return dict
#
#
#    @http.route('/userlogin', type='json', auth="public")
#    def login(self, **req):
##        osv_pool = pooler.get_pool('odoo_demo')
##        user = osv_pool.get('res.users')
#        print "fields-------------",req
##        ero
#        deviceId=req.get('deviceId')
#        auth_reply =req.get('authReply')
#        obj=request.registry['user.auth']
#        print "user----------",obj
#        dict=obj.user_login(request.cr,1,deviceId,auth_reply,{})
#        print "rec---------",dict
#        return dict
#
#
#    @http.route('/voucher', type='json', auth="public")
#    def voucher(self, **req):
##        ero
##        osv_pool = pooler.get_pool('odoo_demo')
##        user = osv_pool.get('res.users')
#        print "fields-------------",req
#        session_token=req.get('sessionToken')
#        voucher_code =req.get('voucherCode')
#        obj=request.registry['user.auth']
#        print "user----------",obj
#        dict=obj.voucher_validation(request.cr,1,session_token,voucher_code,{})
#        print "rec---------",dict
#        return dict
#
#
#    @http.route('/magento_operations', type='json', auth="public")
#    def magento_operations(self, **req):
#        request_type=""
##        ero
#        print "fields-------------",req
#        if req.get('Request',False) and (req.get('Request',False).has_key('RequestType')):
##            request_type=req.get('RequestType')
#            request_type=req['Request']['RequestType']
#        else:
#            return {"Status": {"complete": "False", "error": "Please mention the RequestType"}}
#        print "request_type----------",request_type
#        if request_type=='CreateAndUpdateAccountLogin':
#            print "inside CreateAndUpdateAccountLogin------------"
#            if req.get('Account',False) and (req.get('Account',False).has_key('UserName')) and (req.get('Account',False).has_key('Password')):
#                user_name=req['Account']['UserName']
#                password=req['Account']['Password']
#                obj=request.registry['res.partner']
#
#        if request_type=='OnlinePurchase':
#            print "inside CreateAndUpdateAccountLogin------------"
#            if req:
#                obj=request.registry['sale.order']
#                dict=obj.online_order_process(request.cr,1,req,{})
#                
            



#        voucher_code =req.get('voucherCode')


#        obj=request.registry['res.partner']
#        print "user----------",obj
#        dict=obj.voucher_validation(request.cr,1,session_token,voucher_code,{})
#        print "rec---------",dict
#        return dict
