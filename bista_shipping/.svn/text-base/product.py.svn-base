# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
import stock

class product_template(osv.osv):
    _name = "product.template"
    _inherit = "product.template"

    _columns = {
        'weight': fields.float('Gross weight', digits_compute= dp.get_precision('Stock Weight'), help="The gross weight in Kg."),
        'weight_net': fields.float('Net weight', digits_compute= dp.get_precision('Stock Weight'), help="The net weight in Kg."),
    }
product_template()

class product_category_shipping(osv.osv):
    _name = "product.category.shipping"
    _description = "Product Category Shipping"
    _rec_name = "weight"
    _order = "sequence desc"
    _columns = {
        'product_categ_id':fields.many2one('product.category',String='Product Shipping Category'),
        'sequence': fields.integer('Sequence', required=True, help="Gives the order in which the shipping rules will be checked. The evaluation gives highest priority to lowest sequence and stops as soon as a matching item is found."),
        'weight' : fields.float('Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds"),
#        'shipping_type' : fields.selection(stock._get_shipping_type,'Shipping Type'),
        'shipping_type' : fields.selection([('USPS','USPS')],'Shipping Type'),
        'service_type_usps' : fields.selection(stock._get_service_type_usps, 'Service Type', size=100),
        'first_class_mail_type_usps' : fields.selection(stock._get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
        'container_usps' : fields.selection(stock._get_container_usps,'Container', size=100),
        'size_usps' : fields.selection(stock._get_size_usps,'Size'),
    }
    _defaults = {
        'sequence': lambda *a: 5,
    }

product_category_shipping()

class product_category(osv.osv):
    _inherit = "product.category"
    _columns = {
        'product_categ_shipping_ids':fields.one2many('product.category.shipping','product_categ_id','Product Category'),
    }
product_category()

class product_product_shipping(osv.osv):
    _name = "product.product.shipping"
    _description = "Template"
    _rec_name = "weight"
    _columns = {
        'product_id':fields.many2one('product.product',String='Product'),
        'sequence': fields.integer('Sequence', required=True, help="Gives the order in which the shipping rules will be checked. The evaluation gives highest priority to lowest sequence and stops as soon as a matching item is found."),
        'weight' : fields.float('Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds"),
        'shipping_type' : fields.selection([('USPS','USPS')],'Shipping Type'),
        'service_type_usps' : fields.selection(stock._get_service_type_usps, 'Service Type', size=100),
        'first_class_mail_type_usps' : fields.selection(stock._get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
        'container_usps' : fields.selection(stock._get_container_usps,'Container', size=100),
        'size_usps' : fields.selection(stock._get_size_usps,'Size'),
    }
    _defaults = {
        'sequence': lambda *a: 5,
    }
product_product_shipping()

class product_product(osv.osv):
    _inherit = "product.product"

    def onchange_default_shipping(self,cr,uid,ids,default_shipping,context=None):
        result = {}
        if ids:
            if default_shipping==True:
                categ_id=self.browse(cr,uid,ids[0]).categ_id
                ship_one2many=categ_id.product_categ_shipping_ids
                for each_line in ship_one2many:
                    result = {
                        'sequence':each_line.sequence,
                        'weight':each_line.weight,
                        'shipping_type':each_line.shipping_type,
                        'service_type_usps':each_line.service_type_usps,
                        'first_class_mail_type_usps':each_line.first_class_mail_type_usps,
                        'container_usps':each_line.container_usps,
                        'size_usps':each_line.size_usps,
                        'product_id':ids[0]
                    }
                    self.pool.get('product.product.shipping').create(cr,uid,result)

            else:
                ### Delete Shippng methon if deleted from category
                product_shipping_ids = self.browse(cr,uid,ids[0]).product_shipping_ids
                for product_shipping_id in product_shipping_ids:
                    self.pool.get('product.product.shipping').unlink(cr,uid,product_shipping_id.id,context)
        return True

    _columns = {
        'product_shipping_ids':fields.one2many('product.product.shipping','product_id','Product'),
        'default_shipping':fields.boolean('Use default shipping'),
    }
product_product()
