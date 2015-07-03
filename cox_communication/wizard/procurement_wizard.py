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
        print"contexttttt scan ",context
        context.update({'scan':True,'active_ids':context.get('active_ids'),'active_id':context.get('active_id')})
        return self.pool.get('mrp.product.produce').do_produce(cr,uid,[context.get('active_id')],context)
            
            
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