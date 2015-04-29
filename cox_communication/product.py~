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
class product_product(osv.osv):
    _inherit="product.product"
    _columns={
    'recurring_service':fields.boolean('Recurring Service',help="For Recurring Payment"),
    'free_trail_days':fields.integer('Free Trial Months'),
    'service_promotional_rules' : fields.one2many('service.charges','product_id','Promotion Rules'),
    'termination_fees_charges' : fields.one2many('termination.fee.charges','product_id','Termination Fee Charges'),	
    'prod_length': fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
    'prod_width': fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
    'prod_height': fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),   	
    'unique_offer_id': fields.char('Unique Offer ID',size=256),
    'start_date':fields.date('Start Date'),
    }
    _defaults={
    'recurring_service':True,
    }
product_product()

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
    }
product_category()
