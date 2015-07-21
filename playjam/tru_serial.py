from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
from openerp import models, fields, api, _

class tru_serial(models.Model):
    ''' Tru Serial'''
    _name = 'tru.serial'
    _description = 'Tru Serials'
    _rec_name='serial_no'
  
    truserial_no_sno = fields.Char('TRU SNO',size=32)
    serial_no = fields.Many2one(comodel_name='stock.production.lot',string='Serial Number')
    location_id = fields.Many2one(comodel_name='stock.location',string='Source Location')
    
    
    
tru_serial()