
from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
import urllib
import requests
import json
import ast
from passlib.hash import pbkdf2_sha256
import time
import datetime


class product_template(osv.osv):
    _inherit = 'product.template'
    _columns={

        'exported':fields.boolean('Exported'),
        

    }
    _defaults={
        'exported':False
    }
    
    def get_product_info(self, cr, uid, context=None):
        result=[]
        cr.execute('select id from product_template where exported = %s', (False,))
        product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        print "product_id-------",product_ids
        for each in product_ids:
            dict={}
            prod_obj=self.pool.get('product.template').browse(cr,uid,each)
            default_code= prod_obj.default_code
            if default_code:
                dict.update({'SKU':default_code})
            desc= prod_obj.name
            if desc:
                dict.update({'Description':desc})
            price= prod_obj.product_tmpl_id.list_price
            if price:
                dict.update({'Price':price})

            print "prod_obj.ext_prod_config",prod_obj.ext_prod_config
            if prod_obj.ext_prod_config:
                item_products=[]
                for each in prod_obj.ext_prod_config:
                    sub_dict={}
                    default_code= each.comp_product_id.default_code
                    if default_code:
                        sub_dict.update({'SKU':default_code})
                    desc= each.comp_product_id.name
                    if desc:
                        sub_dict.update({'Description':desc})
                    price= each.price
                    if price:
                        sub_dict.update({'Price':price})
                    item_products.append(sub_dict)
                dict.update({'ItemProducts':item_products})
            result.append(dict)
        return json.dumps(result)


    def update_product_info(self, cr, uid, context=None):
#        cr.execute('select id from product_product where exported = %s', (False,))
        cr.execute("update product_template set exported=True where id in (select id from product_template where exported = False)")
        return True
























