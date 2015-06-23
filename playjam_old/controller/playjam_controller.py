import ast
import base64
import csv
import glob
import itertools
import logging
import operator
import datetime
import hashlib
import os
import re
import simplejson
import time
import urllib
import urllib2
import urlparse
import xmlrpclib
#import zlib
#from xml.etree import ElementTree
#from cStringIO import StringIO

#import babel.messages.pofile
#import werkzeug.utils
#import werkzeug.wrappers
#try:
#    import xlwt
#except ImportError:
#    xlwt = None

import openerp
import openerp.modules.registry
from openerp.tools.translate import _
from openerp.tools import config
import openerp.addons.web.http as http
#import openerp.addons.web
#from openerp.addons.web.http import request
openerpweb = http

class playjam_controller(openerpweb.Controller):
    _cp_path = '/abc'

#    ero
    @openerpweb.httprequest
    def activationcall11(self,req,**kw):
        ero
        result={}
        t='true'
        f='false'
        print "aaaaaaaaaa------",self,kw,req
        want_code=False
        osv_pool = pooler.get_pool('cox_db_12jan')
        user = osv_pool.get('user.auth')
        request=kw.get('request')
        string_con=str(request)
        if t in string_con:
#            ero
            string_con=string_con.replace('true', "True")
            print "string--------------",x

        if f in string_con:
            string_con=string_con.replace(f, "False")

        print "str(request)------",string_con,type(string_con)
        dict_req = ast.literal_eval(x)
        print "request---------",dict_req,type(dict_req)
        a=dict_req.get('deviceId')
        wc=dict_req.get('wantCode')
        print "a-----",a
        print "wc-------",type(wc)
        if wc==u'true':
            want_code=True
        registry = openerp.modules.registry.Registry('cox_db_12jan')
        with registry.cursor() as cr:
            result=user.get_key_code(cr,1,str(a),want_code,{})

        print 'result---------------',result
#        user = osv_pool.get('res.users')
        print "user--------------------",user
#        ero
        return str(result)
