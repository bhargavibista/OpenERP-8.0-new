from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os

class voucher_details(osv.osv):
    '''Voucher related details'''
    _name = 'voucher.details'
    _description = 'Voucher Details'
    _columns={
#        'name': fields.many2one('res.partner',"User Name"),
        'name': fields.many2one('user.auth',"User"),
#        'device_id': fields.char('Device ID', size=32),
        'voucher_code': fields.char('Code', size=128),
        'consumed': fields.boolean('Consumed'),
        'type':fields.selection([('facevalue','Face Value'),('rental','Rental')],'Voucher Type'),
        'expiration': fields.float('Expiration', size=128),
        'flare_bucks':fields.integer('Flare Bucks'),
        'credit':fields.integer('Credit'),
        'rental_apps':fields.many2many('service.apps','voucher_app_rel','voucher_id','app_id','Services'),


    }
    _defaults={
    }

voucher_details()



class service_apps(osv.osv):
    '''Voucher related details'''
    _name = 'service.apps'
    _description = 'Applications'
    _columns={
        'name': fields.char('App Name', size=32),
        'rental_fee':fields.integer('Rental Fee'),

    }
    _defaults={
    }

service_apps()



