# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _

class profile_transaction(osv.osv_memory):
    _name = "profile.transaction"

    def new_payment_profile(self,cr,uid,ids,context={}):
         context['sale_id'] = context.get('active_ids', False)
         context['action_to_do'] = 'new_payment_profile'
         return {
                'name': ('New Payment Profile'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'customer.profile.payment',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                 'context': context
            }
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        result = super(profile_transaction, self).default_get(cr, uid, fields, context=context)
        result['auth_transaction_type'] = 'profileTransAuthCapture'
        sale_order_id = context.get('active_ids', False)
        if sale_order_id:
            customer_id = self.pool.get('sale.order').browse(cr,uid,sale_order_id[0]).partner_id
            cust_profile_id = customer_id.customer_profile_id
            if cust_profile_id:
                result['cust_profile_id'] = cust_profile_id
        return result
    
    def new_customer_profile(self,cr,uid,ids,context={}):
         ids = self.create(cr,uid,{},context)
         context['sale_id'] = context.get('active_ids', False)
         context['action_to_do'] = 'new_customer_profile'
         return {
                'name': ('Payment Profile'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'customer.profile.payment',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                 'context': context
            }
    def charge_customer(self,cr,uid,ids,context={}):
        sale_order_id = context.get('active_ids', False)
        context['sale_id'] = sale_order_id
        return {
                'name': ('Charge Customer'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'charge.customer',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                 'context': context
            }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(profile_transaction, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        fields_list = {}
        authorize_net_config = self.pool.get('authorize.net.config')
        if context is None:
            context = {}
        if view_type=='form':
            arch = """<form string="Authorize.Net Profiles">"""
            active_id = context.get('active_id', False)
            act_model=context.get('active_model',False)
            if act_model == 'sale.order':
                obj_all = self.pool.get('sale.order')
            elif act_model == 'account.invoice':
                obj_all = self.pool.get('account.invoice')
            if active_id:
#                transaction_id = obj_all.browse(cr,uid,sale_order_id[0]).auth_transaction_id
#                if not transaction_id:
                    customer_id = obj_all.browse(cr,uid,active_id).partner_id
                    profile_ids = customer_id.profile_ids
                    if profile_ids:
                            existing_credit_cards = ""
                            for each_profile in profile_ids:
                                if each_profile.active_payment_profile:
                                    if each_profile.credit_card_no:
                                        credit_card = "Credit Card Number "+each_profile.credit_card_no
                                        existing_credit_cards+="""<newline/><label string='%s' colspan="4"/><newline/>"""%(credit_card)
                            if existing_credit_cards:
                                arch+="""<separator string="EXISTING PAYMENT PROFILES" colspan="4"/>"""
                                arch+= existing_credit_cards
                                arch+="""<button name="charge_customer" string="Use Existing Card" type="object" icon="gtk-apply"/>"""
                    if customer_id.customer_profile_id:
                        config_ids =authorize_net_config.search(cr,uid,[])
                        if config_ids:
                            config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                            profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',customer_id.customer_profile_id)
                            if profile_info:
                                arch+="""<newline/><button name="new_payment_profile" string="New Payment Profile" type="object" icon="gtk-apply"/>"""
                            else:
                                arch+="""<button name="new_customer_profile" string="New Customer and Payment Profile" type="object" icon="gtk-apply"/>"""
                    else:
                        arch+="""<button name="new_customer_profile" string="New Customer and Payment Profile" type="object" icon="gtk-apply"/>"""
#                else:
#                    raise osv.except_osv('Transaction Completed!', 'Transaction for this sale order has been already completed!')
            arch += """</form>"""
            context['transaction_type'] = 'auth_transaction_type'
            result['arch'] = arch
            result['fields'] = fields_list
            result['context'] = context
        return result
    
profile_transaction()