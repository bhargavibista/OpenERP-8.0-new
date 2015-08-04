# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from openerp import netsvc
import time
import logging
_logger = logging.getLogger(__name__)

class return_order(osv.osv):
    _inherit = 'return.order'
    _order = 'id desc'	
  
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'shipping_info':False,
            'date_order':datetime.now(),
            'do_both_move':False,
            'receive':False,
            'incoming_exchange':False,
            'outgoing_exchange':False,
            'manual_invoice_invisible':False,
            'email_sent':False,
            'show_components':False,
            'bundle_configuration':False,
	    'carrier_tracking_ref':'',
	    'label_package_barcode':''
        })

        return super(return_order, self).copy(cr, uid, id, default, context=context)
	
    def additional_info(self,cr,uid,data):
        string = "\\'"
        final_data = str(data).replace("'",string)
        return final_data
        
    def refresh_page(self,cr,uid,ids,context=None):
        return_line_ids = self.pool.get('return.order').browse(cr,uid,ids[0]).order_line
        if return_line_ids:
            line_ids_deleted = []
            for return_line_id in return_line_ids:
                line_ids_deleted.append(return_line_id.id)
            if line_ids_deleted:
                self.pool.get('return.order.line').unlink(cr, uid, line_ids_deleted, context=context)
        self.write(cr,uid,ids,{
            'linked_sale_order':False,
            'linked_serial_no':False,
            'partner_id':False,
            'customer_name':False,
                'partner_invoice_id': False,
                'show_components': False,
                'bundle_configuration': False,
                'partner_order_id': False,
                'partner_shipping_id':False,
                'pricelist_id':False,
        'actual_linked_order':False})
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        return_orders = self.read(cr, uid, ids, ['state','name'], context=context)
        unlink_ids = []
        for s in return_orders:
            if s.get('state'):
                if s['state'] in ['draft']:
                    unlink_ids.append(s['id'])
                else:
                    raise osv.except_osv(_('Invalid action !'), _('You cannot Delete Return orders whose state is not In Draft'))
        return super(return_order, self).unlink(cr, uid, unlink_ids, context)
    #Start code Preeti for RMA
    def get_location(self,cr,uid,context={}):
        if uid:
            src_location_id = self.pool.get('res.users').browse(cr,uid,uid).src_location_id
            if src_location_id:
                return src_location_id.id
            else:
                src_location_id = self.pool.get('stock.location').search(cr,uid,[('name','ilike','Return Location')])
                if src_location_id:
                    return src_location_id[0]
        else:
            return False
    #End code Preeti for RMA
    def onchange_show_components(self,cr,uid,ids,show_components,return_order_line,return_type,linked_sale_id,context={}):
        vals,order_line_vals,tax_ids_used = {},[],[]
        if show_components and return_order_line:
            line_obj = self.pool.get('sale.order.line')
            return_line_obj = self.pool.get('return.order.line')
            for return_line in return_order_line:
                sale_line_id = False
                if return_line[1]:
                    sale_line_id = return_line_obj.browse(cr,uid,return_line[1]).sale_line_id.id
                else:
                    data = return_line[2]
                    if type(data) == dict:
                        sale_line_id = data.get('sale_line_id','')
                if sale_line_id:
                    child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',sale_line_id)])
                    for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                        tax_ids = [c.id for c in each_line.tax_id]
                        if return_type == 'exchange':
                            if (each_line.product_id.type != 'service'):
                                order_line_vals.append({'product_id':each_line.product_id.id,
                                            'name':each_line.name,
                                            'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                            'product_uom_qty':each_line.product_uom_qty,
                                            'price_unit':each_line.price_unit,
                                            'discount':each_line.discount,
                                            'tax_id':[(6, 0,tax_ids)],
                                            'state':'draft',
#                                             'type': each_line.type,  cox gen2
                                             'sale_line_id':each_line.id })
                        else:
                            order_line_vals.append({'product_id':each_line.product_id.id,
                                            'name':each_line.name,
                                            'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                            'product_uom_qty':each_line.product_uom_qty,
                                            'price_unit':each_line.price_unit,
                                            'discount':each_line.discount,
                                            'tax_id':[(6, 0,tax_ids)],
                                            'state':'draft',
#                                             'type': each_line.type, ocx gen2
                                             'sale_line_id':each_line.id })
                        tax_ids_used   = tax_ids_used + tax_ids
            if order_line_vals:
                   vals['order_line'] = order_line_vals

        else:
            if linked_sale_id:
                obj_sale_link_order = self.pool.get('sale.order').browse(cr,uid,linked_sale_id)
                for each_line in obj_sale_link_order.order_line:
                    if each_line.sub_components:
                        vals.update({'bundle_configuration': True})
                    else:
                        vals.update({'bundle_configuration': False})
                    tax_ids = [c.id for c in each_line.tax_id]
                    if return_type == 'exchange':
                        if (each_line.product_id.type != 'service'):
                            order_line_vals.append({'product_id':each_line.product_id.id,
                                        'name':each_line.name,
                                        'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                        'product_uom_qty':each_line.product_uom_qty,
                                        'price_unit':each_line.price_unit,
                                        'discount':each_line.discount,
                                        'tax_id':[(6, 0,tax_ids)],
                                        'state':'draft',
#                                         'type': each_line.type, cox gen2
                                         'sale_line_id':each_line.id })
                    else:
                        order_line_vals.append({'product_id':each_line.product_id.id,
                                        'name':each_line.name,
                                        'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                        'product_uom_qty':each_line.product_uom_qty,
                                        'price_unit':each_line.price_unit,
                                        'discount':each_line.discount,
                                        'tax_id':[(6, 0,tax_ids)],
                                        'state':'draft',
#                                         'type': each_line.type,  cox gen2
                                         'sale_line_id':each_line.id })
                    tax_ids_used   = tax_ids_used + tax_ids
                    if order_line_vals:
                           vals['order_line'] = order_line_vals
                    if not tax_ids_used:
                        vals['amount_tax'] = obj_sale_link_order.amount_tax
        return {'value':vals}
    
    def no_of_days_passed(self,cr,uid,sale_id_obj,context={}): 
	today=date.today()
        confirmed_date=datetime.strptime(sale_id_obj.date_confirm, "%Y-%m-%d").date()
        difference=today-confirmed_date
        days = difference.days	
	return days
    #Function in inherited because want to replicate tax amount
   # def onchange_sale_order(self, cr, uid, ids, linked_sale_id,serial_no,line_ids,return_type):
       #obj_sale_order = self.pool.get('sale.order')
       #line_obj = self.pool.get('sale.order.line')
       #vals,warning,message = {},{},''
      # if linked_sale_id:
          # obj_sale_link_order = obj_sale_order.browse(cr, uid, linked_sale_id)
#           today=date.today()
 #          confirmed_date=datetime.strptime(obj_sale_link_order.date_confirm, "%Y-%m-%d").date()
  #         difference=today-confirmed_date
	   #days = self.no_days_passed(cr,uid,obj_sale_link_order,{})
	  # if days <= 30:
		#message = 'This order is within policy. Early Termination Fee will be incurred if ALL hardware is not returned.'
          # if (days >= 31) and (days <= 90):
		#message = "This order was placed %s days ago and is not within the policy so this will be treated as a service cancelation. Early Termination Fee will be incurred if ALL hardware is not returned."%(days)			
	   #if days > 90 :
		#message = "This order was placed %s days ago and is not within the policy so this will be treated as a service cancelation."%(days)	
          # if message:
              # warning = {
                      # 'title': _('Warning!'),
                      # 'message': _("%s")%(message)
               #}
	   #vals['no_days_passed'] = days 
           #if return_type == 'car_return':
               #if obj_sale_link_order.returns_status == 'full_returns':
                  # warning = {
                          # 'title': _('Alert !'),
                          # 'message': _("Returns is already Processed")
                  #}
                   #vals = {'order_line':[],'linked_sale_order':False,'partner_id':False,
                   #'partner_invoice_id':False,'partner_order_id':False,'partner_shipping_id':False,'pricelist_id':False,'show_components':False,'bundle_configuration':False}
                  # return {'value': vals, 'warning': warning}
          # if return_type == 'exchange':
                #res = {}
                #if obj_sale_link_order.returns_status == 'full_returns':
                   #warning = {
                          #'title': _('Alert !'),
                          # 'message': _("Exchange of Product cannot be done because Order is Fully Returned")
                   #}
                  # vals = {'order_line':[],'linked_sale_order':False,'partner_id':False,
                   #'partner_invoice_id':False,'partner_order_id':False,'partner_shipping_id':False,'pricelist_id':False}
                   #return {'value': vals, 'warning': warning}
                #obj_stock_picking = self.pool.get('stock.picking')
               # picking_id = obj_stock_picking.search(cr,uid,[('sale_id','=',linked_sale_id)])
                #if picking_id:
		    #picking_id.sort()       
                   # state_picking = obj_stock_picking.browse(cr,uid,picking_id[0]).state
                    #if state_picking != 'done':
                      # warn_msg = _("Delivery is not yet done for the selected sale order")
                      # warning = { 'title': _('Alert!'),
                          #     'message': warn_msg }
                      # res['linked_sale_order'] = ''
                       #return {'value': res, 'warning': warning}
              #  else:
                    #warn_msg = _("Delivery is not yet done for the selected sale order")
                   # warning = { 'title': _('Alert!'),
                          # 'message': warn_msg }
                   # res['linked_sale_order'] = ''
                    #return {'value': res, 'warning': warning}
          # vals.update({'partner_id' : obj_sale_link_order.partner_id.id,
              # 'partner_invoice_id' : obj_sale_link_order.partner_invoice_id.id,
#              # 'partner_order_id' : obj_sale_link_order.partner_order_id.id,
               #'partner_shipping_id' : obj_sale_link_order.partner_shipping_id.id,
              # 'pricelist_id' : obj_sale_link_order.pricelist_id.id,
               #'payment_term' : obj_sale_link_order.payment_term.id,
               #'linked_sale_order': linked_sale_id })
          # if vals and obj_sale_link_order:
               #order_line_vals,tax_ids_used = [],[]
               #vals.update({'show_components': False})
               #for each_line in obj_sale_link_order.order_line:
                       # if each_line.sub_components:
                           #vals.update({'bundle_configuration': True})
                        #else:
                           # vals.update({'bundle_configuration': False})
                       # tax_ids = [c.id for c in each_line.tax_id]
                        #if return_type == 'exchange':
                            #if (each_line.product_id.type != 'service'):
                               # order_line_vals.append({'product_id':each_line.product_id.id,
                                            #'name':each_line.name,
                                           # 'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                            #'product_uom_qty':each_line.product_uom_qty,
                                            #'price_unit':each_line.price_unit,
                                           # 'discount':each_line.discount,
                                           # 'tax_id':[(6, 0,tax_ids)],
                                           # 'state':'draft',
                                            # 'type': each_line.type,
                                            # 'sale_line_id':each_line.id })
                            #else:
                                #child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',each_line.id)])
                                #for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                    #if (each_line.product_id.type != 'service'):
                                        #order_line_vals.append({'product_id':each_line.product_id.id,
                                                    #'name':each_line.name,
                                                   # 'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                                  #  'product_uom_qty':each_line.product_uom_qty,
                                                   # 'price_unit':each_line.price_unit,
                                                    #'discount':each_line.discount,
                                                    #'tax_id':[(6, 0,tax_ids)],
                                                  #  'state':'draft',
                                                    # 'type': each_line.type,
                                                    # 'sale_line_id':each_line.id })
                        #else:
                           # order_line_vals.append({'product_id':each_line.product_id.id,
                                          #  'name':each_line.name,
                                           # 'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                           # 'product_uom_qty':each_line.product_uom_qty,
                                           # 'price_unit':each_line.price_unit,
                                           # 'discount':each_line.discount,
                                            #'tax_id':[(6, 0,tax_ids)],
                                            #'state':'draft',
                                             #'type': each_line.type,
                                             #sale_line_id':each_line.id })
                        #tax_ids_used   = tax_ids_used + tax_ids
               #if order_line_vals:
                       #vals['order_line'] = order_line_vals
               #if not tax_ids_used:
                    #vals['amount_tax'] = obj_sale_link_order.amount_tax
          #if warning.has_key('title') and warning.has_key('message'):
               #return {'value': vals,'warning': warning}
           #else:
               #return {'value': vals}
       #else:
           #vals['order_line'] = []
           #vals['linked_sale_order'] = False
           #vals['partner_id'] = False
           #vals['partner_invoice_id'] = False
           #vals['partner_order_id'] = False
           #vals['partner_shipping_id'] = False
           #als['pricelist_id'] = False
           #return {'value': vals}
           
    #Start Code Preeti for RMA
    def onchange_partner_invoice(self,cr,uid,ids,partner_invoice):    
        vals={}            
        obj_account_invoice = self.pool.get('account.invoice')
        obj_sale_order = self.pool.get('sale.order')        
        policy_obj = self.pool.get('res.partner.policy')
        if partner_invoice:
            obj_account_invoice_link = obj_account_invoice.browse(cr, uid, partner_invoice)        
            obj_sale_order_link = obj_sale_order.search(cr, uid, [('name', '=', obj_account_invoice_link.origin)])
            sale_brw = obj_sale_order.browse(cr,uid,obj_sale_order_link[0])
            partner_id=obj_account_invoice_link.partner_id.id
            search_policy_id = policy_obj.search(cr,uid,[('sale_order','=',obj_account_invoice_link.origin),('agmnt_partner','=',partner_id)])
            vals.update({'partner_id' : obj_account_invoice_link.partner_id.id,
                   'partner_invoice_id' : sale_brw.partner_invoice_id.id,
    #               'partner_order_id' : sale_brw.partner_order_id.id,
                   'partner_shipping_id' : sale_brw.partner_shipping_id.id,
                   'pricelist_id' : sale_brw.pricelist_id.id,
                   'payment_term' : sale_brw.payment_term.id,
    #               'linked_sale_order': obj_account_invoice_link.origin 
                   })
            return {'value': vals}
        else:
            vals['partner_id'] = False
            vals['partner_invoice_id'] = False            
            vals['partner_shipping_id'] = False
            vals['pricelist_id'] = False
            vals['payment_term'] = False
            return {'value': vals}
        
    def onchange_cancel_option(self,cr,uid,ids,service_id,cancel_option,context={}):
        res={}
        res['value'] = {}
        warning,warning_mesg = {'title': _('Warning!')},''
        policy_object=self.pool.get('res.partner.policy')     
        if cancel_option == 'yes':   
            if service_id:
                policy_brw=policy_object.browse(cr,uid,service_id)
                if (policy_brw.active_service == False):
                    warning_mesg += _('Service is already cancelled for %s.'%(policy_brw.sale_order))                
                    warning = {
                    'title': _('Error!'),
                    'message' : warning_mesg
                       }
                    return {'warning':warning}
                else:
                    return True
        else:
            return True
        
    def onchange_refund_against(self,cr,uid,ids,refund_against,context={}):
        vals={}
        vals['partner_id'] = False
        vals['partner_invoice_id'] = False            
        vals['partner_shipping_id'] = False
        vals['pricelist_id'] = False
        vals['payment_term'] = False
        vals['order_line']=False
        vals['credit_option']=False
        vals['cancel_option']=False
        vals['device_option']=False
        vals['refun_type']=False
        vals['linked_sale_order']=False
        vals['service_id']=False        
        return {'value':vals}
    
    def onchange_return_type(self,cr,uid,ids,return_type,context={}):
        vals={}
        vals['partner_id'] = False
        vals['partner_invoice_id'] = False            
        vals['partner_shipping_id'] = False
        vals['pricelist_id'] = False
        vals['payment_term'] = False
        vals['order_line']=False
        vals['credit_option']=False
        vals['cancel_option']=False
        vals['device_option']=False
        vals['refun_type']=False
        vals['linked_sale_order']=False
        vals['service_id']=False
        vals['refund_against']=False
        return {'value':vals}
        
    def onchange_service_id(self,cr,uid,ids,service_id,context={}):
        res,order_line_vals={},[]
        res['value'] = {}
        vals={}
        warning,warning_mesg = {'title': _('Warning!')},''        
        policy_object=self.pool.get('res.partner.policy')        
        obj_sale_order=self.pool.get('sale.order')
        product_obj=self.pool.get('product.product')
        ext_prod_obj=self.pool.get('extra.prod.config')
        
        if service_id:
            policy_brw=policy_object.browse(cr,uid,service_id)
            linked_sale_id=policy_brw.sale_id
            obj_sale_link_order = obj_sale_order.browse(cr,uid,linked_sale_id)             
#            if (policy_object.cancel_date) and (not policy_object.active_service):
            if (policy_brw.active_service == False) and (policy_brw.cancel_date or policy_brw.return_date or policy_brw.suspension_date) :
                warning_mesg += _('Service is already cancelled for %s.'%(policy_brw.sale_order))
                vals['service_id'] = False
                vals['partner_id'] = False
                vals['partner_invoice_id'] = False            
                vals['partner_shipping_id'] = False
                vals['pricelist_id'] = False
                vals['payment_term'] = False
                vals['order_line']=False
                warning = {
                'title': _('Error!'),
                'message' : warning_mesg
                   }
#                 vals['warning']  = warning
                return {'value':vals, 'warning':warning}
            for each_line in obj_sale_link_order.order_line:
                prod_brw= product_obj.browse(cr,uid,each_line.product_id.id)                
                ext_prod_brw = ext_prod_obj.search(cr,uid,[('product_id','=',prod_brw.id)])
                if ext_prod_brw:
                    for each_prod in ext_prod_brw:
                        sub_comp=ext_prod_obj.browse(cr,uid,each_prod)   
                        prod_prod = product_obj.browse(cr,uid,sub_comp.comp_product_id.id)
                        if prod_prod.type == 'service':
                            if sub_comp.recurring_price != 0:
                                order_line_vals.append({
                                    'product_id':policy_brw.product_id.id,
                                    'name':(policy_brw.sale_order if policy_brw.sale_order else '')+'|'+(policy_brw.product_id.name if policy_brw.product_id else ''),
                                    'product_uom':(policy_brw.product_id.uom_id.id if policy_brw.product_id.uom_id.id else False),
                                    'price_unit':sub_comp.recurring_price,
                                    'copy_unit_price':sub_comp.recurring_price,
                                    'state':'draft',
                                    'product_uom_qty':1,        
                                    'type': 'make_to_stock',
                                    })
                            else:
                                order_line_vals.append({
                                    'product_id':policy_brw.product_id.id,
                                    'name':(policy_brw.sale_order if policy_brw.sale_order else '')+'|'+(policy_brw.product_id.name if policy_brw.product_id else ''),
                                    'product_uom':(policy_brw.product_id.uom_id.id if policy_brw.product_id.uom_id.id else False),
                                    'price_unit':policy_brw.product_id.list_price,
                                    'copy_unit_price':policy_brw.product_id.list_price,
                                    'state':'draft',
                                    'product_uom_qty':1,            
                                    'type': 'make_to_stock',
                                    })  
                else:
                    prod_prod = product_obj.browse(cr,uid,prod_brw.id)
                    if prod_prod.type == 'service':
                        order_line_vals.append({
                                'product_id':policy_brw.product_id.id,
                                'name':(policy_brw.sale_order if policy_brw.sale_order else '')+'|'+(policy_brw.product_id.name if policy_brw.product_id else ''),
                                'product_uom':(policy_brw.product_id.uom_id.id if policy_brw.product_id.uom_id.id else False),
                                'price_unit':policy_brw.product_id.list_price,
                                'copy_unit_price':policy_brw.product_id.list_price,
                                'state':'draft',
                                'product_uom_qty':1,            
                                'type': 'make_to_stock',
                                })  
                _logger.info("order_line_vals.....%s",order_line_vals)
                break;
            vals.update({'partner_id' : obj_sale_link_order.partner_id.id,
               'partner_invoice_id' : obj_sale_link_order.partner_invoice_id.id,
               'partner_shipping_id' : obj_sale_link_order.partner_shipping_id.id,
               'pricelist_id' : obj_sale_link_order.pricelist_id.id,
               })
            if order_line_vals:
                vals['order_line'] = order_line_vals
                return {'value': vals}
    
        else:
            vals['partner_id'] = False
            vals['partner_invoice_id'] = False            
            vals['partner_shipping_id'] = False
            vals['pricelist_id'] = False
            vals['payment_term'] = False
            vals['order_line']=False
            return {'value': vals}                
    
    def onchange_sale_order(self, cr, uid, ids,  linked_sale_id,serial_no,line_ids,return_type,context):
        obj_sale_order = self.pool.get('sale.order')
        line_obj = self.pool.get('sale.order.line')
        policy_obj = self.pool.get('res.partner.policy')
        vals,warning,message = {},{},''
        if context.has_key('r_type') and context.get('r_type'):
            if linked_sale_id:
               
               vals['order_line'] = []
               vals['linked_sale_order'] = False
               vals['partner_id'] = False
               vals['partner_invoice_id'] = False
               vals['partner_order_id'] = False
               vals['partner_shipping_id'] = False
               vals['pricelist_id'] = False
               return {'value': vals}
        if linked_sale_id:
           obj_sale_link_order = obj_sale_order.browse(cr, uid, linked_sale_id)
           partner_id=obj_sale_link_order.partner_id.id
           search_policy_id = policy_obj.search(cr,uid,[('sale_id','=',linked_sale_id),('agmnt_partner','=',partner_id),('active_service','=',True)])
           if search_policy_id:
               policy_brw=policy_obj.browse(cr,uid,search_policy_id[0])
               if return_type == "exchange":
                    if policy_brw.cancel_date or policy_brw.suspension_date or policy_brw.return_date:
                        warning = {
                                'title': _('Error !'),
                                'message': _("You Cannot Place exchange for this Sale Order since its service is already cancelled.")
                        }
                        vals = {'order_line':[],'linked_sale_order':False,'partner_id':False,
                        'partner_invoice_id':False,'partner_order_id':False,'partner_shipping_id':False,'pricelist_id':False,'show_components':False,'bundle_configuration':False}
                        return {'value': vals, 'warning': warning}
               else:
                    if policy_brw.cancel_date or policy_brw.suspension_date or policy_brw.return_date or policy_brw.active_service == False:
                        warning = {
                                'title': _('Error !'),
                                'message': _("You Cannot Place a Return for this Sale Order since its service is already cancelled or hasn't been activated.")
                        }
                        vals = {'order_line':[],'linked_sale_order':False,'partner_id':False,
                        'partner_invoice_id':False,'partner_order_id':False,'partner_shipping_id':False,'pricelist_id':False,'show_components':False,'bundle_configuration':False}
                        return {'value': vals, 'warning': warning}
#                   raise osv.except_osv(_('Error !'),_('You Cannot Place a Return for this Sale Order since its service is already cancelled.'))
           
           days = self.no_of_days_passed(cr,uid,obj_sale_link_order,{})
           
	  # if days <= 30:
	#	message = 'This order is within policy. Early Termination Fee will be incurred if ALL hardware is not returned.'
           if (days >= 31) and (days <= 90):
		message = "This order was placed %s days ago and is not within the return policy Customer will not get refund against sale order. Customer can however exchange the device."%(days)
	   if days > 90 :
		message = "This order was placed %s days ago and is not within the policy so this will be treated as a service cancellation. Customer can to get ONLY refund on subscription"%(days)	
           if message:
               warning = {
                       'title': _('Warning!'),
                       'message': _("%s")%(message)
               }
	   vals['no_days_passed'] = days 
           if return_type == 'car_return':
               if obj_sale_link_order.returns_status == 'full_returns':
                   warning = {
                           'title': _('Alert !'),
                           'message': _("Returns is already Processed")
                   }
                   vals = {'order_line':[],'linked_sale_order':False,'partner_id':False,
                   'partner_invoice_id':False,'partner_order_id':False,'partner_shipping_id':False,'pricelist_id':False,'show_components':False,'bundle_configuration':False}
                   return {'value': vals, 'warning': warning}
           if return_type == 'exchange':
                res = {}
                if obj_sale_link_order.returns_status == 'full_returns':
                   warning = {
                           'title': _('Alert !'),
                           'message': _("Exchange of Product cannot be done because Order is Fully Returned")
                   }
                   vals = {'order_line':[],'linked_sale_order':False,'partner_id':False,
                   'partner_invoice_id':False,'partner_order_id':False,'partner_shipping_id':False,'pricelist_id':False}
                   return {'value': vals, 'warning': warning}
                obj_stock_picking = self.pool.get('stock.picking')
                name = self.pool.get('sale.order').browse(cr,uid,linked_sale_id).name ##cox gen2
#                picking_id = obj_stock_picking.search(cr,uid,[('sale_id','=',linked_sale_id)])
                picking_id = obj_stock_picking.search(cr,uid,[('origin','=',name)])
                if picking_id:
		    picking_id.sort()       
                    state_picking = obj_stock_picking.browse(cr,uid,picking_id[0]).state
                    if state_picking != 'done':
                       warn_msg = _("Delivery is not yet done for the selected sale order")
                       warning = { 'title': _('Alert!'),
                               'message': warn_msg }
                       res['linked_sale_order'] = ''
                       return {'value': res, 'warning': warning}
                else:
                    warn_msg = _("Delivery is not yet done for the selected sale order")
                    warning = { 'title': _('Alert!'),
                           'message': warn_msg }
                    res['linked_sale_order'] = ''
                    return {'value': res, 'warning': warning}
           vals.update({'partner_id' : obj_sale_link_order.partner_id.id,
               'partner_invoice_id' : obj_sale_link_order.partner_invoice_id.id,
#               'partner_order_id' : obj_sale_link_order.partner_order_id.id,
               'partner_shipping_id' : obj_sale_link_order.partner_shipping_id.id,
               'pricelist_id' : obj_sale_link_order.pricelist_id.id,
               'payment_term' : obj_sale_link_order.payment_term.id,
               'linked_sale_order': linked_sale_id })
           if vals and obj_sale_link_order:
               order_line_vals,tax_ids_used = [],[]
               vals.update({'show_components': False})
               for each_line in obj_sale_link_order.order_line:
                        if each_line.sub_components:
                            vals.update({'bundle_configuration': True})
                        else:
                            vals.update({'bundle_configuration': False})
                        tax_ids = [c.id for c in each_line.tax_id]
                        if return_type == 'exchange':
                            if (each_line.product_id.type != 'service'):
                                order_line_vals.append({'product_id':each_line.product_id.id,
                                            'name':each_line.name,
                                            'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                            'product_uom_qty':each_line.product_uom_qty,
                                            'price_unit':each_line.price_unit,
                                            'copy_unit_price':each_line.price_unit,
                                            'discount':each_line.discount,
                                            'tax_id':[(6, 0,tax_ids)],
                                            'state':'draft',
#                                             'type': each_line.type, cox gen2
                                             'sale_line_id':each_line.id })
                            else:
                                child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',each_line.id)])
                                for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                    if (each_line.product_id.type != 'service'):
                                        order_line_vals.append({'product_id':each_line.product_id.id,
                                                    'name':each_line.name,
                                                    'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                                    'product_uom_qty':each_line.product_uom_qty,
                                                    'price_unit':each_line.price_unit,
                                                    'copy_unit_price':each_line.price_unit,
                                                    'discount':each_line.discount,
                                                    'tax_id':[(6, 0,tax_ids)],
                                                    'state':'draft',
#                                                     'type': each_line.type, ##cox gen2
                                                     'sale_line_id':each_line.id })
                        else:
                            order_line_vals.append({'product_id':each_line.product_id.id,
                                            'name':each_line.name,
                                            'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                            'product_uom_qty':each_line.product_uom_qty,
                                            'price_unit':each_line.price_unit,
                                            'copy_unit_price':each_line.price_unit,
                                            'discount':each_line.discount,
                                            'tax_id':[(6, 0,tax_ids)],
                                            'state':'draft',
#                                             'type': each_line.type,
                                             'sale_line_id':each_line.id })
                            
                        tax_ids_used   = tax_ids_used + tax_ids
               if order_line_vals:
                       vals['order_line'] = order_line_vals
               if not tax_ids_used:
                    vals['amount_tax'] = obj_sale_link_order.amount_tax
           if warning.has_key('title') and warning.has_key('message'):
               return {'value': vals,'warning': warning}
           else:
               return {'value': vals}
        else:
           vals['order_line'] = []
           vals['linked_sale_order'] = False
           vals['partner_id'] = False
           vals['partner_invoice_id'] = False
           vals['partner_order_id'] = False
           vals['partner_shipping_id'] = False
           vals['pricelist_id'] = False
           return {'value': vals, 'warning': warning}
    #End Code Preeti for RMA

    def create_lines(self, cr, uid, order_lines):
        lines = []
        sale_line_obj = self.pool.get('sale.order.line')
        for line in order_lines:
            if line.product_id.type != 'service':
                lines.append({
                    'qty': line.product_uom_qty,
                    'itemcode': line.product_id and line.product_id.default_code or None,
                    'description': line.name,
                    'amount': line.price_unit * (1-(line.discount or 0.0)/100.0) * line.product_uom_qty,
                    'tax_code': line.product_id and ((line.product_id.tax_code_id and line.product_id.tax_code_id.name) or
                            (line.product_id.categ_id.tax_code_id  and line.product_id.categ_id.tax_code_id.name)) or None
                })
            elif (line.product_id.type == 'service'):
                child_so_line_ids = sale_line_obj.search(cr,uid,[('parent_so_line_id','=',line.sale_line_id.id)])
                for each_line in sale_line_obj.browse(cr,uid,child_so_line_ids):
                    if each_line.product_id.type != 'service':
                        lines.append({
                                'qty': each_line.product_uom_qty,
                                'itemcode': each_line.product_id and each_line.product_id.default_code or None,
                                'description': each_line.name,
                                'amount': each_line.price_unit * each_line.product_uom_qty,
                                'tax_code': each_line.product_id and ((each_line.product_id.tax_code_id and each_line.product_id.tax_code_id.name) or
                                        (each_line.product_id.categ_id.tax_code_id  and each_line.product_id.categ_id.tax_code_id.name)) or None
                            })
        return lines
    #Start code Preeti for RMA
    def compute_tax(self, cr, uid, ids, context=None):
        avatax_config_obj = self.pool.get('account.salestax.avatax')
        account_tax_obj = self.pool.get('account.tax')
        tax_amount = 0.0
        avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid)
        return_order = self.browse(cr,uid,ids)
        if avatax_config and not avatax_config.disable_tax_calculation and \
        avatax_config.default_tax_schedule_id.id == return_order.partner_id.tax_schedule_id.id:
#            address = (return_order.source_location.partner_id if return_order.source_location.partner_id else False)
            if return_order.linked_sale_order:
		address = (return_order.linked_sale_order.location_id.partner_id if return_order.linked_sale_order.location_id.partner_id else False)
		if not address:
			raise osv.except_osv(_('Error !'),_('Please Specify Address Location for %s')%(return_order.source_location.name))
		else:
			address =  address.id
		lines = self.create_lines(cr, uid, return_order.order_line)
		if lines:

			tax_amount = account_tax_obj._check_compute_tax(cr, uid, avatax_config, return_order.date_confirm or return_order.date_order,
                                                                return_order.name, 'ReturnOrder', return_order.partner_id,address,
                                                                return_order.partner_invoice_id.id,lines,0.0, return_order.user_id,
                                                                context=context).TotalTax
            else:
                tax_amount=0.0                    
        return tax_amount
    #End code Preeti for RMA

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            flag = False
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                if line.tax_id:
                    val += self._amount_line_tax(cr, uid, line, context=context)
                    flag = True
            if not flag:
                if order.linked_sale_order.amount_tax == 0.0:
                    val = order.linked_sale_order.amount_tax
                else:
                    val = self.compute_tax(cr,uid,order.id,context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('return.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    #Start code Preeti for RMA
    def onchange_refund_type(self,cr,uid,ids,return_type,context={}):
        if return_type =='partial_refund':
            raise osv.except_osv(_('Attention !'),
                            _('Please modify unit price in return order lines to refund partial amount. If the field is invisible for you, please call support manager.'))
        return True
    #End code Preeti for RMA

    def service_deactivation(self,cr,uid,return_id_brw,context={}):
        if return_id_brw.linked_sale_order:
    #        need_to_update_data = []
            policy_obj = self.pool.get('res.partner.policy')
            search_policy_id = policy_obj.search(cr,uid,[('sale_id','=',return_id_brw.linked_sale_order.id),('active_service','=',True)])
            if search_policy_id:
                return_reason = return_id_brw.return_reason.name
                if return_reason:
		    context['cancellation_reason'] = return_reason
                    policy_id_brw = policy_obj.browse(cr,uid,search_policy_id[-1])
                    self.pool.get('cancel.service').cancel_service(cr,uid,policy_id_brw,return_id_brw.partner_id.billing_date,False,context)	

    def cancel_service(self,cr,uid,ids,context={}):
        id_brw = self.browse(cr,uid,ids[0])
        self.service_deactivation(cr,uid,id_brw,context)
	self.write(cr,uid,ids[0],{'state':'done'})
        
    def charge_termintion_fees(self,cr,uid,ids,context={}):
         return {
                    'name': ('Charge Termination Fees'),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'charge.termination.fee',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'domain': '[]',
                    'context': context,
                        }
	
#    def onchange_generate_label(self,cr,uid,ids,generate_label,context={}):
#        warning = {}
#        if generate_label:
#            warning = {
#               'title': _('Alert !'),
#               'message': _("To Generate Label,Click on 'Generate Shipping Label' Action which is on right hand side")
#               }
#        return {'warning': warning}
    _columns = {
    'return_reason': fields.many2one('reasons.title','Return Reason',readonly=True, states={'draft': [('readonly', False)]}),
    'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'return.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'return.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'return.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'return.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'return.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'return.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'delivered': fields.boolean('Delivered'),
        'carrier_tracking_ref':fields.char('Tracking Number',size=264,states={'done': [('readonly',True)]}, select=True),
	'label_package_barcode': fields.char('Label Package Barcode',size=264),
        'shipping_info':fields.text('Shipping Details'),
        'email_sent':fields.boolean('Email Sent'),
        'show_components':fields.boolean('Show Components',readonly=True, states={'draft': [('readonly', False)]}),
        'bundle_configuration':fields.boolean('Bundle Configuration'),
        'generate_label':fields.boolean('Generate Label'),
	'refund_type': fields.selection([
            ('complete_refund', 'Complete Refund'),
            ('partial_refund', 'Partial Refund')
            ], 'Refund Type',readonly=True, states={'draft': [('readonly', False)]}),
        'no_days_passed': fields.integer('Number of Days Passed'),
	'state': fields.selection([
            ('draft', 'Quotation'),
            ('waiting_date', 'Waiting Schedule'),
            ('manual', 'To Invoice'),
            ('progress', 'In Progress'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('email_sent', 'Email Sent'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
            ], 'Order State', readonly=True, help="Gives the state of the quotation or sales order. \nThe exception state is automatically set when a cancel operation occurs in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception). \nThe 'Waiting Schedule' state is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
        'email_send_2_week': fields.datetime('Email Sent Date after 2 weeks'),
	'return_option':fields.selection([('refund','Refund Generated'),('cancel_service','Service Cancelled'),('termination_charge','Termination Fee Charged')],'Return Option',readonly=True),
        #Preeti added fields below for RMA	
        'credit_option':fields.selection([
            ('yes', 'Yes'),
            ('no', 'No')
            ], 'Will the customer need refund?',states={'done': [('readonly', True)]}),
        'cancel_option':fields.selection([('yes','Yes'),('no','No')],'Does the customer want to cancel his service?',states={'done': [('readonly', True)]}),
        'device_option':fields.selection([('yes','Yes'),('no','No')],'Will the customer return device?',states={'done': [('readonly', True)]}),
        'cancel_immediately':fields.selection([('yes','Yes'),('no','No')],'Does the customer want to cancel his service immediately?',states={'done': [('readonly', True)]}),
        'partner_invoice':fields.many2one('account.invoice','Refund against Invoice',states={'done': [('readonly', True)]}),
        'cancellation_type':fields.selection([('credits','Credits Only'),('cancel','Cancel Only'),('credits_cancel','Credit and Cancel'),('cancel_immediately','Cancel Immediately')],'Cancellation Type',states={'done': [('readonly', True)]}),        
        'refund_option':fields.selection([('sale_order','Sale Order'),('customer_invoice','Customer Invoice')],'Refund against?',states={'done': [('readonly', True)]}),
        'service_id':fields.many2one('res.partner.policy','Active Service',states={'done': [('readonly', True)]}),        
        'refund_against':fields.selection([
            ('sale_order', 'Sale Order'),
            ('subscription', 'Subscription')
            ], 'Refund Against?',states={'done': [('readonly', True)]}),
    }
    _defaults = {
    'source_location': get_location,
    'delivered':False,
    #RMA Fields    
    'return_type':'',    
    'credit_option':'',
    'cancel_option':'',
    'device_option':'',
    'generate_label':True    
    }
    def check_return_line_qty(self,cr,uid,ids,context={}):
        if ids:
            id_obj = self.browse(cr,uid,ids[0])
            line_obj = self.pool.get('sale.order.line')
            for return_line in id_obj.order_line:
                if (return_line.sale_line_id) and (return_line.product_id.type != 'service'):
#                    cr.execute("select product_qty from stock_move where sale_line_id=%d and state!='done'"%(return_line.sale_line_id.id))
                    cr.execute("select product_qty from stock_move where  state != 'done' and procurement_id in (select id from procurement_order where sale_line_id = '%s')" %(return_line.sale_line_id.id)) ##cox gen2
                    move_qty = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if move_qty:
                        if return_line.product_uom_qty > move_qty[0]:
                            raise osv.except_osv(_('Warning!'),_('Please Change Quantity for %s because you cannot return more quantity than delivered quantity'%(return_line.product_id.name)))
                elif (return_line.sale_line_id) and (return_line.product_id.type == 'service'):
                    if return_line.product_uom_qty > return_line.sale_line_id.product_uom_qty:
                        raise osv.except_osv(_('Warning!'),_('Please Change Quantity for %s because you cannot return more quantity than delivered quantity'%(return_line.product_id.name)))
                    if return_line.sale_line_id.sub_components:
                        child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',return_line.sale_line_id.id)])
                        for each_line in child_so_line_ids:
#                            cr.execute("select product_qty from stock_move where sale_line_id=%d and state!='done'"%(each_line))
                            cr.execute("select product_qty from stock_move where state != 'done' and procurement_id in (select id from procurement_order where sale_line_id = '%s')"%(each_line))
                            move_qty = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if move_qty:
                                if return_line.product_uom_qty > move_qty[0]:
                                    raise osv.except_osv(_('Warning!'),_('Please Change Quantity for %s because you cannot return more quantity than delivered quantity'%(return_line.product_id.name)))
    def flow_option_based_on_days(self,cr,uid,no_days_passed,context={}):
        return_id,return_id_brw = False,False
        if context and context.get('return_id',False):
            return_id= context.get('return_id',False)
	    return_id_brw = self.pool.get('return.order').browse(cr,uid,return_id)
        if return_id and return_id_brw:	
	        if (no_days_passed >= 0) and (no_days_passed <= 30):
	            id = self.pool.get('return.refund.cancellation').create(cr,uid,{'refund_cancel':'refund','return_id':return_id})
		    if not return_id_brw.manual_invoice_invisible:	
	        	    return {
        	        	    'name':_("Payment Finalization"),
	        	            'view_type': 'form',
        	        	    'view_mode': 'form',
		                    'res_id': id,
        		            'res_model': 'return.refund.cancellation',
		                    'type': 'ir.actions.act_window',
	       		            'nodestroy': True,
		                    'target': 'new',
        		            }
	        elif (no_days_passed >30):
                    flag = self.service_product_flag(cr,uid,return_id_brw,context)
                    if flag:
                        id = self.pool.get('return.refund.cancellation').create(cr,uid,{'refund_cancel':'cancel','return_id':return_id})
                        return {
        	        'name':_("Service Cancellation"),
	                'view_type': 'form',
        	        'view_mode': 'form',
	                'res_id': id,
        	        'res_model': 'return.refund.cancellation',
	                'type': 'ir.actions.act_window',
        	        'nodestroy': True,
	                'target': 'new',
        	        }
                self.pool.get('return.order').write(cr,uid,[return_id],{'state':'done'})
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': return_id,
                    'res_model': 'return.order',
                    'type': 'ir.actions.act_window',
                    'context':context
                }
    def service_product_flag(self,cr,uid,return_id_brw,context={}):
        flag = False
        for each_line in return_id_brw.order_line:
            if each_line.product_id.type =='service':
                flag = True
        return flag
    #Start code Preeti for RMA
    def return_confirm(self,cr,uid,ids,context=None):
        return_obj = self.browse(cr,uid,ids[0])
        linked_order = return_obj.linked_sale_order
        if linked_order:
            duplicate_return = self.search(cr,uid,[('linked_sale_order','=',linked_order.id),('state','in',('progress','done')),('id','not in',ids)])
            if duplicate_return:
                raise osv.except_osv(_('Warning!'),_('Returns is Already Processed for %s')%(linked_order.name))
            self.check_return_line_qty(cr,uid,ids,context)
            if return_obj.amount_total > linked_order.amount_total:
                raise osv.except_osv(_('Warning!'),_('Total Of Return Order Cannot Be Greater than %s Total')%(linked_order.name))
            if not return_obj.receive:
                delivered = linked_order.shipped
#                End code Preeti for RMA flow
		context['active_id'] = return_obj.id
                context['active_ids'] = [return_obj.id]
                context['active_model'] = 'return.order'
                wizard_id = self.pool.get('receive.goods').create(cr,uid,{'received':delivered})
                return {
                        'name': ('Receiving Of Goods'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'receive.goods',
                        'view_id': False,
                        'res_id' : wizard_id,
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                         'context': context
                    }
            else:
                no_days_passed = return_obj.no_days_passed
                context['return_id'] = return_obj.id
                return_data = self.flow_option_based_on_days(cr,uid,no_days_passed,context)
                if return_data:
                    return return_data
    #End code Preeti for RMA
    def receive_confirm(self,cr,uid,ids,context=None):
        return_obj = self.browse(cr,uid,ids[0])
        linked_order = return_obj.linked_sale_order
        if linked_order:
            self.check_return_line_qty(cr,uid,ids,context)
	    delivered = linked_order.shipped
            wizard_id = self.pool.get('receive.goods').create(cr,uid,{'received':delivered})
	    context['active_id'] = ids[0]
            context['active_ids'] = ids
            context['active_model'] = 'return.order'	
            return {
                    'name': ('Receiving Of Goods'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'receive.goods',
                    'res_id':wizard_id,
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                     'context': context
                }
    def deactivate_service(self,cr,uid,return_obj,sale_line_id_obj):
        return_reason = return_obj.return_reason.name
        if return_reason:
            additional_info = {'source':'COX','cancel_return_reason':return_reason}
            return_reason = self.pool.get('return.order').additional_info(cr,uid,additional_info)
        cr.execute("update res_partner_policy set active_service=False,cancel_date=%s,additional_info=%s,no_recurring=False where sale_line_id=%s",(time.strftime('%Y-%m-%d'),return_reason,sale_line_id_obj.id))
        need_to_update_data = []
        self.update_billing_date(cr,uid,return_obj.partner_id.id,return_obj.partner_id.billing_date,sale_line_id_obj.id)
        if return_obj.linked_sale_order.magento_so_id:
		data = {'customer_id':return_obj.partner_id.ref,
	            'order_id':return_obj.linked_sale_order.magento_so_id}
		if 'mag' not in return_obj.linked_sale_order.name:
                	data.update({'product_id': sale_line_id_obj.product_id.magento_product_id})
		need_to_update_data.append(data)
        return need_to_update_data
    
    #this function is added to update billing date at the time of returns
    def update_billing_date(self,cr,uid,partner_id,billing_date,sale_line_id):
#        cr.execute("select id from res_partner_policy where agmnt_partner='%s' and active_service=True and free_trial_date > '%s' and cancel_date is null"%(str(partner_id),str(billing_date),))
        cr.execute("select id from res_partner_policy where agmnt_partner='%s' and active_service=True and cancel_date is null"%(str(partner_id)))
        cancelation_req_date=time.strftime('%Y-%m-%d')
        cancelation_req_date=datetime.strptime(cancelation_req_date, "%Y-%m-%d")
        policy_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        policy_obj=self.pool.get('res.partner.policy')
        partner_obj=self.pool.get('res.partner')
        sale_order_obj=self.pool.get('sale.order')
        billing_date=datetime.strptime(billing_date,'%Y-%m-%d')
        if policy_ids and len(policy_ids)==1:
            policy_brw=policy_obj.browse(cr,uid,policy_ids[0])
            free_trial_date=policy_brw.free_trial_date
            if free_trial_date:
                free_trial_date=datetime.strptime(free_trial_date,'%Y-%m-%d')
                new_billing_date=free_trial_date + relativedelta(days=1)
                if new_billing_date<cancelation_req_date:
                    new_billing_date=billing_date+relativedelta(months=1)
                if new_billing_date>billing_date and new_billing_date>cancelation_req_date:
                    new_billing_date=free_trial_date + relativedelta(days=1)
                    policy_brw.write({'extra_days':0,'next_billing_date':new_billing_date})
                else:
                    new_billing_date=billing_date
                partner_obj.write(cr,uid,partner_id,{'billing_date':new_billing_date})
                #policy_brw.write({'extra_days':0})
        elif len(policy_ids) > 1:
            cr.execute("select min(free_trial_date) from res_partner_policy where id in %s"%(tuple(policy_ids),))
            min_free_trial_date = cr.fetchone()
            if min_free_trial_date and min_free_trial_date[0]:
                min_free_trial_date = datetime.strptime(min_free_trial_date[0],'%Y-%m-%d')
                new_billing_date = min_free_trial_date + relativedelta(days=1)
                if new_billing_date>billing_date or cancelation_req_date<min_free_trial_date:
                    new_billing_date=min_free_trial_date + relativedelta(days=1)
                else:
                    new_billing_date=billing_date
                if new_billing_date<cancelation_req_date:
                    new_billing_date=billing_date+relativedelta(months=1)
                partner_obj.write(cr,uid,partner_id,{'billing_date':new_billing_date})
                for policy in policy_obj.browse(cr,uid,policy_ids):
                    free_trial_date = datetime.strptime(policy.free_trial_date,'%Y-%m-%d') #assuming free trials is gonna written in every case, son no exception handling here
                    free_trail_date1 = free_trial_date + relativedelta(days=1)
                    if free_trail_date1 == new_billing_date:
                       policy.write({'extra_days':0,'next_billing_date':new_billing_date})
                    elif free_trail_date1 >new_billing_date:
                        future_date = sale_order_obj.get_future_bill_date(cr,uid,new_billing_date,free_trail_date1)
                        diff = future_date-free_trail_date1
                        if diff:
                            policy.write({'extra_days':int(diff.days),'next_billing_date':new_billing_date})
        partner_obj.cal_next_billing_amount(cr,uid,partner_id)
        return True
    #Function is inherited because want to make entry in the return_order_line and sale_order_line
    def manual_invoice_return(self,cr,uid,ids,context={}):
	type_return=''	
        if context is None:
            context={}
        return_obj = self.browse(cr,uid,ids[0])
        invoice_obj = self.pool.get('account.invoice')
        if not return_obj.order_line:
            raise osv.except_osv(_('Error!'),  _('Please Insert Return Order lines'))
        linked_order=return_obj.linked_sale_order
        need_to_update_data = []
        if linked_order:
            self.check_return_line_qty(cr,uid,ids,context)
            if return_obj.amount_total > linked_order.amount_total:
                raise osv.except_osv(_('Warning!'),_('Total Of Return Order Cannot Be Greater than %s Total')%(linked_order.name))
            if linked_order.auth_transaction_id:
                context['auth_transaction_id'] = linked_order.auth_transaction_id
                context['cc_number'] = linked_order.cc_number
                return {
                'name': ('Refund Payment'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'refund.customer.payment',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                 'context': context
            }
            else:
                cr.execute("select id from account_invoice where (recurring=False or recurring is Null) and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple([return_obj.linked_sale_order.id]),))
                invoice_id = cr.fetchone()
                if invoice_id:
                    state =invoice_obj.browse(cr,uid,invoice_id[0]).state
                    if state =='draft':
                        invoice_obj.action_cancel(cr,uid,[invoice_id[0]],context)
                    else:
                        journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
                        refund_invoice_id = invoice_obj.create(cr,uid,
                                    {'partner_id':return_obj.partner_id.id,
#                                    'address_invoice_id':return_obj.partner_invoice_id.id,
                                    'currency_id':return_obj.pricelist_id.currency_id.id,
                                    'account_id':return_obj.partner_id.property_account_receivable.id,
                                    'name':return_obj.name,
#                                    'address_contact_id':return_obj.partner_shipping_id.id,
                                    'user_id':uid,
                                    'journal_id':journal_id[0],
                                    'type':'out_refund',
                                    'return_id':ids[0],
                                    'origin':return_obj.name,
                                    'location_address_id': return_obj.linked_sale_order.location_id.partner_id.id,
	                            'return_ref':return_obj.name+'/Credit_Return'
                        })
                        acc_invoice_line_obj = self.pool.get('account.invoice.line')
                        for each_order_line in return_obj.order_line:
                            if each_order_line.account_id:
                                account_id = each_order_line.account_id.id
                            else:
                                if each_order_line.product_id.property_account_income.id:
                                    account_id = each_order_line.product_id.property_account_income.id
                                else:
                                    account_id = each_order_line.product_id.categ_id.property_account_income_categ.id
                            account_invoice_line = acc_invoice_line_obj.create(cr,uid,
                            {'product_id':each_order_line.product_id.id,
                             'name':each_order_line.name,
                             'quantity':each_order_line.product_uom_qty,
                             'price_unit':each_order_line.price_unit,
                             'uos_id':each_order_line.product_uom.id,
                             'account_id':account_id,
                             'discount':each_order_line.discount,
                             'invoice_id':refund_invoice_id,
                             'origin': return_obj.name,
                             'invoice_line_tax_id': [(6, 0, [x.id for x in each_order_line.tax_id])],
                            'note': each_order_line.notes,
                            })
                            #insert into return_order_line_invoice_rel
                            cr.execute("insert into return_order_line_invoice_rel (order_line_id,invoice_id) values(%s,%s)",(each_order_line.id,account_invoice_line))
                            #insert into sale_order_line_invoice_rel
                            cr.execute("insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values(%s,%s)",(each_order_line.sale_line_id.id,account_invoice_line))
                        if refund_invoice_id:
                            cr.execute("insert into return_order_invoice_rel (order_id,invoice_id) values(%s,%s)",(return_obj.id,refund_invoice_id))
                            netsvc.LocalService("workflow").trg_validate(uid, 'account.invoice', refund_invoice_id, 'invoice_open', cr)
                            invoice_obj.make_payment_of_invoice(cr, uid, [refund_invoice_id], context=context)
                            #To write refund_generated as True in main Recurring invoice
                            cr.execute("update account_invoice set refund_generated=True where id=%s"%(invoice_id[0]))
                email_to = return_obj.partner_id.emailid
                self.pool.get('sale.order').email_to_customer(cr, uid, return_obj,'return.order','return_confirmation',email_to,context)
                ###Code to Change Delivery Qty
                cr.execute("select id from stock_picking where sale_id=%d and state != 'done'"%(return_obj.linked_sale_order.id))
                picking_id=filter(None, map(lambda x:x[0], cr.fetchall()))
                if picking_id:
                    self.change_delivery_qty(cr,uid,[return_obj.id],context)
                return_lines=return_obj.order_line
                line_obj = self.pool.get('sale.order.line')
                for returns in return_lines:
                    if returns.sale_line_id:
                        if returns.sale_line_id.product_id.id== returns.product_id.id and  returns.sale_line_id.product_uom_qty==returns.product_uom_qty and returns.product_id.type=='service':
                            if returns.sale_line_id.sub_components:
                                child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',returns.sale_line_id.id)])
                                for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                    if (each_line.product_id.type == 'service') and (each_line.product_id.recurring_service):
                                        need_to_update_data += self.deactivate_service(cr,uid,return_obj,each_line)
                            else:
                                need_to_update_data += self.deactivate_service(cr,uid,return_obj,returns.sale_line_id)
                if return_obj.receive:
                    state = 'done'
		    type_return='refund'
                else:
                    state = 'progress'
                self.write(cr,uid,[return_obj.id],{'manual_invoice_invisible': True,'state':state,'return_option':type_return},context)
                return True
    def change_delivery_qty(self,cr,uid,ids,context={}):
        so_line_ids = []
        cr.execute("select sale_line_id from return_order_line where order_id=%s"%(ids[0]))
        parent_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if parent_line_id:
            so_line_ids += parent_line_id
            cr.execute("select id from sale_order_line where parent_so_line_id in %s", (tuple(parent_line_id),))
            child_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
            if child_line_id:
                so_line_ids += child_line_id
#        cr.execute("select id,sale_line_id,product_qty from stock_move where sale_line_id in (select sale_line_id from return_order_line where order_id=%s) order by id desc"%(ids[0]))
        cr.execute("select id,sale_line_id,product_qty from stock_move where sale_line_id in %s order by id desc", (tuple(so_line_ids),))
        stock_mv_data = cr.dictfetchall()
        move_obj = self.pool.get('stock.move')
        id_obj = self.browse(cr,uid,ids[0])
        delivered_qty = 0.0
        existing_return = self.search(cr,uid,[('linked_sale_order','=',id_obj.linked_sale_order.id),('state','in',('progress','done')),('id','not in',ids)])
        if stock_mv_data:
            for each_move in stock_mv_data:
                if each_move.get('id'):
                    move_id_obj = move_obj.browse(cr,uid,each_move.get('id'))
                    if move_id_obj.picking_id.state == 'done':
                        delivered_qty += move_id_obj.product_qty
                    else:
                        move_ids  = []
                        sale_line_id = each_move.get('sale_line_id')
                        if sale_line_id:
                            move_ids.append(each_move.get('id'))
                            ##Sale Order Line Qty
                            cr.execute('select product_uom_qty from sale_order_line where id=%d'%(sale_line_id))
                            so_line_qty = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if so_line_qty:
                                so_line_qty = so_line_qty[0]
                            ##Return Order Line qty
                            cr.execute('select product_uom_qty from return_order_line where sale_line_id=%d'%(sale_line_id))
                            return_line_qty = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if return_line_qty:
                                return_line_qty = return_line_qty[0]
                            #Newly Added Lines
                            else:
                                return_line_qty = so_line_qty
                            ##################    
                            if existing_return:
                                so_line_qty = each_move.get('product_qty')
                            #Final Qty
                            if so_line_qty and return_line_qty:
                                mv_qty = so_line_qty - return_line_qty
                                if delivered_qty > 0.0:
                                    mv_qty  = mv_qty - delivered_qty
                                cr.execute('select id from stock_move where parent_stock_mv_id = %d'%(each_move.get('id')))
                                child_move = filter(None, map(lambda x:x[0], cr.fetchall()))
                                if child_move:
                                    move_ids = move_ids + child_move
                                if move_ids:
                                    if mv_qty == 0.0:
                                        move_obj.action_cancel(cr,uid,move_ids,context)
                                    else:
                                        move_obj.write(cr,uid,move_ids,{'product_qty':abs(mv_qty)})
######End of Customized function
    def deliver_confirm(self,cr,uid,ids,context=None):
        return_obj = self.browse(cr,uid,ids[0])
        linked_order = return_obj.linked_sale_order
        if return_obj.return_type != 'exchange':
            raise osv.except_osv(_('Error!'),  _('You cannot use these functionality when return type is Credit Return'))
        if linked_order:
            self.check_return_line_qty(cr,uid,ids,context)
	    form_res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'cox_communication' ,'view_deliver_goods')
            form_id = form_res and form_res[1] or False   	
            return {
                    'name': ('Delivery Of Goods'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'deliver.goods',
                    'view_id': False,
		'views': [(form_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                     'context': context
                }
    #    Start code Preeti for RMA                
    def credit_refund(self, cr,uid,ids,context):
        res={}        
        context['action_to_do'] = 'cancel_option'
        context['call_from'] = 'function'
        return {
                    'name': ('Cancel Service'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'credit.refund',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                     'context': context
                        }

    def process_order(self,cr,uid,ids,context):
        return_obj=self.browse(cr,uid,ids[0])
        obj_sale_order=self.pool.get('sale.order')
        policy_object=self.pool.get('res.partner.policy')     
        linked_sale_id=return_obj.linked_sale_order
        if linked_sale_id:
            obj_sale_link_order = obj_sale_order.browse(cr, uid, linked_sale_id.id)
            days = self.no_of_days_passed(cr,uid,obj_sale_link_order,{})
        if context:
            if (context.get('device_option') == 'yes'):                
                if (days >= 31) and (days <= 90):
                    raise osv.except_osv(_('Warning!'), _('This order was placed %s days ago and is not within the policy. Customer can either exchange the device or please select refund against subscription to refund or cancel service'%(days)))
                else:
                    id = self.pool.get('return.shipment.label').create(cr,uid,{'return_id':ids[0]})
                    return {
                        'name':_("Shipment Needed ?"),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_id': id,
                        'res_model': 'return.shipment.label',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        }
            elif(context.get('device_option') == 'no'):
                if (days >= 0) and (days <= 30):
	            id = self.pool.get('return.refund.cancellation').create(cr,uid,{'refund_cancel':'refund','return_id':ids[0]})
		    if not return_obj.manual_invoice_invisible:	
	        	    return {
        	        	    'name':_("Payment Finalization"),
	        	            'view_type': 'form',
        	        	    'view_mode': 'form',
		                    'res_id': id,
        		            'res_model': 'return.refund.cancellation',
		                    'type': 'ir.actions.act_window',
	       		            'nodestroy': True,
		                    'target': 'new',
        		            }
                return True
                    
            elif (context.get('credit_option') == 'yes'):
                if (context.get('cancel_option') == 'yes'):
                    
                    if context.get('cancel_option') == 'yes':                           
                        if context.get('service_id'):
                            policy_brw=policy_object.browse(cr,uid,context.get('service_id'))
                            if (policy_brw.active_service == False):
                                raise osv.except_osv(_('Error !'),
                                        _('Service is already cancelled for: "%s"') %(policy_brw.sale_order))
                    self.pool.get('refund.against.invoice').refund_cancel_service(cr,uid,ids,context)
                    return True
                else:
                    self.pool.get('refund.against.invoice').refund_service(cr,uid,ids,context)
            elif (context.get('cancel_option') == 'yes'):
                    service_id = context.get('service_id')
                    policy_object=self.pool.get('res.partner.policy')     
#                    if cancel_option == 'yes':   
                    if service_id:
                        policy_brw=policy_object.browse(cr,uid,context.get('service_id'))
                        if (policy_brw.active_service == False):
                            raise osv.except_osv(_('Error !'),
                                    _('Service is already cancelled for: "%s"') %(policy_brw.sale_order))
                    self.pool.get('refund.against.invoice').cancel_service(cr,uid,ids,context)                        
                    return True
            else:
                raise osv.except_osv(_("Warning"),
                        _("To proceed, Atleast one of the options should be yes."))
        else:
            return True
    
    def create(self,cr,uid,vals,context={}):        
        if vals.get('refund_type') == 'partial_refund':            
            if vals['order_line'][1][2].get('price_unit') >= vals['order_line'][1][2].get('copy_unit_price'):
                raise osv.except_osv(_('Error !'),
                            _('Partial refund amount should be less than subscription price. Please modify unit price in return order lines to refund partial amount. If the field is invisible for you, please call support manager.'))        
        return super(return_order, self).create(cr,uid,vals,context=context)
    
    def write(self,cr,uid,ids,vals,context={}):
         return_obj = self.pool.get('return.order')
         if type(ids) is list:
             return_brw = return_obj.browse(cr,uid,ids[0])
         else:      
             return_brw = return_obj.browse(cr,uid,ids)
         if vals.has_key('refund_type') and vals['refund_type'] != 'complete_refund':
            if return_brw.refund_type == 'partial_refund' or vals['refund_type'] == 'partial_refund' :        
                for line in return_brw.order_line:
                    if vals.has_key('order_line'):
                        if vals['order_line'][0][2].get('price_unit') >= line.copy_unit_price:                
                            raise osv.except_osv(_('Error !'),
                                   _('Partial refund amount should be less than subscription price. Please modify unit price in return order lines to refund partial amount. If the field is invisible for you, please call support manager.'))
                    elif line.price_unit >= line.copy_unit_price:
                         raise osv.except_osv(_('Error !'),
                                   _('Partial refund amount should be less than subscription price. Please modify unit price in return order lines to refund partial amount. If the field is invisible for you, please call support manager.'))                
         return super(return_order, self).write(cr, uid, ids,vals,context=context)
#    End code Preeti for RMA
return_order()

class return_order_line(osv.osv):
    _inherit = 'return.order.line'
    #Start code Preeti for RMA    
    _columns={
        'discount_amt':fields.float('Sales Discount'),
        'actual_price':fields.float('Actual Price'),    
        'copy_unit_price':fields.float('Copy of Unit price')
    }
    
    def onchange_price_unit(self,cr,uid,ids,price_unit,qty,return_type,sale_line_id,copy_unit_price,context={}):
        res={}
        res['value']={}
        if sale_line_id:
            line_brw = self.pool.get('sale.order.line').browse(cr,uid,sale_line_id)            
            if return_type == 'complete_refund':
                if float(copy_unit_price) * float(qty) != float(price_unit) * float(qty):
                    warning = {
                'title': _('Warning!'),
                'message' : _("Entered price doesn't match with Original price as you have selected Refund Type as Complete.")
                    }
                    res['warning'] =  warning
                    stored_price_unit =  line_brw.price_unit
                    stored_qty =  line_brw.product_uom_qty
                    res['value']['price_unit'] = stored_price_unit
                    if stored_qty:
                        res['value']['product_uom_qty'] = stored_qty
            elif return_type == 'partial_refund':
                if float(copy_unit_price) * float(qty) < float(price_unit) * float(qty):
                    warning = {
                    'title': _('Warning!'),
                    'message' : _("Entered price should be less than Original price.")
                        }
                    res['warning'] =  warning
                    stored_price_unit =  line_brw.price_unit
                    stored_qty =  line_brw.product_uom_qty
                    res['value']['price_unit'] = stored_price_unit
                    if stored_qty:
                        res['value']['product_uom_qty'] = stored_qty
        else:
            if float(price_unit) * float(qty) > float(copy_unit_price) * float(qty):
                warning = {
                    'title': _('Warning!'),
                    'message' : _("Entered price should be less than Original price.")
                        }
                res['warning'] =  warning
                stored_price_unit =  float(copy_unit_price) * float(qty)
                stored_qty =  float(qty)
                res['value']['price_unit'] = float(copy_unit_price)
                if stored_qty:
                    res['value']['product_uom_qty'] = stored_qty
        return res	
    def create(self,cr,uid,vals,context={}):
        #if not vals.get('sale_line_id'):
         #   raise osv.except_osv(_('Error!'),  _('Please Check Your Return Order Lines'))
        #else:
             return super(return_order_line, self).create(cr,uid,vals,context=context)
#End code Preeti for RMA
return_order_line()
