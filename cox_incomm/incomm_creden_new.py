# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.pooler as pooler
import httplib, ConfigParser, urlparse
import urllib2
import json
import xml.dom.minidom
from xml.dom.minidom import parse, parseString
import urllib2
import ast
import time
import logging
_logger = logging.getLogger(__name__)

class incomm_cred_details(osv.osv):
    _name = "incomm.cred.details"
    def onchange_test_production(self,cr,uid,ids,test_production,context):
        if test_production:
            res = {}
            if test_production == 'test':
                
                res['server_url'] = 'https://milws4-test.incomm.com/transferedvalue/gateway'
            else:
                res['server_url'] = 'https://milws4-test.incomm.com/transferedvalue/gateway'
            return {'value':res}
    _columns = {
       	'server_url': fields.char('Server Url', size=264),
         'test_production': fields.selection([
            ('test', 'Test'),
            ('production', 'Production')
            ], 'Test/Production'),
    }
incomm_cred_details()

class gift_card_validate_call(osv.osv):
    _name = 'gift.card.validate.call'
    
    """Call to incomm for status inquiry of Gift Card"""
    def api_call_toincomm_statinq(self,cr,uid,card_num,context):
        incomm_config=self.pool.get('incomm.cred.details')
        config_ids = incomm_config.search(request.cr,SUPERUSER_ID,[])
        if config_ids:
            config_obj = incomm_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
            url=config_obj.server_url
        else:
            result={"body":{ 'code':'False', 'message':"Please Define Incomm Configuration!!"}}
            return json.dumps(result)
#        url = "https://milws4-test.incomm.com/transferedvalue/gateway"
        xml_text="""<?xml version='1.0' encoding='UTF-8'?>
        <TransferredValueTxn>
        <TransferredValueTxnReq>
        <ReqCat>TransferredValue</ReqCat>
        <ReqAction>StatInq</ReqAction>
        <Date>%s</Date>
        <Time>%s</Time>
        <PartnerName>%s</PartnerName>
                <CardActionInfo>
                <PIN>%s</PIN>
                <AcctNum>%s</AcctNum>
                <SrcRefNum>%s</SrcRefNum>
        </CardActionInfo>
        </TransferredValueTxnReq>
        </TransferredValueTxn>"""% ('','','Flare Entertainment',card_num,'','')
        r=urllib2.Request(url,data=xml_text,headers={'Content-Type': 'application/xml'})
        u = urllib2.urlopen(r)
        response = u.read()
        _logger.info('request for api_call_toincomm_statinq----------------- %s', response)
        xml1 = xml.dom.minidom.parseString(response)
        stat_inq_data = xml.dom.minidom.parseString(response)
        pretty_xml_as_string_statinq = xml1.toprettyxml()
        return stat_inq_data
        
        """Call to Incomm to Redeem the gift card"""
    def api_call_toincomm_redemption(self,cr,uid,card_num,context):
        incomm_config=self.pool.get('incomm.cred.details')
        config_ids = incomm_config.search(request.cr,SUPERUSER_ID,[])
        if config_ids:
            config_obj = incomm_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
            url=config_obj.server_url
        else:
            result={"body":{ 'code':'False', 'message':"Please Define Incomm Configuration!!"}}
            return json.dumps(result)
#        url = "https://milws4-test.incomm.com/transferedvalue/gateway"
        xml_text="""<?xml version='1.0' encoding='UTF-8'?>
        <TransferredValueTxn>
        <TransferredValueTxnReq>
        <ReqCat>TransferredValue</ReqCat>
        <ReqAction>Redeem</ReqAction>
        <Date>%s</Date>
        <Time>%s</Time>
        <PartnerName>%s</PartnerName>
                <CardActionInfo>
                <PIN>%s</PIN>
                <AcctNum>%s</AcctNum>
                <SrcRefNum>%s</SrcRefNum>
        </CardActionInfo>
        </TransferredValueTxnReq>
        </TransferredValueTxn>"""% ('','','Flare Entertainment',card_num,'','')
        r=urllib2.Request(url,data=xml_text,headers={'Content-Type': 'application/xml'})
        u = urllib2.urlopen(r)
        response = u.read()
        _logger.info('response for api_call_toincomm_redemption----------------- %s', response)
        xml2 = xml.dom.minidom.parseString(response)
        pretty_xml_as_string_redemption = xml2.toprettyxml()
        redemption_data = xml.dom.minidom.parseString(response)
        return redemption_data
        
    """Call to Incomm to reverse the Gift Card Status to Active"""
    def api_call_toincomm_reversal(self,cr,uid,card_num,context):
        incomm_config=self.pool.get('incomm.cred.details')
        config_ids = incomm_config.search(request.cr,SUPERUSER_ID,[])
        if config_ids:
            config_obj = incomm_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
            url=config_obj.server_url
        else:
            result={"body":{ 'code':'False', 'message':"Please Define Incomm Configuration!!"}}
            return json.dumps(result)
#        url = "https://milws4-test.incomm.com/transferedvalue/gateway"
        xml_text="""<?xml version='1.0' encoding='UTF-8'?>
        <TransferredValueTxn>
        <TransferredValueTxnReq>
        <ReqCat>TransferredValue</ReqCat>
        <ReqAction>Reverse</ReqAction>
        <Date>%s</Date>
        <Time>%s</Time>
        <PartnerName>%s</PartnerName>
                <CardActionInfo>
                <PIN>%s</PIN>
                <AcctNum>%s</AcctNum>
                <SrcRefNum>%s</SrcRefNum>
        </CardActionInfo>
        </TransferredValueTxnReq>
        </TransferredValueTxn>"""% ('','','Flare Entertainment',card_num,'','')
        r=urllib2.Request(url,data=xml_text,headers={'Content-Type': 'application/xml'})
        u = urllib2.urlopen(r)
        response = u.read()
        _logger.info('response for api_call_toincomm_reversal----------------- %s', response)
        xml3 = xml.dom.minidom.parseString(response)
        pretty_xml_as_string_reversal = xml3.toprettyxml()
        reversal_data = xml.dom.minidom.parseString(response)
        return reversal_data
        
    _columns = {
       	'partner_id': fields.many2one('res.partner','Partner'),
        'gift_card_details':fields.char('Gift Card',size=256)
    }
gift_card_validate_call()