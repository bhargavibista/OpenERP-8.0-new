# -*- coding: utf-8 -*-
from openerp import models, fields


class user_profile(models.Model):
    """
    Authenticating the user
    """
    _name = 'user.profile'
    _description = 'User Authentication'

    partner_id = fields.Many2one(comodel_name="res.partner", string="User Name", required=False, )
    gender = fields.Selection(selection=[('M', 'Male'), ('F', 'Female'), ('O', 'OTHER')], default='O', required=False, )
    dob = fields.Char()
    pin = fields.Char()
    avatar_id = fields.Char()
    age_rating = fields.Char()
    pc_params = fields.Char()
    playjam_exported = fields.Boolean()
    player_tag = fields.Char(string='Player Tag',size=100)
    _defaults={
    'gender':'O'
    }
    _sql_constraints = [('playertag_uniq', 'unique(player_tag)', 'The Player Tag already exists.')]
