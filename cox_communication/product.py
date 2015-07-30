# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
class service_charges(osv.osv):
    _name="service.charges"
    _rec_name = 'service_charge_amt'
    def onchange_date_range(self,cr,uid,ids,start_month,end_month,product_id,context):
        res,warning_mesg = {},''
        if end_month:
            if end_month < start_month:
                warning_mesg += _("") + 'Month Range is not Proper' +"\n\n"
                value = {'end_range_month': 0}
                res['value'] = value
        product_id = context.get('product_id')
        search_id = self.search(cr, uid, [('start_range_month','=',start_month),'|',('end_range_month','=',end_month),('product_id','=',product_id)])
        if search_id:
            warning_mesg += _("") + 'Month Range is not Proper' +"\n\n"
            value = {'end_range_month': 0,'start_range_month':0}
        if warning_mesg:
             warning = {'title': _('Warning!'),
                'message' : warning_mesg}
             res['warning'] = warning
        return res
    _columns={
    'start_range_month':fields.integer('Start Month'),
    'end_range_month':fields.integer('End Month'),
    'service_charge_amt':fields.float('Amount to be Charged'),
    'product_id' : fields.many2one('product.product','Product ID'),
    }
service_charges()

class termination_fee_charges(osv.osv):
    _name="termination.fee.charges"
    _rec_name = 'termination_fees'
    def onchange_date_range(self,cr,uid,ids,start_days,end_days,product_id,context):
        res,warning_mesg = {},''
        if end_days:
            if end_days < start_days:
                warning_mesg += _("") + 'Days Range is not Proper' +"\n\n"
                value = {'end_range_days': 0}
                res['value'] = value
        product_id = context.get('product_id')
        search_id = self.search(cr, uid, [('start_range_days','=',start_days),('end_range_days','=',end_days),('product_id','=',product_id)])
        if search_id:
            warning_mesg += _("") + 'Days Range is not Proper' +"\n\n"
            value = {'end_range_days': 0,'start_range_days':0}
            res['value'] = value
        else:
            if context.get('one2many_field'):
                for each_line in context.get('one2many_field'):
                    if each_line[0] == 0:
                        start_range_days = each_line[2].get('start_range_days')
                        end_range_days = each_line[2].get('end_range_days')
                        if (start_range_days == start_days) and  (end_range_days == end_days):
                            warning_mesg += _("") + 'Days Range is not Proper' +"\n\n"
                            value = {'end_range_days': 0,'start_range_days':0}
                            res['value'] = value
                            break
        if warning_mesg:
             warning = {'title': _('Warning!'),
                'message' : warning_mesg}
             res['warning'] = warning
        return res
    _columns={
    'start_range_days':fields.integer('Start Days'),
    'end_range_days':fields.integer('End Days'),
    'termination_fees':fields.float('Termination Fee'),
    'product_id' : fields.many2one('product.product','Product ID'),
    }
termination_fee_charges()
class product_template(osv.osv):
    _inherit="product.template"
    _columns={
    'recurring_service':fields.boolean('Recurring Service',help="For Recurring Payment"),
    'free_trail_days':fields.integer('Free Trial Months'),
    'service_promotional_rules' : fields.one2many('service.charges','product_id','Promotion Rules'),
    'termination_fees_charges' : fields.one2many('termination.fee.charges','product_id','Termination Fee Charges'),	
    'prod_length': fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
    'prod_width': fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
    'prod_height': fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),   	
    'unique_offer_id': fields.char('Unique Offer ID',size=256),
    'location_id':fields.many2one('stock.location','Location'),
    'magento_product_id':fields.integer('Product ID'),#field to store product id of the Magento
    'start_date':fields.date('Start Date'),
#    'standard_price': fields.property(type = 'float', digits_compute=dp.get_precision('Product Price'), 
#                                          help="Cost price of the product template used for standard stock valuation in accounting and used as a base price on purchase orders. "
#                                               "Expressed in the default unit of measure of the product.",
#                                          groups="base.group_user", string="Cost Price",store=True),
    'standard_price':fields.float('Cost Price',help="Cost price of the product template used for standard stock valuation in accounting and used as a base price on purchase orders. "
                                               "Expressed in the default unit of measure of the product.",),
    'product_type':fields.selection([('product', 'Product'),
                                            ('service', 'Service'),
                                            ('offer', 'Offer'),
                                            ],'Catalog Type'),
                                            
    'app_id':fields.integer('App Id'),#field to set app id of playjam side
    'exported':fields.boolean('Exported'),
    'pj_product':fields.boolean('PJ Product'),
    'property_account_line_prepaid_revenue': fields.property(
        type='many2one',
        relation='account.account',
        string="Account Prepaid Revenue",
        help="This account will be used as Prepaid Revenue account for service "),#yogita for product configuration

    }
    _defaults={
    'recurring_service':True,
    'exported':False
    }
    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', 'Product Reference must be unique!'),
	('appid_uniq', 'unique(app_id)', 'A product with the same AppId already exists.'),
    ]
    def create(self,cr,uid,vals,context={}):
        price=0
        if vals.get('ext_prod_config',[]):
            sub_comp=vals.get('ext_prod_config',[])
            if sub_comp:
                for each_prod in vals.get('ext_prod_config'):
                    price += each_prod[2].get('price',False)
                vals['list_price']=price
                if vals.get('list_price') != price:
                    raise osv.except_osv(_('Warning !'),_('Sale price should be equal total price of sub components'))
        return super(product_template,self).create(cr,uid,vals,context)

    def write(self,cr,uid,ids,vals,context={}):

        if not isinstance(ids,list):
            ids=[ids]
        ids_obj=self.browse(cr,uid,ids[0])
        extra_prod_config = self.pool.get('extra.prod.config')
        price=0
        if vals.get('ext_prod_config',[]):
            for each_prod in vals.get('ext_prod_config',[]):
                if each_prod[0]==2:
                    continue
                elif not each_prod[1]:
                    price += each_prod[2].get('price',False)
                elif not each_prod[2]:
                    each_comp_obj = extra_prod_config.browse(cr,uid,each_prod[1])
                    price+=each_comp_obj.price
                elif each_prod[2].get('price',False):
                    price += each_prod[2].get('price',False)
            
#            ids_obj.list_price=price
            vals['list_price']=price
        elif ids_obj.ext_prod_config:
            for each_comp in ids_obj.ext_prod_config:
                price=each_comp.price
                
        
        if (ids_obj.ext_prod_config and vals.get('list_price',False)) and float(vals.get('list_price',False)) != price:
            raise osv.except_osv(_('Warning !'),_('Sale price should be equal total price of sub components'))
        return super(product_template, self).write(cr, uid, ids,vals,context=context)

product_template()

class pre_requisites(osv.osv):
    _name = 'pre.requisites'
    _columns={
    'name':fields.char('Name',size=64),
    'category_id' : fields.many2one('product.category','Category ID'),
    }
pre_requisites()

class product_category(osv.osv):
    _inherit = 'product.category'
    _columns={
        'pre_requisites':fields.one2many('pre.requisites','category_id','Pre-Requisites'),
        'property_account_line_prepaid_revenue_categ': fields.property(
            type='many2one',
            relation='account.account',
            string="Account Prepaid Revenue",
            domain="[('type', '=', 'payable')]",
            help="This account will be used as Prepaid Revenue account for service "),#yogita for product configuration

    }
product_category()


#code done by yogita
class extra_prod_config(osv.osv):
    _inherit = 'extra.prod.config'

    def onchange_product_id(self,cr,uid,ids,product_id,qty):
        res=super(extra_prod_config,self).onchange_product_id(cr,uid,ids,product_id,qty)
        if product_id:
            pro_obj=self.pool.get('product.product')
            pro_type=pro_obj.browse(cr,uid,product_id).type
            if pro_type=='service':
                res.get('value').update({'show_recurring':True})
            else:
                res.get('value').update({'show_recurring':False})
        return res

    _columns={
     'recurring_price':fields.float('Recurring Price'),
     'show_recurring':fields.boolean('Show Recurring'),
     'no_recurring':fields.boolean('No Recurring'),
     }
extra_prod_config()
