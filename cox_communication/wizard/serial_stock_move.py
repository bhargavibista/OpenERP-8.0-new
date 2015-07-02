# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
class serial_stock_move_wizard(osv.osv_memory):
    _name = "serial.stock.move.wizard"
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',context=None, toolbar=False, submenu=False):
        res = super(serial_stock_move_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context is None:
           context={}
        active_id = context.get('active_id',False)
        if active_id:
            picking_brw = self.pool.get('stock.picking').browse(cr,uid,active_id)
            move_ids=[move.id for move in picking_brw.move_lines]
            if len(move_ids)==0:
                raise osv.except_osv(_('Warning'), _('No Stock Moves in Selected Delievery Order'))
            if picking_brw.state != 'done':
                raise osv.except_osv(_('Warning'), _('You cannot update the Serial Number'))
            if move_ids:
                if len(move_ids) == 1:
                    cr.execute("select production_lot from stock_move_lot where stock_move_id =%s"%(move_ids[0]))
                else:
                    cr.execute("select production_lot from stock_move_lot where stock_move_id in %s"%(tuple(move_ids),))
                lot_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                if lot_ids:
                    raise osv.except_osv(_('Warning'), _('Serial Number already Assigned'))
        return res

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(serial_stock_move_wizard, self).default_get(cr, uid, fields, context=context)
        move_data=[]
        picking_id = context.get('active_id', [])
        if picking_id:
            move_objects = self.pool.get('stock.picking').browse(cr,uid,picking_id).move_lines
            for move in move_objects:
                move_data.append({
                'move_id':move.id,
                'product_id':move.product_id.id,
                'serial_number':False,
                'qty':move.product_qty
                })
            res.update({'serial_move_id': move_data})
        return res
    
    def assign_serial(self,cr,uid,ids,context={}):
        if context is None:
            context = {}
        prodlot_obj = self.pool.get('stock.production.lot')
        for move in self.browse(cr,uid,ids[0]).serial_move_id:
            serial_number=move.serial_number
            move_id=move.move_id.id
            product_id=move.product_id.id
            if serial_number:
                prodlot_id = prodlot_obj.search(cr,uid,[('name','=',serial_number)])
                if prodlot_id:
                    prodlot_id = prodlot_id[0]
                else:
                    prodlot_id = prodlot_obj.create(cr, uid, {'product_id': product_id,'name': serial_number})
                cr.execute("select production_lot from stock_move_lot where stock_move_id =%s and production_lot=%s"%(move_id,prodlot_id))
                search_record = filter(None, map(lambda x:x[0], cr.fetchall()))
                if not search_record:
                    cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (move_id, prodlot_id))
            else:
                raise osv.except_osv(_('Error'), _('Serial Number not assigned for product %s')%(move.product_id.name_template))
        return {'type': 'ir.actions.act_window_close'}
    
    _columns = {
    'serial_move_id':fields.one2many('serial.stock.move','wizard_move_id','Stock Move'),
    }
serial_stock_move_wizard()

class serial_stock_move(osv.osv_memory):
    _name = "serial.stock.move"
    def onchange_serial(self,cr,uid,ids,serial_number,context):
        res={}
    #    print "onchange_serail number"
        warning = {'title': _('Warning!')}
        prodlot_id = self.pool.get('stock.production.lot').search(cr,uid,[('name','=',serial_number)])
        if prodlot_id:
            warning.update({'message' : _('Serial Number Already Exists')})
            if warning and warning.get('message'):
               res['warning'] = warning
	       res['value'] = {}
	       res['value']['serial_number'] = False
        return res
    _columns = {
    'wizard_move_id':fields.many2one('serial.stock.move.wizard','Stock Move Wizard'),
    'move_id':fields.many2one('stock.move','Stock Move'),
    'product_id':fields.many2one('product.product','Product'),
    'serial_number':fields.char('Serial Number',size=64),
    'qty':fields.float('Quantity'),
    }
serial_stock_move()
