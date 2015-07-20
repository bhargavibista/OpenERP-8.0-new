from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
from openerp import models, fields, api, _

class topup_options(models.Model):
    '''Voucher related details'''
    _name = 'topup.options'
    _description = 'Topup Options'
#    _columns={
#        'name': fields.char("Name" ,size=128),
#        'credit': fields.char('Credit', size=128),
#        'value': fields.char('Value', size=128),
#
#
#    }
    
    name = fields.Char(string='Name',size=128)
    credit = fields.Char(string='Credit',size=128)
    value = fields.Char(string='Value',size=128)
    

topup_options()


class playjam_config_menu(models.Model):
    '''Playjam Configuration'''
    _name = 'playjam.config.menu'
    _description = 'Playjam Configuration'
#    _columns={
#        'wallet_playjam': fields.char("Wallet Playjam" ,size=128),
#        'rental_playjam': fields.char('Rental Playjam', size=128),
#        'account_playjam': fields.char('Account Playjam', size=128),
#        'profile_playjam': fields.char('Profile Playjam', size=128),
#        'device_playjam': fields.char('Device Playjam', size=128),
#        'obtain_transactions_playjam': fields.char('Obtain Transactions Playjam', size=128),
#
#    }

    wallet_playjam = fields.Char(size=128)
    rental_playjam =  fields.Char(size=128)
    account_playjam = fields.Char(size=128)
    profile_playjam = fields.Char(size=128)
    device_playjam = fields.Char(size=128)
    obtain_transactions_playjam = fields.Char(size=128)
    _defaults={
    }

playjam_config_menu()