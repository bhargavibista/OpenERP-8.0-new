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

class procurement_wizard(osv.osv_memory):
    _name = "procurement.wizard"
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}
        res = super(procurement_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        msg = context.get('msg',False)
        if msg:
            res['arch'] = """
                    <form string="Warning" version="7.0">
                      <separator string="Stock Not Available for the Consume Products"  colspan="10" />
                      <label string="%s"/>
                      <separator string="" colspan="4" />
                          <group col="4" colspan="4">
                            <footer>
                              <button name="procurement" string="Proceed" class="oe_highlight" type="object" />
                              or
                              <button special="cancel" class="oe_link" string="Cancel"/>
                            </footer>
                          </group>
                  </form>
                """%(tools.to_xml(msg))
        return res
    def procurement(self, cr, uid, ids, context=None):
        production_id = context.get('active_ids', False)
        product_qty=context.get('production_qty', False)
        mode=context.get('mode', False)
        ### code to produce product after confirmation.
        if production_id and product_qty and mode:
            self.pool.get('mrp.production').action_produce(cr, uid, production_id,
                                product_qty, mode, context=context)
        ###code to update form view of manufacturing
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'mrp', 'mrp_production_form_view')
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Manufacturing Orders'),
            'res_model': 'mrp.production',
            'res_id': production_id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

procurement_wizard()

