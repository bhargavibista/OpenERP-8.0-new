from openerp.osv import osv, fields
from openerp import workflow
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
from datetime import datetime
import re

class mrp_product_produce(osv.osv_memory):
    _inherit = "mrp.product.produce"

    _columns = {
        'product_qty': fields.float('Select Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'mode': fields.selection([('consume_produce', 'Consume & Produce'),], 'Mode', required=True,
                      help="'Consume only' mode will only consume the products with the quantity selected.\n"
                            "'Consume & Produce' mode will consume as well as produce the products with the quantity selected "
                            "and it will finish the production order when total ordered quantities are produced."),
        }
    def do_produce(self, cr, uid, ids, context=None):
        '''Replace do_produce method for checking stock of raw materials
         before produce product.
        '''
        production_id = context.get('active_ids', False)
        prod_obj = self.pool.get('product.product')
        assert production_id, "Production Id should be specified in context as a Active ID."
        production=self.pool.get('mrp.production').browse(cr,uid,production_id)
        data = self.browse(cr, uid, ids[0], context=context)
        if context.get('scan',False)!= True:
            cont = {'lang': 'en_US', 'tz': 'Europe/Brussels', 'uid': 1,'active_model':'mrp.production'}
            return {'name':_("Import Serials"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'pre.import.serial',
                'res_id': False,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': dict(cont, active_ids=production_id, production_qty=data.product_qty, mode=data.mode),
            }
        self.pool.get('mrp.production').action_produce(cr, uid, production_id, data.product_qty, data.mode, data, context=context)

        return {}
