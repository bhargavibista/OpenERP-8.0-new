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
from openerp.http import request


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
        print"vals",vals
        res=super(account_move_line, self).create(cr, uid, vals, context)
        return res
    
    invoice_line_id=fields.Many2one('account.invoice.line','Invoice Lines')

account_move_line()

#code by riyaz for issues related to manual validation of invoice for parter having parent company
class account_voucher(osv.osv):
    _inherit = "account.voucher"
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        print "onchange partner_id-----------",partner_id
        if partner_id:
            print"idffffffffffffffffffffffffffffff"
            parent_id=self.pool.get('res.partner').browse(cr,uid,partner_id).parent_id.id
            print "parent_id----------------",parent_id
            if parent_id:
                partner_id=parent_id
        res=super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context)
        return res
account_voucher()


class account_invoice(models.Model):
    _inherit='account.invoice'
    
    @api.multi
    def check_tax_lines(self, compute_taxes):
        print"self.tax_lineself.tax_lineself.tax_line",self.tax_line
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

    @api.multi
    def action_move_create(self):
        """
        This calls the finalize_invoice_move_lines and creates the moves and the
        revenue recognition schedule.
        """
#        sale_obj=self.pool.get('sale.order')
        sale_obj=self.env['sale.order']
        print"sale_objsale_objsale_objsale_objsale_obj",sale_obj
        for inv in self.browse():
            print"invinvinvinvinvinvinv",inv
            if not inv.date_invoice:
                date_confirm = sale_obj.date_order_confirm(cr,uid,context)
                print"date_invoicedate_invoicedate_invoicedate_invoicedate_invoice------------",inv.date_invoice,date_confirm
                self.write({'date_invoice':date_confirm})
                inv.refresh()
        super(account_invoice,self).action_move_create()
        request.cr.execute("select order_id from sale_order_invoice_rel where invoice_id='%s'"%(self.ids[0])) 
        so_id=filter(None, map(lambda x:x[0], request.cr.fetchall()))
        print"so_idso_idso_idso_idso_idso_idso_idso_idso_idso_idso_idso_idso_idso_id",so_id
        if so_id:
            sale_brw=sale_obj.browse(so_id[0])
            print"sale_brwsale_brwsale_brwsale_brw",sale_brw
            sales_channel=sale_brw.cox_sales_channels
            print"sales_channelsales_channelsales_channel",sales_channel,self
            if not sales_channel=='playjam':
                # Process the invoices
                for inv in self:
                    print"invinvinvinvinvinv",inv
                    if inv.type in ('out_invoice','in_invoice'):
                        move_line_obj=self.pool.get('account.move.line')
                        print'inv.move_id.idinv.move_id.idinv.move_id.id',inv.move_id.id
                        request.cr.execute("select id from account_move_line where credit!=0.00 and product_id in (select id from product_product where product_tmpl_id in (select id from product_template where product_type='service')) and move_id=%s"%(inv.move_id.id))
                        move_line_ids=filter(None, map(lambda x:x[0], request.cr.fetchall()))
                        print"move_objmove_objmove_objmove_obj",move_line_ids
                        if move_line_ids:
                        # Process the customer invoice
                            self._process_invoice_line(move_line_ids, inv)
                return True

    def _amount_currency(self, line, invoice): 
        """
        Calculate the invoice line net amount based on the company currency. This amount will be used
        for the journals.
        """
        price=line.debit if 'Discount' in line.name else line.credit
        curr_obj = self.pool.get('res.currency')
        amount = curr_obj.compute(request.cr, request.uid, invoice.currency_id.id, invoice.company_id.currency_id.id,
                                  price, context={'date':invoice.date_invoice}) 
        return amount

    @api.one
    def _process_invoice_line(self,line, invoice):
        print"lineeeeeee",line
        
        """
        Handle the creation of the revenue recognition schedule and the initial journal to move
        the invoice line amount into the Unearned Income account.
        """
        # Exit if revenue recognition is not required
        if invoice.recurring==True:
            return
        for each_line in line:
            print"request.cr,request.uidrequest.cr,request.uid",request.cr,request.uid
            line_brw = self.pool.get('account.move.line').browse(request.cr,self._uid,each_line)
            # Get the revenue recognition journal
            domain = [('code','=',_('RCJ')),'|',('company_id','=',invoice.company_id.id),('company_id','=',False)]
            journal_ids = self.pool.get('account.journal').search(request.cr,self._uid, domain) 
            print"journal_idsjournal_idsjournal_idsjournal_ids",journal_ids
            if len(journal_ids)==0:
                raise osv.except_osv(_("Error in Invoice Line '%s'" % line_brw.name), _("Cannot find the Recognition Journal for this company."))
            # Generate the revenue recognition schedule
            self._create_schedule(each_line, invoice, journal_ids[0])

    def _create_schedule(self,line, invoice, journal_id): 
        print"_create_schedule_create_schedule_create_schedule_create_schedule",invoice,journal_id
        """
        Generate the revenue recognition schedule records, based on the contract start and end
        and the net invoice line value.
        """
        move_line_obj=self.pool.get('account.move.line')
#        schedule = []
        # Calculate the contract length in days and daily rate (rounded)
        contract_start = datetime.datetime.strptime(str(invoice.date_invoice), '%Y-%m-%d').date()
        for each_inv_line in invoice.invoice_line:
            free_trail_months=each_inv_line.product_id.free_trail_days
            if free_trail_months>0:
                contract_end=contract_start+relativedelta(months=free_trail_months)
            else:
                return
        contract_end = datetime.datetime.strptime(str(contract_end), '%Y-%m-%d').date()
        days = (contract_end - contract_start).days
        print"contract_startcontract_start",contract_start,contract_end,days
            # Create revenue recognition as a list
        if contract_start > datetime.date.today():
            this_date = contract_start
        else:
            this_date = datetime.date.today()

        while this_date<contract_end:
            move_lines=[]
            amount,total_amount,total_amounts=0.0000,0.0000,0.0000
            print"this_datethis_datethis_datethis_datethis_date",this_date
            for each_line in move_line_obj.browse(request.cr,request.uid,line): 
                print"each_lineeach_lineeach_line",each_line
            # Calculate last day of month (or contract)
                amount = self._amount_currency(each_line, invoice)
                day_rate = round(amount / free_trail_months,3)
                print"day_rateday_rateday_rateday_rateday_rateday_rateday_rateday_rateday_rateday_rate",day_rate
                last_day = this_date+relativedelta(months=1)

                if last_day > contract_end:
                    last_day = contract_end
                print"last_daylast_daylast_day",last_day,day_rate
                # Calculate the pro-rata revenue for the last period
                period_amount=day_rate
                total_amount +=period_amount
                print"period_amountperiod_amountperiod_amountperiod_amount-",period_amount,day_rate,amount,total_amount
                # Save this scheduled amount

                if invoice.type=='out_invoice':
                    debit_account_id = each_line.account_id.id
                    credit_account_id = each_line.product_id.property_account_income.id
                else:
                    # Supplier invoice
                    debit_account_id = each_line.product_id.property_account_income.id
        #            credit_account_id = line.unearned_account_id.id
                    credit_account_id = each_line.account_id.id
                ml_credit = self._move_line_create(invoice, journal_id)
                ml_credit.update({
                        'name':'Revenue Recognition/Prepayment',
                        'date':last_day,
                        'date_maturity': last_day,
                        'account_id': credit_account_id,
                        'credit': period_amount})
                move_lines.append((0,0,ml_credit))
                ml_debit = self._move_line_create(invoice, journal_id)
                ml_debit.update({
                        'name':'/',
                        'date_maturity': last_day,
                        'date':last_day,
                        'account_id': debit_account_id,
                        'debit': period_amount})
                move_lines.append((0,0,ml_debit))
                print"ml_creditml_creditml_creditml_credit",ml_credit,ml_debit
#                period_id = self._period_get(invoice.company_id.id,last_day)
#                print"period_idperiod_idperiod_idperiod_idperiod_idperiod_id",period_id
            move = {
                'ref': invoice.move_id.name,
                'line_id': move_lines,
                'journal_id': journal_id,
                'date':last_day,
#                'period_id': period_id,
                }
            context = {'journal_id': journal_id}
            move_id = self.pool.get('account.move').create(request.cr, request.uid, move, context=context)
            this_date = last_day
            print"move_idmove_idmove_idmove_id",move_id

    def _move_line_create(self, invoice, journal_id):
        return {
            'date_maturity': invoice.date_invoice,
            'partner_id': invoice.partner_id.id,
            'date': invoice.date_invoice,
            'ref': invoice.move_id.name,
            'journal_id': journal_id,
            }

    def _period_get(self,company_id, date): 
        # Get the current accounting period for the company
        period_ids = self.pool.get('account.period').search(request.cr, request.uid, [('date_start','<=',date),('date_stop','>=',date), ('company_id', '=', company_id)]) 
        if not period_ids or len(period_ids)==0:
            raise osv.except_osv(_('Error!'), _("Cannot find an Accounting Period for the company."))
        return period_ids[0]


    def post_revenue_recognition(self, *args): 
        """
        Run by a scheduled task (daily).
        Reads the revenue recognition records for the run date (or older) and post financial journals for
        the draft schedule records.
        """
        today=datetime.date.today()
        logger = netsvc.Logger()
        logger.notifyChannel('post_revenue', netsvc.LOG_INFO,'Generating revenue recognition journals')
        acc_move_obj=self.pool.get('account.move')
        domain = [('name','=',_('Recognition Journal'))]
        journal_ids = self.pool.get('account.journal').search(cr, uid, domain)
        print"journal_idsjournal_idsjournal_idsjournal_ids",journal_ids
        if len(journal_ids)==0:
            raise osv.except_osv(_("Error"), _("Cannot find the Recognition Journal for this company."))
        # Get the scheduled revenue recognition records for today
        move_ids=acc_move_obj.search(cr,uid,[('state','=','draft'),('date','<=',today),('journal_id','=',journal_ids[0])])
        if move_ids:
            move_obj=self.pool.get('account.move')
            for each_move in move_obj.browse(request.cr, request.uid,move_ids):
                period_id = self._period_get(request.cr, request.uid, each_move.company_id.id,each_move.date) 
                print"period_idperiod_idperiod_idperiod_idperiod_id",period_id
                each_move.write({'period_id':period_id})
            move_obj.post(request.cr, request.uid, move_ids)
        logger.notifyChannel('post_revenue', netsvc.LOG_INFO,'Completed revenue recognition journals')

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': part,
            'name': x['name'][:64],
            'date': date,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', []),
            'amount_currency': x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount', False),
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
            'invoice_line_id':x.get('invoice_line_id',False),
        }
            
                
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
            print"customer_profile_idcustomer_profile_id",customer_profile_id,config_ids
            act_model='account.invoice'
            next_try_date=current_obj.date_invoice
            next_retry_date=datetime.datetime.strptime(next_try_date, "%Y-%m-%d")
            next_retry_date=next_retry_date+datetime.timedelta(weeks=1)
            if config_ids and customer_profile_id:
		print "config ids//////////////////////////////",config_ids,customer_profile_id
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                cust_payment_profile_id = current_obj.customer_payment_profile_id
                print"cust_payment_profile_idcust_payment_profile_idcust_payment_profile_id",cust_payment_profile_id
                transaction_type = current_obj.auth_transaction_type
                print"transaction_typetransaction_typetransaction_type",transaction_type,current_obj.capture_status
                amount=current_obj.amount_total
                try:
                    capture_status = current_obj.capture_status
		    print "cpature status///////////////////////////////////",capture_status
                    if not capture_status:
                        ccv=''
                        #context['recurring_billing'] =True
                        transaction_details =authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',ids[0],transaction_type,amount,customer_profile_id,cust_payment_profile_id,'',ccv,act_model,'',context)
                        print"transaction_detailstransaction_detailstransaction_details",transaction_details
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
        policy_object=self.pool.get('res.partner.policy') 
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
                if line.product_id.free_trail_days>0:
                    context={'free_trail_days':line.product_id.free_trail_days}
            elif inv_type == 'out_refund':
                return_ref = (inv.return_ref.split("/") if inv.return_ref else  False)
                if return_ref:
                    return_ref = return_ref[0]
                    return_id = return_order.search(cr,uid,[('name','ilike',return_ref)])
                    if return_id:
                        #Start code Preeti for RMA
                        if return_order.browse(cr,uid,return_id[0]).linked_sale_order:
                            sale_order_id = return_order.browse(cr,uid,return_id[0]).linked_sale_order
                            cr.execute("select id from account_invoice where (recurring=False or recurring is Null) and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple([sale_order_id.id]),))
                        else:                            
                            return_brw = return_order.browse(cr,uid,return_id[0])
                            policy_id =return_brw.service_id
                            policy_brw=policy_object.browse(cr,uid,policy_id.id)
                            linked_sale_id=policy_brw.sale_id                                       
                            cr.execute("select id from account_invoice where (recurring=False or recurring is Null) and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple([linked_sale_id]),))
                        #End code Preeti for RMA
                        invoice_id = cr.fetchone()
                        if invoice_id:
                            date_invoice =invoice_obj.browse(cr,uid,invoice_id[0]).date_invoice
                            if date_invoice > '2014-04-03':
                                cr.execute("select id from sale_order_line where parent_so_line_id in (select sale_line_id from return_order_line where id in (select order_line_id from return_order_line_invoice_rel where invoice_id = %s))"%(line.id))
                                child_so_line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#                        sale_order_id = return_order.browse(cr,uid,return_id[0]).linked_sale_order
#                        cr.execute("select id from account_invoice where (recurring=False or recurring is Null) and id in (select invoice_id from sale_order_invoice_rel where order_id in %s)",(tuple([sale_order_id.id]),))
#                        invoice_id = cr.fetchone()
#                        if invoice_id:
#                            date_invoice =invoice_obj.browse(cr,uid,invoice_id[0]).date_invoice
#                            if date_invoice > '2014-04-03':
#                                cr.execute("select id from sale_order_line where parent_so_line_id in (select sale_line_id from return_order_line where id in (select order_line_id from return_order_line_invoice_rel where invoice_id = %s))"%(line.id))
#                                child_so_line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            print"child_so_line_ids",child_so_line_ids,context
#            fjkdhgjf
            if child_so_line_ids:
                for each_so_line in child_so_line_ids:
                    if not context:
                        context={'so_line_id':each_so_line}  ##cox gen2
                    else:
                        context['so_line_id']=each_so_line
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
        print"contextcontextcontextcontext--------------------",context
        ##Extra Code Starts here
        if context and context.get('so_line_id'):
            so_line_id_brw = self.pool.get('sale.order.line').browse(cr,uid,context.get('so_line_id'))
            if so_line_id_brw.product_id.property_account_income.id:
                account_id = so_line_id_brw.product_id.property_account_income.id
            else:
                account_id = so_line_id_brw.product_id.categ_id.property_account_income_categ.id
            if so_line_id_brw.price_unit!=0.00:
                if so_line_id_brw.product_id.type=='service' and context.get('free_trail_days',False)>0:
                    if so_line_id_brw.product_id.property_account_line_prepaid_revenue.id:
                        account_id = so_line_id_brw.product_id.property_account_line_prepaid_revenue.id
                    else:
                        account_id = so_line_id_brw.product_id.categ_id.property_account_line_prepaid_revenue_categ.id
            print"account_idaccount_idaccount_idaccount_idaccount_id",account_id
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
            'invoice_line_id':line.id,
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
            'invoice_line_id':line.id,
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
                print"invoice111111111111"
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
