# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import date, datetime, timedelta
import time
import datetime as dt
import calendar
from openerp import netsvc
import string
import openerp.addons.decimal_precision as dp
import random
from dateutil.relativedelta import relativedelta
#from openerp.addons.base_external_referentials.external_osv import ExternalSession
import pytz
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
import ast

#class sale_shop(osv.osv):
#    _inherit = 'sale.shop'
#    _columns = {
#        'base_url': fields.char('Website Location',size=256)
#                }
#sale_shop()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    #def create(self,cr,uid,vals,context={}):
        #if vals and vals.get('product_id'):
            #if not context.get('child_lines'):
                #search_sale_line = self.search(cr,uid,[('product_id','=',vals.get('product_id')),('order_id','=',vals.get('order_id'))])
                #if search_sale_line:
                    #total_qty = 0.0
                    #sale_line_obj = self.browse(cr,uid,search_sale_line[0])
                    #total_qty += sale_line_obj.product_uom_qty + vals.get('product_uom_qty')
                    #self.write(cr,uid,search_sale_line[0],{'product_uom_qty':total_qty})
                    #return search_sale_line[0]
                #else:
                    #return super(sale_order_line, self).create(cr, uid, vals, context=context)
            #else:
                #return super(sale_order_line, self).create(cr, uid, vals, context=context)
    def create(self,cr,uid,vals,context=None):
#        cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
#        print"vals",vals
#        print"context",context
        res=super(sale_order_line,self).create(cr,uid,vals,context)
        print"res",res
        return res
    def write(self,cr,uid,ids,vals,context={}):
         if vals and vals.get('product_id'):
            ids_obj = self.browse(cr,uid,ids[0])
            order_id = ids_obj.order_id
            if order_id:
                search_sale_line = self.search(cr,uid,[('product_id','=',vals.get('product_id')),('order_id','=',order_id.id),('id','not in',ids)])
                if search_sale_line:
                    total_qty = 0.0
                    sale_line_obj = self.browse(cr,uid,search_sale_line[0])
                    qty = (vals.get('product_uom_qty') if vals.get('product_uom_qty') else ids_obj.product_uom_qty )
                    total_qty += sale_line_obj.product_uom_qty + qty
                    cr.execute("update sale_order_line set product_uom_qty=%s where id=%d"%(total_qty,search_sale_line[0]))
                    self.unlink(cr,uid,ids,context)
                    return True
#         cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
         return super(sale_order_line, self).write(cr, uid, ids,vals,context=context)

    _columns = {
    'start_date': fields.date('Start Date', select=True, help="Date on which service is created."),
    'end_date': fields.date('End Date', select=True, help="Date on which service is closed."),
    'hide_date':fields.boolean('Hide Start and End date for Stockable product'),
    'promo_code_applied': fields.boolean('Promo Code Applied'),
    'order_item_id': fields.char('Order Item ID',size=64),
    'free_trial_days': fields.integer('Free Trial Days'),
    }
    _defaults = {
        'start_date': fields.date.context_today,
        'hide_date':True,
    }
    #Function is inherited because initially it doesnot stores the tax_id properly
    def play_sale_order_line_onchange(self, cr, uid, line, parent_data, previous_lines, defaults=None, context=None):
	context['skip'] = True
        line = self.call_onchange(cr, uid, 'product_id_change', line, defaults=defaults, parent_data=parent_data, previous_lines=previous_lines, context=context)
        #Extra code to know whether discount coupon is used or not
        if parent_data.get('promo_code',''):
            line['promo_code_applied'] = True
        #TODO all m2m should be mapped correctly
        if line.get('tax_id'):
            if type(line.get('tax_id'))== type(list()):
                if (type(line.get('tax_id')[0]))== type(tuple()):
                    line['tax_id'] = line.get('tax_id')
                else:
                    line['tax_id'] = [(6, 0, line.get('tax_id'))]
        return line
#Function is inherited because function is inherited in the sale_bundle_product module and calculates
# Bundle product Prices depending on the Item Set Line Prices
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.order_id:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
                cur = line.order_id.pricelist_id.currency_id
                res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

#    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,uom=False, qty_uos=0, uos=False, name='', partner_id=False,  lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
#        print"context sale order",context
#        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product,qty,uom,qty_uos,uos,name,partner_id ,lang,update_tax,date_order,packaging,fiscal_position,flag, context)
#        print"res",res
#        if not res:
#            res,res['value'],res['warning'] = {},{},{}
#        if context==None:
#            context={}
#        message,child_product_ids = '',[]
#        if res.get('warning',{}):
#            message = res.get('warning',{}).get('message','')
#        
#        if not context.get('skip',False):
#            existing_order_line = context.get('order_line')
#            if res.get('value',{}).get('sub_components',[]):
#                [child_product_ids.append(each_comp[2].get('product_id',False)) if each_comp[2].get('product_id',False) and each_comp[2].get('product_type',False) == 'service' else '' for each_comp in res.get('value',{}).get('sub_components',[])]
#            else:
#                child_product_ids.append(product)
#            cr.execute("select product_id from res_partner_policy where agmnt_partner=%s and active_service = True"%(partner_id))
#            existing_pack_id = filter(None, map(lambda x:x[0], cr.fetchall()))
#            final_list = set(child_product_ids) & set(existing_pack_id)
#            cr.execute("select product_id from res_partner_policy where agmnt_partner=%s and cancel_date<=CURRENT_DATE"%(partner_id))
#            cancel_pack_id1 = filter(None, map(lambda x:x[0], cr.fetchall()))
#            cancel_final_list=set(child_product_ids) & set(cancel_pack_id1)
#
#            if cancel_pack_id1 and cancel_final_list==final_list:
#                final_list=[]
#            if len(final_list) > 0:
#                message += message + '\n Customer already has same active subscription.'
#                print"message",message
#                if res['warning']==False:
#                    res['warning']={}
#                res['warning']['message'] = message
#                res['value'].update({'product_id':False,'name':'','sub_components':[]})
#                print"res",res
#            elif existing_order_line:
#                for each_line in  existing_order_line:
#                    lines_product_ids = []
#                    if each_line[0]==2:
#                        continue
#                    if not each_line[1]:
#                        [lines_product_ids.append(each_comp[2].get('product_id',False)) if each_comp[2].get('product_id',False) and each_comp[2].get('product_type',False) == 'service' else '' for each_comp in each_line[2].get('sub_components',[])]
#                    else:
#                        cr.execute("select product_id from sub_components where so_line_id =%s and product_type='service'"%(each_line[1]))
#                        lines_product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#                    if child_product_ids:
#                        if child_product_ids==lines_product_ids:
#                                message += message + '\n You cannot select same pack at same time.'
#                                
#                                res['warning']['message'] = message
#                                res['value'].update({'product_id':False,'name':'','sub_components':[]})
#         #Modification starts from here
#        if product:
#            product_id_obj = self.pool.get('product.product').browse(cr,uid,product)
#            res['value']['start_date']=False
#            res['value']['end_date']=False
#            if product_id_obj.type=='service' and product_id_obj.recurring_service==True:
#                if date_order:
#                    res['value']['start_date']=date_order
#                    res['value']['end_date']=str(datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S")+relativedelta(months=24)) ##x=cox gen2 date_order field is datetime now
#                res['value']['hide_date']=False
#            ##To check whether added product is shipping product or not
##            product_ref = ('base_sale_multichannels', 'product_product_shipping')
#            product_ref = ('bista_shipping', 'product_product_shipping')  ##cox gen2
#            model, product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, *product_ref)
#            if product_id == product:
#                call_center_pickup = context.get('call_center_pickup')
#                if call_center_pickup:
#                    message += message + '\n You cannot add shipping Cost because you have choosen Pick UP'
#                    if res['warning']==False:
#                        res['warning']={}
#                    res['warning']['message'] = message
#                    res['value'].update({'product_id':False,'name':'','sub_components':[]})
#        if message:
#            if not res.get('warning',{}).get('title'):
#                res['warning']['title'] = _('Warning!')
#        product_categ_ids=[]
#        if context.get('all_lines',False) and product:
#            for each_line in all_lines:
#                print"each_line[0]",each_line[0]
#                if each_line[0] == 4:
#                   product_categ_ids.append(self.browse(cr,uid,each_line[1]).product_id.id)
#                   
#                elif each_line[0] in (0,1) and isinstance(each_line[2], (dict)):
#                   print"elseeeeeeeeeeeee"
#                   product_categ_ids.append(each_line[2].get('product_id',0.0))
#                   print"product_categ_ids---------------",product_categ_ids
#            if product_categ_ids and product in product_categ_ids:
#
#                warning = {
#                'title': _('Warning!'),
#                'message' : _('Record is already selected . Please just increase the quantity of that line.')
#                   }
#                res['warning']  = warning
#                res['value']['product_id'] = False
#        return res

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False, 
            all_lines=False,lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        if isinstance(fiscal_position,bool):fiscal_position=[]#vijay
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product,qty,uom,qty_uos,uos,name,partner_id,lang,update_tax,date_order,packaging,fiscal_position,flag, context)
        
        product_category_obj = self.pool.get('product.category') #vijay
        product_obj = self.pool.get('product.product') #Preeti
        policy_obj = self.pool.get('res.partner.policy')
#         partner_id = partner_obj.search(cr,uid,[('ref','=',cust_id)])
        existing_parent_services,existing_child_services,existing_parent_services2=[],[],[]
        if not res:
            res,res['value'],res['warning'] = {},{},{}
            print"desired_service_id",res
        if context==None:
            context={}
        message,child_product_ids = '',[]
        if res.get('warning',{}):
            message = res.get('warning',{}).get('message','')
        if res.get('warning',False)==False:
            res['warning']={}
        if not context.get('skip',False):
#            existing_order_line = context.get('order_line')
            existing_order_line = context.get('order_line')
            if res.get('value',{}).get('sub_components',[]):
                [child_product_ids.append(each_comp[2].get('product_id',False)) if each_comp[2].get('product_id',False) and each_comp[2].get('product_type',False) == 'service' else '' for each_comp in res.get('value',{}).get('sub_components',[])]
            else:
                child_product_ids.append(product)
            #start code preeti <!--Preeti for Product Configuration-->
            res['value']['discount_amt']=0.0
            res['value']['actual_price']=0.0            
            for components in res.get('value',{}).get('sub_components',[]):                                
                res['value']['discount_amt']+= components[2].get('discount_amt',False)
                res['value']['actual_price'] += components[2].get('actual_price',False)
            #end code preeti
            #start code Preeti
            for each_child_product_id in child_product_ids:
                print"child_product_ids",child_product_ids
                desired_id =product_obj.browse(cr,uid,each_child_product_id)
                print"desired_id",desired_id
                if desired_id.id != 0:
                    desired_service=desired_id.product_tmpl_id.categ_id  ##cox gen2
                    print"desired_service",desired_service
                    desired_service_id=desired_id.product_tmpl_id.categ_id.id  ##cox gen2
                    if partner_id:
                        current_active_ids = policy_obj.search(cr,uid,[('agmnt_partner','=',partner_id),('active_service', '=', True)])
                        for each_existing_id in policy_obj.browse(cr,uid,current_active_ids):
                            prod_id = each_existing_id.product_id
                            print"prod_id",prod_id
                            existing_service_brw = product_category_obj.browse(cr,uid,prod_id.product_tmpl_id.categ_id.id)
                            print "existing_service_brw",existing_service_brw##cox gen2
#                            print"existing_service_brwexisting_service_brw",existing_service_brw
                            if (existing_service_brw.parent_id):
                                existing_parent_services.append(existing_service_brw.parent_id.id)
                            else:
                                existing_parent_services2.append(existing_service_brw.id)
                            existing_child_services.append(existing_service_brw.id)
                        print"existing_child_services",existing_child_services,existing_parent_services
                    if desired_service_id:
                        if (desired_service_id in existing_child_services) or (desired_service_id in existing_parent_services):
                            message += message + '\n Customer already has same active subscription.'
                            print"(desired_service.parent_id.id in existing_parent_services2)(desired_service.parent_id.id in existing_parent_services2)"
                            res['warning']['message'] = message
                            res['value'].update({'product_id':False,'name':'','sub_components':[]})
#                                break;
                        elif (desired_service.parent_id.id in existing_child_services) or (desired_service.parent_id.id in existing_parent_services): #here
                            if (desired_service_id in existing_child_services) or (desired_service.parent_id.id in existing_parent_services2):
                                message += message + '\n Customer already has same active subscription.'
                                res['warning']['message'] = message
                                res['value'].update({'product_id':False,'name':'','sub_components':[]})
#                                    break;

        #end code Preeti
##########code done by yogita
                        elif existing_order_line:
                            print"existing_order_lineexisting_order_lineexisting_order_line",existing_order_line
                            for each_line in existing_order_line:
                                print"each_line[1]",each_line[1]
                                lines_product_ids = []
                                existing_parent_services=[]
                                existing_child_services=[]
                                existing_parent_services2=[]
                                if each_line[0]==2:
                                    continue
                                if not each_line[1]:
                                    if each_line[2]:  ##cox gen2
                                        if isinstance(each_line[2].get('sub_components',[]), (dict)):
                                            
                                            [lines_product_ids.append(each_comp[2].get('product_id',False)) if each_comp[2].get('product_id',False) and each_comp[2].get('product_type',False) == 'service' else '' for each_comp in each_line[2].get('sub_components',[])]
                                        else:
                                            print"each_line[2].get('product_id',False)",each_line[2].get('product_id',False)
                                            [lines_product_ids.append(each_line[2].get('product_id',False)) if each_line[2].get('product_id',False) else '']
                                else:
                                    cr.execute("select product_id from sub_components where so_line_id =%s and product_type='service'"%(each_line[1]))
                                    lines_product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                                    print"lines_product_ids",lines_product_ids
                                for each_child_product_id in lines_product_ids:
                                    existing_id =product_obj.browse(cr,uid,each_child_product_id)
                                    if existing_id.id != 0:
                                        existing_service=existing_id.product_tmpl_id.categ_id  ##cox gen2
                                        print"existing_service***************************",existing_service,desired_service_id,desired_service.parent_id
                                        existing_service_id=existing_id.product_tmpl_id.categ_id.id ##cox gen2
                                        if partner_id and existing_service_id:
            #                                if desired_service_id:
                                            if existing_service.parent_id:
                                                print"existing_parent_services.append(existing_service_id)",existing_service.parent_id
                                                existing_parent_services.append(existing_service.parent_id.id)
                                            else:
                                                existing_parent_services2.append(existing_service_id)
                                            existing_child_services.append(existing_service_id)
#                                                existing_parent_services2.append(existing_service_id)
                                            print"existing_child_servicesexisting_child_services",existing_child_services
                                            print"existing_parent_servicesexisting_parent_services",existing_parent_services
                                            print"existing_parent_servicesexisting_parent_services",existing_parent_services2
                                            if desired_service.parent_id and (desired_service.parent_id.id in existing_child_services) :
#                                                if (desired_service.parent_id.id in existing_child_services) :
#                                                or (desired_service.parent_id.id in existing_parent_services): #here
                #                                    print "active"
                                                message += message + '\n You cannot select same pack at same time.'
                                                res['warning']['message'] = message
                                                res['value'].update({'product_id':False,'name':'','sub_components':[]})
                                            elif (desired_service_id in existing_child_services) or (desired_service_id in existing_parent_services):
                                                    print "active------------------"
                                                    message += message + '\n You cannot select same pack at same time.'
                                                    res['warning']['message'] = message
                                                    res['value'].update({'product_id':False,'name':'','sub_components':[]})
                                                    break;
#                                            elif (desired_service.parent_id.id in existing_child_services) or (desired_service.parent_id.id in existing_parent_services): #here
#                                                if (desired_service_id in existing_child_services) or (desired_service.parent_id.id in existing_parent_services2):
#                #                                    print "active"
#                                                  message += message + '\n You cannot select same pack at same time.'
#                                                  res['warning']['message'] = message
#                                                  res['value'].update({'product_id':False,'name':'','sub_components':[]})
                                        
############code done by yogita
#          #Modification starts from here
        if product:
            product_id_obj = self.pool.get('product.product').browse(cr,uid,product)
            res['value']['start_date']=False
            res['value']['end_date']=False
            if product_id_obj.type=='service' and product_id_obj.recurring_service==True:
                if date_order:
                    res['value']['start_date']=date_order
                    res['value']['end_date']=str(datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S")+relativedelta(months=24))
                res['value']['hide_date']=False
             ##To check whether added product is shipping product or not
#            product_ref = ('base_sale_multichannels', 'product_product_shipping')
            product_ref = ('bista_shipping', 'product_product_shipping')
            model, product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, *product_ref)
            if product_id == product:
                call_center_pickup = context.get('call_center_pickup')
                if call_center_pickup:
                    message += message + '\n You cannot add shipping Cost because you have choosen Pick UP'
                    res['warning']['message'] = message
                    res['value'].update({'product_id':False,'name':'','sub_components':[]})
        if message:
            if not res.get('warning',{}).get('title'):
                res['warning']['title'] = _('Warning!')
        product_categ_ids=[]
        if context.get('all_lines',False) and product:
            for each_line in context.get('all_lines',False):
                if each_line[0] == 4:
                   product_categ_ids.append(self.browse(cr,uid,each_line[1]).product_id.id)
                elif each_line[0] in (0,1) and isinstance(each_line[2], (dict)):
                   product_categ_ids.append(each_line[2].get('product_id',0.0))
            if product_categ_ids and product in product_categ_ids:

                warning = {
                'title': _('Warning!'),
                'message' : _('Record is already selected . Please just increase the quantity of that line.')
                   }
                res['warning']  = warning
                res['value']['product_id'] = False
        return res
	
    def _prepare_order_line_invoice_line_cox(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sale order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).
           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        def _get_line_qty(line):
            if line.product_uos:
                return line.product_uos_qty or 0.0
            return line.product_uom_qty

        def _get_line_uom(line):
            if line.product_uos:
                return line.product_uos.id
            return line.product_uom.id
        
        
        ###cox gen2 start
#        def _get_line_qty(line):
#            if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
#                if line.product_uos:
#                    return line.product_uos_qty or 0.0
#                return line.product_uom_qty
#            else:
#                return self.pool.get('procurement.order').quantity_get(cr, uid,
#                        line.procurement_id.id, context=context)

#        def _get_line_uom(line):
#            if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
#                if line.product_uos:
#                    return line.product_uos.id
#                return line.product_uom.id
#            else:
#                return self.pool.get('procurement.order').uom_get(cr, uid,
#                        line.procurement_id.id, context=context)

##############end

#        if not line.invoiced:
        if not account_id:
            if line.product_id:
                account_id = line.product_id.product_tmpl_id.property_account_income.id
                if not account_id:
                    account_id = line.product_id.categ_id.property_account_income_categ.id
                if not account_id:
                    raise osv.except_osv(_('Error !'),
                            _('There is no income account defined for this product: "%s" (id:%d)') % \
                                (line.product_id.name, line.product_id.id,))
            else:
                prop = self.pool.get('ir.property').get(cr, uid,
                        'property_account_income_categ', 'product.category',
                        context=context)
                account_id = prop and prop.id or False
        uosqty = _get_line_qty(line)
        uos_id = _get_line_uom(line)
        pu = 0.0
        if uosqty:
            pu = round(line.price_unit * line.product_uom_qty / uosqty,
                    self.pool.get('decimal.precision').precision_get(cr, uid, 'Sale Price'))
        fpos = line.order_id.fiscal_position or False
        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
        if not account_id:
            raise osv.except_osv(_('Error !'),
                        _('There is no income category account defined in default Properties for Product Category or Fiscal Position is not defined !'))
        return {
            'name': line.name,
            'origin': (line.order_id.name if line.order_id else line.so_id.name),
            'account_id': account_id,
            'price_unit': pu,
            'quantity': uosqty,
            'discount': line.discount,
            'uos_id': uos_id,
            'product_id': line.product_id.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
        #    'note': line.notes,
            'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
        }
sale_order_line()

class sale_order(osv.osv):
    _inherit='sale.order'
    
    
    def action_ship_create(self, cr, uid, ids, context=None):
        """Create the required procurements to supply sales order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sales order's requested location.

        :return: True
        """
        procurement_obj = self.pool.get('procurement.order')
        sale_line_obj = self.pool.get('sale.order.line')
        sub_component_obj = self.pool.get('sub.components')
        for order in self.browse(cr, uid, ids, context=context):
            proc_ids = []
            vals = self._prepare_procurement_group(cr, uid, order, context=context)
            if not order.procurement_group_id:
                group_id = self.pool.get("procurement.group").create(cr, uid, vals, context=context)
                order.write({'procurement_group_id': group_id})

            for line in order.order_line:
                #Try to fix exception procurement (possible when after a shipping exception the user choose to recreate)
                if line.procurement_ids:
                    #first check them to see if they are in exception or not (one of the related moves is cancelled)
                    procurement_obj.check(cr, uid, [x.id for x in line.procurement_ids if x.state not in ['cancel', 'done']])
                    line.refresh()
                    #run again procurement that are in exception in order to trigger another move
                    proc_ids += [x.id for x in line.procurement_ids if x.state in ('exception', 'cancel')]
                    procurement_obj.reset_to_confirmed(cr, uid, proc_ids, context=context)
                elif sale_line_obj.need_procurement(cr, uid, [line.id], context=context):
                    if (line.state == 'done') or not line.product_id:
                        continue
                    vals = self._prepare_order_line_procurement(cr, uid, order, line, group_id=order.procurement_group_id.id, context=context)
                    proc_id = procurement_obj.create(cr, uid, vals, context=context)
                    proc_ids.append(proc_id)
             
                elif line.sub_components:
                    for sub_line in line.sub_components:
                        result = sub_component_obj.need_procurement(cr, uid, [sub_line.id], context=context)
                        if result:
                            print"sub_line",sub_line.id
                            if not sub_line.product_id:
                                continue
                            vals = self._prepare_order_line_procurement(cr, uid, order, line, sub_line, group_id=order.procurement_group_id.id,  context=context)
                            proc_id = procurement_obj.create(cr, uid, vals, context=context)
                            proc_ids.append(proc_id)
            #Confirm procurement order such that rules will be applied on it
            #note that the workflow normally ensure proc_ids isn't an empty list
            procurement_obj.run(cr, uid, proc_ids, context=context)

            #if shipping was in exception and the user choose to recreate the delivery order, write the new status of SO
            if order.state == 'shipping_except':
                val = {'state': 'progress', 'shipped': False}

                if (order.order_policy == 'manual'):
                    for line in order.order_line:
                        if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                            val['state'] = 'manual'
                            break
                order.write(val)
        return True

    def procurement_needed(self, cr, uid, ids, context=None):
        #when sale is installed only, there is no need to create procurements, that's only
        #further installed modules (sale_service, sale_stock) that will change this.
        sale_line_obj = self.pool.get('sale.order.line')
        sub_prod_obj = self.pool.get('sub.components')
        res = []
        
        for order in self.browse(cr, uid, ids, context=context):
            
            res.append(sale_line_obj.need_procurement(cr, uid, [line.id for line in order.order_line], context=context))
            if not any(res):
                for each in order.order_line:
                    for line in self.pool.get('sale.order.line').browse(cr, uid, each.id, context=context):
                        res.append(sub_prod_obj.need_procurement(cr, uid, [line.id for line in line.sub_components], context=context))
        return any(res)

    def welcome_email_offer(self,cr,uid,sale_id_brw,data,context):
        if sale_id_brw:
            cr.execute("select name_template from product_product where id in (select product_id from sale_order_line where order_id=%d)"%(sale_id_brw.id))
            product_names = filter(None, map(lambda x:x[0], cr.fetchall()))
            product_names = [ each_name.lower() for each_name in product_names]
            if len(product_names) == 1:
                product_names = str(product_names)
                if ('pop' in product_names) or ('casual' in product_names):
                    self.email_to_customer(cr,uid,sale_id_brw.partner_id,'res.partner','welcome_email_pop',sale_id_brw.partner_id.emailid,context)
                else:
		    if data.get('new_customer',False):	
	                    self.email_to_customer(cr,uid,sale_id_brw.partner_id,'res.partner','welcome_email',sale_id_brw.partner_id.emailid,context)
            else:
                product_names = str(product_names)
                if ('pop' in product_names) or ('casual' in product_names):
                    self.email_to_customer(cr,uid,sale_id_brw.partner_id,'res.partner','welcome_email_pop',sale_id_brw.partner_id.emailid,context)
		    if data.get('new_customer',False):
	                    self.email_to_customer(cr,uid,sale_id_brw.partner_id,'res.partner','welcome_email',sale_id_brw.partner_id.emailid,context)
                else:
		    if data.get('new_customer',False):	
	                    self.email_to_customer(cr,uid,sale_id_brw.partner_id,'res.partner','welcome_email',sale_id_brw.partner_id.emailid,context) 	
    def search_income_account(self,cr,uid,ids,context={}):
        cr.execute("select product_id from sale_order_line where order_id=%d"%(ids[0]),)
        product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        account_ids = []
        if product_ids:
            product_ids = self.pool.get('product.product').browse(cr,uid,product_ids)
            val = [account_ids.append(each_product.property_account_income.id) for each_product in product_ids]
        return account_ids
    def get_src_user_location(self,cr,uid,context):
        if context.get('default_cox_sales_channels'):
            if context.get('default_cox_sales_channels') == 'call_center':
                location_id = self.pool.get('stock.location').search(cr,uid,[('name','ilike','vista')])
                if location_id:
                    return location_id[0]
            if context.get('default_cox_sales_channels') == 'amazon':
                location_id = self.pool.get('stock.location').search(cr,uid,[('name','ilike','stock')])
                if location_id:
                    return location_id[0]
		#start code Preeti
            if context.get('default_cox_sales_channels') == 'tru':
                location_id = self.pool.get('stock.location').search(cr,uid,[('name','ilike','solutions 2 go')])
                if location_id:
                    return location_id[0]    
                #end code Preeti
        src_location = self.pool.get('res.users').browse(cr,uid,uid).src_location_id
        if src_location:
            return src_location.id
        else:
            return False
    
    #Function is inherited because its not bringing sale taxes for online orders:
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        for order in self.browse(cr, uid, ids, context=context):
            if order.cox_sales_channels == 'ecommerce':
                res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0 }
                val = val1 = 0.0
                cur = order.pricelist_id.currency_id
                for line in order.order_line:
                    val1 += line.price_subtotal
                    val += self._amount_line_tax(cr, uid, line, context=context)
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
                res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
#                tax_amount = res[order.id]['amount_tax']
#                if tax_amount <= 0.0:
#                    if order.ext_total_amount:
#                        res[order.id]['amount_tax'] = float(order.ext_total_amount) - res[order.id]['amount_untaxed']
                res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    #Function to know whether the order is returned or not
    def get_returns_status(self, cr, uid, ids, name=None, args=None, context=None):
        result = {}
        for order in self.browse(cr, uid, ids, context=context):
            return_total,flag = 0.0,False
            result[order.id] = 'no_returns'
            if order.sale_return_ids:
                for each_return in order.sale_return_ids:
                    if each_return.return_type == 'car_return':
			flag=True
                        return_total += each_return.amount_total
                if flag and round(float(order.amount_total)) == round(float(return_total)):
                        result[order.id] = 'full_returns'
                elif return_total > 0.0:
                    result[order.id] = 'partial_returns'
        return result 

    def date_order_confirm(self,cr,uid,context):
        estern_time_obj = pytz.timezone('EST')
        date_time = datetime.now(estern_time_obj).strftime('%Y-%m-%d')
        return date_time
	#TRU added by Preeti
    _columns={
     'user_id': fields.many2one('res.users', 'Salesperson', readonly=True,states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True, track_visibility='onchange'), ###inherited to make the field readonly
    'billing_date':fields.datetime('Billing Date'),
    'agreement_approved': fields.boolean('EULA Signed'),
    'location_id': fields.many2one('stock.location', 'Shop'),
    'magento_exported':fields.boolean('Magento Exported'),
    'order_type':fields.boolean('Retail Order',help="Sale order from Retail Store "),
    'call_center_pickup':fields.boolean('Pick UP',help="Check if Customer is Ready to Pickup at Call Center "),
    'magento_so_id': fields.char('Magneto Increment ID',size=256),
    'magento_db_id': fields.char('Magneto Database ID',size=256),
    'prov_by_fanha':fields.selection([
            ('yes', 'Yes'),
            ('no', 'No'),
    ],'Provisioned by Fanhattan'),
    'cox_sales_channels': fields.selection([
                ('call_center', 'Call Center'),
            ('ecommerce', 'Ecommerce'),
            ('retail', 'Retail'),
            ('amazon', 'Amazon'),
            #('playjam','Playjam'),
	    ('tru', 'TRU'),
	    ('playjam','Playjam'),
            ], 'Sales Channels'),
    'payment_policy': fields.selection([
            ('pro', 'Pro Rate'),
            ('eom', 'End of Month')
            ], 'Payment Policy', help="Pro Rate option generates invoice after one month from current date.\n End of month policy generates \n invoices at every end of month. "),
    'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'magento_incrementid': fields.char('Magento Order ID', size=64),########## cox gen2 changes by yogita
        'promo_code' : fields.char('Promo code',size=256,readonly=True,states={'draft': [('readonly', False)]}),
        'returns_status' : fields.function(get_returns_status, method=True,string="Returns Status", type="char",size=64),
        'tracking_no': fields.char('Tracking Number', size=64,readonly=True,states={'draft': [('readonly', False)],'progress': [('readonly', False)]}),
#
##Newly Added filed to show the stock move
#        'stock_move_ids' : fields.related('picking_ids', 'move_lines',
#                type='many2many', relation='stock.move',
#                string='Stock Moves'),

    }
    _defaults={
    'cox_sales_channels':'call_center',
    'date_order': date_order_confirm, 	
    'order_policy': 'prepaid',
    'prov_by_fanha': 'no',
    'magento_exported':False,
    'location_id':get_src_user_location,
    }
    def procurement_lines_get(self, cr, uid, ids, *args):
        res = []
        sale_line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context={}):
            cr.execute("select id from sale_order_line where order_id=%s or so_id=%s"%(order.id,order.id))
            line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            line_ids_brw = sale_line_obj.browse(cr,uid,line_ids)
            for line in line_ids_brw:
                if line.procurement_id:
                    res.append(line.procurement_id.id)
        return res
    def test_state(self, cr, uid, ids, mode, *args):
        assert mode in ('finished', 'canceled'), _("invalid mode for test_state")
        finished = True
        canceled = False
        notcanceled = False
        write_done_ids = []
        write_cancel_ids = []
        sale_line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context={}):
            cr.execute("select id from sale_order_line where order_id=%s or so_id=%s"%(order.id,order.id))
            line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            line_ids_brw = sale_line_obj.browse(cr,uid,line_ids)
            for line in line_ids_brw:# initially it was order.order_line
                if (not line.procurement_id) or (line.procurement_id.state=='done'):
                    if line.state != 'done':
                        write_done_ids.append(line.id)
                else:
                    finished = False
                if line.procurement_id:
                    if (line.procurement_id.state == 'cancel'):
                        canceled = True
                        if line.state != 'exception':
                            write_cancel_ids.append(line.id)
                    else:
                        notcanceled = True
        if write_done_ids:
            sale_line_obj.write(cr, uid, write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            sale_line_obj.write(cr, uid, write_cancel_ids, {'state': 'exception'})
        if mode == 'finished':
            return finished
        elif mode == 'canceled':
            return canceled
            if notcanceled:
                return False
            return canceled
    #Function is inherited because want to make that field as False
#    def onchange_shop_id(self, cr, uid, ids, shop_id,context=None):
#        v = {}
#        if shop_id:
#            if shop_id == 1:
#                if uid:
#                    uid_brw = self.pool.get('res.users').browse(cr,uid,uid)
#                    if uid_brw.mag_store_id:
#                        shop_id = uid_brw.mag_store_id.id
#                    else:
#                        search_magento_shop = self.pool.get('sale.shop').search(cr,uid,[('magento_shop','=',True),('name','=','Flare Play Store')])
#			search_magento_shop.sort()	
#                        if search_magento_shop:
##                            shop_id = search_magento_shop[-1]
#			     shop_id = search_magento_shop[0]	
#            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
#            if context and context.get('cox_sales_channels','') == 'call_center':
#                if shop.warehouse_id and shop.warehouse_id.lot_stock_id:
#                    v['location_id'] = shop.warehouse_id.lot_stock_id.id
#                else:
#                    raise osv.except_osv(_('Error !'),_('Please specify Loction id for the Warehouse for %s'%(shop.name)))
#            v['shop_id'] = shop_id
#            v['project_id'] = shop.project_id.id
#            if shop.pricelist_id.id:
#                v['pricelist_id'] = shop.pricelist_id.id
#        return {'value': v}
    ####Function is inherited because not to calculate taxes on the services
    def create_lines(self, cr, uid, order_lines):
        lines = []
        for line in order_lines:
            if (line.product_id.type != 'service') :
                lines.append({
                    'qty': line.product_uom_qty,
                    'itemcode': line.product_id and line.product_id.default_code or None,
                    'description': line.name,
                    'amount': line.price_unit * (1-(line.discount or 0.0)/100.0) * line.product_uom_qty,
                    'tax_code': line.product_id and ((line.product_id.tax_code_id and line.product_id.tax_code_id.name) or
                            (line.product_id.categ_id.tax_code_id  and line.product_id.categ_id.tax_code_id.name)) or None
                })
            elif (line.product_id.type == 'service' and line.sub_components):
                    for each_line in line.sub_components:
                        if each_line.product_id.type != 'service':
                            lines.append({
                                    'qty': each_line.qty_uom,
                                    'itemcode': each_line.product_id and each_line.product_id.default_code or None,
                                    'description': each_line.name,
                                    'amount': each_line.price * each_line.qty_uom,
                                    'tax_code': each_line.product_id and ((each_line.product_id.tax_code_id and each_line.product_id.tax_code_id.name) or
                                            (each_line.product_id.categ_id.tax_code_id  and each_line.product_id.categ_id.tax_code_id.name)) or None
                                })
        return lines
    ###Function is inherited from Sales Avatax because to prevent tax calculation for
    #ecommerce orders and also to calculate tax based on the retail and call center locations
    def compute_tax(self, cr, uid, ids, context=None):
        avatax_config_obj = self.pool.get('account.salestax.avatax')
        account_tax_obj = self.pool.get('account.tax')
        avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid)
        for order in self.browse(cr, uid, ids):
            if order.cox_sales_channels != 'ecommerce':#Extra Code
                print"order.location_id.",order.location_id
                tax_amount = 0.0
                if avatax_config and not avatax_config.disable_tax_calculation and \
                avatax_config.default_tax_schedule_id.id == order.partner_id.tax_schedule_id.id:
                    address = (order.location_id.partner_id if order.location_id else False)
                    if not address:
                        raise osv.except_osv(_('Error !'),_('Please Specify Address Location for %s')%(order.location_id.name))
                    else:
                        address =  address.id
                    lines = self.create_lines(cr, uid, order.order_line)
                    if lines:
                        if order.date_confirm:
                            order_date = (order.date_confirm).split(' ')[0]
                        else:
                            order_date = (order.date_order).split(' ')[0]
                        tax_amount = account_tax_obj._check_compute_tax(cr, uid, avatax_config, order_date,
                                                                        order.name, 'SalesOrder', order.partner_id, address,
                                                                        order.partner_invoice_id.id, lines, order.shipcharge, order.user_id,
                                                                        context=context).TotalTax
                    self.write(cr, uid, [order.id], {'tax_amount': tax_amount, 'order_line': []})
        return True
    #Function is to delete shipping and costs product on selecting of Pick UP
    def onchange_call_center_pick_up(self,cr,uid,ids,pickup,context={}):
        picking_obj = self.pool.get('stock.picking')
        if ids:
            if pickup:
#                product_ref = ('base_sale_multichannels', 'product_product_shipping')
                product_ref = ('bista_shipping', 'product_product_shipping')
                model, product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, *product_ref)
                if product_id:
                    cr.execute("select id from sale_order_line where product_id = %s and order_id=%s",(product_id,ids[0]))
                    result = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if result:
                        cr.execute("delete from sale_order_line where id=%d"%(result[0]))
                    picking_id = picking_obj.search(cr,uid,[('sale_id','=',ids[0]),('state','not in',('done','cancel'))])
                    if picking_id:
                        picking_obj.write(cr,uid,picking_id,{'pick_up_back_office':True})
            else:
                picking_id = picking_obj.search(cr,uid,[('sale_id','=',ids[0]),('state','not in',('done','cancel')),('pick_up_back_office','=','True')])
                if picking_id:
                    picking_obj.write(cr,uid,picking_id,{'pick_up_back_office':False})
        return {'value':{}}
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
        return {
            'name': pick_name,
            'origin': order.name,
            'date': order.date_order,
            'type': 'out',
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'partner_id': order.partner_shipping_id.id, #chnaged address_id to partner_id
            'note': order.note,
            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
            'company_id': order.company_id.id,
            #Extra Line
            'pick_up_back_office': ( True if order.call_center_pickup else False)
        }
        
    #Function Is inheited to do change location_id for Retail Store Orders
    def _prepare_order_line_procurement(self, cr, uid, order, line, sub_comp = False, group_id=False, context=None):
        date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
#        cr.execute("select id from sale_order_line where parent_so_line_id='%s' and product_id in (select id from product_product where product_tmpl_id in (select id from product_template where type !='service'))"%(line.id))
#        sale_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
#        print"sale_line_id",sale_line_id
#        sale_line_id = self.pool.get('sale.order.line').search(cr,uid,[('parent_so_line_id','=',line.id)])
        #Extra code
#        rule_id= False
#        location_id = self.pool.get('stock.location').search(cr,uid,[('name','ilike','stock')])
#        if location_id:
#            location_id = location_id[0]
#        if order.order_type:
#            location_id = (order.location_id.id if order.location_id else location_id)
#        else:
#            location_id = (order.warehouse_id.wh_output_stock_loc_id.id if order.warehouse_id else location_id)
        rule_id= self.pool.get('procurement.rule').search(cr,uid,[('location_src_id','=',order.location_id.id),('warehouse_id','=',order.warehouse_id.id)])
        if rule_id:
            rule_id = rule_id[0]
#        print"rule_idrule_idrule_idrule_id",rule_id
#        output_id = order.warehouse_id.wh_output_stock_loc_id.id
#        print"output_idoutput_id",output_id
#        partner_dest_id = order.partner_id.id
#        print"partner_dest_id",partner_dest_id
        #########end
        location_id = order.partner_shipping_id.property_stock_customer.id
#        vals['location_id'] = location_id
#        print"rule_id",rule_id
        #Ends here
        if not sub_comp:
            vals= {
                'name': line.name,
                'origin': order.name,
                'date_planned': date_planned,
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                        or line.product_uom_qty,
                'product_uos': (line.product_uos and line.product_uos.id)\
                        or line.product_uom.id,
                #'location_id': order.shop_id.warehouse_id.lot_stock_id.id,

                'group_id': group_id,
                'location_id': location_id,
    #            'procure_method': line.type,
    #            'move_id': move_id,
                'company_id': order.company_id.id,
                'invoice_state': (order.order_policy == 'picking') and '2binvoiced' or 'none',
                'sale_line_id': line.id,
                'rule_id':rule_id,
            }
        else:
            vals =  {

                'name': line.name,
                'origin': order.name,
                'date_planned': date_planned,
                'product_id': sub_comp.product_id.id,
                'product_qty': sub_comp.qty_uom,
                'product_uom': sub_comp.uom_id.id,
                'product_uos_qty': (sub_comp.qty_uom)\
                        ,
                'product_uos': (sub_comp.uom_id and sub_comp.uom_id.id)\
                        or sub_comp.uom_id.id,
                #'location_id': order.shop_id.warehouse_id.lot_stock_id.id,

                'group_id': group_id,
                'location_id': location_id,
    #            'procure_method': line.type,
    #            'move_id': move_id,
                'company_id': order.company_id.id,
                'invoice_state': (order.order_policy == 'picking') and '2binvoiced' or 'none',
                'sale_line_id': line.id,
                'rule_id':rule_id,
            }
        routes = line.route_id and [(4, line.route_id.id)] or []
        vals['route_ids'] = routes
        vals['warehouse_id'] = order.warehouse_id and order.warehouse_id.id or False
        vals['partner_dest_id'] = order.partner_shipping_id.id
        vals['location_id'] = location_id
        return vals
    #Function Is inheited to do change location_id for Retail Store Orders
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        #Extra Code
        location_id = self.pool.get('stock.location').search(cr,uid,[('name','ilike','stock')])
        if location_id:
            location_id = location_id[0]
        if order.order_type:
            location_id = (order.location_id.id if order.location_id else location_id)
        else:
            location_id = (order.shop_id.warehouse_id.lot_stock_id.id if order.shop_id.warehouse_id else location_id)
        ##Ends Here
        output_id = order.shop_id.warehouse_id.lot_output_id.id
        return {
            'name': line.name[:250],
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
#            'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
#            'note': line.notes,
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0,
        }

    #Function is inherited because to make agreement approved as False
    def copy(self,cr,uid,ids,vals,context):
        vals.update({'agreement_approved':False,'magento_exported':False,'magento_so_id':'','magento_db_id':'','call_center_pickup':False,'tracking_no':''})
        return super(sale_order, self).copy(cr, uid, ids, vals,context=context)
    
    def onchange_partner_id(self, cr, uid, ids, part,context=None):
        print"onchange"
        val = {}
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}
        if context.get('shop_id','') and context.get('default_cox_sales_channels','') == 'call_center':
            shop = self.pool.get('sale.shop').browse(cr, uid, context.get('shop_id'))
            if shop.warehouse_id and shop.warehouse_id.lot_stock_id:
                val['location_id'] = shop.warehouse_id.lot_stock_id.id
            else:
                raise osv.except_osv(_('Error !'),_('Please specify Loction id for the Warehouse for %s'%(shop.name)))
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['delivery', 'invoice', 'contact'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        payment_term = part.property_payment_term and part.property_payment_term.id or False
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        val.update({
            'partner_invoice_id': addr['invoice'],
#            'partner_order_id': addr['contact'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'fiscal_position': fiscal_position,
            'user_id': dedicated_salesman,
            'order_policy':'prepaid',
            'agreement_approved': False #new line added to make checkbox as false
        })
        if pricelist:
            val['pricelist_id'] = pricelist
        return {'value': val}

    def create(self, cr, uid, vals, context=None):
        if context == None:
            context = {}
        if context.get('default_order_type',False):
            vals.update({'order_type':context['default_order_type']})
        return super(sale_order, self).create(cr, uid, vals, context=context)
    def get_billing_date(self,cr,uid,order_date,free_trail_days,billing_date):
        if free_trail_days > 0:
            free_trial_date = order_date + relativedelta(months = free_trail_days)
            billing_date_compare = free_trial_date
            free_trial_date = free_trial_date - relativedelta(days=1)
        else:
            free_trial_date = order_date + relativedelta(months=1)
            billing_date_compare = free_trial_date
            free_trial_date = free_trial_date - relativedelta(days=1)
        if billing_date_compare:
            if not billing_date:
                billing_date = billing_date_compare
            else:
		if isinstance(billing_date,str):
	                billing_date=datetime.strptime(billing_date, "%Y-%m-%d")
                if billing_date_compare < billing_date:
                    billing_date = billing_date_compare
                billing_date = billing_date.strftime("%Y-%m-%d")     
        print"billing_datebilling_date",billing_date
        return billing_date,free_trial_date
    def shipping_product(self,cr,uid,ids,context={}):
        product_ref = ('bista_shipping', 'product_product_shipping')
        model, product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, *product_ref)
        return product_id
    
    '''def write_selected_agreement(self, cr, uid, ids,context={}):
        if context is None:
            context = {}
        sale_id_brw = self.browse(cr,uid,ids[0])
        policy_object=self.pool.get('res.partner.policy')
        line_obj =self.pool.get('sale.order.line')
        billing_date = False
        so_name=sale_id_brw.name
        partner_id=sale_id_brw.partner_id.id
        if sale_id_brw.cox_sales_channels == 'playjam':
            return True
        order_date=datetime.strptime(str(date.today()), "%Y-%m-%d")
#        confirm_date=sale_id_brw.date_confirm
#        sales_channel = sale_id_brw.cox_sales_channels
#        if sale_id_brw.cox_sales_channels == 'ecommerce':
#           confirm_date=sale_id_brw.date_order
#        if sale_id_brw.cox_sales_channels == 'call_center':
#            confirm_date=datetime.now()
#            confirm_date = confirm_date.strftime("%Y-%m-%d")
#        print "sale_id_brw.cox_sales_channels",sale_id_brw.cox_sales_channels,confirm_date
#        order_date=datetime.strptime(confirm_date, "%Y-%m-%d")
#        print "order date......................",order_date
#        jkhkjhj
#        nextmonth = order_date + relativedelta(months=1)
#        days=calendar.monthrange(order_date.year,order_date.month)[1]
#        if order_date.day==31:
#            days=calendar.monthrange(nextmonth.year,nextmonth.month)[1]
#            nextmonth=str(nextmonth.year)+'-'+str(nextmonth.month)+'-'+str(days)
        order_lines = sale_id_brw.order_line
        active_services=policy_object.search(cr,uid,[('agmnt_partner','=',partner_id),('active_service','=',True)])
        billing_date = sale_id_brw.partner_id.billing_date
        shipping_prod_id = self.shipping_product(cr,uid,[],{})
        for order_line in order_lines:
            free_trial_date,no_recurring = '',False
            if order_line.product_id.type=='service' and order_line.product_id.id != shipping_prod_id:
		if order_line.product_id.start_date:
                   order_date=datetime.strptime(order_line.product_id.start_date, "%Y-%m-%d")
                order_line.write({'start_date':order_date})
                free_trail_days = order_line.product_id.free_trail_days
                if sales_channel == 'ecommerce':
                    free_trail_days = (order_line.free_trial_days)
		    if not free_trail_days:
                        free_trail_days = order_line.product_id.free_trail_days 	
                billing_date_fun,free_trial_date  = self.get_billing_date(cr,uid,order_date,free_trail_days,billing_date)
                if billing_date_fun:
                    billing_date = billing_date_fun
                if order_line.sub_components:
#                    changes done by yogita
                    for each_sub_com in order_line.sub_components:
                        if each_sub_com.product_id.type=='service':
                            no_recurring=each_sub_com.no_recurring
#                changes done by yogita
                    child_sol_id = line_obj.search(cr,uid,[('parent_so_line_id','=',order_line.id)])
                    for each_child_sol in line_obj.browse(cr,uid,child_sol_id):
                        if each_child_sol.product_id.type=='service':
                            if each_child_sol.product_id.recurring_service:
                                search_policy_id = policy_object.search(cr,uid,[('sale_id','=',ids[0]),('sale_line_id','=',each_child_sol.id),('sale_order','=',so_name)])
                                if not search_policy_id:
                                    vals={'sale_order':so_name,
                                        'active_service':(False if sale_id_brw.cox_sales_channels == 'call_center' else True),
                                        'product_id':each_child_sol.product_id.id,
                                        'start_date':(False if sale_id_brw.cox_sales_channels == 'call_center' else order_date),
                                        'agmnt_partner':partner_id,
                                        'sale_id':ids[0],
                                        'sale_line_id':each_child_sol.id,
                                        'free_trial_date': (False if sale_id_brw.cox_sales_channels == 'call_center' else free_trial_date),
                                        'free_trail_days':order_line.product_id.free_trail_days,
					'last_amount_charged': float(each_child_sol.price_unit) * float(each_child_sol.product_uom_qty),
                                        'no_recurring':no_recurring,
                                        'recurring_reminder':False,
                                        }
                                    policy_object.create(cr,uid,vals)
                                else:
                                    policy_object.write(cr,uid,search_policy_id,{'active_service':True,
                                    'start_date':order_date,
                                    'free_trial_date':free_trial_date,
                                    })
                else:
                    if order_line.product_id.recurring_service:
                        search_policy_id = policy_object.search(cr,uid,[('sale_id','=',ids[0]),('sale_line_id','=',order_line.id),('sale_order','=',so_name)])
                        if not search_policy_id:
                            vals={'sale_order':so_name,
                                'active_service':(False if sale_id_brw.cox_sales_channels == 'call_center' else True),
                                'product_id':order_line.product_id.id,
                                'start_date':(False if sale_id_brw.cox_sales_channels == 'call_center' else order_date),
                                'agmnt_partner':partner_id,
                                'sale_id':sale_id_brw.id,
                                'sale_line_id':int(order_line.id),
                                'free_trial_date': (False if sale_id_brw.cox_sales_channels == 'call_center' else free_trial_date),
                                'free_trail_days':order_line.product_id.free_trail_days,
				'last_amount_charged': float(order_line.price_unit) * float(order_line.product_uom_qty),
                                'no_recurring':no_recurring,
                                'recurring_reminder':False,	
                                }
                            policy_object.create(cr,uid,vals)
                        else:
                            policy_object.write(cr,uid,search_policy_id,{'active_service':True,
                            'start_date':order_date,
                            'free_trial_date':free_trial_date,
                            })
        if billing_date and ((sale_id_brw.cox_sales_channels != 'call_center') or (context.get('update'))) :
            value = "billing_date='%s'"%billing_date
            if not active_services:
                value += ",start_date='%s'"%order_date
            if value:
                if sale_id_brw.cox_sales_channels != 'amazon':
                    cr.execute('update res_partner set %s where id=%s'%(value,partner_id))
            self.calculate_extra_days(cr,uid,partner_id,billing_date)
        return True'''
    
    def write_selected_agreement(self, cr, uid, ids,context={}):
        if context is None:
            context = {}
            
        sale_id_brw = self.browse(cr,uid,ids[0])
        policy_object=self.pool.get('res.partner.policy')
        line_obj =self.pool.get('sale.order.line')
        partner_obj=self.pool.get('res.partner')
        user_auth_obj=self.pool.get('user.auth')
        billing_date = False
        so_name=sale_id_brw.name
        partner_id=sale_id_brw.partner_id.id
        confirm_date=sale_id_brw.date_confirm
        sales_channel = sale_id_brw.cox_sales_channels
        if sale_id_brw.cox_sales_channels == 'ecommerce':
           confirm_date=sale_id_brw.date_order
        if sale_id_brw.cox_sales_channels == 'call_center':
            confirm_date=datetime.now()
            confirm_date = confirm_date.strftime("%Y-%m-%d")
        if confirm_date and (' ' in confirm_date):
            confirm_date = confirm_date.split(' ')[0]
        order_date=datetime.strptime(confirm_date, "%Y-%m-%d")
        nextmonth = order_date + relativedelta(months=1)
        days=calendar.monthrange(order_date.year,order_date.month)[1]
        if order_date.day==31:
            days=calendar.monthrange(nextmonth.year,nextmonth.month)[1]
            nextmonth=str(nextmonth.year)+'-'+str(nextmonth.month)+'-'+str(days)
        order_lines = sale_id_brw.order_line
        active_services=policy_object.search(cr,uid,[('agmnt_partner','=',partner_id),('active_service','=',True)])
        if active_services:
		billing_date = sale_id_brw.partner_id.billing_date
        shipping_prod_id = self.shipping_product(cr,uid,[],{})
        for order_line in order_lines:
            free_trial_date,no_recurring,recurring_price='',False,0.0
            if order_line.product_id.type=='service' and order_line.product_id.id != shipping_prod_id:
		if order_line.product_id.start_date:
                   print"order_date",order_date
                   order_date=datetime.strptime(order_line.product_id.start_date, "%Y-%m-%d")
                order_line.write({'start_date':order_date})
                free_trail_days = order_line.product_id.free_trail_days
                if sales_channel == 'ecommerce':
                    free_trail_days = (order_line.free_trial_days)
		    if not free_trail_days:
                        free_trail_days = order_line.product_id.free_trail_days 	
                billing_date_fun,free_trial_date  = self.get_billing_date(cr,uid,order_date,free_trail_days,billing_date)
                if billing_date_fun:
                    billing_date = billing_date_fun
                if type(billing_date)==str:
                    billing_date=datetime.strptime(billing_date, "%Y-%m-%d")
                if order_line.sub_components:
#                    changes done by yogita
                    for each_sub_com in order_line.sub_components:
                        if each_sub_com.product_id.type=='service':
                            if each_sub_com.recurring_price>0.0:
                                recurring_price=each_sub_com.recurring_price
                            no_recurring=each_sub_com.no_recurring
#                changes done by yogita
                    child_sol_id = line_obj.search(cr,uid,[('parent_so_line_id','=',order_line.id)])
                    for each_child_sol in line_obj.browse(cr,uid,child_sol_id):
                        if each_child_sol.product_id.type=='service':
                            if each_child_sol.product_id.recurring_service:
                                search_policy_id = policy_object.search(cr,uid,[('sale_id','=',ids[0]),('sale_line_id','=',each_child_sol.id),('sale_order','=',so_name)])
                                if not search_policy_id:
                                    print"search_policy_id",search_policy_id
                                    vals={'sale_order':so_name,
                                       # 'active_service':(False if sale_id_brw.cox_sales_channels == 'call_center' else True),
                                        'product_id':each_child_sol.product_id.id,
                                        #'start_date':(False if sale_id_brw.cox_sales_channels == 'call_center' else order_date),
                                        'agmnt_partner':partner_id,
                                        'sale_id':ids[0],
                                        'sale_line_id':each_child_sol.id,
                                        #'free_trial_date': (False if sale_id_brw.cox_sales_channels == 'call_center' else free_trial_date),
                                        'free_trail_days':order_line.product_id.free_trail_days,
					'last_amount_charged': float(each_child_sol.price_unit) * float(each_child_sol.product_uom_qty),
                                        'no_recurring':no_recurring,
                                        'recurring_reminder':False,
                                        'recurring_price':recurring_price,
                                        }
                                    policy_object.create(cr,uid,vals)
                                else:
                                    print"eeeeelllllllllllllllseeeeeeeee"
                                    policy_object.write(cr,uid,search_policy_id,{'active_service':True,
                                    'start_date':order_date,
                                    'free_trial_date':free_trial_date,
                                    'next_billing_date':billing_date if billing_date >=free_trial_date else free_trial_date+relativedelta(days=1),
                                    })
                else:
                    
                    print"eleeeeeeeeeeeeeeeeeeeee"
                    if order_line.product_id.recurring_service:
                        search_policy_id = policy_object.search(cr,uid,[('sale_id','=',ids[0]),('sale_line_id','=',order_line.id),('sale_order','=',so_name)])
                        if not search_policy_id:
                            vals={'sale_order':so_name,
                                #'active_service':(False if sale_id_brw.cox_sales_channels == 'call_center' else True),
                                'product_id':order_line.product_id.id,
                                #'start_date':(False if sale_id_brw.cox_sales_channels == 'call_center' else order_date),
                                'agmnt_partner':partner_id,
                                'sale_id':sale_id_brw.id,
                                'sale_line_id':int(order_line.id),
                                #'free_trial_date': (False if sale_id_brw.cox_sales_channels == 'call_center' else free_trial_date),
                                'free_trail_days':order_line.product_id.free_trail_days,
				'last_amount_charged': float(order_line.price_unit) * float(order_line.product_uom_qty),
                                'no_recurring':no_recurring,
                                'recurring_reminder':False,	
                                'recurring_price':recurring_price,
                                }
                            duration=time.mktime(datetime.strptime('2020-12-31', "%Y-%m-%d").timetuple())
                            rental_resp=user_auth_obj.rental_playjam(partner_id,order_line.product_id.product_tmpl_id.app_id,duration)
#                            rental_res=ast.literal_eval(rental_resp)
                            if ast.literal_eval(str(rental_resp)).has_key('body') and ast.literal_eval(str(rental_resp)).get('body')['result'] == 4113:
                                print "rentalres---------------------",rental_resp
#                            if rental_res.has_key('body') and (rental_res.get('body')).has_key('result'):
                                vals.update({
                                'start_date':order_date,
                                'active_service':True,
                                'free_trial_date':(False if sale_id_brw.cox_sales_channels == 'call_center' else free_trial_date),
                                'next_billing_date':billing_date if billing_date >=free_trial_date else free_trial_date+relativedelta(days=1),
                                'rental_response':True,})
                                if not context:
                                    context={'update':True}
                                else:
                                    context['update']=True
                            else:
                                vals.update({'rental_response':False})
                            print"valsvalsvalsvalsvalsvalsvalsvalsvalsvalsvalsvals",vals
                            policy_object.create(cr,uid,vals)
                        else:
                            policy_object.write(cr,uid,search_policy_id,{'active_service':True,
                            'start_date':order_date,
                            'free_trial_date':free_trial_date,
                            'next_billing_date':billing_date if billing_date >=free_trial_date else free_trial_date+relativedelta(days=1),
                            })
        #if billing_date and ((sale_id_brw.cox_sales_channels != 'call_center') or (context.get('update'))) :
        print"contextttttttttttttttt",context
        if billing_date and (context.get('update')) :
            print"ifffffffffffffff"
            value = "billing_date='%s'"%billing_date
            if not active_services:
                value += ",start_date='%s'"%order_date
            if value:
                print"value",value,sale_id_brw.cox_sales_channels
                if sale_id_brw.cox_sales_channels != 'amazon':
                    print"ffffffffffffffffff"
                    result=partner_obj.write(cr,uid,partner_id,{'billing_date':billing_date})
                    print"resultttttttttttttt",result
#                    cr.execute('update res_partner set %s where id=%s'%(value,partner_id))
#                    cr.commit()
            self.calculate_extra_days(cr,uid,partner_id,billing_date)
            billing=partner_obj.browse(cr,uid,partner_id)
            print"billingbillingbillingbillingbilling",billing,billing.billing_date
            partner_obj.cal_next_billing_amount(cr,uid,partner_id)
        return True

    def calculate_extra_days(self,cr,uid,partner_id,billing_date):
        policy_obj=self.pool.get('res.partner.policy')
        cr.execute("select id "\
                   "from res_partner_policy r1 "\
                   "where free_trial_date > (select min(r2.free_trial_date) "\
                   "from res_partner_policy r2 "\
                   "where r1.agmnt_partner=r2.agmnt_partner and r2.agmnt_partner=%s and r1.free_trial_date>='%s')"%(str(partner_id),str(billing_date),))
        policy_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        for policy in policy_obj.browse(cr,uid,policy_ids):
            trial_date=policy.free_trial_date
            free_trial_date=datetime.strptime(trial_date, "%Y-%m-%d") + relativedelta(days=1)
            free_trial_date_str = free_trial_date.strftime("%Y-%m-%d")
            future_bill_date=self.get_future_bill_date(cr,uid,billing_date,free_trial_date_str)
            if type(future_bill_date)==str:
                future_bill_date=datetime.strptime(future_bill_date, "%Y-%m-%d")
            diff_days=future_bill_date-free_trial_date
            if diff_days:
                next_billing_date=future_bill_date-relativedelta(months=1)
                policy.write({'extra_days':int(diff_days.days),'next_billing_date':next_billing_date})
        return True

    def get_future_bill_date(self,cr,uid,billing_date,free_trial_date):
        if type(billing_date)==str:
            billing_date=datetime.strptime(billing_date, "%Y-%m-%d")
        if type(free_trial_date)==str:
            free_trial_date=datetime.strptime(free_trial_date, "%Y-%m-%d")
        while not (billing_date >= free_trial_date):
            billing_date = billing_date + relativedelta(months=1)
        return billing_date
        
    def order_confirm_cox(self,cr,uid,ids,context=None):
        if context is None:
            context={}
        o = self.browse(cr, uid, ids[0])
        if not o.order_line:
                raise osv.except_osv(_('Error !'),_('You cannot confirm a sale order which has no line.'))
        if not o.partner_id.emailid:
            raise osv.except_osv(_('Error !'),_('Please Enter Email Address for Customer'))
        if o.order_type and o.cox_sales_channels == 'retail':
            if not o.agreement_approved:
                raise osv.except_osv(_('Error !'),_('The Customer must accept the retail agreements before confirming the order.'))
#        if o.amount_total <= 0.0:
#            raise osv.except_osv(_('Error !'),_('Total Cannot be Zero'))
        self.compute_tax(cr, uid, ids, context=context)##Function to Get tax from the Avalara
#        self.validations_export_order(cr,uid,ids,context)
	#To check smtp permission
        '''smtp_obj = self.pool.get('email.smtpclient')
        search_smtp_ids = smtp_obj.search(cr,uid,[('pstate','=','running'),('active','=',True)])'''
#        print "search_smtp",search_smtp_ids

        ###cox gen2 stmp.client module is not needed now
#        if search_smtp_ids:
#           for each_smtp in search_smtp_ids:
#        #        smtp_obj.open_connection(cr,uid,ids,each_smtp)
#		if not smtp_obj.check_permissions(cr, uid, [each_smtp]):
#                    raise osv.except_osv(_('Permission Error!'), _('You have no permission to access SMTP Server '))
        ##########################
        context['sales_channel'] = o.cox_sales_channels
        context['sale_id'] = o.id
        context['active_model'] = 'sale.order'
        context['active_id'] = ids[0]
        context['active_ids'] = ids
        return {
            'name': ('Pre Requisites'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pre.requisites.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
             'context': context
        }

    def action_wait(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_wait(cr, uid, ids,context)
	#Extra Code
        for o in self.browse(cr, uid, ids):
            date_confirm = self.date_order_confirm(cr,uid,context)
            print"date_confirm",date_confirm
            self.write(cr, uid, [o.id], {'date_confirm': date_confirm})
        self.write_selected_agreement(cr,uid,ids,context=context)
        return True

    def action_retail_agreement(self,cr,uid,ids,context={}):
        return {
                'name':_("Retail Agreement"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'retail.agreement',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,
            }
    def action_process_deliver(self, cr, uid, ids, context=None):
            return {
                'name':_("Retail Delivery"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'retail.delivery',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,
            }

    def action_cancel(self, cr, uid, ids, context=None):
        if ids:
            if super(sale_order,self).action_cancel(cr, uid, ids, context=context):
                sale_id_obj=self.browse(cr,uid,ids[0])
                transaction_id=sale_id_obj.auth_transaction_id
                if sale_id_obj.cox_sales_channels=='ecommerce' and transaction_id:
                    authorize_obj = self.pool.get('authorize.net.config')
                    config_ids = authorize_obj.search(cr,uid,[])
                    cust_profile_id=sale_id_obj.partner_id.customer_profile_id
                    cust_payment_profile_id=sale_id_obj.customer_payment_profile_id
                    config_obj = authorize_obj.browse(cr,uid,config_ids[0])
                    api_call =authorize_obj.call(cr,uid,config_obj,'VoidTransaction',cust_profile_id,cust_payment_profile_id,transaction_id)
                    emailto = sale_id_obj.partner_id.emailid
                    self.email_to_customer(cr,uid,sale_id_obj,'sale.order','cancel_order',emailto,context)
                    referential_id_obj = sale_id_obj.shop_id.referential_id
                    try:
                        if referential_id_obj:
                            attr_conn = referential_id_obj.external_connection(True)
                            attr_conn.call('sales_order.status_change',[sale_id_obj.magento_incrementid,'canceled','canceled'])
                    except Exception, e:
                        print "Error in URLLIB",str(e)
        return True

    def paid_and_update(self, cr, uid, external_session, order_id, resource, context=None):
        wf_service = netsvc.LocalService("workflow")
        paid = self.create_external_payment(cr, uid, external_session, order_id, resource, context)
        order = self.browse(cr, uid, order_id, context=context)
        validate_order = order.workflow_process_id.validate_order
        if validate_order == 'always' or validate_order == 'if_paid' and paid:
            try:
                wf_service.trg_validate(uid, 'sale.order', order.id, 'order_confirm', cr)
                cr.execute("select invoice_id from sale_order_invoice_rel where order_id=%s"%(order.id))
                invoice_id=cr.fetchone()
                if invoice_id and invoice_id[0]:
                    wf_service.trg_validate(uid, 'account.invoice', invoice_id[0], 'invoice_open', cr)
                    self.pool.get('account.invoice').make_payment_of_invoice(cr, uid, [invoice_id[0]], context=context)
            except:
                raise
                #What we should do?? creating the order but not validating it???
                #Maybe setting a special flag can be a good solution? with a retry method?
            return True
        elif validate_order == 'if_paid' and order.payment_method_id.automatic_update:
            days_before_order_cancel = order.workflow_process_id.days_before_order_cancel or 30
            order_date = datetime.strptime(order.date_order, DEFAULT_SERVER_DATE_FORMAT)
            order_cancel_date = order_date + relativedelta(days=days_before_order_cancel)
            if order.state == 'draft' and order_cancel_date < datetime.now():
                wf_service.trg_validate(uid, 'sale.order', order.id, 'cancel', cr)
                self.write(cr, uid, order.id, {'need_to_update': False})
#                self.log(cr, uid, order.id, ("order %s canceled in OpenERP because older than %s days"
#                                     "and still not confirmed") % (order.id, days_before_order_cancel))
                #TODO eventually call a trigger to cancel the order in the external system too
                external_session.logger.info(("order %s canceled in OpenERP because older than %s days and "
                                "still not confirmed") %(order.id, days_before_order_cancel))
            else:
                self.write(cr, uid, order_id, {'need_to_update': True}, context=context)
        return False
    def calculate_month(self,cr,uid,current_dt,service_start_dt):
        date1 = datetime.strptime(str(service_start_dt), '%Y-%m-%d')
        date2 = datetime.strptime(str(current_dt), '%Y-%m-%d')
        x = (date2.year - date1.year) * 12 + date2.month - date1.month
#        r = relativedelta(date2, date1)
#        return r.months
	#print "x",x
        return x
        
    def action_invoice_merge(self, cr, uid,maerge_invoice_data, date_inv, nextmonth, service_start_date,customer_profile_id=False, context=None):
        returnval,res,invoice_lines,sale_ids,invoice_ref,invoice_vals= False,False,[],[],'',{}
    #    print "actioinv merge function",context  
	invoice = self.pool.get('account.invoice')
        policy_obj=self.pool.get('res.partner.policy')
        invoice_line_obj = self.pool.get('account.invoice.line')
        obj_sale_order_line = self.pool.get('sale.order.line')
#        service_charges = self.pool.get('service.charges')
        partner_obj = self.pool.get('res.partner')
        #prev_month = date_inv - relativedelta(months=1)
        partner_id_obj = context.get('partner_id_obj',False)
        if partner_id_obj:
            journal_ids = self.pool.get('account.journal').search(cr, uid,
                [('type', '=', 'sale'), ('company_id', '=', partner_id_obj.company_id.id)],limit=1)
         #   if service_start_date and service_start_date.day==31:
          #      days_prevmonth=calendar.monthrange(prev_month.year,prev_month.month)[1]
           #     prev_month=str(prev_month.year)+'-'+str(prev_month.month)+'-'+str(days_prevmonth)
            #    prev_month=datetime.strptime(prev_month, "%Y-%m-%d").date()
            for service_data in maerge_invoice_data:
                vals={}
#		print "service_data",service_data
                line=obj_sale_order_line.browse(cr,uid,service_data.get('line_id',False))
                product_price=line.product_id.list_price
                line_start_date=datetime.strptime(line.start_date, "%Y-%m-%d").date()
		#print"line start data",line_start_date,customer_profile_id
                order_id = line.order_id
                if not customer_profile_id:
                    customer_profile_id=order_id.customer_payment_profile_id
                unit_price = product_price
                #Newly added Code
                month_diff = self.calculate_month(cr,uid,date_inv,line_start_date)
#		print "month_difff",month_diff
                if month_diff:
#                    service_charge_id = service_charges.search(cr,uid,[('start_range_month','>=',month_diff),('end_range_month','<',month_diff),('product_id','=',line.product_id.id)])
                    cr.execute('select service_charge_amt from service_charges where product_id=%s and %s between start_range_month and end_range_month'%(line.product_id.id,int(month_diff)))
                    advance_price=cr.fetchone()
                    if advance_price and advance_price[0]:
                        unit_price = advance_price[0]
                #################
                vals = obj_sale_order_line._prepare_order_line_invoice_line_cox(cr, uid, line, False, context)
#		print "vals after prepare",vals
                if vals:
                    vals.update({'price_unit':unit_price})
                if service_data.get('extra_days', 0)>0 :
                    extra_days=service_data.get('extra_days')
                    days=366 if calendar.isleap(date_inv.year) else 365
                    partial_price=(unit_price*12/days)*int(extra_days)
                    vals.update({'price_unit':unit_price+partial_price})
                    policy_obj.write(cr,uid,service_data['policy_id'],{'extra_days':0})
                if vals:
                    if vals.get('invoice_line_tax_id'):
                        vals['invoice_line_tax_id']=[]
                    vals.update({'line_id':service_data.get('line_id',False)})
		    cr.execute('update res_partner_policy set last_amount_charged=%s where id =%s'%(unit_price,service_data.get('policy_id',False))) 	
                    invoice_lines+=[vals]
                    invoice_ref+= service_data.get('order_name','') + '|'
                    if not service_data.get('sale_id',False) in sale_ids:
                       sale_ids.append(service_data.get('sale_id',False))
            if invoice_lines:
             #   addr = partner_obj.address_get(cr, uid, [partner_id_obj.id], ['delivery', 'invoice', 'contact'])
                address = False
                com_obj = self.pool.get('res.company')
                search_company = com_obj.search(cr,uid,[])
                if search_company:
                    search_company_id = com_obj.browse(cr,uid,search_company[0])
                    address = partner_obj.address_get(cr, uid, [search_company_id.partner_id.id], ['default'])
                    if address:
                        address = address.get('default',False)
                invoice_vals.update({
                    'origin': 'RB'+ str(invoice_ref[:-1]),
                    'name': (partner_id_obj.ref if partner_id_obj.ref else invoice_ref[:-1]),
                    'type': 'out_invoice',
                    'reference': invoice_ref[:-1],
                    'account_id': partner_id_obj.property_account_receivable.id,
                    'partner_id': partner_id_obj.id,
#                    'address_invoice_id': addr.get('invoice') or addr.get('contact') or addr.get('delivery'),
#                    'address_contact_id': addr.get('contact') or addr.get('invoice') or addr.get('delivery'),
                    'journal_id': journal_ids[0],
                    'currency_id':  partner_id_obj.company_id.currency_id.id,
                    'company_id': partner_id_obj.company_id.id,
                    'date_invoice':str(date_inv),
                    'auth_transaction_id':False,
                    'authorization_code':False,
                    'customer_payment_profile_id':customer_profile_id,
                    'auth_transaction_type':'profileTransAuthCapture',
                    'cc_number':context.get('cc_number'),
                    'auth_respmsg':False,
                    'location_address_id': address,
                    'next_billing_date':str(nextmonth),
                    'recurring':True,
                })
 #               print "invoice_vals",invoice_vals 
                res=invoice.create(cr,uid,invoice_vals)
                if res:
                    for invoice_line in invoice_lines:
                        sale_line_id=invoice_line.get('line_id',False)
                        del invoice_line['line_id']
                        invoice_line.update({'invoice_id':res})
                        inv_line_id=invoice_line_obj.create(cr,uid,invoice_line,context)
                        if inv_line_id:
                            cr.execute('insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values (%s,%s)', (sale_line_id, inv_line_id))
                    context['customer_profile_id'] = partner_id_obj.customer_profile_id
                    if not context.get('giftcard',False):
                        returnval=invoice.charge_customer_recurring_or_etf(cr,uid,[res],context)
#                        gift card else part
                    else:
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'account.invoice', res, 'invoice_open', cr)
                        returnval = invoice.make_payment_of_invoice(cr, uid, [res], context=context)
                        invoice.write(cr,uid,res,{'procesesd_by':'giftcard'})
                for sale_id in sale_ids:
                    cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (sale_id, res))
            if returnval:
                if res:
                    return res
            else:
                return False
        return False
    
#Function exports sale order from OE to Magento
    def validations_export_order(self,cr,uid,ids,context):
        so_obj = self.pool.get('sale.order')
        for order_id in ids:
            sale_obj = so_obj.browse(cr,uid,order_id)
            if not sale_obj.partner_id.emailid:
                raise osv.except_osv(_('Warning!'), _('Please Enter Email ID for %s in %s'%(sale_obj.partner_id.subname,sale_obj.name)))
            elif not sale_obj.partner_id.group_id:
                raise osv.except_osv(_('Warning!'), _('Please Specify Magento Group for %s in %s'%(sale_obj.partner_id.subname,sale_obj.name)))
            elif not sale_obj.partner_id.website_id:
                raise osv.except_osv(_('Warning!'), _('Please Specify Magento Website for %s in %s'%(sale_obj.partner_id.subname,sale_obj.name)))
    

    def addr_tosearch_data(self,cr,uid,mag_cust_id,addr_brw,context):
        if addr_brw.street2:
             street = addr_brw.street+' '+ addr_brw.street2
        else:
             street  = addr_brw.street
        addr_filter = {
         'street': street,
        'city': addr_brw.city,
        'country_code': addr_brw.country_id.code,
        'state_name': addr_brw.state_id.name,
        'zip': addr_brw.zip,
        'mag_cust_id':mag_cust_id,
        'type':addr_brw.type
        }
        return addr_filter

    def customer_address(self,cr,uid,bill_brw,ship_brw,mag_cust_id,context):
        dict_add_bill,ship_add_id,bill_add_id = {},False,False
        conn = context.get('conn')
        partner_obj = self.pool.get('res.partner')
        if conn:
            addr_to_search = self.addr_tosearch_data(cr,uid,mag_cust_id,bill_brw,context)
            bill_add_id = conn.call('ol_customer.cust_address_id_exists',[addr_to_search])
            if bill_brw.id == ship_brw.id:
                dict_add_bill['is_default_shipping'] = True
                ship_add_id = bill_add_id
            else:
                addr_to_search = self.addr_tosearch_data(cr,uid,mag_cust_id,ship_brw,context)
                ship_add_id = conn.call('ol_customer.cust_address_id_exists',[addr_to_search])
            if not bill_add_id:
                region_name = (bill_brw.state_id.name if bill_brw.state_id else '')
                region_id = (bill_brw.state_id.region_id if bill_brw.state_id else '')
                billfirstname,billlastname = partner_obj.func_customer_name(bill_brw.name)
                if bill_brw.street2:
                    bill_street = bill_brw.street+'\n'+''+ bill_brw.street2
                else:
                    bill_street  = bill_brw.street
                dict_add_bill.update({'firstname': billfirstname,
                        'lastname' : billlastname,
                        'country_id' : bill_brw.country_id.code,
                        'region_name' : region_name,
                        'region_id' : region_id,
                        'company' : bill_brw.name,
                        'city'  : bill_brw.city,
                        'street' : bill_street,
                        'telephone' : bill_brw.phone,
                        'postcode': bill_brw.zip,
                        'fax': bill_brw.fax,
                        'is_default_billing':True})
                bill_add_id = conn.call('customer_address.create',[mag_cust_id,dict_add_bill])
                if bill_brw.id == ship_brw.id:
                    ship_add_id = bill_add_id
            if not ship_add_id:
                region_name_ship = (ship_brw.state_id.name if ship_brw.state_id else '')
                region_id_ship = (ship_brw.state_id.region_id if ship_brw.state_id else '')
                shipfirstname,shiplastname = partner_obj.func_customer_name(ship_brw.name)
                if ship_brw.street2:
                    ship_street = ship_brw.street+'\n'+''+ ship_brw.street2
                else:
                    ship_street  = ship_brw.street
                dict_add_ship ={'firstname': shipfirstname,
                            'lastname' : shiplastname,
                            'country_id' : ship_brw.country_id.code,
                            'region_name' : region_name_ship,
                            'region_id' : region_id_ship,
                            'company' : ship_brw.name,
                            'city'  : ship_brw.city,
                            'street' : ship_street,
                            'telephone' : ship_brw.phone,
                            'postcode': ship_brw.zip,
                            'fax': ship_brw.fax,
                            'is_default_shipping':True}
                ship_add_id = conn.call('customer_address.create',[mag_cust_id,dict_add_ship])
        return bill_add_id,ship_add_id
    def export_sale_order(self,cr,uid,ids,context):
#        shop_obj = self.pool.get('sale.shop')
        order_line_obj = self.pool.get('sale.order.line')
        partner_obj= self.pool.get('res.partner')
        so_obj = self.pool.get('sale.order')
        website_obj = self.pool.get('external.shop.group')
        product_obj = self.pool.get('product.product')
        for order_id in ids:
            dict_cust,bill_add_id,ship_add_id,customer_id,firstname,lastname,webiste_id_partner,return_data = {},False,False,False,'','',False,{}
            sale_obj = so_obj.browse(cr,uid,order_id)
            if context.get('shop_id'):
                mag_shop_brw = context.get('shop_id')
            else:
                mag_shop_brw = shop_obj.browse(cr,uid,sale_obj.shop_id.id)
            conn = mag_shop_brw.referential_id.external_connection()
            context['conn'] = conn
            customer_id = self.magento_id(cr,uid,ids,'res.partner',sale_obj.partner_id.id)
            group_id = self.magento_id(cr,uid,ids,'res.partner.category',sale_obj.partner_id.group_id.id)
            if sale_obj.partner_id.website_id:
                webiste_id_partner = website_obj.oeid_to_extid(cr, uid, sale_obj.partner_id.website_id,sale_obj.partner_id.website_id.id)#will give Website magento ID
            website_id = website_obj.search(cr,uid,[])
            if not website_id:
                website_ids = [webiste_id_partner]
            website_ids = partner_obj.get_website_magento_id(cr,uid,website_id)
            if not customer_id:
                #Get Magento Customer Id from this API call
                customer_id = conn.call('ol_customer.customerExists',[sale_obj.partner_id.emailid,website_ids,sale_obj.partner_id.name])
                if customer_id:
                    customer_id = customer_id.get('Id')
                if not customer_id:
                    name=(sale_obj.partner_id.name.lstrip().rstrip() if sale_obj.partner_id.name else '')
                    firstname,lastname = partner_obj.func_customer_name(name)
                    group_id = self.magento_id(cr,uid,ids,'res.partner.category',sale_obj.partner_id.group_id.id)
		    if sale_obj.partner_id.magento_pwd:
		    	password = sale_obj.partner_id.magento_pwd
		    else:		
	            	password=''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
                    dict_cust = {'firstname': str(firstname),
                        'lastname' : str(lastname),
                        'email'  : sale_obj.partner_id.emailid,
                        'password' :str(password),
                        'store_id' :sale_obj.shop_id.default_storeview_integer_id,
                        'website_id':webiste_id_partner,
                        'taxvat': sale_obj.partner_id.mag_vat,
                        'group_id': group_id}
                    customer_id = conn.call('customer.create',[dict_cust])
                    if customer_id:
                        cr.execute("update res_partner set magento_pwd='%s' where id=%d"%(password,sale_obj.partner_id.id))
                        return_data['new_customer'] = True
                if customer_id:
                    if (customer_id != sale_obj.partner_id.ref) or (not sale_obj.partner_id.ref):
                        cr.execute("update res_partner set ref=%s where id=%d"%(customer_id,sale_obj.partner_id.id))
                    id_val = partner_obj.extid_to_existing_oeid(cr, uid,sale_obj.shop_id.referential_id.id,customer_id,context)
                    if not id_val:
                        partner_obj.create_external_id_vals(cr,uid,sale_obj.partner_id.id,customer_id,mag_shop_brw.referential_id.id)
            if customer_id:
                bill_add_id,ship_add_id = self.customer_address(cr,uid,sale_obj.partner_invoice_id,sale_obj.partner_shipping_id,customer_id,context)
            oe_product_details = self.get_product_details(cr, uid, sale_obj.order_line,order_line_obj,customer_id)
#            print"oe_product_details",oe_product_details
            if oe_product_details.get('product_data'):
                result = self.create_order(cr, uid, ids,conn,customer_id,oe_product_details.get('product_data'),bill_add_id,ship_add_id,sale_obj,mag_shop_brw.default_storeview_integer_id,context)
                #print "mag_order_details",result
                if result.get('increment_id',False):
                    so_obj.write(cr,uid,[sale_obj.id],{'magento_exported':True,'magento_incrementid':result.get('increment_id',''),'magento_so_id':result.get('increment_id',''),'magento_db_id':result.get('db_id','')})
                    id_val = self.extid_to_existing_oeid(cr, uid,mag_shop_brw.referential_id.id,result.get('increment_id',''),context=context)
                    if not id_val:
                        self.create_external_id_vals(cr,uid,ids[0],result.get('increment_id',False),mag_shop_brw.referential_id.id)
                    ##code to update magento order item id in the sale line which is used to create shipment in the magento
                    if result.get('order_line'):
                        for each_line in result.get('order_line'):
                            product_id = product_obj.search(cr,uid,[('magento_product_id','=',each_line.get('product_id'))])
                            search_line_id = order_line_obj.search(cr,uid,[('order_id','=',order_id),('product_id','in',product_id),('price_unit','=',each_line.get('price')),('order_item_id','=',False)])
                            if search_line_id:
                                cr.execute("update sale_order_line set order_item_id=%s where id=%d"%(each_line.get('item_id'),search_line_id[0]))
                return_data['shop_brw'] = mag_shop_brw
                return_data['api_response'] = result
                return_data['service_data'] = oe_product_details.get('service_data')
        return return_data

    def magento_id(self, cr, uid,ids,model_name,res_id,context={}):
        if model_name and res_id:
            cr.execute("select name from ir_model_data where model='%s' and res_id=%d and name like '%s'"%(str(model_name),int(res_id),'%/%'))
            id = filter(None, map(lambda x:x[0], cr.fetchall()))
            if id and len(id) > 0:
               if id[0].find("/") != -1:
                   id  = id[0].split('/')[-1:]
                   return id[0]
        return False
    
    def get_product_details(self,cr,uid,line_ids,line_obj,customer_id):
        product_details,service_data,data= {},[],{}
        for line_id in line_ids:
            magento_product_id = line_id.product_id.magento_product_id    #magento product id
            order_qty = line_id.product_uom_qty                           #Operation qty
            if magento_product_id:
                product_details[str(magento_product_id)] = {'product': str(magento_product_id),
                                                        'qty' :  int(order_qty),
                                                        'price_unit': line_id.price_unit,
                                                        'price_subtotal': line_id.price_subtotal }
                if (line_id.sub_components):
                    child_sol_id= line_obj.search(cr,uid,[('parent_so_line_id','=',line_id.id)])
                    if child_sol_id:
                        for each_line in line_obj.browse(cr,uid,child_sol_id):
                            if (each_line.product_id.magento_product_id) and (each_line.product_id.recurring_service) and (each_line.product_id.type == 'service'):
                                service_data.append({'customer_id':customer_id,'product_id':each_line.product_id.magento_product_id,
                                'name':each_line.name,'description':each_line.product_id.description,'status':1,'update_date':time.strftime('%Y-%m-%d')})
                elif (line_id.product_id.recurring_service) and (line_id.product_id.type == 'service'):
                   service_data.append({'customer_id':customer_id,'product_id':magento_product_id,
                   'name':line_id.name,'description':line_id.product_id.description,'status':1,'update_date':time.strftime('%Y-%m-%d')})

        if product_details:
            data['product_data'] = product_details
        if service_data:
            data['service_data'] = service_data
        return data

#    def get_product_details(self,cr,uid,line_ids,line_obj,customer_id):
#        product_details,service_data,data= {},[],{}
#        line_obj = self.pool.get('sale.order.line')
#        for line_id in line_ids:
#            magento_product_id = line_id.product_id.magento_product_id    #magento product id
#            order_qty = line_id.product_uom_qty                           #Operation qty
#            if (line_id.product_id.type == 'service') and line_id.sub_components:
#                child_sol_id= line_obj.search(cr,uid,[('parent_so_line_id','=',line_id.id)])
#                if child_sol_id:
#                    for each_line in line_obj.browse(cr,uid,child_sol_id):
#                        if (each_line.product_id.magento_product_id) and (each_line.product_id.recurring_service) and (each_line.product_id.type == 'service'):
#                            service_data.append({'customer_id':customer_id,'product_id':each_line.product_id.magento_product_id,
#                            'name':each_line.name,'description':each_line.product_id.description,'status':1,'update_date':time.strftime('%Y-%m-%d')})
#                            if each_line.product_id.magento_product_id:
#                                product_details[str(each_line.product_id.magento_product_id)] = {'product': str(each_line.product_id.magento_product_id),
#                                'qty' :  int(order_qty),
#                                'price_unit': line_id.price_unit,
#                                'price_subtotal': line_id.price_subtotal }
#                        else:
#                            if each_line.product_id.magento_product_id:
#                                product_details[str(each_line.product_id.magento_product_id)] = {'product': str(each_line.product_id.magento_product_id),
#                                'qty' :  int(order_qty),
#                                'price_unit': line_id.price_unit,
#                                'price_subtotal': line_id.price_subtotal }
#            else:
#                if magento_product_id:
#                    product_details[str(magento_product_id)] = {'product': str(magento_product_id),
#                                'qty' :  int(order_qty),
#                                'price_unit': line_id.price_unit,
#                                'price_subtotal': line_id.price_subtotal }
#                    if (line_id.product_id.recurring_service) and (line_id.product_id.type == 'service'):
#                        service_data.append({'customer_id':customer_id,'product_id':magento_product_id,
#                        'name':line_id.name,'description':line_id.product_id.description,'status':1,'update_date':time.strftime('%Y-%m-%d')})
#        if product_details:
#            data['product_data'] = product_details
#        if service_data:
#            data['service_data'] = service_data
#        return data
    def add_shipping_charges(self,cr,uid,order_obj,shipping_method,context):
        product_id,shipping_data = False,{}
        sol_obj = self.pool.get('sale.order.line')
#        product_ref = ('base_sale_multichannels', 'product_product_shipping')
        product_ref = ('base_shipping', 'product_product_shipping')
        model, product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, *product_ref)
        if product_id:
            cr.execute("select id from sale_order_line where product_id = %s and order_id=%s",(product_id,order_obj.id))
            result = filter(None, map(lambda x:x[0], cr.fetchall()))
            if result:
                price_subtotal = sol_obj.browse(cr,uid,result[0]).price_subtotal
                if price_subtotal > 0.0:
                    shipping_data = {'shipping_method':shipping_method,'shipping_charges':price_subtotal}
        return shipping_data
    def create_order(self,cr,uid,ids,conn,mag_customer_id,oe_product_details,bill_add,ship_add,order_obj,shop_id,context):
        #NEED ALL MAGENTO IDS
        shipping_data = self.add_shipping_charges(cr,uid,order_obj,'flatrate_flatrate',context)
        payment_data = {
#        'method':'authorizenetcim',
        'method':'checkmo',
        'last_trans_id':str(order_obj.auth_transaction_id),
        'cc_last4':str(order_obj.cc_number).replace('x','').replace('X',''),
        'authorizenetcim_customer_id':str(order_obj.partner_id.customer_profile_id),
        'authorizenetcim_payment_id':str(order_obj.customer_payment_profile_id),
        'processed_amount': order_obj.amount_total,
        'cc_type':order_obj.cc_type
        }
        result = self.call_service(cr, uid, ids, conn,'sales_order.place', [mag_customer_id,oe_product_details,shop_id,bill_add,ship_add,shipping_data,payment_data,order_obj.amount_tax,order_obj.cox_sales_channels])
        return result
   
    def call_service(self,cr,uid,ids,conn,model_name,vals):
        try:
            returnid = conn.call(model_name,vals)
            return returnid
        except Exception, e:
            #print e
            if e.message != '':
                return e.message
            else:
                return e.faultString
            
    def raise_error(self,message):
        raise osv.except_osv(_('Warning!'), _('%s')%(str(message)))

    def email_to_customer(self, cr, uid, ids_obj,model,email_type,email_to,context={}):
        print"emaillllllllllllllllll",email_type
        
#        smtp_obj = self.pool.get('email.smtpclient')
        template_obj=self.pool.get('email.template')
        context.update({'email_to':email_to})
#        message_obj = self.pool.get('mail.compose.message')
#        smtpserver_id = smtp_obj.search(cr,uid,[('pstate','=','running'),('active','=',True)])
        if not email_type:
            template_search = template_obj.search(cr,uid,[('model','=',model)])
        else:
            template_search = template_obj.search(cr,uid,[('model','=',model),('email_type','=',email_type)])
        if template_search:
            print"template_search",template_search
#        template_id_obj = template_obj.browse(cr,uid,template_search[0])
            self.pool.get('email.template').send_mail(cr,uid,template_search[0],ids_obj.id,'True',False,context)
#        if smtpserver_id:
##            email_to = ['poonam.dafal@bistasolutions.com']
#            if smtpserver_id:
#                if not email_type:
#                    template_search = template_obj.search(cr,uid,[('model','=',model)])
#                else:
#                    template_search = template_obj.search(cr,uid,[('model','=',model),('email_type','=',email_type)])
#                if template_search:
#                    content,subject = '',''
#                    
#                    content = message_obj.render_template(cr, uid, template_id_obj.body_html, model, ids_obj.id)
#                    subject=message_obj.render_template(cr, uid, template_id_obj.subject, model, ids_obj.id)
#                    queue_id = smtp_obj.send_email(cr, uid, smtpserver_id[0], email_to, subject, content,[])
#                    if queue_id:
#                        result=smtp_obj._my_check_queue(cr,uid,queue_id) #function to send them imediately

# These code is added to reflect authorize_net info in sale order
    def _transform_one_resource(self, cr, uid, external_session, convertion_type, resource, mapping, mapping_id,
                     mapping_line_filter_ids=None, parent_data=None, previous_result=None, defaults=None, context=None):
        location_id = False
        exp_date=''
        if not context: context={}
        vals = super(sale_order, self)._transform_one_resource(cr, uid, external_session, convertion_type, resource,
                            mapping, mapping_id, mapping_line_filter_ids=mapping_line_filter_ids, parent_data=parent_data,
                            previous_result=previous_result, defaults=defaults, context=context)
        #To set location id for ecommerce Orders
        location_id = self.pool.get('stock.location').search(cr,uid,[('name','ilike','stock')])
        if location_id:
            location_id = location_id[0]
#        if vals.get('shop_id'):
#            warehouse_id = self.pool.get('sale.shop').browse(cr,uid,vals.get('shop_id')).warehouse_id
#            if warehouse_id:
#                if warehouse_id.lot_stock_id:
#                    location_id = warehouse_id.lot_stock_id.id
        if location_id:
            vals.update({'location_id':location_id})
	#start code Preeti
        if vals.get('shop_id') == 6:
            vals.update({'cox_sales_channels':'tru','agreement_approved':True,'magento_so_id':resource.get('increment_id',''),'magento_exported':True})
        else:
            vals.update({'cox_sales_channels':'ecommerce','agreement_approved':True,'magento_so_id':resource.get('increment_id',''),'magento_exported':True})
	#end code Preeti
        if resource.get('payment',False):
            payment_info = resource.get('payment')
            vals.update({
            'customer_payment_profile_id':payment_info.get('authorizenetcim_payment_id'),
            'customer_profile_id':payment_info.get('authorizenetcim_customer_id'),
            'auth_transaction_id':payment_info.get('last_trans_id',''),
            'cc_number':payment_info.get('cc_last4',''),
            'auth_respmsg':'This transaction has been approved.'
            })
            #if payment_info.get('method','') == 'authorizenetcim':
            if payment_info.get('authorizenetcim_customer_id'):
                    payment_profile_data = {payment_info.get('cc_last4',''):payment_info.get('authorizenetcim_payment_id')}
                    self.pool.get('res.partner').cust_profile_payment(cr,uid,vals.get('partner_id'),payment_info.get('authorizenetcim_customer_id'),payment_profile_data,exp_date,context)
		    cust_id_obj=self.pool.get('res.partner').browse(cr,uid,vals.get('partner_id'))
                    if cust_id_obj.ref:
                        mag_profile_id = external_session.connection.call('sales_order.magento_Authorize_profile',[cust_id_obj.ref,payment_info.get('authorizenetcim_customer_id')])
        #    external_session.connection.call('sales_order.process_invoice', [payment_info.get('entity_id',''),resource.get('increment_id',''),'checkmo'])

        return vals
    #Function is inherited because want to set order is complete on the magento site
#    def action_ship_end(self, cr, uid, ids, context=None):
#        print "def action_ship_enddddddddddddd"
#        res = super(sale_order, self).action_ship_end(cr, uid, ids,context)
        ##cox gen2 this code was for magento update
#        sale_id_obj = self.browse(cr,uid,ids[0])
#        if sale_id_obj.magento_incrementid:
#            referential_obj = self.pool.get('external.referential')
#            search_referential = referential_obj.search(cr,uid,[])
#            if search_referential:
#                referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
#                try:
#                    attr_conn = referential_id_obj.external_connection(True)
#                    attr_conn.call('sales_order.status_change',[sale_id_obj.magento_incrementid,'complete','complete'])
#                except Exception, e:
#                    print "error string",e
        return res
    #Function is inherited because want to pass location address in the invoice
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals['location_address_id'] = (order.location_id.partner_id.id if order.location_id.partner_id else False)
        invoice_vals['partner_id'] = (order.partner_id.id if order.partner_id else False)
        return invoice_vals
    #functionality added to create tax on shipping 
    def _add_order_extra_line(self, cr, uid, vals, option, context):
        """ Add or substract amount on order as a separate line item with single quantity for each type of amounts like :
        shipping, cash on delivery, discount, gift certificates...
        :param dict vals: values of the sale order to create
        :param option: dictionnary of option for the special field to process
        """
        if not context: context={}
        sign = option.get('sign', 1)
        if context.get('is_tax_included') and vals.get(option['price_unit_tax_included']):
            price_unit = vals.pop(option['price_unit_tax_included']) * sign
        elif vals.get(option['price_unit_tax_excluded']):
            price_unit = vals.pop(option['price_unit_tax_excluded']) * sign
        else:
            for key in ['price_unit_tax_excluded', 'price_unit_tax_included', 'tax_rate_field']:
                if option.get(key) and option[key] in vals:
                    del vals[option[key]]
            return vals #if there is not price, we have nothing to import
        model_data_obj = self.pool.get('ir.model.data')
        model, product_id = model_data_obj.get_object_reference(cr, uid, *option['product_ref'])
        product = self.pool.get('product.product').browse(cr, uid, product_id, context)
        extra_line = {
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': 1,
                        'price_unit': price_unit,
                    }
        extra_line = self.pool.get('sale.order.line').play_sale_order_line_onchange(cr, uid, extra_line, vals, vals['order_line'], context=context)
        if context.get('use_external_tax'):
            tax_rate = vals.pop(option['tax_rate_field'])
            if tax_rate:
                line_tax_id = self.pool.get('account.tax').get_tax_from_rate(cr, uid, tax_rate, context.get('is_tax_included'), context=context)
                if not line_tax_id:
                    line_tax_id = self.pool.get('account.tax').create(cr,uid,{
		       'name':'Tax '+ str(tax_rate) ,
                       'amount':tax_rate,
                        'active':True,
                        'type':'percent'
                        })
#                    raise osv.except_osv(_('Error'), _('No tax id found for the rate %s with the tax include = %s')%(tax_rate, context.get('is_tax_included')))
                extra_line['tax_id'] = [(6, 0, [line_tax_id])]
        ext_code_field = option.get('code_field')
        if ext_code_field and vals.get(ext_code_field):
            extra_line['name'] = "%s [%s]" % (extra_line['name'], vals[ext_code_field])
        vals['order_line'].append((0, 0, extra_line))
        return vals

sale_order()

class schedular_function(osv.osv):
    _name = 'schedular.function'
    def agreement_status(self,cr,uid,context={}):
#        cr.execute("select magento_incrementid from sale_order where cox_sales_channels='call_center' and agreement_approved=False and magento_incrementid is not null ")
#        increment_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        #Query has been changed for checking only for play orders
        cr.execute("select so.magento_incrementid "\
                   "from sale_order so,sale_shop sp "\
                   "where so.shop_id=sp.id and sp.name ilike '%s' and cox_sales_channels ='call_center' and agreement_approved=False and magento_incrementid is not null"%('%play%'))
        increment_ids= filter(None, map(lambda x:x[0], cr.fetchall()))
        #print "increment_ids",increment_ids
#         increment_ids = ['200000298']
        if increment_ids:
            referential_obj = self.pool.get('external.referential')
            invoice_obj = self.pool.get('account.invoice')
            sale_obj = self.pool.get('sale.order')
            ir_model_obj = self.pool.get('ir.model.data')
            search_referential = referential_obj.search(cr,uid,[])
            if search_referential:
                referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
                attr_conn = referential_id_obj.external_connection(True)
                return_val = attr_conn.call('sales_order.agreement_acceptance_check', [increment_ids])
                #print "return_val",return_val
                if return_val:
                    wf_service = netsvc.LocalService("workflow")
                    for each in return_val:
                        val = return_val.get(each,'')
                        if val == '1':
                            sale_id = sale_obj.search(cr, uid, [('magento_incrementid','=',each)])
                            if sale_id:
                                cr.execute("select invoice_id from sale_order_invoice_rel where order_id in %s", (tuple(sale_id),))
                                invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                                sale_id_obj = sale_obj.browse(cr,uid,sale_id[0])
                                partner_id_obj = sale_id_obj.partner_id
                                external_session = ExternalSession(referential_id_obj, sale_id_obj.shop_id)
                                for each_invoice in invoice_obj.browse(cr,uid,invoice_ids):
                                    try:
                                        capture_status = each_invoice.capture_status
                                        if not capture_status:
                                            capture_response = invoice_obj.capture_payment(cr,uid,[each_invoice.id],context)
                                            if capture_response:
                                                if capture_response.get('resultCode') != 'Ok':
                                                    capture_response = capture_response.get('response')
                                                    if capture_response:
                                                        if capture_response[2] in ('8','16','237','317'):
                                                            invoice_obj.action_cancel(cr,uid,[each_invoice.id],context)
                                                            sale_obj.action_cancel(cr,uid,sale_id,context)
                                                            continue
                                            #Code to make service active after accepting agreement
                                            context['update'] = True ##paremeter set in below function
                                            sale_obj.write_selected_agreement(cr,uid,[sale_id_obj.id],context)
                                            #Welcome Mail to Call Center Order Partner
                                            sale_obj.email_to_customer(cr,uid,partner_id_obj,'res.partner','welcome_email',partner_id_obj.emailid,context)
                                            ##Payment Confirmation Mail
                                            sale_obj.email_to_customer(cr,uid,sale_id_obj,'sale.order','payment_confirmation',partner_id_obj.emailid,context)
#                                        print "invoice_id_obj.state",invoice_id_obj.state
                                        if each_invoice.state == 'draft':
                                            wf_service.trg_validate(uid, 'account.invoice', each_invoice.id, 'invoice_open', cr)
                                            returnval = invoice_obj.make_payment_of_invoice(cr, uid, [each_invoice.id], context=context)
					elif each_invoice.state == 'open':
                                            returnval = invoice_obj.make_payment_of_invoice(cr, uid, [each_invoice.id], context=context)
                                        search_inv_ext_not = ir_model_obj.search(cr,uid,[('model','=','account.invoice'),('res_id','=',each_invoice.id)])
                                        sale_obj.write(cr,uid,sale_id,{'agreement_approved':True})
                                        if not search_inv_ext_not:
                                            context = {'main_lang':'en_US','lang':'en_US','active_model':'account.invoice','active_id':each_invoice.id}#this line is very important because other wise invoice doesnot gets exported
                                            invoice_obj._export_one_resource(cr, uid, external_session, each_invoice.id, context=context)
                                            increment_id = sale_id_obj.magento_so_id
                                            if increment_id:
                                                attr_conn.call('sales_order.process_invoice', ['',increment_id,'authorizenetcim'])
                                    except Exception, e:
                                        #print "error string",e
                                        invoice_obj.write(cr,uid,[each_invoice.id],{'comment':str(e)})

    ######## scheduler to activate subscription if error comes while placing SO for it.
    def rental_call_for_subscription(self,cr,uid,context={}):
        print"context;;;;;;;;;;",context
        user_auth_obj=self.pool.get('user.auth')
        policy_obj=self.pool.get('res.partner.policy')
        sale_obj=self.pool.get('sale.order')
        policy_ids=policy_obj.search(cr,uid,[('rental_response','=',False)])
        print"policy_idspolicy_idspolicy_idspolicy_idspolicy_ids",policy_ids
        if policy_ids:
            for each_policy in policy_obj.browse(cr,uid,policy_ids):
                expiry_epoch=time.mktime(datetime.strptime('2020-12-31', "%Y-%m-%d").timetuple())
                print"expiry_epochexpiry_epochexpiry_epochexpiry_epoch",expiry_epoch
                rental_response=user_auth_obj.rental_playjam(cr,uid,each_policy.agmnt_partner.id,each_policy.product_id.app_id,expiry_epoch)
                print"rental_responserental_responserental_responserental_response",rental_response
#                result=4113
                if ast.literal_eval(str(rental_response)).has_key('body') and ast.literal_eval(str(rental_response)).get('body')['result'] == 4113:
#                if result==4113:
                    print"sucessssssssssssssssssssssssss"
                    context['update']=True
                    sale_obj.write_selected_agreement(cr,uid,each_policy.sale_id,context)
            return True
        
    def recurring_billing(self,cr,uid,context={}):
        print"context",context
        self.pool.get('res.partner').recurring_billing(cr,uid,context)
    def sch_for_unprovision_list(self,cr,uid,context={}):
        self.pool.get('unprovision.customer').sch_for_unprovision_list(cr,uid,context)
    def check_new_cc(self,cr,uid,context={}):
        referential_obj = self.pool.get('external.referential')
        search_referential = referential_obj.search(cr,uid,[])
        if search_referential:
            attr_conn = False
            referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
            try:
                attr_conn = referential_id_obj.external_connection(True)
                if attr_conn:
                    #API Call for getting changed credit card information
                    return_val = attr_conn.call('sales_order.new_credit_card', [])
                    if return_val:
                        partner_obj = self.pool.get('res.partner')
			exception_obj = self.pool.get('partner.payment.error')
                        magento_profile_id = []
                        for each_val in return_val:
                            customer_id = each_val.get('customer_id')
                            payment_profile_id = each_val.get('default_payment_id')
                            if customer_id and payment_profile_id:
#                                search_partner_id = partner_obj.search(cr,uid,[('ref','=',customer_id)])
                                cr.execute("select id from res_partner where ref='%s' and create_date >= '2013-10-28'"%(customer_id))
                                search_partner_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                                if search_partner_id:
                                    active_payment_profile_id = []
                                    partner_id_brw = partner_obj.browse(cr,uid,search_partner_id[0])
                                    cust_profile_id = each_val.get('gateway_id')
                                    mag_profile_id = each_val.get('profile_id')
                                    card_no = each_val.get('card_no')
                                    if (cust_profile_id != '0') and payment_profile_id:
                                        if not (partner_id_brw.customer_profile_id) or (partner_id_brw.customer_profile_id != cust_profile_id):
                                            cr.execute("update res_partner set customer_profile_id=%s where id=%s"%(cust_profile_id,search_partner_id[0]))
                                        payment_obj = self.pool.get('custmer.payment.profile')
                                        search_payment_profile = payment_obj.search(cr,uid,[('profile_id','=',payment_profile_id),('credit_card_no','=',card_no)])
                                        magento_profile_id.append(mag_profile_id)
                                        if not search_payment_profile:
                                            create_payment = payment_obj.create(cr,uid,{'active_payment_profile':True,'profile_id':payment_profile_id,'credit_card_no':card_no,'customer_profile_id':cust_profile_id})
                                            active_payment_profile_id.append(create_payment)
                                            cr.execute("INSERT INTO partner_profile_ids \
                                                    (partner_id,profile_id) values (%s,%s)", (search_partner_id[0], create_payment))
                                        else:
                                            active_payment_profile_id.append(search_payment_profile[0])
                                        cr.execute("select profile_id from partner_profile_ids where partner_id=%s and profile_id not in %s",(search_partner_id[0],tuple(active_payment_profile_id),))
                                        in_active_payment_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                                        if in_active_payment_ids:
                                            payment_obj.write(cr,uid,in_active_payment_ids,{'active_payment_profile':False})
					exception_obj.cc_update_time_exceptions(cr,uid,search_partner_id,context)
                        if magento_profile_id:
                            if len(magento_profile_id) == 1:
                                profile_ids = str(tuple(magento_profile_id)).replace(',','')
                            else:
                                profile_ids = str(tuple(magento_profile_id))
                            if profile_ids:
                                return_val = attr_conn.call('sales_order.update_cc_status', [profile_ids])
                        ##Ends Here
                    ###API Call for checking Services Deactivated on the Magento Site or not
                    date = str(datetime.strptime(time.strftime('%Y-%m-%d'), "%Y-%m-%d")-relativedelta(days=3))
                    service_data = {'last_imported_date':date.split(' ')[0]}
                    deactived_services = attr_conn.call('sales_order.recurring_services', ['import',service_data,''])
                    if deactived_services:
                        sale_obj = self.pool.get('sale.order')
                        policy_obj = self.pool.get('res.partner.policy')
                        cancel_service = self.pool.get('cancel.service')
                        for each_service in deactived_services:
                            order_id = each_service.get('order_id')
                            product_id = each_service.get('product_id')
                            if order_id and product_id:
                                search_sale_order = sale_obj.search(cr,uid,[('magento_so_id','=',order_id)])
                                if search_sale_order:
                                    cr.execute("select id from res_partner_policy where sale_id =%d and product_id in (select id from product_product where magento_product_id=%s)"%(search_sale_order[0],product_id,))
                                    service_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                                    if service_id:
                                        for policy_brw in policy_obj.browse(cr,uid,service_id):
                                            active_service = policy_brw.active_service
                                            if active_service:
    #                                            cr.execute("update res_partner_policy set active_service=False where id=%s"%(service_id[0]))
                                                result = cancel_service.cancel_service(cr,uid,policy_brw,policy_brw.agmnt_partner.billing_date,False,context)
                        #################Ends here ################################
            except Exception, e:
                print "Error in URLLIB",str(e)
                
    
                
#    #    function to send mail to customer for expired credit card or no credit card
#    def expiry_credit_card_check(self,cr,uid,ids,context):
#        no_of_days=context.get('no_of_days')
#        now = datetime.datetime.now()
#        print "nownownownownownownownownownownow",now,context
#        sale_obj=self.pool.get('sale.order')
#        partner_obj=self.pool.get('res.partner')
#        billing_after_no_of_days=now+datetime.timedelta(days=no_of_days)
#        print "billing_after_no_of_days//////////////////",billing_after_no_of_days
#        billing_date=billing_after_no_of_days.strftime("%Y-%m-%d")
#        billing_month=billing_after_no_of_days.strftime("%Y-%m")
#        print "billing_monthbilling_month",billing_month
#        customer_id=partner_obj.search(cr,uid,[('billing_date','=',billing_date)])
#        print "customer_idcustomer_idcustomer_id",customer_id
#        if customer_id:
#            for each in customer_id:
#                partner_brw=partner_obj.browse(cr,uid,each)
#                cust_profile_id=partner_brw.customer_profile_id
#                if cust_profile_id:
#                    cr.execute("select exp_date from custmer_payment_profile where customer_profile_id='%s' and active_payment_profile=True"%(str(cust_profile_id)))
#                    payment_profile_data=cr.dictfetchall()
#                    if payment_profile_data:
#                        expiration_date=payment_profile_data[0].get('exp_date')
#                        if expiration_date<billing_month:
#                            partner_obj.write(cr,uid,each,{'comment':'Credit Card Expired'})
#                            sale_obj.email_to_customer(cr,uid,partner_brw,'res.partner','expiry_card_mail',partner_brw.emailid,context)
#                    else:
#                        partner_obj.write(cr,uid,each,{'comment':'No Credit Card'})
#                        sale_obj.email_to_customer(cr,uid,partner_brw,'res.partner','expiry_card_mail',partner_brw.emailid,context)
#                else:
#                    partner_obj.write(cr,uid,each,{'comment':'No Credit Card'})
#                    sale_obj.email_to_customer(cr,uid,partner_brw,'res.partner','expiry_card_mail',partner_brw.emailid,context)
#            return True
        
        
    def expiry_credit_card_check_14_days(self,cr,uid,context={}):
        config_obj=self.pool.get('service.configuration')
        config_ids=config_obj.search(cr,uid,[('scheduler_type','=','expiry_credit_card_check_14_days')])
        print"config_idsconfig_idsconfig_idsconfig_ids",config_ids
        if config_ids:
            no_of_days=config_obj.browse(cr,uid,config_ids[0]).no_days
        else:
            no_of_days=14
        context['no_of_days']=no_of_days
        self.pool.get('res.partner').expiry_credit_card_check(cr,uid,[],context)
        
        
    ##### schedular check expiry of credit card
    def expiry_credit_card_check_7_days(self,cr,uid,context={}):
        config_obj=self.pool.get('service.configuration')
        config_ids=config_obj.search(cr,uid,[('scheduler_type','=','expiry_credit_card_check_7_days')])
        print"config_idsconfig_idsconfig_idsconfig_ids",config_ids
        if config_ids:
            no_of_days=config_obj.browse(cr,uid,config_ids[0]).no_days
        else:
            no_of_days=7
        context['no_of_days']=no_of_days
        self.pool.get('res.partner').expiry_credit_card_check(cr,uid,[],context)
        
    ##### schedular to send mail before 10 days of billing date
    def advance_billing_notice(self,cr,uid,context={}):
        self.pool.get('res.partner').advance_billing_notice(cr,uid,[],{})
        
        
    def recurring_payment_reminder(self,cr,uid,context={}):
        so_obj = self.pool.get('sale.order')
        payment_error_obj = self.pool.get('partner.payment.error')
        search_exceptions = payment_error_obj.search(cr,uid,[('cc_update_date','=',False),('invoice_date','>=','2014-05-10'),('status','=',False),('active_payment','=',True)])
        if search_exceptions:
            today=datetime.now()
            for each_exception in payment_error_obj.browse(cr,uid,search_exceptions):
                invoice_date=datetime.strptime(each_exception.invoice_date, "%Y-%m-%d").date()
                difference= today.date()-invoice_date
                if int(difference.days) == 15:
                    so_obj.email_to_customer(cr,uid,each_exception,'partner.payment.error','payment_exception',each_exception.email_id,context)
  
    def eula_reminder(self,cr,uid,context={}):
        so_obj = self.pool.get('sale.order')
        company_obj = self.pool.get('res.company')
        search_sale_id = so_obj.search(cr,uid,[('agreement_approved','=',False),('date_order','<',time.strftime('%Y-%m-%d')),('magento_db_id','!=',''),('returns_status','=','no_returns')])
        search_company = company_obj.search(cr,uid,[])
        if search_sale_id:
            if search_company:
                eula_accpt_days = company_obj.browse(cr,uid,search_company[0]).eula_accpt_days
                if eula_accpt_days:
                    today=datetime.now()
                    for sale_id_brw in so_obj.browse(cr,uid,search_sale_id):
                        order_date=datetime.strptime(sale_id_brw.date_order, "%Y-%m-%d").date()
                        difference=today.date()-order_date
#                        if sale_id_brw.returns_status != 'no_returns':
                        if int(difference.days) == eula_accpt_days:
                            email_to = sale_id_brw.partner_id.emailid
                            so_obj.email_to_customer(cr, uid, sale_id_brw,'sale.order','eula_reminder',email_to,context)
    #added this scheduler to create delivery report for flare play
    def generate_vista_report(self,cr,uid,context={}):
        self.pool.get('vista.report').create_delivery_report(cr,uid,context)
    def cancellation_of_service(self,cr,uid,context={}):
        self.pool.get('cancel.service').cancellation_of_service(cr,uid,[],{})
    def etf_workflow(self,cr,uid,context={}):
        return_obj = self.pool.get('return.order')
        termination_fees_bj = self.pool.get('charge.termination.fee')
        today=datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        search_returns_order = return_obj.search(cr,uid,[('return_type','=','car_return'),('state','=','email_sent'),('email_send_2_week','<=',today_str)])
        cancel_refund_obj = self.pool.get('return.refund.cancellation')
 #       search_returns_order = [613]
        if search_returns_order:
            for each_return in return_obj.browse(cr,uid,search_returns_order):
                context['active_id'] = each_return.id
                context['active_ids'] = [each_return.id]
                context['active_model'] = 'return.order'
                context['called_from_schedular'] = True
                context['source'] = 'ETF Exception'
		context['return_id'] = each_return.id
		termination_fees = termination_fees_bj.get_termination_fees(cr,uid,context)
		if termination_fees > 0.0:
	                termination_wizard_id = termination_fees_bj.create(cr,uid,{},context)
	                termination_fees_bj.charge_termiation_fees(cr,uid,[int(termination_wizard_id)],context) 
		else:
                    flag = return_obj.service_product_flag(cr,uid,each_return,context)
                    if flag:
                        cancel_refund_obj.cancel_service(cr,uid,False,context)
                    else:
                        return_obj.write(cr,uid,[each_return.id],{'state':'done'})
    def charge_weekly_exceptions(self,cr,uid,context={}):
        self.pool.get('partner.payment.error').charge_weekly_exceptions(cr,uid,[],{})
    ##### scheduler to generate recurring journal entry
    def post_revenue_recognition(self,cr,uid,context={}):
        print"post_revenue_recognition"
        self.pool.get('account.invoice').post_revenue_recognition(cr,uid,[],{})
    def cancel_service_not_paid(self,cr,uid,context={}):
        self.pool.get('partner.payment.error').cancel_service_not_paid(cr,uid,[],{})
##### schedular to export partners log
    def export_auth_log(self,cr,uid,context={}):
        self.pool.get('res.partner.auth.log').export_auth_log(cr,uid,[],{})
##### schedular to set cancel date in policy for whom no_recurring is true
    def cancellation_for_no_recurring(self,cr,uid,context={}):
        self.pool.get('res.partner.policy').cancellation_for_no_recurring(cr,uid,[],{})
schedular_function()

class cancel_service(osv.osv):
    _name = 'cancel.service'
 
    #  Start code Preeti for RMA
    #  Start code Preeti for RMA
    
    def cancel_service(self,cr,uid,ids,service_id,billing_date,credit_line,context={}):
        print"cancel serviceeeeeeeeeeeeeeeeeee"
	res,main_reason,cancellation_reason = {},'',''
	return_obj= self.pool.get('return.order')
        user_auth_obj = self.pool.get('user.auth')
        return_object=return_obj.browse(cr,uid,ids[0])        
        reason_id = return_object.return_reason.id
	if context is None: context={}
        main_reason = self.pool.get('reasons.title').browse(cr,uid,reason_id).name
        if credit_line:
            service_name = credit_line.name	
        else:
            service_name = service_id.service_name
	if main_reason:
            additional_info = {'source':'COX','cancel_return_reason':main_reason}
            cancellation_reason = self.pool.get('return.order').additional_info(cr,uid,additional_info)
        if not billing_date:
            #TODO call Rental API
#             user_id=partner_id[0]
            user_id = return_object.partner_id.id
            app_id=service_id.product_id.app_id
#            app_id=108    
#                                    app_id=284
            today = date.today().strftime('%Y-%m-%d')
            cancel_time=time.strftime('%Y-%m-%d')
            print "user_id---------",user_id
            print "app_id---------",app_id
            print "expiry_epoch---------",today
            expiry_epoch=time.mktime(datetime.strptime(str(cancel_time), "%Y-%m-%d").timetuple())
            print"expiry_epochexpiry_epochexpiry_epochexpiry_epoch",expiry_epoch,type(expiry_epoch),int(expiry_epoch)
            expiry_epoch=expiry_epoch+3600.0
            print"expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1",expiry_epoch
            old_policy_result = user_auth_obj.rental_playjam(cr,uid,user_id,app_id,expiry_epoch)
            print "voucher_return----------",old_policy_result
            result=4113
#                    if ast.literal_eval(str(old_policy_result)).has_key('body') and ast.literal_eval(str(old_policy_result)).get('body')['result'] == 4113:
                #4113 is the result response value for successfull rental update
            if result==4113:
                cr.execute("update res_partner_policy set active_service=False,cancel_date=%s,no_recurring=False,additional_info=%s,return_cancel_reason=%s where id=%s",(time.strftime('%Y-%m-%d'),cancellation_reason,main_reason,service_id.id))
                res['state'] = 'done'
            return res
        
        if (context and context.get('immediate_cancel')):
            print "Context=======> ", context.get('immediate_cancel')
            cancellation_date = date.today().strftime('%Y-%m-%d')
        else:
            cancellation_date = billing_date
        if service_id.free_trial_date:
                print"hereeeeeeeeeeeeeeeee"
		if (context and context.get('refund_cancel_service')) or (time.strftime('%Y-%m-%d') >= billing_date) or (context and context.get('immediate_cancel')):
                        user_id = return_object.partner_id.id
                        app_id=service_id.product_id.app_id
                        today = date.today().strftime('%Y-%m-%d')
                        cancel_time=time.strftime('%Y-%m-%d')
                        print "user_id---------",user_id
                        print "app_id---------",app_id
                        print "expiry_epoch---------",today
#                        expiry_epoch=time.mktime(datetime.strptime(str(cancel_time), "%Y-%m-%d").timetuple())
                        expiry_epoch=time.mktime(datetime.now().timetuple())
                        print"expiry_epochexpiry_epochexpiry_epochexpiry_epoch",expiry_epoch,type(expiry_epoch),int(expiry_epoch)
                        expiry_epoch=expiry_epoch+3600.0
                        print"expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1",expiry_epoch
                        old_policy_result = user_auth_obj.rental_playjam(user_id,app_id,expiry_epoch)
                        print "voucher_return----------",old_policy_result
                        if ast.literal_eval(str(old_policy_result)).has_key('body') and ast.literal_eval(str(old_policy_result)).get('body')['result'] == 4113:
                            if (context and  (context.get('refund_cancel_service') or (context.get('active_model')=='credit.service'))) or (context and context.get('immediate_cancel')):
                                cr.execute("update res_partner_policy set active_service=False,cancel_date=%s,additional_info=%s,no_recurring=False,return_cancel_reason=%s where id=%s",(time.strftime('%Y-%m-%d'),cancellation_reason,main_reason,service_id.id))
                                return_obj.update_billing_date(cr,uid,service_id.agmnt_partner.id,billing_date,service_id.sale_line_id)
                            else:
                                if (not service_id.return_date):
                                    cr.execute("update res_partner_policy set active_service=False,return_date=%s,additional_info=%s,no_recurring=False,return_cancel_reason=%s where id=%s",(time.strftime('%Y-%m-%d'),cancellation_reason,main_reason,service_id.id))
                                    return_obj.update_billing_date(cr,uid,service_id.agmnt_partner.id,billing_date,service_id.sale_line_id)
                                    res['state'] = 'done'
                                    return_obj.update_billing_date(cr,uid,service_id.agmnt_partner.id,billing_date,service_id.sale_line_id)
			return res
            	elif service_id.free_trial_date>=billing_date or time.strftime('%Y-%m-%d')<service_id.free_trial_date:
                	free_trial_date=datetime.strptime(service_id.free_trial_date, "%Y-%m-%d")
                	cancellation_date= free_trial_date + relativedelta(days=1)
            	else:
                	cancellation_date = billing_date
                print"str(cancellation_date)",str(cancellation_date)
#                cancellation_date = datetime.strptime(str(cancellation_date), "%Y-%m-%d").date()
            	res['state'] = 'done'
        search_id = self.search(cr,uid,[('sale_id','=',service_id.sale_id),('sale_line_id','=',service_id.sale_line_id),('partner_policy_id','=',service_id.id)])
        if search_id:
                return {}
	if (not service_id.cancel_date):
	        self.create(cr,uid,{'service_name':service_name,
                'sale_id': service_id.sale_id,
                'sale_line_id': service_id.sale_line_id,
                'partner_policy_id': service_id.id,
                'cancellation_date': cancellation_date,
		'cancellation_reason': main_reason,
                'cancelled': False
                })        

                cr.execute("update res_partner_policy set cancel_date=%s,additional_info=%s,no_recurring=False,return_cancel_reason=%s where id=%s",(cancellation_date,cancellation_reason,main_reason,service_id.id))	
                res['state'] = 'done'

        return res
    

    #End code preeti for RMA
    #End code preeti for RMA
	
    def cancellation_of_service(self,cr,uid,ids,context={}):
        today=datetime.now()
        current_date = today.date()
        search_rec = self.search(cr,uid,[('cancellation_date','<=',current_date),('cancelled','=',False)])
        final_dict,service_to_cancel = {},[]
	return_obj = self.pool.get('return.order')
        user_auth_obj = self.pool.get('user.auth')
        if search_rec:
            for each_rec in self.browse(cr,uid,search_rec):
#                need_to_update_data = []
                if each_rec.sale_id and each_rec.sale_line_id:
                    user_id = each_rec.partner_policy_id.agmnt_partner.id
                    app_id= each_rec.partner_policy_id.product_id.app_id 
                    today = date.today().strftime('%Y-%m-%d')
                    cancel_time=time.strftime('%Y-%m-%d')
                    print "user_id---------",user_id
                    print "app_id---------",app_id
                    print "expiry_epoch---------",today
                    expiry_epoch=time.mktime(datetime.strptime(str(cancel_time), "%Y-%m-%d").timetuple())
                    print"expiry_epochexpiry_epochexpiry_epochexpiry_epoch",expiry_epoch,type(expiry_epoch),int(expiry_epoch)
                    expiry_epoch=expiry_epoch+3600.0
                    print"expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1",expiry_epoch
                    old_policy_result = user_auth_obj.rental_playjam(cr,uid,user_id,app_id,expiry_epoch)
                    print "voucher_return----------",old_policy_result
                    if ast.literal_eval(str(old_policy_result)).has_key('body') and ast.literal_eval(str(old_policy_result)).get('body')['result'] == 4113:
		    #Code to write cancellation data and marking service as deactive
                        additional_info = {'source':'COX','cancel_return_reason':each_rec.cancellation_reason}
                        cancellation_data = return_obj.additional_info(cr,uid,additional_info)
                        cr.execute("update res_partner_policy set active_service=False,cancel_date=%s,additional_info=%s,return_cancel_reason=%s where id=%s",(current_date,cancellation_data,each_rec.cancellation_reason,each_rec.partner_policy_id.id))
                        #  code to update billing date during cancelation of service
                        return_obj.update_billing_date(cr,uid,each_rec.partner_policy_id.agmnt_partner.id,each_rec.partner_policy_id.agmnt_partner.billing_date,each_rec.sale_line_id)
                        ######################
                        service_to_cancel.append(each_rec.id)
                    #if each_rec.sale_id.magento_so_id:
                     #   data={}
                      #  data = {'customer_id':each_rec.sale_id.partner_id.ref,
                       # 'order_id':each_rec.sale_id.magento_so_id}
                        #if 'mag' not in each_rec.sale_id.name:
                        #    data.update({'product_id': each_rec.sale_line_id.product_id.magento_product_id})
                        #if data:
                        #    need_to_update_data.append(data)
                        #if not each_rec.sale_id.shop_id.referential_id.id in final_dict.iterkeys():
                         #   final_dict[each_rec.sale_id.shop_id.referential_id.id] = need_to_update_data
                        #else:
                         #   value = final_dict[each_rec.sale_id.shop_id.referential_id.id]
                          #  new_value = value + need_to_update_data
                           # final_dict[each_rec.sale_id.shop_id.referential_id.id] = new_value
        #print "final_dict",final_dict
        if service_to_cancel:
            self.write(cr,uid,service_to_cancel,{'cancelled':True})
        ##cox gen2 this one is for magento update
#        if final_dict:
#            referential_obj = self.pool.get('external.referential')
#            for each_key in final_dict.iterkeys():
#                value = final_dict[each_key]
#                referential_id_obj = referential_obj.browse(cr,uid,each_key)
#                attr_conn = referential_id_obj.external_connection(True)
#                deactived_services = attr_conn.call('sales_order.recurring_services', ['update',value,''])
        return True

    _columns = {
    'service_name': fields.char('Service Name',size=256),
    'sale_id': fields.many2one('sale.order','Order ID'),
    'sale_line_id': fields.many2one('sale.order.line','Sale Line ID'),
    'partner_policy_id': fields.many2one('res.partner.policy','Policy ID'),
    'cancellation_date': fields.date('Cancellation Date'),
    'cancelled': fields.boolean('Cancelled'),
    'cancellation_reason': fields.text('Cancellation Reason')
    }
cancel_service()

class sub_components(osv.osv):
    _inherit = 'sub.components'
    _columns = {
        'recurring_price':fields.float('Recurring Price'),
        'no_recurring':fields.boolean('No Recurring'),
     }
##cox gen2 changes for sub_components product
    def need_procurement(self, cr, uid, ids, context=None):
        #when sale is installed only, there is no need to create procurements, that's only
        #further installed modules (sale_service, sale_stock) that will change this.
        prod_obj = self.pool.get('product.product')
        for line in self.browse(cr, uid, ids, context=context):
            if prod_obj.need_procurement(cr, uid, [line.product_id.id], context=context):
                return True
        return False
sub_components()
