# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class in_store_pickup(osv.osv_memory):
    _name = "in.store.pickup"
    _rec_name = 'src_location'
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(in_store_pickup, self).default_get(cr, uid, fields, context=context)
        picking_id = context.get('active_id', [])
        if picking_id:
            picking_id_obj = self.pool.get('stock.picking').browse(cr,uid,picking_id)
            source_location = ( picking_id_obj.sale_id.location_id.id if picking_id_obj.sale_id.location_id else False)
            res.update({'src_location': source_location})
        return res
    def default_picking_flow(self,cr, uid, ids, context=None):
       if context is None: context = {}
       context = dict(context, active_ids=context.get('active_ids'), active_model=context.get('active_model'))
       picking_id=context.get('active_ids')
       self.pool.get('stock.picking').write(cr, uid, picking_id, {'skip_barcode': True})
#       cox gen2
#       partial_id = self.pool.get("stock.partial.picking").create(cr, uid, {}, context=context)
       id_obj = self.browse(cr,uid,ids[0])
       pick_up_location = id_obj.pick_up_location
       src_location = id_obj.src_location
       context['pick_up_location'] = (pick_up_location.id if pick_up_location else False)
       context['src_location'] = (src_location.id if src_location else False) 
       return True
#       return {
#           'name':_("Products to Process"),
#           'view_mode': 'form',
#           'view_id': False,
#           'view_type': 'form',
#           'res_model': 'stock.partial.picking',
#           'res_id': partial_id,
#           'type': 'ir.actions.act_window',
#           'nodestroy': True,
#           'target': 'new',
#           'domain': '[]',
#           'context': context,
#       }
    def barcode_scanning(self,cr,uid,ids,context={}):
        if context is None:
            context = {}
        if context.get('active_id') and ids:
            pick_id = context.get('active_ids')
            id_obj = self.browse(cr,uid,ids[0])
            pick_up_location = id_obj.pick_up_location
            src_location = id_obj.src_location
            context['pick_up_location'] = (pick_up_location.id if pick_up_location else False)
            context['src_location'] = (src_location.id if src_location else False)
            context = dict(context, active_ids=pick_id, active_model='stock.picking')
            bar_code_scanning = self.pool.get("picking.scanning").create(cr, uid, {},context)
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
    _columns = {
    'src_location':fields.many2one('stock.location','Source Location'),
    'pick_up_location':fields.many2one('stock.location','Pick Up Location')
    }
in_store_pickup()
