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
from osv import fields,osv
import decimal_precision as dp
import time


class shipping_rate_card(osv.osv):
    _name = 'ups.shipping.rate.card'
    _description = "Ground Shipping Calculation Table"
    _columns = {
                'name':fields.char('Shipping Method',size=128,required=True),
                'from_date':fields.datetime('From Date', ),
                'to_date':fields.datetime('To Date', ),
                'rate_ids': fields.one2many('ups.shipping.rate','card_id','Shipping Rates', required=True),
    }
    
shipping_rate_card()

class shipping_rate_config(osv.osv):
    _inherit = 'shipping.rate.config'
    
    
    _columns = {
                'rate_card_id':fields.many2one('ups.shipping.rate.card','Shipping Rate Card'),
    }
shipping_rate_config()

class shipping_rate(osv.osv):
    _name = 'ups.shipping.rate'
    _description = "Shipping Calculation Table"
    _columns = {
                'name':fields.char('Shipping Method',size=128),
                'from_weight': fields.integer('From Weight', required=True),
                'to_weight': fields.integer('To Weight'),
                'charge': fields.float('Shipping Charge'),
                'over_cost': fields.float('Shipping Charge per pound over'),
                'country_id':fields.many2one('res.country','Country'),
                'zone':fields.integer('Zone', required=True),
                'card_id':fields.many2one('ups.shipping.rate.card','Shipping Table')
    }
    
shipping_rate()

class sale_order(osv.osv):
    _name = "sale.order"
    _inherit="sale.order"
    _description = "Sale Order"
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_id = super(sale_order, self)._make_invoice(cr, uid, order, lines, context=None)
        if inv_id and order._table_name == 'sale.order':
            if order.sale_account_id:
                self.pool.get('account.invoice').write(cr,uid,inv_id,{
                                                        'shipcharge':order.shipcharge,
                                                        'ship_method':order.ship_method,
                                                        'ship_method_id':order.ship_method_id.id,
                                                        'sale_account_id':order.sale_account_id.id,
                                                        })
                self.pool.get('account.invoice').button_reset_taxes(cr, uid, [inv_id], context=context)
                    
        return inv_id
    
    def _get_order(self, cr, uid, ids, context=None):
        return super(sale_order, self)._get_order(cr, uid, ids, context=context)
    
    def _amount_shipment_tax(self, cr, uid, shipment_taxes, shipment_charge):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, shipment_taxes, shipment_charge, 1)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        for order in self.browse(cr, uid, ids, context=context):
            cur = order.pricelist_id.currency_id
            if order.ship_method_id:
                if order.ship_method_id.shipment_tax_ids and len(order.ship_method_id.shipment_tax_ids) > 0:
                    val = self._amount_shipment_tax(cr, uid, order.ship_method_id.shipment_tax_ids, order.shipcharge)
                    res[order.id]['amount_tax'] += cur_obj.round(cr, uid, cur, val)
                res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + order.shipcharge
        return res
    
    _columns = {
                'shipcharge':  fields.float('Shipping Cost', readonly=True),
                'ship_method': fields.char('Shipping Method',size=128, readonly=True),
                'ship_method_id': fields.many2one('shipping.rate.config','Shipping Method', readonly=True),
                'sale_account_id':fields.many2one('account.account','Shipping Account',help='This account represents the g/l account for booking shipping income.', readonly=True),
                'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
                store = {
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'ship_method_id'], 10),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                },
                multi='sums', help="The amount without tax."),
                'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
                store = {
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'ship_method_id'], 10),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                },
                multi='sums', help="The tax amount."),
                'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
                store = {
                    'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'ship_method_id'], 10),
                    'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                },
                multi='sums', help="The total amount."),
            }
    
sale_order()

# Added to calculate tax for shipment in invoice
class account_invoice_tax_inherit(osv.osv):
    _name = "account.invoice.tax"
    _inherit = "account.invoice.tax"
    
    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = super(account_invoice_tax_inherit, self).compute(cr, uid, invoice_id, context=context)
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id

        if inv.ship_method_id and inv.ship_method_id.shipment_tax_ids and len(inv.ship_method_id.shipment_tax_ids) > 0:
            for tax in tax_obj.compute_all(cr, uid, inv.ship_method_id.shipment_tax_ids, inv.shipcharge, 1)['taxes']:
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax['price_unit'] * 1
    
                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
    
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
    
account_invoice_tax_inherit()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
