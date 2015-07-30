from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
from openerp import models, fields, api, _

class voucher_details(models.Model):
    '''Voucher related details'''
    _name = 'voucher.details'
    _description = 'Voucher Details'

    name = fields.Many2one(comodel_name='user.auth',string="User")
    device_id = fields.Char(string='Device ID',size=32)
    voucher_code = fields.Char(stirng='Code',size=128)
    consumed = fields.Boolean(string='Consumed')
    type = fields.Selection([('facevalue','Face Value'),('rental','Rental')],string='Voucher Type')
    expiration = fields.Float(string='Expiration',size=128)
    flare_bucks = fields.Integer(string='Flare Bucks')
    credit = fields.Integer(string='Credit')
    rental_apps = fields.Many2many('service.apps','voucher_app_rel','voucher_id','app_id',string='Services')
    

voucher_details()



class service_apps(models.Model):
    '''Voucher related details'''
    _name = 'service.apps'
    _description = 'Applications'

    name =  fields.Char(string='App Name',size=32)
    rental_fee = fields.Integer(string='Rental Fee')
service_apps()
