from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
import datetime
import hashlib
import md5
from datetime import timedelta
from datetime import date
import time
import requests
import json
import urllib
import ast


class user_profile(osv.osv):
    '''Authenticating the user'''
    _name = 'user.profile'
    _description = 'User Authentication'

    _columns={
        'partner_id': fields.many2one('res.partner',"User Name"),
        'gender': fields.selection([
                ('M', 'Male'),
                ('F', 'Female'),
                ('O', 'OTHER')], 'Gender'),
        'dob': fields.date('DOB', size=128),
        'pin': fields.char('Pin', size=128),
        'avatar_id': fields.integer('Avatar Id'),
        'age_rating':fields.integer('Age Rating', size=128),
        'pc_params':fields.char('PC Params', size=128),
        'playjam_exported': fields.boolean('Playjam Exported'),
	'player_tag': fields.char('Player Tag'),

    }
    _defaults={
    'gender':'O'
    }
    
    _sql_constraints = [('playertag_uniq', 'unique(player_tag)', 'The Player Tag already exists.')]


user_profile()
    
