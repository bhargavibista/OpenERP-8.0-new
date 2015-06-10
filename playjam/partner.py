# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
class res_partner(models.Model):
    '''Voucher related details'''
    _inherit = 'res.partner'

    wal_bal = fields.Char(string="Wallet Balance", size=32)
    user_auth_ids = fields.One2many(comodel_name="user.auth", inverse_name="partner_id", string="Auth User")
    user_profile_ids = fields.One2many(comodel_name="user.profile", inverse_name="partner_id", string="User Profile")
    playjam_exported = fields.Boolean( )

    _sql_constraints = [('username_uniq', 'unique(name)', 'A partner already exists with this User Name')]