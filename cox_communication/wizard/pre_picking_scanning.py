# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import osv, fields

class pre_picking_scanning(osv.osv_memory):
    _name="pre.picking.scanning"
    _columns={}
    
## cox gen2 don't need skip barcode scanning button

#    def default_picking_flow(self,cr, uid, ids, context=None):
#        if context is None: context = {}
#        context = dict(context, active_ids=context.get('active_ids'), active_model=context.get('active_model'))
#        picking_id=context.get('active_ids')
#        self.pool.get('stock.picking').write(cr, uid, picking_id, {'skip_barcode': True})
##        cox gen2
##        partial_id = self.pool.get("stock.partial.picking").create(cr, uid, {}, context=context)
#        if context and context.get('trigger') == 'retail_store':
#            return True
##            return {
##                    'name':_("Products to Process"),
##                    'view_mode': 'form',
##                    'view_id': False,
##                    'view_type': 'form',
##                    'res_model': 'stock.partial.picking',
##                    'res_id': partial_id,
##                    'type': 'ir.actions.act_window',
##                    'nodestroy': True,
##                    'target': 'new',
##                    'domain': '[]',
##                    'context': context,
##                }
#        else:
#            return {
#                'name':_("Shipping Process"),
#                'view_mode': 'form',
#                'view_id': False,
#                'view_type': 'form',
#                'res_model': 'pre.shipping.process',
#                'type': 'ir.actions.act_window',
#                'nodestroy': True,
#                'target': 'new',
#                'domain': '[]',
#                'context': context,
#            }
	
    def barcode_scanning(self,cr, uid, ids, context=None):
        if context is None: context = {}
        context = dict(context, active_ids=context.get('active_ids'), active_model=context.get('active_model'))
        picking_id=context.get('active_ids')
        self.pool.get('stock.picking').write(cr, uid, picking_id, {'skip_barcode': False})
        bar_code_scanning = self.pool.get("picking.scanning").create(cr, uid, {}, context=context)
        return {
            'name':_("Bar Code Scanning"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'picking.scanning',
            'res_id': bar_code_scanning,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }

pre_picking_scanning()
