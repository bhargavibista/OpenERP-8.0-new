# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class scan_label_device(osv.osv_memory):
    _name = "scan.label.device"
    _columns = {
    'number': fields.char('Barcode/SO Number/Sales Return No.'),
    'search_by_choice': fields.selection([
            ('search_returns', 'Search by Sales Return Number'),
            ('search_sales', 'Search by Sales Number'),
            ('search_incoming', 'Search by Barcode/Tracking Number')
            ], 'Search Criteria'),
    }
    def default_get(self, cr, uid, fields, context=None):
        res = super(scan_label_device, self).default_get(cr, uid, fields, context=context)
        res.update({'search_by_choice':'search_incoming'})
        return res
    
    def search_record(self,cr,uid,ids,context):
        ids_brw = self.browse(cr,uid,ids[0])
        so_obj = self.pool.get('sale.order')
        stock_move_obj = self.pool.get('stock.move')
        return_obj = self.pool.get('return.order')
        picking_obj = self.pool.get('stock.picking')
        model_obj = self.pool.get('ir.model.data')
        number = ids_brw.number
        sales_return_id = False
        if ids_brw.search_by_choice == 'search_sales':
            search_so = so_obj.search(cr,uid,[('name','=',number)])
            if search_so:
                sales_return_id = return_obj.search(cr,uid,[('linked_sale_order','in',search_so)])
        elif ids_brw.search_by_choice == 'search_returns':
            sales_return_id = return_obj.search(cr,uid,[('name','=',number)])
        else:
	    sales_return_id = return_obj.search(cr,uid,['|',('label_package_barcode','=',number),('carrier_tracking_ref','=',number)])	
            if not sales_return_id:		
	            cr.execute("select id from stock_production_lot where name='%s'"%(number))
        	    serial_data = cr.dictfetchone()
	            if not serial_data:
        	        raise osv.except_osv(_('Warning !'), _('Record not Found'))
	            else:
        	        linked_serial_no_id = serial_data.get('id')
                	cr.execute("select stock_move_id from stock_move_lot where production_lot=%s"%(linked_serial_no_id))
	                stock_moves_val = cr.dictfetchone()
        	        if stock_moves_val:
                	    move_id = stock_moves_val.get('stock_move_id')
	                    if move_id:
        	                stock_moves_ids = stock_move_obj.browse(cr, uid ,move_id)
                	        picking_id = stock_moves_ids.picking_id
	                        if picking_id.type=='out':
        	                    sale_id = (picking_id.sale_id.id if picking_id.sale_id else False)
                	            if not sale_id:
	                       	        raise osv.except_osv(_('Warning !'), _('Record not Found'))
        	                    else:
                	                sales_return_id = return_obj.search(cr,uid,[('linked_sale_order','=',sale_id)])
        if sales_return_id:
                    search_incoming_shipment = picking_obj.search(cr,uid,[('return_id','in',sales_return_id),('state','not in',('done','cancel'))])
                    tree_res = model_obj.get_object_reference(cr, uid, 'stock', 'view_picking_in_tree')
                    tree_id = tree_res and tree_res[1] or False
                    form_res = model_obj.get_object_reference(cr, uid, 'stock', 'view_picking_in_form')
                    form_id = form_res and form_res[1] or False
                    return {
                            'name': _('Incoming Shipment'),
                            'view_type': 'form',
                            'view_mode': 'tree,form',
                            'res_model': 'stock.picking.in',
                            'res_id': False,
                            'view_id': False,
                            'views': [(tree_id, 'tree'), (form_id, 'form')],
                            'target': 'current',
                            'type': 'ir.actions.act_window',
                            'domain': [('id','in',search_incoming_shipment)]
                            }
                    
        else:
            raise osv.except_osv(_('Warning !'), _('Record not Found'))
    
scan_label_device()
