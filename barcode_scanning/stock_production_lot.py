from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
import openerp.addons.decimal_precision as dp


class stock_production_lot(osv.osv):

    _inherit = 'stock.production.lot'


#    def create(self, cr, uid, vals, context=None):
#
#        t = type(vals['name'])
#        b = ()
#        if type(vals['name']) == type(b):
#            new_lot_number = int(vals['name'][0]) + 600000000
#        else:
#            new_lot_number = int(vals['name']) + 600000000
#        vals.update({'name': str(new_lot_number)})
#        new_id = super(stock_production_lot, self).create(cr, uid, vals, context)
#        return new_id


    _columns = {
        'serial_used' : fields.boolean('InActive'),
#        'stock_move_id' : fields.many2one('stock.move','Stock Move'),
    }

stock_production_lot()
