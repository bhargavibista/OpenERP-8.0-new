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
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
import time

#Shipping rate configuration model
class shipping_rate_config(osv.osv):
    _name = 'shipping.rate.config'
    _description = "Configuration for shipping rate"
    _rec_name = 'shipmethodname'
    _columns = {
                'real_id':fields.integer('ID',readonly=True, ),
                'shipmethodname':fields.char('Shipping Method Name',size=128,help='Shipping method name. Displayed in the wizard.'),
                'active':fields.boolean('Active',help='Indicates whether a shipping method is active'),
                'use':fields.boolean('Select',),
                'calc_method':fields.selection([('country_weight','Country & Weight'),('state_zone_weight','State-Zone-Weight'),('manual','Manually Calculate')],'Shipping Calculation Method',help='Shipping method name. Displayed in the wizard.'),
                'ups_shipping_wizard': fields.integer('Shipping Wizard'),
               # 'rate_card_id':fields.many2one('ups.shipping.rate.card','Shipping Rate Card'),
                'zone_map_ids':fields.one2many('ups.zone.map','rate_config_id','Zone Map'),
                'account_id':fields.many2one('account.account','Account',help='This account represents the g/l account for booking shipping income.'),
                # Added to include tax configuration for shipment
                'shipment_tax_ids': fields.many2many('account.tax', 'shipment_tax_rel', 'shipment_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
    }
    _defaults = {
                 'calc_method':'country_weight'
                }

shipping_rate_config()

#    State - Zone table
class zone_map(osv.osv):
    _name = 'ups.zone.map'
    _description = "Zone Mapping Table"
    _rec_name = 'zone'
    _columns = {
                'zone':fields.integer('Zone'),
                'state_id':fields.many2one('res.country.state','State / Zone'),
                'rate_config_id':fields.many2one('shipping.rate.config','Shipping Rate Configuration')
    }
    
zone_map()
'''
Adding shipping method field on delivery order and delivery products
'''
class stock_picking(osv.osv):
    
    _inherit = "stock.picking"
    def _get_sale_order(self, cr, uid, ids, context={}):
        result = []
        for id in ids:
            stock_pick_ids = self.pool.get('stock.picking').search(cr,uid,[('sale_id','=',id)])
            result += stock_pick_ids
        result = list(set(result))
        return result
    _columns = {
        'ship_method':  fields.related('sale_id', 'ship_method', string='Shipping Method', type='char', size=128, #store=True
                store={
                'sale.order': (_get_sale_order, ['ship_method'], -10),}
        ),
        }

stock_picking()
class stock_move(osv.osv):
    
    _inherit = "stock.move"
    
    def _get_sale_order(self, cr, uid, ids, context={}):
        result = []
        move_ids = []
        for id in ids:
            stock_pick_ids = self.pool.get('stock.picking').search(cr,uid,[('sale_id','=',id)])
            if stock_pick_ids:
                move_ids += self.pool.get('stock.move').search(cr,uid,[('picking_id','in',stock_pick_ids)])
        move_ids = list(set(move_ids))
        return move_ids
    _columns = {
        'ship_method':  fields.related('picking_id','sale_id', 'ship_method', string='Shipping Method', type='char', size=128,# store=True
                store={
                'sale.order': (_get_sale_order, ['ship_method'], -10),}
        ),
        }

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

