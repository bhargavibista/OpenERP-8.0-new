from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.pooler as pooler
import httplib, ConfigParser, urlparse
from xml.dom.minidom import parse, parseString
import time

class maxmind_cred_details(osv.osv):
    _name = "maxmind.cred.details"
    def onchange_test_production(self,cr,uid,ids,test_production,context):
        if test_production:
            res = {}
            if test_production == 'test':
                res['server_url'] ='https://minfraud.maxmind.com/app/bin_http'
            else:
                res['server_url'] = 'https://minfraud.maxmind.com/app/bin_http'
            return {'value':res}
    _columns = {
       	'server_url': fields.char('Server Url', size=264),
        'test_production': fields.selection([
            ('test', 'Test'),
            ('production', 'Production')
            ], 'Test/Production'),
        'licensekey':fields.char('License Key', size=264),
    }
maxmind_cred_details()
class prepaid_cards_rejected(osv.osv):
    _name = "prepaid.cards.rejected"
    
    _columns = {
       	'card_no': fields.char('Card No', size=264),
        'transaction_id':fields.char('Transaction ID', size=264),
        'date':fields.date('Date of Rejection'),
        'partner_id':fields.many2one('res.partner','Partner ID'),
    }
