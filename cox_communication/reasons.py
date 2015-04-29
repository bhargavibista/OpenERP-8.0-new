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