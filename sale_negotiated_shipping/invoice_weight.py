# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

"""Compute the net weight of sale orders."""

from osv import osv, fields
import decimal_precision as dp
import time

class account_invoice(osv.osv):
    """Add the total net weight to the object "Sale Order"."""

    _inherit = "account.invoice"

    def _total_weight_net(self, cr, uid, ids, field_name, arg, context):
        """Compute the total net weight of the given Invoice."""
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            result[invoice.id] = 0.0
            for line in invoice.invoice_line:
                if line.product_id:
                    result[invoice.id] += line.weight_net or 0.0
        return result

    def _get_invoice(self, cr, uid, ids, context={}):
        """Get the invoice ids of the given Invoice Lines."""
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids,
            context=context):
            result[line.invoice_id.id] = True
        return result.keys()
    
    def _amount_shipment_tax(self, cr, uid, shipment_taxes, shipment_charge):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, shipment_taxes, shipment_charge, 1)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = super(account_invoice, self)._amount_all(cr, uid, ids, name, args, context=context)
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.ship_method_id:
                res[invoice.id]['amount_total'] = res[invoice.id]['amount_untaxed'] + res[invoice.id]['amount_tax'] + invoice.shipcharge
        return res
    
    def _get_invoice_tax(self, cr, uid, ids, context=None):
        invoice = self.pool.get('account.invoice')
        return super(account_invoice, invoice)._get_invoice_tax(cr, uid, ids, context=context)
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        invoice = self.pool.get('account.invoice')
        return super(account_invoice, invoice)._get_invoice_line(cr, uid, ids, context=context)
    
    def _get_invoice_from_line(self, cr, uid, ids, context=None):
        invoice = self.pool.get('account.invoice')
        return super(account_invoice, invoice)._get_invoice_from_line(cr, uid, ids, context=context)
    
    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """
        move_lines = super(account_invoice, self).finalize_invoice_move_lines(cr, uid, invoice_browse, move_lines)
        if invoice_browse.type == "out_refund":
            account = invoice_browse.account_id.id
        else:
            account = invoice_browse.sale_account_id.id
        if invoice_browse.sale_account_id and invoice_browse.shipcharge:
            lines1={
                    'analytic_account_id' :  False,
                    'tax_code_id' :  False,
                    'analytic_lines' :  [],
                    'tax_amount' :  False,
                    'name' :  'Shipping Charge',
                    'ref' : '',
                    'currency_id' :  False,
                    'credit' :  invoice_browse.shipcharge,
                    'product_id' :  False,
                    'date_maturity' : False,
                    'debit' : False,
                    'date' : time.strftime("%Y-%m-%d"),
                    'amount_currency' : 0,
                    'product_uom_id' :  False,
                    'quantity' : 1,
                    'partner_id' : invoice_browse.partner_id.id,
                    'account_id' : account,}
            
            move_lines.append((0,0,lines1))
            # Retrieve the existing debit line if one exists
            has_entry = False
            for move_line in move_lines:
                journal_entry = move_line[2]
                if journal_entry['account_id'] == invoice_browse.journal_id.default_debit_account_id.id:
                    journal_entry['debit'] += invoice_browse.shipcharge
                    has_entry = True
                    break
            # If debit line does not exist create one. Generally this condition will not happen. Just a fail-safe option    
            if not has_entry:
                lines2={
                        'analytic_account_id' :  False,
                        'tax_code_id' :  False,
                        'analytic_lines' :  [],
                        'tax_amount' :  False,
                        'name' :  '/',
                        'ref' : '',
                        'currency_id' :  False,
                        'credit' :  False,
                        'product_id' :  False,
                        'date_maturity' : False,
                        'debit' : invoice_browse.shipcharge,
                        'date' : time.strftime("%Y-%m-%d"),
                        'amount_currency' : 0,
                        'product_uom_id' :  False,
                        'quantity' : 1,
                        'partner_id' : invoice_browse.partner_id.id,
                        'account_id' : invoice_browse.journal_id.default_debit_account_id.id,}
            
                move_lines.append((0,0,lines2))
        return move_lines
    
    
    
    
    _columns = {
                
        'amount_total': fields.function(_compute_amount, method=True, digits_compute=dp.get_precision('Account'), string='Total',
            store=True),

        'total_weight_net': fields.function(_total_weight_net, method=True,
            readonly=True, string='Total Net Weight',
            help="The cumulated net weight of all the invoice lines.",
            store={
                # Low priority to compute this before fields in other modules
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                     ['invoice_line'], 10),
                'account.invoice.line': (_get_invoice,
                     ['quantity', 'product_id'], 10),
            },
        ),
        'shipcharge':  fields.float('Shipping Cost', readonly=True),
        'ship_method': fields.char('Shipping Method',size=128, readonly=True),
        'ship_method_id': fields.many2one('shipping.rate.config','Shipping Method', readonly=True),
        'sale_account_id':fields.many2one('account.account','Shipping Account',help='This account represents the g/l account for booking shipping income.', readonly=True)

    }
account_invoice()

# Record the net weight of the order line
class invoice_line(osv.osv):
    """Add the net weight to the object "Invoice Line"."""
    _inherit = 'account.invoice.line'

    def _weight_net(self, cr, uid, ids, field_name, arg, context):
        """Compute the net weight of the given Invoice Lines."""
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = 0.0

            if line.product_id:
                result[line.id] += (line.product_id.weight_net
                     * line.quantity)# / line.product_uom.factor)
        return result
    _columns = {
        'weight_net': fields.function(_weight_net, method=True,
            readonly=True, string='Net Weight', help="The net weight in Kg.",
            store={
                # Low priority to compute this before fields in other modules
               'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids,
                   ['quantity', 'product_id'], -11),
            },
        ),

    }
invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
