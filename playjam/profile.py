# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class user_profile(models.Model):
    '''Authenticating the user'''
    _name = 'user.profile'
    _description = 'User Authentication'

    partner_id = fields.Many2one(comodel_name="res.partner", string="User Name", required=False, )
    gender = fields.Selection(selection=[('M', 'Male'), ('F', 'Female'),('O', 'OTHER') ],default='O', required=False, )
    dob = fields.Char()
    pin = fields.Char()
    avatar_id = fields.Char()
    age_rating = fields.Char()
    pc_params = fields.Char()
    playjam_exported = fields.Boolean()
