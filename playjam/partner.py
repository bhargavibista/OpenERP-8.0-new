# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import requests
import urllib
import ast


class res_partner(models.Model):
    """
        Voucher related details
    """
    _inherit = 'res.partner'
    wal_bal = fields.Char(string="Wallet Balance", size=32)
    user_auth_ids = fields.One2many(comodel_name="user.auth", inverse_name="partner_id", string="Auth User")
    user_profile_ids = fields.One2many(comodel_name="user.profile", inverse_name="partner_id", string="User Profile")
    playjam_exported = fields.Boolean()

    _sql_constraints = [('username_uniq', 'unique(name)', 'A partner already exists with this User Name')]

    def get_wallet_update(self):
        url = "http://54.172.158.69/api/rest/flare/wallet/view.json"
        headers = {'content-type': 'application/x-www-form-urlencoded', 'content-length': 68}
        #                    payload = '{"uid": uid, "quantity":float(value)}'
        payload = '{"uid": "FLARE1124", "quantity":0}'
        request = urllib.quote(payload.encode('utf-8'))
        print "request-----------------", request

        response = requests.post(
            url, data="request=" + request, headers=headers)

        print "response------------------", response.text
        resp = response.text
        res = ast.literal_eval(resp)
        print 'res----------------', type(res), res
        #        ero
        if res and 'body' in res and ('quantity' in res.get('body')):
            qty = res['body']['quantity']
            if qty:
                self.write({'wal_bal': qty})
                return True
        self.write({'wal_bal': 'Error'})
        return True

    @api.one
    def account_deactivate(self):
        payload = dict(mode='U', uid=self.ids, active=False)
        res = self.pool.get('user.auth').account_playjam(payload)
        print "res-------------", res
        dict_res = ast.literal_eval(res)
        if 'body' in dict_res and ('result' in dict_res.get('body')):
            if dict_res['body']['result'] == 4097:
                res.write({'active': False,})
                return True
        raise Warning(_('Deactivation Call to Playjam Failed.'))

    @api.one
    def account_reactivate(self):
        payload = dict(mode= 'U', uid= self.ids, active=False)
        res = self.pool.get('user.auth').account_playjam(payload)
        print "res-------------",res
        dict_res = ast.literal_eval(res)
        if 'body' in dict_res and ('result' in dict_res.get('body')):
            if dict_res['body']['result'] == 4097:
                res.write({'active': True})
                return True
        raise Warning(_('Reactivation Call to Playjam Failed. '))
res_partner()
