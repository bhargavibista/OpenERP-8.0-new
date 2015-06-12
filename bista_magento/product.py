
from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
import urllib
from openerp.http import request
import json
import ast
from passlib.hash import pbkdf2_sha256
import time
import datetime
from openerp import models, fields, api, _
from openerp import SUPERUSER_ID

class product_template(models.Model):
    _inherit = 'product.template'
    
    exported = fields.Boolean(default=False)
    
product_template()

class product_product(models.Model):
    _inherit = 'product.product'
    
    exported = fields.Boolean(default=False)
    
    
    
    
    def get_product_info(self, context=None):
        result=[]
        request.cr.execute('select id from product_product where exported = %s', (False,))
        product_ids = filter(None, map(lambda x:x[0], request.cr.fetchall()))
        print "product_id-------",product_ids
         
        for each in product_ids:
	    dict={}
            dict.update({'ProductId':each})
            prod_obj=self.pool.get('product.product').browse(request.cr,SUPERUSER_ID,each)
            default_code= prod_obj.default_code
            #if default_code:
            dict.update({'SKU':default_code})
            desc= prod_obj.name
            #if desc:
            dict.update({'Description':desc})
            price= prod_obj.product_tmpl_id.list_price
            #if price:
            dict.update({'Price':price})

            print "prod_obj.ext_prod_config",prod_obj.ext_prod_config
            if prod_obj.ext_prod_config:
                item_products=[]
                for each in prod_obj.ext_prod_config:
                    sub_dict={}
                    default_code= each.comp_product_id.default_code
                    #if default_code:
		    sub_dict.update({'ProductId':each.comp_product_id.id})
                    sub_dict.update({'SKU':default_code})
                    desc= each.comp_product_id.name
                    #if desc:
                    sub_dict.update({'Description':desc})
                    price= each.price
                    #if price:
                    sub_dict.update({'Price':price})
                    item_products.append(sub_dict)
                dict.update({'ItemProducts':item_products})
            result.append(dict)
        return json.dumps({"body":{"code":True,'message':'Success.','ProductInfo':result}})


    def update_product_info(self, context=None):
#        cr.execute('select id from product_product where exported = %s', (False,))
        request.cr.execute("update product_product set exported=True where id in (select id from product_product where exported = False)")
        return json.dumps({"body":{'code':True,'message':'Success.'}})
























