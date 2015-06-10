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
        osv_pool = pooler.get_pool('test_odoo8_1')
        # user = osv_pool.get('user.auth')

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
            # registry = openerp.modules.registry.Registry('playjam_test')
            # with registry.cursor() as cr:
            #     result=user.get_key_code(cr,1,str(a),wc,dev_id,{})
#            obj=self.env['user.auth']
            registry = RegistryManager.get('test_odoo8_1')
            with registry.cursor() as cr:
                u = registry['user.auth']
                result = u.get_key_code(dev_id, wc)
#            print"request.registry.get('user.auth')",obj
#            result=obj.get_key_code(request.cr,dev_id,wc)

            print 'result---------------',result
            #        user = osv_pool.get('res.users')
            #        ero
            return str(result)
        return str({"body":{'result':-1537}})