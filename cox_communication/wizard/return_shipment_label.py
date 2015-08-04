# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class return_shipment_label(osv.osv_memory):
    _name = "return.shipment.label"
    def generate_label(self,cr,uid,ids,context={}):
        if ids:
            id_brw = self.browse(cr,uid,ids[0])
            return_id  = id_brw.return_id
            context['active_id'] = return_id.id
            context['active_ids'] = [return_id.id]
            context['active_model'] = 'return.order'
            if return_id:
                return {
                    'name':_("Generate Label"),
                    'view_type': 'form',
                    'view_mode': 'form',
#                    'res_id': id,
                    'res_model': 'shipping.returns',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'context': context
                        }
    def receive_refund(self,cr,uid,ids,context={}):
        search_incoming_shipment=False
        if ids:
            id_brw = self.browse(cr,uid,ids[0])
            return_id  = id_brw.return_id
            context['active_id'] = return_id.id
            context['active_ids'] = [return_id.id]
            context['active_model'] = 'return.order'
            search_shipment = self.pool.get('stock.picking').search(cr,uid,[('return_id','=',return_id.id),('state','=','draft')])	
            if search_shipment:
                for each in self.pool.get('stock.picking').browse(cr,uid,search_shipment):
                    if each.picking_type_id.code=='incoming':
                        search_incoming_shipment.append(each.id)
	    if search_incoming_shipment:
		context['picking_id_in'] = search_incoming_shipment[0]
            return self.pool.get('receive.goods').receive_goods_wizard(cr,uid,ids,context)
        
    _columns = {
    
    'return_id':fields.many2one('return.order','Return Order ID')}
    
return_shipment_label()
