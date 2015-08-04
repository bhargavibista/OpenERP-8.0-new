import openerp.netsvc as netsvc
from openerp.osv import fields, osv
import time
from openerp.tools.translate import _

class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'

    def create_returns(self, cr, uid, ids, context=None):
        """
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('stock.return.picking.memory')
        wf_service = netsvc.LocalService("workflow")
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        new_picking = None
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        set_invoice_state_to_none = True
        returned_lines = 0

#        Create new picking for returned products
        if pick.picking_type_id.code=='outgoing':
            new_type = 'in'
        elif pick.picking_type_id.code=='incoming':
            new_type = 'out'
        else:
            new_type = 'internal'
        seq_obj_name = 'stock.picking.' + new_type
        new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
        new_picking = pick_obj.copy(cr, uid, pick.id, {'name':'%s-%s-return' % (new_pick_name, pick.name),
                'move_lines':[], 'state':'draft', 'type':new_type,
                'date':date_cur, 'invoice_state':data['invoice_state'],})
#overwrite function and added this if condition to write selected invoice_state in wizard into return order
        if data['invoice_state']=='none':
            pick_obj.write(cr,uid,new_picking,{'invoice_state':data['invoice_state']})

        val_id = data['product_return_moves']
        for v in val_id:
            data_get = data_obj.browse(cr, uid, v, context=context)
            mov_id = data_get.move_id.id
            new_qty = data_get.quantity
            move = move_obj.browse(cr, uid, mov_id, context=context)
            new_location = move.location_dest_id.id
            returned_qty = move.product_qty
            for rec in move.move_history_ids2:
                returned_qty -= rec.product_qty

            if returned_qty != new_qty:
                set_invoice_state_to_none = False
            if new_qty:
                returned_lines += 1
                new_move=move_obj.copy(cr, uid, move.id, {
                    'product_qty': new_qty,
                    'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id,
                        new_qty, move.product_uos.id),
                    'picking_id':new_picking, 'state':'draft',
                    'location_id':new_location, 'location_dest_id':move.location_id.id,
                    'date':date_cur,})
                move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]})
        if not returned_lines:
            raise osv.except_osv(_('Warning !'), _("Please specify at least one non-zero quantity!"))

        if set_invoice_state_to_none:
            pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'})
        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        pick_obj.force_assign(cr, uid, [new_picking], context)
        # Update view id in context, lp:702939
        view_list = {
                'out': 'view_picking_out_tree',
                'in': 'view_picking_in_tree',
                'internal': 'vpicktree',
            }
        data_obj = self.pool.get('ir.model.data')
        res = data_obj.get_object_reference(cr, uid, 'stock', view_list.get(new_type, 'vpicktree'))
        context.update({'view_id': res and res[1] or False})
        return {
            'domain': "[('id', 'in', ["+str(new_picking)+"])]",
            'name': 'Picking List',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'stock.picking',
            'type':'ir.actions.act_window',
            'context':context,
        }

stock_return_picking()
