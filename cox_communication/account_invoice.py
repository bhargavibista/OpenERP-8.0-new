# -*- coding: utf-8 -*-               
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import models, fields, api, _
from openerp.http import request
import datetime
import time
from dateutil.relativedelta import relativedelta
from openerp import netsvc
from openerp.addons.account_salestax_avatax.wizard import suds_client
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


#code by riyaz for issues related to manual validation of invoice for parter having parent company
class account_move_line(osv.osv):
    _inherit = "account.move.line"
    def create(self,cr,uid,vals,context={}):
        print "valssssssssssssss-----123------",vals
        pat_id= vals.get('partner_id')
        if pat_id:
            parent_id=self.pool.get('res.partner').browse(cr,uid,pat_id).parent_id.id
            if parent_id:
                vals.update({'partner_id': parent_id })
        print "parent_id---------",parent_id
        print "pat_id----------------",pat_id
        res=super(account_move_line, self).create(cr, uid, vals, context=context)
        return res
account_move_line()

#code by riyaz for issues related to manual validation of invoice for parter having parent company
class account_voucher(osv.osv):
    _inherit = "account.voucher"
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        print "partner_id-----------",partner_id
        if partner_id:
            parent_id=self.pool.get('res.partner').browse(cr,uid,partner_id).parent_id.id
            print "parent_id----------------",parent_id
            if parent_id:
                partner_id=parent_id
        res=super(account_voucher, self).onchange_journal( cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        return res
account_voucher()


class account_invoice(models.Model):
    _inherit='account.invoice'
    
    @api.multi
    def check_tax_lines(self, compute_taxes):
        account_invoice_tax = self.env['account.invoice.tax']
        company_currency = self.company_id.currency_id
        if not self.tax_line:
            for tax in compute_taxes.values():
                account_invoice_tax.create(tax)
        else:
            tax_key = []
            precision = self.env['decimal.precision'].precision_get('Account')
            for tax in self.tax_line:
                if tax.manual:
                    continue
                key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id,tax.account_analytic_id.id)
                tax_key.append(key)
                if key not in compute_taxes:
                    raise except_orm(_('Warning!'), _('Global taxes defined, but they are not in invoice lines !'))
                base = compute_taxes[key]['base']
                if float_compare(abs(base - tax.base), company_currency.rounding, precision_digits=precision) == 1:
                    raise except_orm(_('Warning!'), _('Tax base different!\nClick on compute to update the tax base.'))
            for key in compute_taxes:
                if key not in tax_key:
                    raise except_orm(_('Warning!'), _('Taxes are missing!\nClick on compute button.'))
    #Function is inherited from the avatax module because it again calculates and exports tax back to
    #Avalara for magento orders and for recurring billing so to restrict it to these.
    
#    @api.one
#    @api.depends('invoice_line')
    '''def _avatax_calc(self, cr, uid, ids, name, args, context=None):
        res = {}
        avatax_config_obj = self.pool.get('account.salestax.avatax')
        avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid)
        print"avatax_config",avatax_config
        for invoice in self:
            #Extra Code Starts here
            #Code to skip avalara tax calculation for the recurring billing because they are not
            #applying tax for the services
            if invoice.recurring:
                res[invoice.id] = False
            ###Ends Here###############
            #Code to skip avalara tax calculation for the magento Orders
            if invoice.origin:
                cr.execute("select cox_sales_channels from sale_order where name='%s'"%(invoice.origin))
                sales_channel = filter(None, map(lambda x:x[0], cr.fetchall()))
                if sales_channel and len(sales_channel) > 0:
                    if sales_channel[0] == 'ecommerce':
                        res[invoice.id] = False
                        return res
            #Ends Here
            ####Code Ends here
            if invoice.type in ['out_invoice', 'out_refund'] and \
            avatax_config and not avatax_config.disable_tax_calculation and \
            avatax_config.default_tax_schedule_id.id == invoice.partner_id.tax_schedule_id.id:
                cr.execute("select tax_id from account_invoice_line_tax where invoice_line_id in (select id from account_invoice_line where invoice_id = %d)"%(invoice.id))
                tax_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                if tax_id:
                    res[invoice.id] = False
                else:
                    if invoice.origin:
                        amount_tax = 0.0
                        if 'SO' in invoice.origin:
                            cr.execute("select amount_tax from sale_order where name='%s'"%(invoice.origin))
                            amount_tax = filter(None, map(lambda x:x[0], cr.fetchall()))
                            print"amount_tax",amount_tax
                            
                        elif 'RO' in invoice.origin:
                            cr.execute("select amount_tax from return_order where name='%s'"%(invoice.origin))
                            amount_tax = filter(None, map(lambda x:x[0], cr.fetchall()))
                        if amount_tax and amount_tax[0] > 0.0:
                            res[invoice.id] = True
                        else:
                            res[invoice.id] = False
                    else:
                        res[invoice.id] = True
            else:
                res[invoice.id] = False
        return res'''
                
                
    @api.one
    @api.depends('invoice_line')
    def _avatax_calc(self):
#        print"avatax function "
        res = {}
        avatax_config_obj = self.env['account.salestax.avatax']
        avatax_config = avatax_config_obj._get_avatax_config_company()
        print"avatax_config",avatax_config
        for invoice in self:
            #Extra Code Starts here
            #Code to skip avalara tax calculation for the recurring billing because they are not
            #applying tax for the services
            if invoice.recurring:
                res[invoice.id] = False
            ###Ends Here###############
            #Code to skip avalara tax calculation for the magento Orders
            if invoice.origin:
                self._cr.execute("select cox_sales_channels from sale_order where name='%s'"%(invoice.origin))
                sales_channel = filter(None, map(lambda x:x[0], self._cr.fetchall()))
                if sales_channel and len(sales_channel) > 0:
                    if sales_channel[0] == 'ecommerce':
                        res[invoice.id] = False
                        return res
            #Ends Here
            ####Code Ends here
            if invoice.type in ['out_invoice', 'out_refund'] and \
            avatax_config and not avatax_config.disable_tax_calculation and \
            avatax_config.default_tax_schedule_id.id == invoice.partner_id.tax_schedule_id.id:
                self._cr.execute("select tax_id from account_invoice_line_tax where invoice_line_id in (select id from account_invoice_line where invoice_id = %d)"%(invoice.id))
                tax_id = filter(None, map(lambda x:x[0], self._cr.fetchall()))
                if tax_id:
                    res[invoice.id] = False
                else:
                    if invoice.origin:
                        amount_tax = 0.0
                        if 'SO' in invoice.origin:
                            self._cr.execute("select amount_tax from sale_order where name='%s'"%(invoice.origin))
                            amount_tax = filter(None, map(lambda x:x[0], self._cr.fetchall()))
                            print"amount_tax",amount_tax
                            
                        elif 'RO' in invoice.origin:
                            self._cr.execute("select amount_tax from return_order where name='%s'"%(invoice.origin))
                            amount_tax = filter(None, map(lambda x:x[0], self._cr.fetchall()))
                        if amount_tax and amount_tax[0] > 0.0:
                            res[invoice.id] = True
                        else:
                            res[invoice.id] = False
                    else:
                        res[invoice.id] = True
            else:
                res[invoice.id] = False
        return res
#    #Function is inherited from the avatax module to pass location address id
    def action_commit_tax(self, cr, uid, ids, context=None):
        avatax_config_obj = self.pool.get('account.salestax.avatax')
        account_tax_obj = self.pool.get('account.tax')
#        partner_obj = self.pool.get('res.partner')
        for invoice in self.browse(cr, uid, ids, context=context):
            print"invoice.avatax_calc",invoice.avatax_calc
            if invoice.avatax_calc:
                avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid)
                print"avatax_config",avatax_config
                sign = invoice.type == 'out_invoice' and 1 or -1
                lines = self.create_lines(cr, uid, invoice.invoice_line, sign)
		refund_or_not = invoice.type == 'out_invoice' and 'SalesInvoice' or 'ReturnInvoice'
                if lines:
#                   address = partner_obj.address_get(cr, uid, [invoice.company_id.partner_id.id], ['default'])
                    address = invoice.location_address_id.id #Extra Line of code
                    try:
                        
                        account_tax_obj._check_compute_tax(cr, uid, avatax_config, invoice.date_invoice,
                                                       invoice.internal_number, refund_or_not,
                                                       invoice.partner_id, address,
                                                       invoice.partner_id.id, lines, invoice.shipcharge, invoice.user_id,
                                                       True, invoice.invoice_date,
                                                       invoice.origin,context=context)
                    except Exception, e:
                        self.pool.get('account.invoice').write(cr,uid,invoice.id,{'comment':str(e)})
                        print "error in avatax",str(e)
        return True
    
    def charge_customer_recurring_or_etf(self,cr,uid,ids,context={}):
        if ids:
            if context is None:
                context={}
            #Newly Added
            source = 'Recurring Exception'
            if context.get('source'):
                source = context.get('source','')
            ####
	    next_try_date=False
            customer_profile_id,returnval = False,False
            authorize_net_config = self.pool.get('authorize.net.config')
            exception_object=self.pool.get('partner.payment.error')
            current_obj=self.browse(cr,uid,ids[0])
            config_ids = authorize_net_config.search(cr,uid,[])
            customer_profile_id=current_obj.partner_id.customer_profile_id
            act_model='account.invoice'
            next_try_date=current_obj.date_invoice
            next_retry_date=datetime.datetime.strptime(next_try_date, "%Y-%m-%d")
            next_retry_date=next_retry_date+datetime.timedelta(weeks=1)
            if config_ids and customer_profile_id:
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                cust_payment_profile_id = current_obj.customer_payment_profile_id
                transaction_type = current_obj.auth_transaction_type
                amount=current_obj.amount_total
                try:
                    capture_status = current_obj.capture_status
                    if not capture_status:
                        #context['recurring_billing'] =True
                        transaction_details =authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',ids[0],transaction_type,amount,customer_profile_id,cust_payment_profile_id,'',act_model,'',context)
                        if transaction_details:
                            transaction_response = transaction_details.get('response')
                            if transaction_response:
                                if transaction_details.get('resultCode') == 'Ok':
                                    cr.execute("UPDATE account_invoice SET capture_status='captured' where id=%d"%(ids[0]))
                                    self.api_response(cr,uid,ids[0],transaction_response,cust_payment_profile_id,transaction_type,context)
                                else:
                                    if transaction_details.get('message'):
                                        vals={'partner_id':current_obj.partner_id.id,
                                                'invoice_name':current_obj.origin,
                                                'invoice_date':current_obj.date_invoice,
                                                'invoice_id':ids[0],
                                                'message':transaction_details.get('message'),
						'source': source,
						'next_retry_date':next_retry_date,
						'active_payment':True,
                                                }
					if not context.get('called_from_rentals',False):
	                                        exception_id = exception_object.create(cr,uid,vals,context)
						exception_id_brw =exception_object.browse(cr,uid,exception_id)
#                                    transaction_response =  transaction_response[2]
 #                                   if transaction_response in ('2','3') :
                	                        self.pool.get('sale.order').email_to_customer(cr,uid,exception_id_brw,'partner.payment.error','payment_exception',current_obj.partner_id.emailid,context)
					else:
                                            	msg=vals.get('message')
                                            	cr.execute("UPDATE account_invoice SET comment='%s' where id=%d"%(msg,ids[0]))
                                    return False
                    state = current_obj.state
                    if state != 'paid':
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'account.invoice', ids[0], 'invoice_open', cr)
                        returnval = self.make_payment_of_invoice(cr, uid, ids, context=context)
                except Exception, e:
                        #print "Error in URLLIB",str(e)
                        self.write(cr,uid,ids,{'comment':str(e)})
			if not context.get('called_from_rentals',False):
		        	vals={
                	        'partner_id':current_obj.partner_id.id,
	                        'invoice_name':current_obj.origin,
        	                'invoice_date':current_obj.date_invoice,
                	        'invoice_id':ids[0],
                        	'message':str(e),
				'source': source,
				'next_retry_date':next_retry_date
	                        }
        	                exception_object.create(cr,uid,vals,context)
            return returnval

    def run_recurring_billing_scheduler(self, cr, uid, context=None):
        self.recurring_billing(self,cr,uid,args=None)
    #####Code to not to calculate taxes for service Products
    def create_lines(self, cr, uid, invoice_lines, sign):
        lines = []
        for line in invoice_lines:
            if line.product_id.type != 'service':
                lines.append({
                    'qty': line.quantity,
                    'itemcode': line.product_id and line.product_id.default_code or None,
                    'description': line.name,
                    'amount': sign * line.price_unit * (1-(line.discount or 0.0)/100.0) * line.quantity,
                    'tax_code': line.product_id and ((line.product_id.tax_code_id and line.product_id.tax_code_id.name) or
                            (line.product_id.categ_id.tax_code_id  and line.product_id.categ_id.tax_code_id.name)) or None
                })
            else:
                cr.execute('select order_line_id from sale_order_line_invoice_rel where invoice_id=%d'%(line.id))
                search_so_line = filter(None, map(lambda x:x[0], cr.fetchall()))
                if search_so_line:
                    line_obj =  self.pool.get('sale.order.line')
                    child_so_line_ids = line_obj.search(cr,uid,[('parent_so_line_id','=',search_so_line[0])])
                    for line in line_obj.browse(cr,uid,child_so_line_ids):
                        if line.product_id.type != 'service':
                            lines.append({
                                    'qty': line.product_uom_qty,
                                    'itemcode': line.product_id and line.product_id.default_code or None,
                                    'description': line.name,
                                    'amount': sign * line.price_unit * (1-(line.discount or 0.0)/100.0) * line.product_uom_qty,
                                    'tax_code': line.product_id and ((line.product_id.tax_code_id and line.product_id.tax_code_id.name) or
                                            (line.product_id.categ_id.tax_code_id  and line.product_id.categ_id.tax_code_id.name)) or None
                                        })
        return lines
        
    ########*
    recurring = fields.Boolean('Recurring Payment')
    credit_id = fields.Many2one('credit.service',string="Service Credit ID",help="Date on which next Payment will be generated.")
    next_billing_date = fields.Datetime('Next Billing Date',select=True, help="Date on which next Payment will be generated.")
    avatax_calc = fields.Boolean(string='Avatax Calculation',store=True,compute='_avatax_calc')
    location_address_id = fields.Many2one('res.partner','Location Address')
    refund_generated  = fields.Boolean('Refund Generated')
account_invoice()

class account_tax(osv.osv):
    _inherit='account.tax'
#    _columns = {
#    'account_collected_id':fields.property(
##            'account.account',
#            type='many2one',
#            relation='account.account',
#            string="Invoice Tax Account",
##            view_load=True
#            ),
#    'account_paid_id':fields.property(
##            'account.account',
#            type='many2one',
#            relation='account.account',
#            string="Refund Tax Account ",
##            view_load=True
#            )}
    #Function is inherited because want to send customer billing address not shipping address
    def _check_compute_tax(self, cr, uid, avatax_config, doc_date, doc_code, doc_type, partner, ship_from_address_id, billing_address_id,
                          lines, shipping_charge, user=None, commit=False, invoice_date=False, reference_code=False, context=None):
        address_obj = self.pool.get('res.partner')
        if not ship_from_address_id:
            raise osv.except_osv(_('No Ship from Address Defined !'), _('There is no company address defined.'))
        if not billing_address_id:
                raise osv.except_osv(_('No Billing Address Defined !'), _('There is no Billing address defined for the partner.'))
        ship_from_address = address_obj.browse(cr, uid, ship_from_address_id, context=context)
        billing_address = address_obj.browse(cr, uid, billing_address_id, context=context)
        if not lines:
            raise osv.except_osv(_('Error !'), _('AvaTax needs atleast one sale order line defined for tax calculation.'))
        if avatax_config.force_address_validation:
            if not billing_address.date_validation:
                raise osv.except_osv(_('Address Not Validated !'), _('Please validate the Billing address for the partner %s.'
                            % (partner.name)))
        if not ship_from_address.date_validation:
            raise osv.except_osv(_('Address Not Validated !'), _('Please validate the company/Location address.'))
        if shipping_charge:
            lines.append({
                'qty': 1,
                'amount': shipping_charge,
                'itemcode': '',
                'description': '',
                'tax_code': avatax_config.default_shipping_code_id.name
            })
        avapoint = suds_client.AvaTaxService(avatax_config.account_number, avatax_config.license_key,
                                 avatax_config.service_url, avatax_config.request_timeout, avatax_config.logging)
        avapoint.create_tax_service()
        addSvc = avapoint.create_address_service().addressSvc
        origin = suds_client.BaseAddress(addSvc, ship_from_address.street or None,
                             ship_from_address.street2 or None,
                             ship_from_address.city, ship_from_address.zip,
                             ship_from_address.state_id and ship_from_address.state_id.code or None,
                             ship_from_address.country_id and ship_from_address.country_id.code or None, 0).data
        destination = suds_client.BaseAddress(addSvc, billing_address.street or None,
                                  billing_address.street2 or None,
                                  billing_address.city, billing_address.zip,
                                  billing_address.state_id and billing_address.state_id.code or None,
                                  billing_address.country_id and billing_address.country_id.code or None, 1).data
        
        result = avapoint.get_tax(avatax_config.company_code, doc_date, doc_type,
                                 partner.name, doc_code, origin, destination,
                                 lines, partner.exemption_number or None,
                                 partner.exemption_code_id and partner.exemption_code_id.code or None,
                                 user and user.name or None, commit, invoice_date, reference_code)
        return result
    #Function is inherited becuase search tax id based on the exact amount not in range
    def get_tax_from_rate(self, cr, uid, rate, is_tax_included=False, context=None):
        #TODO improve, if tax are not correctly mapped the order should be in exception (integration with sale_execption)
        tax_ids = self.pool.get('account.tax').search(cr, uid, [('price_include', '=', is_tax_included),
                ('type_tax_use', 'in', ['sale', 'all']), ('amount', '=', rate)])
        if tax_ids and len(tax_ids) > 0:
            return tax_ids[0]
        return False
account_tax()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    def move_line_get(self, cr, uid, invoice_id, context=None):
#        print"move line get context",context
        if context==None:
            context = {}
        res,cox_sales_channels = [],''
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        invoice_obj = self.pool.get('account.invoice')
        inv = invoice_obj.browse(cr, uid, invoice_id, context=context)
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        inv_type = inv.type
        return_order = self.pool.get('return.order')
        so_obj = self.pool.get('sale.order')
        search_sale =  so_obj.search(cr,uid,[('name','=',inv.origin)])
        if search_sale:
            cox_sales_channels = so_obj.browse(cr,uid,search_sale[-1]).cox_sales_channels
        for line in inv.invoice_line:
            ##Extra Code Starts here
            child_so_line_ids = []
            if inv_type == 'out_invoice':
                if cox_sales_channels == 'amazon':
                    child_so_line_ids = []
                else:
                    cr.execute("select id from sale_order_line where parent_so_line_id in (select order_line_id from sale_order_line_invoice_rel where invoice_id = %s)"%(line.id))
                    child_so_line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                    print"child_so_line_ids",child_so_line_ids
            elif inv_type == 'out_refund':
                return_ref = (inv.return_ref.split("/") if inv.return_ref else  False)
                if return_ref:
                    return_ref = return_ref[0]
                    return_id = return_order.search(cr,uid,[('name','ilike',return_ref)])
                    if return_id:
                        sale_order_id = return_order.browse(cr,uid,return_id[0]).linked_sale_order
                        cr.execute("select id from account_invoice where (recurring=False or recurring is Null) and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple([sale_order_id.id]),))
                        invoice_id = cr.fetchone()
                        if invoice_id:
                            date_invoice =invoice_obj.browse(cr,uid,invoice_id[0]).date_invoice
                            if date_invoice > '2014-04-03':
                                cr.execute("select id from sale_order_line where parent_so_line_id in (select sale_line_id from return_order_line where id in (select order_line_id from return_order_line_invoice_rel where invoice_id = %s))"%(line.id))
                                child_so_line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            print"child_so_line_ids",child_so_line_ids,context
#            fjkdhgjf
            if child_so_line_ids:
                for each_so_line in child_so_line_ids:
                    context={'so_line_id':each_so_line}  ##cox gen2
                    mres = self.move_line_get_item(cr, uid, line, context)
                    if not mres:
                        continue
                    res.append(mres)
            else:
            #Endes here
#                context.update({'so_line_id' : False})  cox gen2
                context={}
                mres = self.move_line_get_item(cr, uid, line, context)
                if not mres:
                    continue
                res.append(mres)
            tax_code_found= False
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
                    (line.price_unit * (1.0 - (line['discount'] or 0.0) / 100.0)),
                    line.quantity, line.product_id,
                    inv.partner_id)['taxes']:

                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = line.price_subtotal * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = line.price_subtotal * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context={'date': inv.date_invoice})
        return res

    def move_line_get_item(self, cr, uid, line, context=None):
        ##Extra Code Starts here
        if context and context.get('so_line_id'):
            so_line_id_brw = self.pool.get('sale.order.line').browse(cr,uid,context.get('so_line_id'))
            if so_line_id_brw.product_id.property_account_income.id:
                account_id = so_line_id_brw.product_id.property_account_income.id
            else:
                account_id = so_line_id_brw.product_id.categ_id.property_account_income_categ.id
            return {
            'type':'src',
            'name': so_line_id_brw.name.split('\n')[0][:64],
            'price_unit':so_line_id_brw.price_unit,
            'quantity':so_line_id_brw.product_uom_qty,
            'price':(so_line_id_brw.price_unit) * (so_line_id_brw.product_uom_qty),
            'account_id':account_id,
            'product_id':so_line_id_brw.product_id.id,
            'uos_id':so_line_id_brw.product_uom.id,
            'account_analytic_id':False,
            'taxes':so_line_id_brw.tax_id,
            }
        else:
        #Endes here
            return {
            'type':'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit':line.price_unit,
            'quantity':line.quantity,
            'price':line.price_subtotal,
            'account_id':line.account_id.id,
            'product_id':line.product_id.id,
            'uos_id':line.uos_id.id,
            'account_analytic_id':line.account_analytic_id.id,
            'taxes':line.invoice_line_tax_id,
            }
account_invoice_line()

class account_invoice_tax(models.Model):
    _inherit = 'account.invoice.tax'
    #Function is inherited because want to pass location address id
    def compute(self, cr, uid, invoice, context=None):
        print"cox communication"
#        invoice = invoice_id
#        invoice_id = invoice_id.id
        try:
            avatax_config_obj = self.pool.get('account.salestax.avatax')
            invoice_obj = self.pool.get('account.invoice')
            account_tax_obj = self.pool.get('account.tax')
            jurisdiction_code_obj = self.pool.get('jurisdiction.code')
            cur_obj = self.pool.get('res.currency')
            state_obj = self.pool.get('res.country.state')
#            invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
            tax_grouped = {}
            if invoice._avatax_calc():
#                print"invoice111111111111"
                cur = invoice.currency_id
                company_currency = invoice.company_id.currency_id.id
                lines = invoice_obj.create_lines(cr, uid, invoice.invoice_line, 1)
                if lines:
                    avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid)
                    # to check for company address
    #                company_address = partner_obj.address_get(cr, uid, [invoice.company_id.partner_id.id], ['default'])
                    address = invoice.location_address_id.id
                    for tax in account_tax_obj._check_compute_tax(cr, uid, avatax_config,
                                                                  invoice.date_invoice or time.strftime('%Y-%m-%d'),
                                                                  invoice.internal_number, 'SalesOrder', invoice.partner_id,
                                                                  address, invoice.partner_id.id,
                                                                  lines, invoice.shipcharge, invoice.user_id, False,
                                                                  invoice.date_invoice or time.strftime('%Y-%m-%d'),
                                                                  context=context).TaxSummary[0]:
                        val = {}
                        state_ids = state_obj.search(cr, uid, [('code', '=', tax.Region)], context=context)
                        state_id = state_ids and state_ids[0] or False
                        jurisdiction_code_ids = jurisdiction_code_obj.search(cr, uid, [('type', '=', tax['JurisType'].lower()),
                                                                            ('tax_schedule_id', '=', avatax_config.default_tax_schedule_id.id),
                                                                            ('state_id', '=', state_id)],
                                                                            context=context)
                        if not jurisdiction_code_ids:
                            jurisdiction_code_ids = jurisdiction_code_obj.create(cr,uid,
                            {'name': str(tax.Region) + tax['JurisType'].lower(),
                                'code': str(tax.Region),
                                'type': tax['JurisType'].lower(),
                                'state_id':state_id,
                                'tax_schedule_id':avatax_config.default_tax_schedule_id.id
                            })
                            if jurisdiction_code_ids:
                                jurisdiction_code_ids = [int(jurisdiction_code_ids)]
                            if not jurisdiction_code_ids:
                                raise osv.except_osv(
                                _('Jurisdiction Code is not defined !'),
                                _('You must define a jurisdiction code for %s type for %s state in the tax schedule for %s.'
                                  % (tax['JurisType'], tax['Region'], avatax_config.default_tax_schedule_id.name)))
                        jurisdiction_code = jurisdiction_code_obj.browse(cr, uid, jurisdiction_code_ids[0], context=context)
                        val['invoice_id'] = invoice.id
                        val['name'] = tax['TaxName'] or '/'
                        ###val['amount'] = tax['Tax']
			
                        val['amount'] = tax['Tax']
			#val['amount'] = tax['Tax'] - (tax['Tax'] * (invoice.add_disc/100)) # added for additional discount
                        val['manual'] = False
                        val['base'] = tax['Base']
                        if invoice.type == 'out_invoice':
                            val['base_code_id'] = jurisdiction_code.base_code_id.id
                            val['tax_code_id'] = jurisdiction_code.tax_code_id.id
                            val['base_amount'] = cur_obj.compute(cr, uid, invoice.currency_id.id,
                                                                 company_currency, val['base'] * jurisdiction_code.base_sign,
                                                                 context={'date': invoice.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                            val['tax_amount'] = cur_obj.compute(cr, uid, invoice.currency_id.id,
                                                                company_currency, val['amount'] * jurisdiction_code.tax_sign,
                                                                context={'date': invoice.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                            val['account_id'] = jurisdiction_code.account_collected_id.id
                            val['base_sign'] = jurisdiction_code.base_sign
                        else:
                            val['base_code_id'] = jurisdiction_code.ref_base_code_id.id
                            val['ref_base_code_id'] = jurisdiction_code.ref_base_code_id.id
                            val['tax_code_id'] = jurisdiction_code.ref_tax_code_id.id
                            val['base_amount'] = cur_obj.compute(cr, uid, invoice.currency_id.id,
                                                                 company_currency, val['base'] * jurisdiction_code.ref_base_sign,
                                                                 context={'date': invoice.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                            val['tax_amount'] = cur_obj.compute(cr, uid, invoice.currency_id.id,
                                                                company_currency, val['amount'] * jurisdiction_code.ref_tax_sign,
                                                                context={'date': invoice.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                            val['account_id'] = jurisdiction_code.account_paid_id.id
                            val['ref_base_sign'] = jurisdiction_code.ref_base_sign
                            
                        key = (val['tax_code_id'], val['base_code_id'], val['account_id'],False) # Added at place of analytic account
                        if not key in tax_grouped:
                            tax_grouped[key] = val
                        else:
                            tax_grouped[key]['amount'] += val['amount']
                            tax_grouped[key]['base'] += val['base']
                            tax_grouped[key]['base_amount'] += val['base_amount']
                            tax_grouped[key]['tax_amount'] += val['tax_amount']
                    for t in tax_grouped.values():
                        t['base'] = cur_obj.round(cr, uid, cur, t['base'])
                        t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
                        t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
                        t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
                    print "tax_grouped",tax_grouped    
                    return tax_grouped
        except Exception, e:
            print"exceptionnnnnnnnnnnn",e,invoice
            self.pool.get('account.invoice').write(cr,uid,invoice.id,{'comment':str(e)})
#            invoice_obj.write(cr,uid,invoice_id,{'comment':str(e)})
        return super(account_invoice_tax, self).compute(cr, uid,invoice)
account_invoice_tax()


#class account_invoice_report(osv.osv):
#    _inherit = 'account.invoice.report'
#    
#    _columns={
#        'year':fields.char('Year',size=64, readonly=True),
#        'day':fields.char('Day', size=64, readonly=True),
#        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
#        ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
#        ('10','October'), ('11','November'), ('12','December')], 'Month' , readonly=True),
#    }
##    year = fields.Char(string='Year', size=4,index=True, readonly=True)
##    day = fields.Char(string='Day', size=128, index=True, readonly=True)
##    month = fields.Selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
##        ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
##        ('10','October'), ('11','November'), ('12','December')], string= 'Month', index=True, readonly=True)
#    
#account_invoice_report()
