# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

import openerp.netsvc as netsvc
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _columns = {
        'return_id': fields.many2one('return.order','Return Id'),
        'return_ref':fields.char('Return Ref',size=64,readonly=True),
    }

# Overwrite function to pass negative amount if type of invoice is refund
##more modifications continued in account_voucher::recompute_voucher_lines funtion
    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        inv = self.browse(cr, uid, ids[0], context=context)
# Added if else condition to pass negative(-) paid amount
        if inv.type in ('out_refund','in_refund'):
            amount=-inv.residual
        else:
            amount=inv.residual
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {
                'default_partner_id': inv.partner_id.id,
                'default_amount': amount,
                'default_name':inv.name,
                'close_after_process': True,
                'invoice_type':inv.type,
                'invoice_id':inv.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
                }
        }
        
account_invoice()

class account_voucher(osv.osv):
    _inherit = "account.voucher"

# TODO overwrite function and added abs(amount) to calculate proper difference amount for refund invoice payment
    def _compute_writeoff_amount(self, cr, uid, line_dr_ids, line_cr_ids, amount,type): #parameter type is added for OE7
        sign = type == 'payment' and -1 or 1
        debit = credit = 0.0
        for l in line_dr_ids:
            debit += l['amount']
        for l in line_cr_ids:
            credit += l['amount']
        return abs(abs(amount) - sign *abs(credit - debit))

# TODO overwrite function and added abs(voucher.amount) to calculate proper difference amount for refund invoice payment
    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        currency_obj = self.pool.get('res.currency')
        res = {}
        debit = credit = 0.0
        for voucher in self.browse(cr, uid, ids, context=context):
            for l in voucher.line_dr_ids:
                debit += l.amount
            for l in voucher.line_cr_ids:
                credit += l.amount
            currency = voucher.currency_id or voucher.company_id.currency_id
            res[voucher.id] =  currency_obj.round(cr, uid, currency, abs(abs(voucher.amount) - abs(credit - debit)))
        return res
#
#    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
#        print "xxxxx voucher",ids
#        if not ids: return {}
#        currency_obj = self.pool.get('res.currency')
#        res = {}
#        debit = credit = 0.0
#        for voucher in self.browse(cr, uid, ids, context=context):
#            for l in voucher.line_dr_ids:
#                debit += l.amount
#            for l in voucher.line_cr_ids:
#                credit += l.amount
#            currency = voucher.currency_id or voucher.company_id.currency_id
#            print "voucher amount credit debit",voucher.amount,debit,credit
#            res[voucher.id] =  currency_obj.round(cr, uid, currency, abs(voucher.amount - abs(credit - debit)))
#            amount = currency_obj.round(cr, uid, currency, abs(voucher.amount - abs(credit - debit)))
#            x = cr.execute("update account_voucher set amount=%s where id=%s",(amount,voucher.id))
#            print "res voucher id",res[voucher.id]
#        return res
#
    _columns = {
        'writeoff_amount': fields.function(_get_writeoff_amount, string='Difference Amount', type='float', readonly=True, help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines."),
    }

#    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
#        '''
#        Set a dict to be use to create the writeoff move line.
#
#        :param voucher_id: Id of voucher what we are creating account_move.
#        :param line_total: Amount remaining to be allocated on lines.
#        :param move_id: Id of account move where this line will be added.
#        :param name: Description of account move line.
#        :param company_currency: id of currency of the company to which the voucher belong
#        :param current_currency: id of currency of the voucher
#        :return: mapping between fieldname and value of account move line to create
#        :rtype: dict
#        '''
#
#        currency_obj = self.pool.get('res.currency')
#        move_line = {}
#
#        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
#        current_currency_obj = voucher_brw.currency_id or voucher_brw.journal_id.company_id.currency_id
#
#        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
#            diff = line_total
#            account_id = False
#            write_off_name = ''
#            if voucher_brw.payment_option == 'with_writeoff':
#                account_id = voucher_brw.writeoff_acc_id.id
#                write_off_name = voucher_brw.comment
#            elif voucher_brw.type in ('sale', 'receipt'):
#                account_id = voucher_brw.partner_id.property_account_receivable.id
#            else:
#                if voucher_brw.account_supplier_debit:
#                    account_id = voucher_brw.account_supplier_debit.id
#                else:
#                    account_id = voucher_brw.partner_id.property_account_payable.id
#                print "account id supplier",account_id
#            print "account id",account_id
#            move_line = {
#                'name': write_off_name or name,
#                'account_id': account_id,
#                'move_id': move_id,
#                'partner_id': voucher_brw.partner_id.id,
#                'date': voucher_brw.date,
#                'credit': diff > 0 and diff or 0.0,
#                'debit': diff < 0 and -diff or 0.0,
#                'amount_currency': company_currency <> current_currency and voucher_brw.writeoff_amount or False,
#                'currency_id': company_currency <> current_currency and current_currency or False,
#                'analytic_account_id': voucher_brw.analytic_id and voucher_brw.analytic_id.id or False,
#            }
#
#        return move_line

##more modifications continued from account_invoice::invoice_pay_customer funtion
# overwrite function to change allocation amount negative to positive because invoice_pay_customer funtion return negative amount when invoice type is refund i.e in_refund or out_refund
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        if context is None:
            context = {}
        context_multi_currency = context.copy()
        if date:
            context_multi_currency.update({'date': date})

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        #set default values
        default = {
            'value': {'line_ids': [] ,'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id
        account_id = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        default['value']['account_id'] = account_id

        if journal.type not in ('cash', 'bank'):
            return default

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'
    
        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        for line in account_move_lines:
            if line.credit and line.reconcile_partial_id and ttype == 'receipt':
                continue
            if line.debit and line.reconcile_partial_id and ttype == 'payment':
                continue
            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_line_found = line.id
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        #voucher line creation
        for line in account_move_lines:
            if line.credit and line.reconcile_partial_id and ttype == 'receipt':
                continue
            if line.debit and line.reconcile_partial_id and ttype == 'payment':
                continue
            if line.currency_id and currency_id==line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, line.amount_residual)
#TODO           addede if condition to change allocation amount negative(-) to positive(+)
                if price<0.0:
                    price=price * -1
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (move_line_found == line.id) and min(price, amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }


            #split voucher amount by most old first, but only for lines in the same currency
            if not move_line_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price,ttype)
        return default

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)

            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
#            print "first move line",move_line_brw.id,move_line_brw.account_id.id
            line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)
#            print "line_total",line_total,rec_list_ids
            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, context)
#                print "write off"
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)

#            mrp_repair_obj = self.pool.get('mrp.repair')
            rma_name = voucher.name
#### To make return order status done
            inv = True
            deli = True
            memo = voucher.name
            account_invoice_obj = self.pool.get('account.invoice')
            account_invoice_id = account_invoice_obj.search(cr,uid,[('name','=',memo)])
            if len(account_invoice_id):
                return_id = account_invoice_obj.browse(cr,uid,account_invoice_id[0]).return_id
                if return_id:
                    invoice_ids = return_id.invoice_ids
                    picking_ids = return_id.picking_ids
                    for picking_id in picking_ids:
                        if picking_id.state!='done':
                            deli=False
                            break
                    if deli:
                        for invoice_id in invoice_ids:
                            if invoice_id.state!='paid':
                                inv=False
                                break
                    if inv and deli:
                        self.pool.get('return.order').write(cr,uid,[return_id.id],{'state':'done'})
#####End of to make return order status done
#            rma_id = mrp_repair_obj.search(cr,uid,[('name','=',rma_name)])
#            if len(rma_id):
#                invoice_method = mrp_repair_obj.browse(cr,uid,rma_id[0]).invoice_method
##                print"invoice_method",invoice_method
#                if invoice_method=='b4repair':
#                    mrp_repair_obj.write(cr,uid,rma_id,{'state':'ready'})
#                    print"voucher.id",voucher.id
#                if invoice_method=='after_repair':
#                    mrp_repair_obj.write(cr,uid,rma_id,{'state':'done'})
##                    status = mrp_repair_obj.action_repair_done(cr, uid, rma_id)

        return True
account_voucher()