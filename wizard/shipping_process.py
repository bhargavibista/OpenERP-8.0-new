# To change this template, choose Tools | Templates
# and open the template in the editor.

from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp import netsvc
import tempfile
from openerp import pooler
import time
def sortedDictValues(adict):
    keys = adict.keys()
    keys.sort()
    return map(adict.get, keys)
class generate_packing_list(osv.osv_memory):
    _name = 'generate.packing.list'
    _description = 'Print Sorted Picking Lists'
    _columns = {
        'carrier_id': fields.many2one('delivery.carrier', 'Carrier'),
#        'shop_id': fields.many2one('sale.shop', 'Shop'),
        'limit': fields.integer('Limit Orders'),
        'skip_wholesale': fields.boolean('Skip wholesale orders?'),
        'redo_search': fields.boolean('Redo search', help='This will select all available orders')
    }
    _defaults = {
        'limit': lambda *a: 150,
        #'shop_id': lambda *a: 1,
        'skip_wholesale': lambda *a: True,
    }
generate_packing_list()