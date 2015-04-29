# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.netsvc as netsvc
from openerp.addons.base_external_referentials.external_osv import ExternalSession
import time

class profile_transaction(osv.osv_memory):
    _inherit = "profile.transaction"
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(profile_transaction, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form':
            active_id = context.get('active_id', False)
            act_model=context.get('active_model',False)
            if act_model == 'sale.order':
                    obj_all = self.pool.get('sale.order')
            elif act_model == 'account.invoice':
                    obj_all = self.pool.get('account.invoice')
            if active_id:
                obj_brw = obj_all.browse(cr,uid,active_id)
                if (obj_brw.auth_transaction_id) and str(obj_brw.auth_transaction_id) != '0':
                        raise osv.except_osv('Warning!', 'Transaction is already completed!')
                if context.get('call_from') != 'function':
                    if act_model == 'sale.order':
                        if ((obj_brw.state) not in ('progress','done')) or (obj_brw.returns_status != 'no_returns'):
                            raise osv.except_osv('Warning!', 'You Cannot able to Create Authorize.net Transaction')
        return result
profile_transaction()

class charge_customer(osv.osv_memory):
    _inherit = "charge.customer"
    def get_transaction_type(self,cr,uid,context={}):
        if context is None:
            context = {}
        active_id = context.get('active_id')
        if context.get('active_model',False)=='account.invoice':
            return 'profileTransAuthCapture'
        if active_id:
            sale_id_obj = self.pool.get('sale.order').browse(cr,uid,context.get('active_id'))
            if sale_id_obj.cox_sales_channels and sale_id_obj.cox_sales_channels == 'retail':
                return 'profileTransAuthCapture'
            elif sale_id_obj.cox_sales_channels and sale_id_obj.cox_sales_channels == 'ecommerce':
                return 'profileTransPriorAuthCapture'
            else:
                return 'profileTransAuthOnly'
        return 'profileTransAuthOnly'

    def charge_customer(self,cr,uid,ids,context={}):
#        active_id = context.get('sale_id',False)
        context['main_lang'] = 'en_US'
        active_id = context.get('active_id',False)
        active_model=context.get('active_model',False)
        so_obj = self.pool.get('sale.order')
	partner_obj = self.pool.get('res.partner')
	payment_obj = self.pool.get('partner.payment.error')
        wf_service = netsvc.LocalService("workflow")
        return_data = {'view_type': 'form',
                'view_mode': 'form',
                'res_model': active_model,
                'type': 'ir.actions.act_window',
                'context':context
        }
        if active_id:
            return_data.update({'res_id': active_id})
            if active_model=='account.invoice':
                result = super(charge_customer, self).charge_customer(cr, uid, ids, context=context)
    #            partner_obj=self.pool.get('res.partner')
                partner_id=context.get('partner_id',False)
                invoice_id_obj = self.pool.get(active_model).browse(cr,uid,active_id)
		payment_exception_id = context.get('payment_exception_id',False)
		source =  context.get('source',False)
                if result.get('resultCode') == 'Ok':
                    cr.execute("UPDATE account_invoice SET capture_status='captured' where id=%d"%(active_id))
                    if invoice_id_obj.state =='draft':
			cr.execute("update account_invoice set date_invoice='%s' where id =%s"%(time.strftime('%Y-%m-%d'),invoice_id_obj.id))
                        wf_service.trg_validate(uid, 'account.invoice', active_id, 'invoice_open', cr)
                        self.pool.get(active_model).make_payment_of_invoice(cr, uid, [active_id], context=context)
			if 'recurring' in source.lower():
				if partner_id:
#	                            cr.execute("update res_partner set billing_date='%s' where id = '%s'"%(context.get('nextmonth',''),partner_id))
   	  	                    partner_obj.write(cr,uid,partner_id,{'billing_date':context.get('nextmonth',False)},context)
			            so_obj.email_to_customer(cr,uid,invoice_id_obj,'account.invoice','',invoice_id_obj.partner_id.emailid,context)
				    self.pool.get('res.partner').export_recurring_profile(cr,uid,[invoice_id_obj.id],{})
				    if payment_exception_id:
                                        payment_obj.write(cr,uid,[payment_exception_id],{'active_payment':False})
                        else:
                            return_object = self.pool.get('return.order')
                            search_sales_return = return_object.search(cr,uid,[('name','ilike',invoice_id_obj.origin),('state','!=','done')])
                            if search_sales_return:
                                return_id_brw = return_object.browse(cr,uid,search_sales_return[-1])
                                return_object.service_deactivation(cr,uid,return_id_brw,context)
#                                return_object.write(cr,uid,[return_id_brw.id],{'state':'done'})
				return_object.write(cr,uid,[return_id_brw.id],{'state':'done','auth_transaction_id':invoice_id_obj.auth_transaction_id,'auth_respmsg':'Transaction has been approved','customer_payment_profile_id':invoice_id_obj.customer_payment_profile_id,
                                'cc_number':invoice_id_obj.cc_number})
                else:
    #                transaction_response = result.get('response')
                    if context.get('payment_exception_id',False):
                        message = result.get('message')
#                        payment_exception_id = context.get('payment_exception_id',False)
                        if payment_exception_id and message:
                            message = result.get('message')
                            exception_brw = payment_obj.browse(cr,uid,payment_exception_id)
                            payment_obj.write(cr,uid,[payment_exception_id],{'message':message})
    #                if transaction_response and transaction_response[2] in ('2','3') :
                            so_obj.email_to_customer(cr,uid,exception_brw,'partner.payment.error','payment_exception',invoice_id_obj.partner_id.emailid,context)
		if payment_exception_id:
                    return_data.update({'res_id': payment_exception_id})
                    return_data.update({'res_model': 'partner.payment.error'})
            else:
                account_id = so_obj.search_income_account(cr,uid,[active_id],context)
                if False in account_id:
                    raise osv.except_osv(_('Error !'),_("No Income Account is defined for Products.Please check"))
		#response =self.pool.get('authorize.net.config').check_authorize_net(cr,uid,'sale.order',active_id,context)
		#if not response:
	        result = super(charge_customer, self).charge_customer(cr, uid, ids, context=context)
                invoice_id,flag = False,False
                sale_object=so_obj.browse(cr,uid,active_id)
                if (sale_object.auth_transaction_id) and context.get('call_from','') != 'wizard':
                    invoice_obj = self.pool.get('account.invoice')
                    tax_obj = self.pool.get('account.tax')
                    wf_service.trg_validate(uid, 'sale.order', active_id, 'order_confirm', cr)
                    email_to = sale_object.partner_id.emailid
                    if sale_object.cox_sales_channels in ('retail','ecommerce'):
                        cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(active_id))
                        invoice_id=cr.fetchone()
                        if invoice_id:
                            wf_service.trg_validate(uid, 'account.invoice', invoice_id[0], 'invoice_open', cr)
                            returnval = invoice_obj.make_payment_of_invoice(cr, uid, invoice_id, context=context)
                            so_obj.email_to_customer(cr, uid, sale_object,'sale.order','payment_confirmation',email_to,context)
                    try:
                        magento_shop_brw = sale_object.shop_id
                        magento_exported = sale_object.magento_exported
                        external_session = ExternalSession(magento_shop_brw.referential_id, magento_shop_brw)
                        #Only For Ecommerce Orders
                        if sale_object.cox_sales_channels == 'ecommerce':
                            incrementid = sale_object.magento_incrementid
                            line_data,shipping_data = {},{}
                            for line in sale_object.order_line:
                                tax_amount,tax_percent = 0.0,0.0
                                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                                taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
                                if taxes:
                                    subtotal = taxes.get('total')
                                    if subtotal > 0.0:
                                        if taxes.get('taxes'):
                                            tax_amount = taxes.get('taxes')[0].get('amount')
                                            tax_percent = round((tax_amount * 100) / (subtotal))
                                if line.order_item_id:
                                    line_data[line.order_item_id] = {'name':line.product_id.name,'sku':line.product_id.default_code,'product_id':line.product_id.magento_product_id,'price': line.price_unit,'qty':line.product_uom_qty,'tax_percent':tax_percent,'tax_amount':tax_amount}
                                else:
                                    shipping_data = {'shipping_method':'flatrate_flatrate','shipping_charges':line.price_subtotal,'tax_amount':tax_amount}
                            if line_data:
                                return_val = external_session.connection.call('sales_order.update_order', [incrementid,line_data,shipping_data,sale_object.amount_tax])
                            if invoice_id:
                                invoice_obj._export_one_resource(cr, uid, external_session, invoice_id[0], context=context)
                            return_val = external_session.connection.call('sales_order.process_invoice', ['',incrementid,'authorizenetcim'])
                        if not magento_exported:
                            data = so_obj.export_sale_order(cr,uid,[active_id],context)
                            if data:
                                api_response = data.get('api_response')
                                increment_id = api_response.get('increment_id')
                                if sale_object.cox_sales_channels == 'retail':
                                    if data.get('shop_brw',False):
                                        if invoice_id:
                                            invoice_obj._export_one_resource(cr, uid, external_session, invoice_id[0], context=context)
                                        if api_response:
                                            payment_id = api_response.get('payment_id')
                                            return_val = external_session.connection.call('sales_order.process_invoice', [payment_id,increment_id,'authorizenetcim'])
#                                        if data.get('new_customer',False):
					    so_obj.welcome_email_offer(cr,uid,sale_object,data,context)
#                                            so_obj.email_to_customer(cr,uid,sale_object.partner_id,'res.partner','welcome_email',sale_object.partner_id.emailid,context)
                                        flag = True
                                #Code to export services on the magento services view
                                if data.get('service_data',{}):
                                    external_session.connection.call('sales_order.recurring_services',['export',data.get('service_data',{}),increment_id])
                                if api_response.get('db_id',''):
                                    if sale_object.cox_sales_channels == 'call_center':
                                        so_obj.email_to_customer(cr, uid, sale_object,'sale.order','account_set_up',email_to,context)
                    except Exception, e:
                        print "error string",e
                    if not flag and sale_object.cox_sales_channels == 'retail':
#                        cr.execute("update res_partner set magento_pwd='ZmwyNDc2' where id=%d"%(sale_object.partner_id.id))
                        self.pool.get('res.partner').write(cr,uid,sale_object.partner_id.id,{'magento_pwd':'ZmwyNDc2'})
                        so_obj.email_to_customer(cr,uid,sale_object.partner_id,'res.partner','welcome_email',sale_object.partner_id.emailid,context)
        ##Query To delete all records in charge_customer
            cr.execute('delete from charge_customer')
        if 'conn' in return_data.get('context',{}):
            del return_data['context']['conn']
        return return_data
#        return {'type': 'ir.actions.act_window_close'}
    _columns = {
    ##Function is inherited because want to include capture only option for the Ecommerce option
        'transaction_type':fields.selection([('profileTransAuthCapture','Authorize and Capture'),('profileTransAuthOnly','Authorize Only'),('profileTransPriorAuthCapture','Capture Only')], 'Transaction Type',readonly=True),
    }
    _defaults = {
    'transaction_type': get_transaction_type
    }
charge_customer()

class customer_profile_payment(osv.osv_memory):
    _inherit = "customer.profile.payment"
    def get_transaction_type(self,cr,uid,context={}):
        if context is None:
            context = {}
        active_id = context.get('active_id')
        if context.get('active_model',False)=='account.invoice':
            return 'profileTransAuthCapture'
        if active_id:
            sale_id_obj = self.pool.get('sale.order').browse(cr,uid,context.get('active_id'))
            if sale_id_obj.cox_sales_channels and sale_id_obj.cox_sales_channels in ('retail','ecommerce'):
                return 'profileTransAuthCapture'
            else:
                return 'profileTransAuthOnly'
        return 'profileTransAuthOnly'
    
    def charge_customer(self,cr,uid,ids,context={}):
#         active_id = context.get('sale_id',False)
        context['main_lang'] = 'en_US'
        active_id = context.get('active_id',False)
        active_model=context.get('active_model',False)
        so_obj = self.pool.get('sale.order')
	partner_obj = self.pool.get('res.partner')
	payment_obj = self.pool.get('partner.payment.error')
        wf_service = netsvc.LocalService("workflow")
        return_data = {'view_type': 'form',
                'view_mode': 'form',
                'res_model': active_model,
                'type': 'ir.actions.act_window',
                'context':context
                    }
        if active_id:
            return_data.update({'res_id': active_id})
            if active_model=='account.invoice':
                result = super(customer_profile_payment, self).charge_customer(cr, uid, ids, context=context)
    #            partner_obj=self.pool.get('res.partner')
                partner_id=context.get('partner_id',False)
                invoice_id_obj = self.pool.get(active_model).browse(cr,uid,active_id)
		payment_exception_id = context.get('payment_exception_id',False)
		source =  context.get('source',False)
                if result.get('resultCode') == 'Ok':
                    cr.execute("UPDATE account_invoice SET capture_status='captured' where id=%d"%(active_id))
                    if invoice_id_obj.state =='draft':
			cr.execute("update account_invoice set date_invoice='%s' where id =%s"%(time.strftime('%Y-%m-%d'),invoice_id_obj.id))
                        wf_service.trg_validate(uid, 'account.invoice', active_id, 'invoice_open', cr)
                        self.pool.get(active_model).make_payment_of_invoice(cr, uid, [active_id], context=context)
                        if 'recurring' in source.lower():
	                        if partner_id:
	                            partner_obj.write(cr,uid,partner_id,{'billing_date':context.get('nextmonth',False)},context)
#        	                    cr.execute("update res_partner set billing_date='%s' where id = '%s'"%(context.get('nextmonth',''),partner_id))
                	            so_obj.email_to_customer(cr,uid,invoice_id_obj,'account.invoice','',invoice_id_obj.partner_id.emailid,context)
				    self.pool.get('res.partner').export_recurring_profile(cr,uid,[invoice_id_obj.id],{})
				    if payment_exception_id:
                                        payment_obj.write(cr,uid,[payment_exception_id],{'active_payment':False})
			else:
                            return_object = self.pool.get('return.order')
                            search_sales_return = return_object.search(cr,uid,[('name','ilike',invoice_id_obj.origin),('state','!=','done')])
                            if search_sales_return:
                                return_id_brw = return_object.browse(cr,uid,search_sales_return[-1])
                                return_object.service_deactivation(cr,uid,return_id_brw,context)
        #                        return_object.write(cr,uid,[return_id_brw.id],{'state':'done'})
				return_object.write(cr,uid,[return_id_brw.id],{'state':'done','auth_transaction_id':invoice_id_obj.auth_transaction_id,'auth_respmsg':'Transaction has been approved','customer_payment_profile_id':invoice_id_obj.customer_payment_profile_id,
                                'cc_number':invoice_id_obj.cc_number})
                else:
#                    transaction_response = result.get('response')
                    if context.get('payment_exception_id',False):
                        message = result.get('message')
#                        payment_exception_id = context.get('payment_exception_id',False)
                        if payment_exception_id and message:
                            message = result.get('message')
                            payment_obj = self.pool.get('partner.payment.error')
                            exception_brw = payment_obj.browse(cr,uid,payment_exception_id)
                            payment_obj.write(cr,uid,[payment_exception_id],{'message':message})
#                    if transaction_response and transaction_response[2] in ('2','3') :
                            so_obj.email_to_customer(cr,uid,exception_brw,'partner.payment.error','payment_exception',invoice_id_obj.partner_id.emailid,context)
		if payment_exception_id:
                    return_data.update({'res_id': payment_exception_id})
                    return_data.update({'res_model': 'partner.payment.error'})
            else:
                account_id = so_obj.search_income_account(cr,uid,[active_id],context)
                if False in account_id:
                    raise osv.except_osv(_('Error !'),_("No Income Account is defined for Products.Please check Accounting Configuration of Product"))
#		response =self.pool.get('authorize.net.config').check_authorize_net(cr,uid,'sale.order',active_id,context)
#		if not response:
	        result = super(customer_profile_payment, self).charge_customer(cr, uid, ids, context=context)
                invoice_id,flag = False,False
                sale_object = so_obj.browse(cr,uid,active_id)
                if (sale_object.auth_transaction_id) and context.get('call_from','') != 'wizard':
                    invoice_obj = self.pool.get('account.invoice')
                    tax_obj = self.pool.get('account.tax')
                    wf_service.trg_validate(uid, 'sale.order', active_id, 'order_confirm', cr)
                    email_to = sale_object.partner_id.emailid
                    if sale_object.cox_sales_channels in ('retail','ecommerce'):
                        cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(active_id))
                        invoice_id=cr.fetchone()
                        if invoice_id:
                            wf_service.trg_validate(uid, 'account.invoice', invoice_id[0], 'invoice_open', cr)
                            returnval = invoice_obj.make_payment_of_invoice(cr, uid, invoice_id, context=context)
                            so_obj.email_to_customer(cr, uid, sale_object,'sale.order','payment_confirmation',email_to,context)
                    try:
                        magento_shop_brw = sale_object.shop_id
                        magento_exported = sale_object.magento_exported
                        external_session = ExternalSession(magento_shop_brw.referential_id, magento_shop_brw)
                        #Only For Ecommerce Orders
                        if sale_object.cox_sales_channels == 'ecommerce':
                            incrementid = sale_object.magento_incrementid
                            line_data,shipping_data = {},{}
                            for line in sale_object.order_line:
                                tax_amount,tax_percent = 0.0,0.0
                                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                                taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
                                if taxes:
                                    subtotal = taxes.get('total')
                                    if subtotal > 0.0:
                                        if taxes.get('taxes'):
                                            tax_amount = taxes.get('taxes')[0].get('amount')
                                            tax_percent = round((tax_amount * 100) / (subtotal))
                                if line.order_item_id:
                                    line_data[line.order_item_id] = {'name':line.product_id.name,'sku':line.product_id.default_code,'product_id':line.product_id.magento_product_id,'price': line.price_unit,'qty':line.product_uom_qty,'tax_percent':tax_percent,'tax_amount':tax_amount}
                                else:
                                    shipping_data = {'shipping_method':'flatrate_flatrate','shipping_charges':line.price_subtotal,'tax_amount':tax_amount}
                            if line_data:
                                return_val = external_session.connection.call('sales_order.update_order', [incrementid,line_data,shipping_data,sale_object.amount_tax])
                            if invoice_id:
                                invoice_obj._export_one_resource(cr, uid, external_session, invoice_id[0], context=context)
                            return_val = external_session.connection.call('sales_order.process_invoice', ['',incrementid,'authorizenetcim'])
                        if not magento_exported:
                            data = so_obj.export_sale_order(cr,uid,[active_id],context)
                            if data:
                                api_response = data.get('api_response')
                                increment_id = api_response.get('increment_id')
                                if sale_object.cox_sales_channels == 'retail':
                                    if data.get('shop_brw',False):
                                        if invoice_id:
                                            invoice_obj._export_one_resource(cr, uid, external_session, invoice_id[0], context=context)
                                        if api_response:
                                            payment_id = api_response.get('payment_id')
                                            return_val = external_session.connection.call('sales_order.process_invoice', [payment_id,increment_id,'authorizenetcim'])
#                                        if data.get('new_customer',False):
					    so_obj.welcome_email_offer(cr,uid,sale_object,data,context)
#                                            so_obj.email_to_customer(cr,uid,sale_object.partner_id,'res.partner','welcome_email',sale_object.partner_id.emailid,context)
                                        flag = True
                                #Code to export services on the magento services view
                                if data.get('service_data',{}):
                                    external_session.connection.call('sales_order.recurring_services',['export',data.get('service_data',{}),increment_id])
                                if api_response.get('db_id',''):
                                    if sale_object.cox_sales_channels == 'call_center':
                                        so_obj.email_to_customer(cr, uid, sale_object,'sale.order','account_set_up',email_to,context)
                    except Exception, e:
                        print "error string",e
                    if not flag and sale_object.cox_sales_channels == 'retail':
#                            cr.execute("update res_partner set magento_pwd='ZmwyNDc2' where id=%d"%(sale_object.partner_id.id))
                            self.pool.get('res.partner').write(cr,uid,sale_object.partner_id.id,{'magento_pwd':'ZmwyNDc2'})
                            so_obj.email_to_customer(cr,uid,sale_object.partner_id,'res.partner','welcome_email',sale_object.partner_id.emailid,context)
            ##Query To delete all records in customer_profile_payment
            cr.execute('delete from customer_profile_payment')
        if 'conn' in return_data.get('context',{}):
            del return_data['context']['conn']
        return return_data
#        return {'type': 'ir.actions.act_window_close'}
    _defaults = {
        'transaction_type': get_transaction_type
    }
customer_profile_payment()
