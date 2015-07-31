from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
from openerp import models, fields, api, _

class topup_options(models.Model):
    '''Voucher related details'''
    _name = 'topup.options'
    _description = 'Topup Options'
    
    name = fields.Char(string='Name',size=128)
    credit = fields.Char(string='Credit',size=128)
    value = fields.Char(string='Value',size=128)
    

topup_options()


class playjam_config_menu(models.Model):
    '''Playjam Configuration'''
    _name = 'playjam.config.menu'
    _description = 'Playjam Configuration'

    wallet_playjam = fields.Char(size=128)
    rental_playjam =  fields.Char(size=128)
    account_playjam = fields.Char(size=128)
    profile_playjam = fields.Char(size=128)
    device_playjam = fields.Char(size=128)
    obtain_transactions_playjam = fields.Char(size=128)
    magento_api_id= fields.Char(string='Magento API', size=128)
    current_db= fields.Char(string='Current DB', size=128)

    _defaults={
    }

playjam_config_menu()
