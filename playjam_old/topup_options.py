from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os

class topup_options(osv.osv):
    '''Voucher related details'''
    _name = 'topup.options'
    _description = 'Topup Options'
    _columns={
        'name': fields.char("Name" ,size=128),
        'credit': fields.char('Credit', size=128),
        'value': fields.char('Value', size=128),


    }
    _defaults={
    }

topup_options()


