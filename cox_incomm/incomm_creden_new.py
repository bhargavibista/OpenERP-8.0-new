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
import xml.dom.minidom
from xml.dom.minidom import parse, parseString
import urllib2
import ast
import time

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
    
    def api_call_toincomm_statinq(self,cr,uid,card_num,context):
        url = "https://milws4-test.incomm.com/transferedvalue/gateway"
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
#        print "rrrrrrrrrrrrrrrrrrrrrr",r
        u = urllib2.urlopen(r)
        response = u.read()
#        print "response...............",response
        xml1 = xml.dom.minidom.parseString(response)
        stat_inq_data = xml.dom.minidom.parseString(response)
        pretty_xml_as_string_statinq = xml1.toprettyxml()
        print "pretty_xml_as_string_statinq...............",pretty_xml_as_string_statinq,stat_inq_data
#        resp_msg=xml1.getElementsByTagName("RespMsg")[0].childNodes[0].nodeValue
#        face_value=xml1.getElementsByTagName("FaceValue")[0].childNodes[0].nodeValue
#        print "face valieueeeeeeeeee...........",face_value
        return stat_inq_data
        
    def api_call_toincomm_redemption(self,cr,uid,card_num,context):
        url = "https://milws4-test.incomm.com/transferedvalue/gateway"
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
        print "response...............",response
        xml2 = xml.dom.minidom.parseString(response)
        pretty_xml_as_string_redemption = xml2.toprettyxml()
        print "pretty_xml_as_string_statinq...............",pretty_xml_as_string_redemption
        redemption_data = xml.dom.minidom.parseString(response)
#        print "redemption data...............",redemption_data
        return redemption_data
        

    def api_call_toincomm_reversal(self,cr,uid,card_num,context):
        url = "https://milws4-test.incomm.com/transferedvalue/gateway"
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
        print "response...............",response
        xml3 = xml.dom.minidom.parseString(response)
        pretty_xml_as_string_reversal = xml3.toprettyxml()
        print "pretty_xml_as_string_statinq...............",pretty_xml_as_string_reversal
        reversal_data = xml.dom.minidom.parseString(response)
        print "reversal_data data...............",reversal_data
        return reversal_data
        
    _columns = {
       	'partner_id': fields.many2one('res.partner','Partner'),
        'gift_card_details':fields.char('Gift Card',size=256)
    }
gift_card_validate_call()