# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

import time
from openerp.osv import osv, fields
from openerp.tools.translate import _

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    def capture_payment(self,cr,uid,ids,context={}):
        if context is None:
            context={}
        (data,) = self.browse(cr,uid,ids)
        config_ids = self.pool.get('authorize.net.config').search(cr,uid,[])
        model = 'sale.order'
        if config_ids:
            config_obj = self.pool.get('authorize.net.config').browse(cr,uid,config_ids[0])
            obj_all = self.browse(cr,uid,ids[0])
            model = 'account.invoice'
            amount_total = obj_all.amount_total
            customer_id = obj_all.partner_id
            approval_code = obj_all.auth_transaction_id
            customer_payment_profile_id = obj_all.customer_payment_profile_id
            customer_profile_id = customer_id.customer_profile_id
            context['captured_api'] = True
            transaction_details =self.pool.get('authorize.net.config').call(cr,uid,config_obj,'CreateCustomerProfileTransaction',ids[0],'profileTransPriorAuthCapture',amount_total,customer_profile_id,customer_payment_profile_id,approval_code,model,'',context)
            
            if transaction_details:
                if transaction_details.get('resultCode') == 'Ok':
                    cr.execute("UPDATE account_invoice SET capture_status='captured' where id=%d"%(ids[0]))
                return transaction_details
#                    context.update({'captured':True})
#                    wf_service = netsvc.LocalService("workflow")
#                    wf_service.trg_validate(uid, 'account.invoice', data.id, 'invoice_open', cr)
#                    returnval = self.make_payment_of_invoice(cr, uid, ids, context=context)
#                    inv_payment = super(account_invoice, self).invoice_pay_customer(cr, uid, ids, context=context)
            
        else:
            raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
        return True
    _columns = {
            'auth_transaction_id' :fields.char('Transaction ID', size=40,readonly=True),
            'auth_transaction_type': fields.char('Transaction Type',size=156),
            'authorization_code': fields.char('Authorization Code',size=64,readonly=True),
            'customer_profile_id': fields.char('Customer Profile ID',size=64,readonly=True),
            'customer_payment_profile_id': fields.char('Payment Profile ID',size=64,readonly=True),
            'capture_status': fields.char('Capture Status',size=64),
            'auth_respmsg' :fields.text('Response Message',readonly=True),
            'cc_number' :fields.char('Credit Card Number', size=64),
	}

    def api_response(self,cr,uid,ids,response,payment_profile_id,transaction_type,context={}):
        split = response.split(',')
        vals = {}
        transaction_id = split[6]
        transaction_message = split[3]
        authorize_code = split[4]
        if transaction_id and transaction_message:
            vals['auth_transaction_id'] = transaction_id
            vals['auth_respmsg'] = transaction_message
        if authorize_code:
            vals['authorization_code'] = authorize_code
        if payment_profile_id:
            vals['customer_payment_profile_id'] = payment_profile_id
        if transaction_type:
            vals['auth_transaction_type'] = transaction_type
        if context.get('cc_number'):
            vals['cc_number'] = context.get('cc_number')
        if context.get('customer_profile_id'):
            vals['customer_profile_id'] = context.get('customer_profile_id')
        if vals:
                self.write(cr,uid,ids,vals)
        self.log(cr,uid,ids,transaction_message)
        return True
    def make_payment_of_invoice(self, cr, uid, ids, context):
#         logger = netsvc.Logger()
         if not context:
             context = {}
         inv_obj = self.browse(cr,uid,ids[0])
	 account_obj=self.pool.get('account.account')
         voucher_id = False
         invoice_number = inv_obj.number
         voucher_pool = self.pool.get('account.voucher')
         journal_pool = self.pool.get('account.journal')
         period_obj = self.pool.get('account.period')
	 if context.get('journal_type',''):
            bank_journal_ids=  journal_pool.search(cr, uid, [('type', '=', context.get('journal_type'))])
         else:
            bank_journal_ids = journal_pool.search(cr, uid, [('type', '=', 'bank')])
         if not len(bank_journal_ids):
             return True
         context.update({
                 'default_partner_id': inv_obj.partner_id.id,
                 'default_amount': inv_obj.amount_total,
                 'default_name':inv_obj.name,
                 'close_after_process': True,
                 'invoice_type':inv_obj.type,
                 'invoice_id':inv_obj.id,
                 'journal_id':bank_journal_ids[0],
                 'default_type': inv_obj.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
         })
         if inv_obj.type in ('out_refund','in_refund'):
             context.update({'default_amount':-inv_obj.amount_total})
         tax_id = self._get_tax(cr, uid, context)
         account_data = self.get_accounts(cr,uid,inv_obj.partner_id.id,bank_journal_ids[0])
         account_id=account_data['value']['account_id']
         if context.has_key('wallet_purchase'):
            account_id=inv_obj.partner_id.deferred_revenue_account.id
            if account_id:
                account_id = account_id[0]
         date = time.strftime('%Y-%m-%d')
         voucher_data = {
                 'period_id': inv_obj.period_id.id,
                 'account_id': account_id,
                 'partner_id': inv_obj.partner_id.id,
                 'journal_id':bank_journal_ids[0],
                 'currency_id': inv_obj.currency_id.id,
                 'reference': inv_obj.name,   #payplan.name +':'+salesname
                 #'narration': data[0]['narration'],
                 'amount': inv_obj.amount_total,
                 'type':account_data['value']['type'],
                 'state': 'draft',
                 'pay_now': 'pay_later',
                 'name': '',
                 'date': time.strftime('%Y-%m-%d'),
                 'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher',context=None),
                 'tax_id': tax_id,
                 'payment_option': 'without_writeoff',
                 'comment': _('Write-Off'),
             }
         if inv_obj.type in ('out_refund','in_refund'):
             voucher_data.update({'amount':-inv_obj.amount_total})
         if not voucher_data['period_id']:
             period_ids = period_obj.find(cr, uid, inv_obj.date_invoice, context=context)
             period_id = period_ids and period_ids[0] or False
             voucher_data.update({'period_id':period_id})
#         logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_data '%s'." % voucher_data)
         voucher_id = voucher_pool.create(cr,uid,voucher_data)
#         logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_id '%s'." % voucher_id)
 
         if voucher_id:
             #Get all the Documents for a Partner
             if inv_obj.type in ('out_refund','in_refund'):
                 amount=-inv_obj.amount_total
                 res = voucher_pool.onchange_partner_id(cr, uid, [voucher_id], inv_obj.partner_id.id, bank_journal_ids[0], amount, inv_obj.currency_id.id, account_data['value']['type'], date, context=context)
             else:
                 res = voucher_pool.onchange_partner_id(cr, uid, [voucher_id], inv_obj.partner_id.id, bank_journal_ids[0], inv_obj.amount_total, inv_obj.currency_id.id, account_data['value']['type'], date, context=context)
             #Loop through each document and Pay only selected documents and create a single receipt
             for line_data in res['value']['line_cr_ids']:
#                 logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data '%s'." % line_data)
 
    #             if not line_data['amount']:
     #                continue
#                 name = line_data['name']
 #                print "Name",name
#                 logger.notifyChannel("warning", netsvc.LOG_WARNING,"inv.number '%s'." % inv_obj.number)
#                 logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data['name'] '%s'." % line_data['name'])
#
                 if line_data['name'] in [invoice_number]:
                     voucher_lines = {
                         'move_line_id': line_data['move_line_id'],
                         'amount': inv_obj.amount_total,
                         'name': line_data['name'],
                         'amount_unreconciled': line_data['amount_unreconciled'],
                         'type': line_data['type'],
                         'amount_original': line_data['amount_original'],
                         'account_id': line_data['account_id'],
                         'voucher_id': voucher_id,
                     }
#                     logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_lines '%s'." % voucher_lines)
                     voucher_line_id = self.pool.get('account.voucher.line').create(cr,uid,voucher_lines)
#                     logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_line_id '%s'." % voucher_line_id)
             for line_data in res['value']['line_dr_ids']:
#                 logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data '%s'." % line_data)
 
      #           if not line_data['amount']:
       #              continue
#                 name = line_data['name']
 #                print "Name",name
#                 logger.notifyChannel("warning", netsvc.LOG_WARNING,"inv.number '%s'." % inv_obj.number)
#                 logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data['name'] '%s'." % line_data['name'])
 
                 if line_data['name'] in [invoice_number]:
                     voucher_lines = {
                         'move_line_id': line_data['move_line_id'],
                         'amount': inv_obj.amount_total,
                         'name': line_data['name'],
                         'amount_unreconciled': line_data['amount_unreconciled'],
                         'type': line_data['type'],
                         'amount_original': line_data['amount_original'],
                         'account_id': line_data['account_id'],
                         'voucher_id': voucher_id,
                     }
#                     logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_lines '%s'." % voucher_lines)
                     voucher_line_id = self.pool.get('account.voucher.line').create(cr,uid,voucher_lines)
#                     logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_line_id '%s'." % voucher_line_id)
 
             #Add Journal Entries
             voucher_pool.action_move_line_create(cr,uid,[voucher_id])
 
         return voucher_id

    def _get_tax(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if not journal_id:
            ttype = context.get('type', 'bank')
            res = journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)
            if not res:
                return False
            journal_id = res[0]

        if not journal_id:
            return False
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id
            return tax_id
        return False

    def get_accounts(self, cr, uid, partner_id=False, journal_id=False, context=None):
        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        default = {
            'value':{},
        }
        if not partner_id or not journal_id:
            return default

        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
        tr_type = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
            tr_type = 'sale'
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
            tr_type = 'purchase'
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            tr_type = 'receipt'

        default['value']['account_id'] = account_id
        default['value']['type'] = tr_type

        return default


#    def action_number(self, cr, uid, ids, context=None):
#        if context is None:
#            context={}
#        result = super(account_invoice,self).action_number(cr,uid,ids,context)
#        type = self.browse(cr,uid,ids[0]).type
#        if result:
#            cr.execute("select order_id from sale_order_invoice_rel where invoice_id='%s'"%(ids[0]))
#            sale_id = cr.fetchone()
#            if sale_id:
#                sale_brw = self.pool.get('sale.order').browse(cr,uid,sale_id[0]) # Code modified by Mohsin
#                authorization_code = sale_brw.authorization_code
#                if authorization_code:
#                    if type == 'out_invoice':
#                        if context.get('captured',False):
#                            returnval = self.make_payment_of_invoice(cr, uid, ids, context=context)
#            return True

account_invoice()
