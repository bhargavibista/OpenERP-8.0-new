# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class return_refund_cancellation(osv.osv_memory):
    _name='return.refund.cancellation'
    def cancel_service(self,cr,uid,ids,context={}):
	return_id =  False
	return_object = self.pool.get('return.order')
        if ids:
	        ids_brw =  self.browse(cr,uid,ids[0])
        	return_id =  ids_brw.return_id
	if context and context.get('return_id',False):
            return_id =  context.get('return_id',False)
	    return_id = return_object.browse(cr,uid,return_id)
        if return_id:
            return_object.cancel_service(cr,uid,[return_id.id],context)
            return_object.write(cr,uid,[return_id.id],{'state':'done','return_option':'cancel_service'})
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': return_id.id,
                'res_model': 'return.order',
                'type': 'ir.actions.act_window',
		'context':context
                }
    def create_refund(self,cr,uid,ids,context={}):
        ids_brw =  self.browse(cr,uid,ids[0])
        return_id =  ids_brw.return_id
        if return_id:
            return_object = self.pool.get('return.order')
            context['active_id'] = return_id.id
            context['active_ids'] = [return_id.id]
            context['active_model'] = 'return.order'
	    if not return_id.manual_invoice_invisible:
	            return return_object.manual_invoice_return(cr,uid,[return_id.id],context)
	    else:	        
		    return_object.write(cr,uid,[return_id.id],{'state':'done','return_option':'refund'})
        	    return {
                	'view_type': 'form',
	                'view_mode': 'form',
        	        'res_id': return_id.id,
	                'res_model': 'return.order',
        	        'type': 'ir.actions.act_window',
			'context':context
        	        }
    _columns = {
    'refund_cancel':fields.char('Refund/Cancel',size=256),
    'return_id':fields.many2one('return.order','Return Order ID')
    }
return_refund_cancellation()
