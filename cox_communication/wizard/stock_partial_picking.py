# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date

class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"
    def do_partial(self, cr, uid, ids, context=None):
	if context is None: context = {}
        move_obj = self.pool.get('stock.move')
	picking_obj = self.pool.get('stock.picking')
        return_obj = self.pool.get('return.order')
        pick_up_location = context.get('pick_up_location',False)
        src_location = context.get('src_location',False)
        picking_ids = context.get('active_ids',[])
	picking_id = context.get('active_id',False)
        picking_id_brw = picking_obj.browse(cr,uid,picking_id)
        if pick_up_location and pick_up_location != src_location:
            search_move_ids = move_obj.search(cr, uid, [('picking_id', 'in', picking_ids)])
            if search_move_ids:
                move_obj.write(cr,uid,search_move_ids,{'location_id':pick_up_location})
        res = super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
        if context and context.get('trigger') == 'retail_store' and context.get('sale_id'):
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': context.get('sale_id'),
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window'
            }
        elif context and context.get('return_id',False):
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': context.get('return_id',False),
                'res_model': 'return.order',
                'type': 'ir.actions.act_window'
            }
	elif context and context.get('active_id') and context.get('active_model','') in ('stock.picking','stock.picking'):
                return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': context.get('active_id',False),
                'res_model': context.get('active_model',''),
                'type': 'ir.actions.act_window'
            }
	elif context and context.get('active_id') and context.get('active_model','') in ('stock.picking.in'):
            if picking_id_brw.return_id and picking_id_brw.type == 'in':
                return_obj.write(cr, uid,picking_id_brw.return_id.id, {'receive':True})
		if picking_id_brw.return_id.return_type == 'car_return':
			no_days_passed = return_obj.no_days_passed(cr,uid,picking_id_brw.return_id.linked_sale_order,context)
	                context['return_id'] = picking_id_brw.return_id.id
	                return_data = return_obj.flow_option_based_on_days(cr,uid,no_days_passed,context)
	                if return_data:
        	            return return_data
		else:
			form_res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'cox_communication','view_deliver_goods_from_in')
		        form_id = form_res and form_res[1] or False
			context['active_id']=picking_id_brw.return_id.id
			context['active_ids']= [picking_id_brw.return_id.id]
			context['active_model'] ='return.order'
		        return {
                    'name': ('Delivery Of Goods'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'deliver.goods',
                    'view_id': False,
                'views': [(form_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                     'context': context
                }
        return res
stock_partial_picking()
