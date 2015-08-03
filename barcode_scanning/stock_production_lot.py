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

    _columns = {
        'serial_used' : fields.boolean('InActive'),
    }

stock_production_lot()
