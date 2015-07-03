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
import netsvc
from tools.translate import _

class shipping_rate_wizard(osv.osv_memory):
    _name = "shipping.rate.wizard"
    _description = "Calculates shipping charges"
    _columns = {
                'name': fields.one2many('shipping.rate.config','ups_shipping_wizard','Shipping Method'),
                'shipping_cost':fields.float('Shipping Cost'),
                'last_used':fields.char('Last Used',size="128"),
                'account_id':fields.many2one('account.account', 'Account'),
                'rate_select': fields.many2one('shipping.rate.config','Select'),
    }
    def _get_default_val(self,cr, uid, ids,context={}):
        '''
        Function to initialize shipping methods in shipping charge calculating wizard
        '''
        ret=[]
        ship_conf_obj = self.pool.get('shipping.rate.config')
        ship_conf_ids = ship_conf_obj.search(cr,uid,[])
        account_id = False
        for ship_conf in ship_conf_obj.browse(cr,uid,ship_conf_ids):
            if ship_conf.account_id:
                account_id = ship_conf.account_id.id
            ret.append({'shipmethodname':ship_conf.shipmethodname,'use': 0,'real_id':ship_conf.id,'account_id':account_id})
        return ret
    _defaults = {'name':_get_default_val,
                'last_used':'',
                
                    }
    def update_sale_order(self, cr, uid, ids,context={}):
        '''
        Function to update sale order and invoice with new shipping cost and method
        '''
        datas = self.browse(cr, uid, ids[0], context=context)
        if context.get('active_model',False) == 'sale.order':
            sale_id = context.get('active_id',False)
            sale_id and self.pool.get('sale.order').write(cr,uid,[sale_id],{'shipcharge':datas.shipping_cost,
                                                                            'ship_method':datas.last_used,
                                                                            'sale_account_id':datas.account_id.id,
                                                                            'ship_method_id':datas.rate_select.id,})
            self.pool.get('sale.order').button_dummy(cr, uid, [sale_id], context=context)
            return {'nodestroy':False,'type': 'ir.actions.act_window_close'}
        elif context.get('active_model',False) == 'account.invoice':
            invoice_id = context.get('active_id',False)
            if invoice_id:
                if datas.account_id:
                    account_id = datas.account_id.id
                else:
                    account_id = False
                self.pool.get('account.invoice').write(cr,uid,[invoice_id],{
                                                            'shipcharge':datas.shipping_cost,
                                                            'ship_method':datas.last_used,
                                                            'ship_method_id':datas.rate_select.id,
                                                            'sale_account_id':datas.account_id.id,
                                                            })
                self.pool.get('account.invoice').button_reset_taxes(cr, uid, [invoice_id], context=context)
#                For future development to add invoice line for shipping method
#                inv_line_ids = self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','=',invoice_id),('name','=','Shipping Charge')])
#                if inv_line_ids:
#                    self.pool.get('account.invoice').write(cr,uid,invoice_id,{
#                                                                'shipcharge':datas.shipping_cost,
#                                                                'ship_method':datas.last_used,
#                                                                })
#                    self.pool.get('account.invoice.line').write(cr,uid,inv_line_ids,{'price_unit':datas.shipping_cost})
#                else:
#                    if datas.account_id:
#                        self.pool.get('account.invoice').write(cr,uid,invoice_id,{
#                                                                'shipcharge':datas.shipping_cost,
#                                                                'ship_method':datas.last_used,
#                                                                'invoice_line':[(0,0,{'name':'Shipping Charge',
#                                                                                 'quantity':1,
#                                                                                 'state':'article',
#                                                                                 'account_id':datas.account_id.id,
#                                                                                 'price_unit':datas.shipping_cost})]
#                                                                })
#                    else:
#                        raise osv.except_osv(_('Warning !'), _('No account defined for this shipping rate configuration.')) 
                            
                                   
            
        return {'nodestroy':False,'type': 'ir.actions.act_window_close'}
    def find_cost(self, cr, uid, config_id, address, model_obj, type='sale_order', context={}):
        '''
        Function to calculate shipping cost
        '''
        cost=0
        table_pool = self.pool.get('ups.shipping.rate')
        config_pool = self.pool.get('shipping.rate.config')
#        logger = netsvc.Logger()
        config_obj = config_pool.browse(cr,uid,config_id, context=context)        
        if config_obj.calc_method == 'country_weight':
            table_id = table_pool.search(cr,uid,[('card_id','=',config_obj.rate_card_id.id),('country_id','=',address.country_id.id),('from_weight','<=',model_obj.total_weight_net),('to_weight','>',model_obj.total_weight_net),])
            if table_id:
                table_obj = table_pool.browse(cr,uid,table_id[0],)
                if table_obj.charge == 0.0 and table_obj.over_cost:
                    cost = model_obj.total_weight_net*table_obj.over_cost
                else:
                    cost = table_obj.charge
                    
            else:
                table_ids = table_pool.search(cr,uid,[('card_id','=',config_obj.rate_card_id.id),('country_id','=',address.country_id.id),('over_cost','>',0)])
                if table_ids:
                    table_objs = table_pool.browse(cr,uid,table_ids)
                    table_obj = table_objs[0]
                    for table in table_objs:
                        if table_obj.from_weight < table.from_weight:
                            table_obj = table
                    weight = model_obj.total_weight_net
                    if table_obj.charge > 0:
                        cost = table_obj.charge
                        weight -= table_obj.from_weight
                        if weight>0:
                            cost += weight*table_obj.over_cost
                    else:
                        cost = weight*table_obj.over_cost
                else:
                    print"Unable to find rate table with Shipping Table"
#                    logger.notifyChannel(_("Calculate Shipping"), netsvc.LOG_WARNING, _("Unable to find rate table with Shipping Table = %s and Country = %s and Over Cost > 0."%(config_obj.rate_card_id.name,address.country_id.name)))
                
        elif config_obj.calc_method == 'state_zone_weight':
            zone_pool = self.pool.get('ups.zone.map')
            zone_id = zone_pool.search(cr,uid,[('rate_config_id','=',config_obj.id),('state_id','=',address.state_id.id),])
            if zone_id:
                zone = zone_pool.read(cr,uid,zone_id,['zone'])[0]['zone']
                table_id = table_pool.search(cr,uid,[('card_id','=',config_obj.rate_card_id.id),('zone','=',zone),])
                if table_id:
                    table_obj = table_pool.browse(cr,uid,table_id)[0]
                    weight = model_obj.total_weight_net
                    if table_obj.charge > 0:
                        cost = table_obj.charge
                        weight -= table_obj.to_weight
                        if weight>0:
                            cost += weight*table_obj.over_cost
                    else:
                        cost = weight*table_obj.over_cost
                else:
                    print"Unable to find rate table with Shipping Table"
#                    logger.notifyChannel(_("Calculate Shipping"), netsvc.LOG_WARNING, _("Unable to find rate table with Shipping Table = %s and Zone = %s."%(config_obj.shipmethodname,zone)))
            else:
                print"Unable to find Zone Mapping Table with Shipping Rate Configuration"
#                logger.notifyChannel(_("Calculate Shipping"), netsvc.LOG_WARNING, _("Unable to find Zone Mapping Table with Shipping Rate Configuration = %s and State = %s."%(config_obj.shipmethodname,address.state_id.name)))
        elif config_obj.calc_method == 'manual':
            cost = 0.0
        return cost
    
    def onchange_select_ups(self, cr, uid, ids, name, last_used, context={}):
        '''
        Function to update shipping charge when clicking on different types of shipping method
        '''
        new_list = []
        new_last_used = last_used
        cost = 0
        account_id = False
        ret = {}
        ship_conf_obj = self.pool.get('shipping.rate.config')
        ship_conf_ids = ship_conf_obj.search(cr,uid,[])
        if context.get('active_model',False) == 'sale.order' and context.get('active_id',False):
            if name and len(name) == len(ship_conf_ids):
                new_last_used = ''
                value = 0
                for line in name:
                    if line[2]['shipmethodname'] == last_used:
                        line[2]['use'] = 0
                    line[2]['shipmethodname'] and new_list.append(line[2])
                    if line[2]['use']:
                        new_last_used = line[2]['shipmethodname']
                        account_id = line[2]['account_id']
                        sale_id = context.get('active_id',False)
                        sale_order = self.pool.get('sale.order').browse(cr,uid,sale_id,context=context)
                        cr.execute('select type,id from res_partner where partner_id IN %s',(tuple([sale_order.partner_id.id]),))
                        res = cr.fetchall()
                        adr = dict(res)
                        if adr:
                            if adr.get('delivery',False):
                                adr_id = adr['delivery']
                            elif adr.get('default',False):
                                adr_id = adr['default']
                            else:
                                adr_id = adr.values()[0]
                            address = self.pool.get('res.partner').browse(cr, uid,adr_id,context=context)
                            config_id = line[2]['real_id']
                            cost=self.find_cost(cr, uid, config_id, address,sale_order, type='sale_order', context=context)
                ret = {'value':{'shipping_cost':cost,'last_used':new_last_used,'name':new_list,'account_id':account_id}}
            elif len(name) > len(ship_conf_ids):
                for ship_conf in ship_conf_obj.browse(cr,uid,ship_conf_ids):
                    new_list.append({'shipmethodname':ship_conf.shipmethodname,'use': 0})
                ret = {'value':{'last_used':new_last_used,'name':new_list}}
        elif context.get('active_model',False) == 'account.invoice' and context.get('active_id',False):
            if name and len(name) == len(ship_conf_ids):
                new_last_used = ''
                value = 0
                for line in name:
                    if line[2]['shipmethodname'] == last_used:
                        line[2]['use'] = 0
                    line[2]['shipmethodname'] and new_list.append(line[2])
                    if line[2]['use']:
                        new_last_used = line[2]['shipmethodname']
                        account_id = line[2]['account_id']
                        invoice_id = context.get('active_id',False)
                        invoice = self.pool.get('account.invoice').browse(cr,uid,invoice_id,context=context)
                        cr.execute('select type,id from res_partner where partner_id IN %s',(tuple([invoice.partner_id.id]),))
                        res = cr.fetchall()
                        adr = dict(res)
                        if adr:
                            if adr.get('delivery',False):
                                adr_id = adr['delivery']
                            elif adr.get('default',False):
                                adr_id = adr['default']
                            else:
                                adr_id = adr.values()[0]
                            address = self.pool.get('res.partner').browse(cr, uid,adr_id,context=context)
                            config_id = line[2]['real_id']
                            cost=self.find_cost(cr, uid, config_id, address,invoice, type='invoice', context=context)
                ret = {'value':{'shipping_cost':cost,'last_used':new_last_used,'name':new_list,'account_id':account_id,}}
            elif len(name) > len(ship_conf_ids):
                for ship_conf in ship_conf_obj.browse(cr,uid,ship_conf_ids):
                    new_list.append({'shipmethodname':ship_conf.shipmethodname,'use': 0})
                ret = {'value':{'last_used':new_last_used,'name':new_list}}
        return ret
    
    def onchange_select(self, cr, uid, ids, name, last_used, rate_select, context={}):
        new_list = []
        ship_conf_obj = self.pool.get('shipping.rate.config')
        ship_conf_ids = ship_conf_obj.search(cr,uid,[])
        account_id = False
        for line in ship_conf_obj.browse(cr,uid,ship_conf_ids):
            use = 0
            if line.id == rate_select:
                use=1
            new_list.append((0,0,{'use':use,'real_id':line.id,'account_id':line.account_id.id,'shipmethodname':line.shipmethodname}))
        ret = self.onchange_select_ups(cr, uid, ids, new_list, last_used, context=context)
        return ret
    
shipping_rate_wizard()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
