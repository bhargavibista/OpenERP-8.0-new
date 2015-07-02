# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date
from openerp import netsvc

class charge_termination_fee(osv.osv_memory):
    _name='charge.termination.fee'
    def default_get(self, cr, uid, fields, context=None):
        res = super(charge_termination_fee, self).default_get(cr, uid, fields, context=context)
        termination_fees = self.get_termination_fees(cr,uid,context)
        res['termination_fees'] = termination_fees
        customer_payment_id = self.customer_payment_id(cr,uid,context)
        if customer_payment_id:
            res['cust_payment_profile_id'] = customer_payment_id[0][0]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',context=None, toolbar=False, submenu=False):
        res = super(charge_termination_fee, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context is None:
           context={}
        active_id = context.get('active_id',False)
        if active_id:
            return_id_obj = self.pool.get('return.order').browse(cr,uid,active_id)
            no_days = self.no_days_passed(cr,uid,return_id_obj,context)
            if no_days > 90:
                raise osv.except_osv(_('Warning'), _('You cannot Charge Termination Fees because return days are greater than 90'))
        return res
    def cc_authorize_net_charge(self,cr,uid,invoice_id,return_id_brw,context):
        if invoice_id:
            invoice_obj = self.pool.get('account.invoice')
            invoice_id_brw = invoice_obj.browse(cr,uid,invoice_id)
            authorize_net_config = self.pool.get('authorize.net.config')
            customer_profile_id =  invoice_id_brw.customer_profile_id
            cust_payment_profile_id = invoice_id_brw.customer_payment_profile_id
            amount = invoice_id_brw.amount_total
            config_ids = authorize_net_config.search(cr,uid,[])
            if config_ids and customer_profile_id and cust_payment_profile_id:
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                transaction_response =authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',invoice_id,'profileTransAuthCapture',amount,customer_profile_id,cust_payment_profile_id,'','account.invoice','',context)
                cr.execute("select credit_card_no from custmer_payment_profile where profile_id='%s'"%(cust_payment_profile_id))
                cc_number = filter(None, map(lambda x:x[0], cr.fetchall()))
                if cc_number:
                    cc_number = cc_number[0]
                if transaction_response :
                    context['cc_number'] ='XXXX'+cc_number
                    context['customer_profile_id'] = customer_profile_id
                    invoice_obj.api_response(cr,uid,int(invoice_id),transaction_response,cust_payment_profile_id,'CreateCustomerProfileTransaction',context)
                    self.pool.get('return.order').api_response(cr,uid,int(return_id_brw.id),transaction_response,customer_profile_id,cust_payment_profile_id,cc_number,context)

    def create_invoice(self,cr,uid,return_order_id_brw,context={}):
        address,invoice_vals = False,{}
        com_obj = self.pool.get('res.company')
        search_company = com_obj.search(cr,uid,[])
        if search_company:
            search_company_id = com_obj.browse(cr,uid,search_company[0])
            address = self.pool.get('res.partner').address_get(cr, uid, [search_company_id.partner_id.id], ['default'])
            if address:
                address = address.get('default',False)
            journal_ids = self.pool.get('account.journal').search(cr, uid,
                [('type', '=', 'sale'), ('company_id', '=', return_order_id_brw.partner_id.company_id.id)],limit=1)
            invoice_vals.update({
                    'origin': return_order_id_brw.name,
                    'name': (return_order_id_brw.partner_id.ref if return_order_id_brw.partner_id.ref else ''),
                    'type': 'out_invoice',
                    'reference': return_order_id_brw.name,
                    'account_id': return_order_id_brw.partner_id.property_account_receivable.id,
                    'partner_id': return_order_id_brw.partner_id.id,
                    'journal_id': journal_ids[0],
                    'currency_id':  return_order_id_brw.partner_id.company_id.currency_id.id,
                    'company_id': return_order_id_brw.partner_id.company_id.id,
                    'date_invoice':str(date.today()),
                    'auth_transaction_id':False,
                    'authorization_code':False,
                    'auth_respmsg':False,
                    'customer_payment_profile_id':context.get('cust_payment_profile_id',''),
                    'customer_profile_id':context.get('customer_profile_id',''),
                    'auth_transaction_type':'profileTransAuthCapture',
                    'location_address_id': address,
                    'invoice_line':[]
                })
            product_obj = self.pool.get('product.product')
            search_product = product_obj.search(cr,uid,[('default_code','=','termination_fee')])
            if search_product:
                product_brw = product_obj.browse(cr,uid,search_product[0])
                if product_brw.property_account_income.id:
                    account_id = product_brw.property_account_income.id
                else:
                    account_id = product_brw.categ_id.property_account_income_categ.id
                invoice_line = {
                         'product_id':product_brw.id,
                         'name':product_brw.name,
                         'quantity':1.00,
                         'price_unit':context.get('termination_fees',0.0),
                         'uos_id':product_brw.uom_id.id,
                         'account_id':account_id,
                         'origin': return_order_id_brw.name,
                        'invoice_line_tax_id': [],
                                }
                invoice_vals['invoice_line'].append((0, 0, invoice_line))
                invoice_id=self.pool.get('account.invoice').create(cr,uid,invoice_vals)
                return invoice_id
        return False
    def no_days_passed(self,cr,uid,id_brw,context):
        linked_sale_order = id_brw.linked_sale_order
        today=date.today()
        confirmed_date=datetime.strptime(linked_sale_order.date_confirm, "%Y-%m-%d").date()
        difference=today-confirmed_date
        no_days = difference.days
        return no_days
    def get_termination_fees(self,cr,uid,context={}):
        if context and context.get('active_id',False) and context.get('active_model') =='return.order':
            id_brw = self.pool.get('return.order').browse(cr,uid,context.get('active_id',False))
            no_days = self.no_days_passed(cr,uid,id_brw,context)
            termination_fees,service_price,final_price = 0.0,0.0,0.0
            line_obj = self.pool.get('sale.order.line')
            for each_line in id_brw.order_line:
                product_id = each_line.product_id.id
                cr.execute("select termination_fees from termination_fee_charges where product_id=%s and  %s between start_range_days and end_range_days"%(product_id,no_days))
                termination_charges = cr.fetchone()
                if termination_charges  and termination_charges:
                    termination_fees += termination_charges[0]
                if each_line.sale_line_id:
                    child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',each_line.sale_line_id.id)])
                    if child_so_line_ids:
                        for each_line in line_obj.browse(cr,uid,child_so_line_ids):
                                if (each_line.product_id.type == 'service'):
                                    service_price += float(each_line.product_uom_qty) * float(each_line.price_unit)
            if termination_fees > 0.0 and no_days < 30:
                amount_total = id_brw.linked_sale_order.amount_total
                if amount_total > service_price:
                    final_price = float(amount_total) - float(service_price)
    #            if float(final_price) > float(termination_fees):
     #               termination_fees = float(final_price) -  float(termination_fees)
      #          else:
       #             termination_fees = float(termination_fees) -  float(final_price)
#		termination_fees = float(final_price) -  float(termination_fees)
		termination_fees =  float(termination_fees) - float(final_price)
            return termination_fees
        
    def customer_payment_id(self, cr, uid, context={}):
        res = []
        if context and context.get('active_id',False) and context.get('active_model') =='return.order':
           id_brw = self.pool.get('return.order').browse(cr,uid,context.get('active_id',False))
           customer_id = id_brw.partner_id
           if customer_id:
                profile_ids = customer_id.profile_ids
                for each_profile in profile_ids:
                    if each_profile.active_payment_profile:
                        cc_number = each_profile.credit_card_no
                        profile_id = each_profile.profile_id
                        res.append((profile_id, cc_number))
        return res
    def charge_termiation_fees(self,cr,uid,ids,context):
        cust_profile_id,cust_payment_profile_id = False,False
        id_brw = self.browse(cr,uid,ids[0])
        if id_brw.termination_fees <= 0.0:
            raise osv.except_osv(_('Warning!'), _('Termination Fee cannot be equal or less'))
        cust_payment_profile_id = id_brw.cust_payment_profile_id
	diff_cc = id_brw.diff_cc
        if context and context.get('active_id',False) and context.get('active_model') =='return.order':
            return_object = self.pool.get('return.order')
            invoice_obj = self.pool.get('account.invoice')
            return_id_brw = return_object.browse(cr,uid,context.get('active_id',False))
            cust_profile_id =  return_id_brw.partner_id.customer_profile_id
            if diff_cc and cust_profile_id:
                new_cc_number = id_brw.new_cc_number
                cc_expiration_date = id_brw.cc_expiration_date
                cust_payment_profile_id = self.pool.get('custmer.payment.profile').create_payment_profile(cr,uid,return_id_brw.partner_id.id,return_id_brw.partner_invoice_id,return_id_brw.partner_shipping_id,cust_profile_id,new_cc_number,cc_expiration_date,context)
            if return_id_brw and cust_payment_profile_id and cust_profile_id:
                context['cust_payment_profile_id'] = cust_payment_profile_id
                context['customer_profile_id'] = cust_profile_id
                context['termination_fees'] = id_brw.termination_fees
                invoice_id = self.create_invoice(cr,uid,return_id_brw,context)
		print"invoice_id",invoice_id
                if invoice_id:
		    invoice_id_obj = invoice_obj.browse(cr,uid,int(invoice_id))
                    cr.execute("insert into return_order_invoice_rel (order_id,invoice_id) values(%s,%s)",(return_id_brw.id,invoice_id))
                    if context.get('called_from_schedular',''):
                        return_val = invoice_obj.charge_customer_recurring_or_etf(cr,uid,[invoice_id],context)
                        if return_val:
                            return_object.service_deactivation(cr,uid,return_id_brw,context)
		            return_object.write(cr,uid,[return_id_brw.id],{'state':'done','auth_transaction_id':invoice_id_obj.auth_transaction_id,'auth_respmsg':'Transaction has been approved','customer_payment_profile_id':invoice_id_obj.customer_payment_profile_id,'auth_transaction_type':invoice_id_obj.auth_transaction_type,
                            'cc_number':invoice_id_obj.cc_number,'customer_profile_id':invoice_id_obj.customer_profile_id})			
#                            return_object.write(cr,uid,[return_id_brw.id],{'state':'done'})
                    else:
                        self.cc_authorize_net_charge(cr,uid,invoice_id,return_id_brw,context)
                        netsvc.LocalService("workflow").trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
                        self.pool.get('account.invoice').make_payment_of_invoice(cr, uid, [invoice_id], context=context)
                        return_object.service_deactivation(cr,uid,return_id_brw,context)
                        return_object.write(cr,uid,[return_id_brw.id],{'state':'done','return_option':'termination_charge'})
		    return {
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_id': return_id_brw.id,
                            'res_model': 'return.order',
                            'type': 'ir.actions.act_window',
                            'context':context
                            }
    def onchange_termination_fees(self,cr,uid,ids,termination_fee,context={}):
        res,warning_mesg,group_names = {},'',[]
        if uid:
            group_ids = self.pool.get('res.users').browse(cr,uid,uid).groups_id
            if group_ids:
                for each_group in group_ids:
                    group_names.append(each_group.name.lower())
                if 'manager' not in group_names:
                    warning_mesg += _("") + 'You cannot edit Termination Fees' +"\n\n"
                    value = {'termination_fees': self.get_termination_fees(cr,uid,context)}
                    res['value'] = value
        if warning_mesg:
             warning = {'title': _('Warning!'),
                'message' : warning_mesg}
             res['warning'] = warning
        return res
    _columns={
    'termination_fees': fields.float('Termination Fees'),
    'cust_payment_profile_id':fields.selection(customer_payment_id, 'Credit Card Number', help="Credit Card Numer", select=True),
     'diff_cc' : fields.boolean('Charge on Different CC'),
    'new_cc_number' :fields.char('New CC Number',size=256,help="Credit Card Number"),
    'cc_expiration_date' :fields.char('CC Exp Date [MMYYYY]',size=6,help="Credit Card Expiration Date"),
    }

charge_termination_fee()
