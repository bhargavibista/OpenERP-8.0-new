import itertools
from lxml import etree
from openerp.osv import fields, osv
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from openerp import models, fields, api, _


class account_invoice(models.Model):
    _inherit = 'account.invoice'
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """
        finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        Args:
            invoice: browsable record of the invoice that is generating the move lines
            move_lines: list of dictionaries with the account.move.lines (as for create())
        Returns:
            The (possibly updated) final move_lines to create for this invoice
        """
        move_lines = super(account_invoice, self).finalize_invoice_move_lines(move_lines)
        if self.type == "out_refund":
            account = self.account_id.id
        else:
            account = self.sale_account_id.id
        if self.sale_account_id and self.shipcharge:
            lines1 = {
                'analytic_account_id': False,
                'tax_code_id': False,
                'analytic_lines': [],
                'tax_amount': False,
                'name': 'Shipping Charge',
                'ref': '',
                'currency_id': False,
                'credit': self.shipcharge,
                'product_id': False,
                'date_maturity': False,
                'debit': False,
                'date': time.strftime("%Y-%m-%d"),
                'amount_currency': 0,
                'product_uom_id':  False,
                'quantity': 1,
                'partner_id': self.partner_id.id,
                'account_id': account
                }
            move_lines.append((0, 0, lines1))
            has_entry = False
            for move_line in move_lines:
                journal_entry = move_line[2]
                if journal_entry['account_id'] == self.journal_id.default_debit_account_id.id:
                    journal_entry['debit'] += self.shipcharge
                    has_entry = True
                    break
            if not has_entry:       # If debit line does not exist create one
                lines2 = {
                    'analytic_account_id': False,
                    'tax_code_id': False,
                    'analytic_lines': [],
                    'tax_amount': False,
                    'name': '/',
                    'ref': '',
                    'currency_id': False,
                    'credit': False,
                    'product_id': False,
                    'date_maturity': False,
                    'debit': self.shipcharge,
                    'date': time.strftime("%Y-%m-%d"),
                    'amount_currency': 0,
                    'product_uom_id': False,
                    'quantity': 1,
                    'partner_id': self.partner_id.id,
                    'account_id': self.journal_id.default_debit_account_id.id
                    }
                move_lines.append((0, 0, lines2))
        return move_lines
    
    def _total_weight_net(self, cr, uid, ids, field_name, arg, context=None):
        """Compute the total net weight of the given Invoice."""
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            result[invoice.id] = 0.0
            for line in invoice.invoice_line:
                if line.product_id:
                    result[invoice.id] += line.weight_net or 0.0
        return result
    
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
        self.amount_tax = sum(line.amount for line in self.tax_line)
#        self.amount_total = self.amount_untaxed + self.amount_tax
        self.amount_total= (self.shipcharge if self.ship_method_id else self.amount_untaxed + self.amount_tax) 
        print"self.amount_total",self.amount_total
        
    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Tax', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount')
    total_weight_net = fields.Float(string='Total Net Weight',
        store=True, readonly=True, compute='_total_weight_net')
    shipcharge = fields.Float(string='Shipping Cost', readonly=True,
        )
    ship_method = fields.Char(string='Shipping Method',   size=128, readonly=True)
    ship_method_id = fields.Many2one('shipping.rate.config', string='Shipping Method',
        readonly=True)
    sale_account_id = fields.Many2one('account.account', string='Shipping Account',
        readonly=True,help='This account represents the g/l account for booking shipping income.')
        
account_invoice()

class invoice_line(models.Model):
    """Add the net weight to the object "Invoice Line"."""
    _inherit = 'account.invoice.line'

    def _weight_net(self, cr, uid, ids, field_name, arg, context=None):
        """Compute the net weight of the given Invoice Lines."""
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = 0.0
            if line.product_id:
                result[line.id] += line.product_id.weight_net * line.quantity
        return result
    
    weight_net = fields.Float(string='Net Weight',
        store=True, readonly=True, compute='_weight_net')
##    _columns = {
##        'weight_net': fields.function(_weight_net, method=True, readonly=True, string='Net Weight', help="The net weight in Kg.",
##            store = {
##                'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids,['quantity', 'product_id'], -11),
##                })
#        }

invoice_line()

class account_invoice_tax(osv.osv):
    _inherit = "account.invoice.tax"
    def compute(self, cr, uid, invoice, context=None):
        print"sale negotiated",invoice
#        tax_grouped = super(account_invoice_tax, self).compute(invoice)
        
        tax_grouped={}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = invoice
#        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id
        tax_ids = inv.ship_method_id and inv.ship_method_id.shipment_tax_ids 
        if tax_ids:
            for tax in tax_obj.compute_all(cr, uid, tax_ids, inv.shipcharge, 1)['taxes']:
                val = {}
                val.update({
                    'invoice_id': inv.id,
                    'name': tax['name'],
                    'amount': tax['amount'],
                    'manual': False,
                    'sequence': tax['sequence'],
                    'base': tax['price_unit'] * 1
                    })
                if inv.type in ('out_invoice','in_invoice'):
                    val.update({
                        'base_code_id': tax['base_code_id'],
                        'tax_code_id': tax['tax_code_id'],
                        'base_amount': cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], 
                                                       context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                        'tax_amount': cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], 
                                                      context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                        'account_id': tax['account_collected_id'] or line.account_id.id
                        })
                else:
                    val.update({
                        'base_code_id': tax['ref_base_code_id'],
                        'tax_code_id': tax['ref_tax_code_id'],
                        'base_amount': cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], 
                                                       context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                        'tax_amount': cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], 
                                                      context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False),
                        'account_id': tax['account_paid_id'] or line.account_id.id
                        })
                    
                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
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
        return tax_grouped
    
account_invoice_tax()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
