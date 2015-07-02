# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class order_confirmation(osv.osv_memory):
    _name = "order.confirmation"
    _rec_name = 'order_info'
    _columns={
    'order_info':fields.text('Order Information')
    }
    def default_get(self, cr, uid, fields, context=None):
        res,message,count={},'',0
        sale_id=context.get('active_id',False)
        if sale_id:
            so_obj = self.pool.get('sale.order')
            sale_data = so_obj.browse(cr,uid,sale_id)
            order_lines = sale_data.order_line
            if order_lines:
                message+='Order contains following Products : \n'
                for line in order_lines:
                    message+=line.name+' with quantity '+str(line.product_uom_qty)+'\n'
                    if line.product_id.type=='service' and line.product_id.recurring_service==True:
                        count+=1
                if count==0:
                    message+='\n Warning: This order does not contain any Service Product.\n'
                res['order_info']=message
        return res
    def want_to_close(self,cr,uid,ids,context=None):
        return {'type': 'ir.actions.act_window_close'}

    def proceed_to_checkout(self,cr,uid,ids,context=None):
        return {
            'name': ('Pre Requisites'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pre.requisites.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
             'context': context
        }
order_confirmation()