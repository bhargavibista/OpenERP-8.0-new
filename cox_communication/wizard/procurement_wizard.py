# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import itertools
from openerp import netsvc
from openerp import tools

class pre_import_serial(osv.osv):
    _name='pre.import.serial'
    _columns={
        'want_to_import':fields.boolean('Want to Import'),
    }
    
    def import_csv(self,cr,uid,ids,context=None):
        obj = self.pool.get('pre.import.serial')
        obj.write(cr,uid,ids,{'want_to_import':True})
        return {'name':_("Import Serials"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'pre.import.serial',
            'res_id': ids[0],
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,}
            
    def scan(self,cr,uid,ids,context=None):
        context = dict(context, active_ids=context.get('active_ids'), active_model=context.get('active_model'),scan=True, trigger= 'mrp', manufacture_id = context.get('active_ids'))
        print"context.get('active_ids')",context.get('active_ids')
        manufacturing_id = context.get('active_ids')
        manf_brw = self.pool.get('mrp.production').browse(cr,uid,manufacturing_id[0])
        product_qty = manf_brw.product_qty
        context.update({'product_qty':product_qty})
#        picking_id=context.get('active_ids')
#        self.pool.get('stock.picking').write(cr, uid, picking_id, {'skip_barcode': False,'manufacture_id':context.get('active_ids')})
        scanning = self.pool.get("manual.scanning").create(cr, uid, {}, context=context)
        return {
            'name':_("Bar Code Scanning"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'manual.scanning',
            'res_id': scanning,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }
            
            
    def import_serial_number(self,cr,uid,ids,context=None):
        import_serails = False
        if context is None: context = {}
        if context.get('active_ids',False):
            print"contextttttttttt",context
            if context.get('active_model',False) == 'mrp.production':
                import_serails = self.pool.get("import.serials").create(cr, uid, {'mrp_object':True,'csv_file_supplier':False}, context=context)
#            
            return {
            'name':_("Import Serials"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'import.serials',
            'res_id': import_serails,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }
        return True
    
pre_import_serial()


class manual_scanning(osv.osv):
    _name='manual.scanning'
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(manual_scanning, self).default_get(cr, uid, fields, context=context)
        manufacture_id = context.get('manufacture_id',False)
        mrp_brw = self.pool.get('mrp.production').browse(cr,uid,manufacture_id[0])
        location_id = mrp_brw.location_src_id.id
        res.update({'location_id':location_id})
        return res
    
    
    def get_product_ids(self,cr,uid,context={}):
        context = dict(context, active_ids=context.get('active_ids'), active_model=context.get('active_model'),scan=True, trigger= 'mrp', manufacture_id = context.get('active_ids'),active_id= context.get('active_id'))
        product_obj = self.pool.get('product.product')
        new_product_ids,move_prod_id = [],[]
        if context.get('manufacture_id',False):
            manufacture_id = context.get('manufacture_id',False)
            cr.execute("select move_id from mrp_production_move_ids where production_id='%s'"%(manufacture_id[0]))
            move_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            cr.execute("select product_id from stock_move where id in %s and state not in ('done','cancel')", (tuple(move_ids),))
            product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if product_ids:
                for each_prod_id in product_obj.browse(cr,uid,product_ids): 
                    if each_prod_id.track_incoming==True or each_prod_id.track_production==True:
                            new_product_ids.append(each_prod_id.id)
        if new_product_ids:
           product_obj = self.pool.get('product.product')
           [move_prod_id.append((each_prod.id,each_prod.name))for each_prod in product_obj.browse(cr,uid,new_product_ids)]
        return list(set(move_prod_id))
    
    _columns={
        'product_id': fields.selection(get_product_ids,'Product'),
        'serial_ids':fields.one2many('stock.production.lot','scanning_id','Serial Numbers'),
        'location_id':fields.many2one('stock.location'),
    }
    
    def scanning(self,cr,uid,ids,context={}):
        production_id = context.get('active_ids', False)
        production=self.pool.get('mrp.production').browse(cr,uid,production_id[0])
        data = self.pool.get('mrp.product.produce').browse(cr, uid, context.get('active_id'), context=context)
        serial_list = []
        obj = self.browse(cr,uid,ids[0])
        serial_ids = obj.serial_ids
        if len(serial_ids) < production.product_qty:
            raise osv.except_osv(_('Warning!'), _('Produce Qty is more than serial count. Please provide more serial number'))
        
        for each in serial_ids:
            serial_list.append(each.id)
        if serial_list:
            context.update({'serial_number_list':serial_list})
        self.pool.get('mrp.production').action_produce(cr, uid, production_id,
                                data.product_qty, data.mode, context=context)
        return True
    
    
manual_scanning()
