# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
class reasons_title(osv.osv):
    _name = 'reasons.title'
    _columns = {
    'name': fields.char('Title', size=256, select=True),
    'active': fields.boolean('Active'),
    'module': fields.selection([
            ('returns', 'Returns'),
            ('tech_supp', 'Technical Support')
            ], 'Returns/Technical Support'),
    }
    _defaults = {
    'active': True
    }
reasons_title()

class tru_subscription_options(osv.osv):
    '''Gift Card Subscription Details'''
    _name = 'tru.subscription.options'
    _description = 'TRU Subscriptions'
    _columns={
        'product_id': fields.many2one('product.product', 'Product', ondelete='set null', select=True),
        'sales_channel_tru': fields.selection([
            ('tru', 'TRU'),
            ], 'Sales Channels'),


    }
    _defaults={
    }

tru_subscription_options()
