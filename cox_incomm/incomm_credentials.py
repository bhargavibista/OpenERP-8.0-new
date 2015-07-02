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
#from xml.dom.minidom import parse, parseString
import urllib2
import time

class incomm_cred_details(osv.osv):
    _name = "incomm.cred.details"
    def onchange_test_production(self,cr,uid,ids,test_production,context):
        if test_production:
            res = {}
            if test_production == 'test':
                
                res['server_url'] = 'https://milws4-test.incomm.com/transferedvalue/gateway'
#                'https//milws4-test.incomm.com/transferedvalue/gateway'
#                res['server_url'] = 'https://milws.tst.incomm.com:8443/transferedvalue/gateway'
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

class SessionIncomm:
    def InitializeIncomm(self,ServerURL):
        self.ServerURL = ServerURL
        print "self.ServerURL",self.ServerURL
        urldat = urlparse.urlparse(self.ServerURL)
        print "url dattttttttt",urldat
        self.Serverhost = urldat[1]
        print "urldaturldaturldaturldat",urldat[1]
        self.Path = urldat[2]
        print "url dataaa22222222222222",urldat[2]
######### Call
class CallIncomm:
    RequestData = "<xml />"  # just a stub
    
    def MakeCallIncomm(self):
        conn = httplib.HTTPSConnection(self.Session.Serverhost)
        print "connnnnnnnnnnnnnn",conn
        length  = len(self.RequestData)
        print "lenghth.............",length
        conn.request("POST", self.Session.Path, self.RequestData, self.GenerateHeadersIncomm(length))
        response = conn.getresponse()
        print "response................",response
        data = response.read()
        print "datadatadatadatadata",data
        conn.close()
        responseDOM = parseString(data)
        # check for any <Error> tags and print
        # TODO: Return a real exception and log when this happens
        tag = responseDOM.getElementsByTagName('Error')
        print "tag............",tag
        kkkk
        if (tag.count!=0):
            for error in tag:
                print "\n",error.toprettyxml("  ")
        return responseDOM

    def GenerateHeadersIncomm(self,length):
        headers = {"Content-Type":"text/xml",
                    "Content-Length":str(length)}
        print "headers...............",headers
        return headers
    
class GiftCardStatInq:
    Session = SessionIncomm()
    def __init__(self, ServerURL,context={}):
        print "ServerURLServerURL1223",ServerURL
        self.Session.InitializeIncomm(ServerURL)
#        
    def get_response(self,nodelist):
        info = {}
        for node in nodelist:
            for cNode in node.childNodes:
                if cNode.nodeName == 'RespMsg':
                    if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
#                elif cNode.nodeName == 'FaceValue':
#                    info[cNode.nodeName] = cNode.childNodes[0].data
#                    for gcNode in cNode.childNodes:
#                        if gcNode.nodeName == 'text':
#                            info[cNode.nodeName] = gcNode.childNodes[0].data
        return info
##      api call for status inquiry of gift card
    def Get(self,date,time,partner_name,pin,acc_num,src_refnum):
        print "date",date,time,partner_name,pin,acc_num,src_refnum
        api = CallIncomm()
        api.Session = self.Session
        api.RequestData =""" <?xml version="1.0" encoding="UTF-8"?> 
        < TransferredValueTxn> 
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
        </TransferredValueTxn>#"""% (date,time,partner_name,pin,acc_num,src_refnum)
        print "api request data...................",api.RequestData
#        r=urllib2.Request("https://milws.tst.incomm.com:8443/transferedvalue/gateway",data= api.RequestData,headers={'Content-Type': 'application/xml'})
#        u = urllib2.urlopen(r)
#        print "uuuuuuuuuuuuuuuuuuuuuuuuuu",u
#        content = u.read()
#        print "uuuuuu45656768uuuuuuuuuuuuuuuuuuuu",u
#        dfgfhg
        responseDOM = api.MakeCallIncomm()
        response_ids = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('TransferredValueTxnResp'))
        print "response_okresponse_okresponse_ok",response_ok
        if response_ok.get('RespMsg',False) == 'Card is Active':
            response_ids=response_ok.get('RespMsg',False)
#            response_ids=self.getfacevalue(responseDOM.getElementsByTagName('Product'))
            
        else:
            text = response_ok.get('RespMsg',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        print"xml########",responseDOM.toprettyxml()
        responseDOM.unlink()
        return response_ids
    
    def getfacevalue(self,nodelist):
       facevalue,final_info = [],{}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'FaceValue':
                   if cNode.childNodes:
                         facevalue.append(cNode.childNodes[0].data)
       final_info['FaceValue'] = facevalue
       return final_info
 
class GiftCardRedemption:
    Session = SessionIncomm()
    def __init__(self, ServerURL,context={}):
        print "ServerURLServerURL1234",ServerURL
        self.Session.InitializeIncomm(ServerURL)
#        
    def get_response(self,nodelist):
        dfhgfghj
        info = {}
        for node in nodelist:
            for cNode in node.childNodes:
                if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'message':
                    for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
        return info
##    api call for Redemption of gift card
    def Get(self,date,time,partner_name,pin,acc_num,src_refnum):
        print "date",date,time,partner_name,pin,acc_num,src_refnum
        api = CallIncomm()
        api.Session = self.Session
        api.RequestData =""" <?xml version="1.0" encoding="UTF-8"?>
                < TransferredValueTxn
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-
                instance" >
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
                </TransferredValueTxn>"""% (date,time,partner_name,pin,acc_num,src_refnum)
        print "api request data...................",api.RequestData
        responseDOM = api.MakeCallIncomm()
        
        response_ids = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        print "response_okresponse_okresponse_ok",response_ok
        kjhkjh
        if response_ok.get('resultCode',False) == 'Ok':
            cvcgbhg
#            response_ids = self.get_profile_ids(responseDOM.getElementsByTagName('ids'))
        else:
            text = response_ok.get('message',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        print"xml########",responseDOM.toprettyxml()
        responseDOM.unlink()
        return response_ids
#    
class GiftCardReversal:
    Session = SessionIncomm()
    def __init__(self, ServerURL,context={}):
        print "ServerURLServerURL1234",ServerURL
        self.Session.InitializeIncomm(ServerURL)
#        
    def get_response(self,nodelist):
        info = {}
        for node in nodelist:
            for cNode in node.childNodes:
                if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
                elif cNode.nodeName == 'message':
                    for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
        return info
#    api call for Reversal of Redemption request of gift card and making it active again
    def Get(self,date,time,partner_name,pin,acc_num,src_refnum):
        print "date",date,time,partner_name,pin,acc_num,src_refnum
        api = CallIncomm()
        api.Session = self.Session
        api.RequestData =""" <?xml version="1.0" encoding="UTF-8"?>
                    < TransferredValueTxn
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-
                    instance" >
                    < TransferredValueTxnReq>
                    <ReqCat>TransferredValue</ReqCat>
                    <ReqAction>Reverse</ReqAction>
                    <Date>%s</Date>
                    <Time>%s</Time>
                    <PartnerName>%s</ PartnerName >
                    <CardActionInfo>
                    <PIN>%s</ PIN>
                    <AcctNum>%s</AcctNum>
                    <SrcRefNum>%s</SrcRefNum>
                    </CardActionInfo>
                    </TransferredValueTxnReq>
                    </ TransferredValueTxn >"""% (date,time,partner_name,pin,acc_num,src_refnum)
        print "api request data...................",api.RequestData
        responseDOM = api.MakeCallIncomm()
        response_ids = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        print "response_okresponse_okresponse_ok",response_ok
        if response_ok.get('resultCode',False) == 'Ok':
            fdhgf
#            response_ids = self.get_profile_ids(responseDOM.getElementsByTagName('ids'))
        else:
            text = response_ok.get('message',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        print"xml########",responseDOM.toprettyxml()
        responseDOM.unlink()
        return response_ids
#    
 
class gift_card_validate_call(osv.osv):
    _name = 'gift.card.validate.call'
    
    def api_call_toincomm_test(self,cr,uid,ids,context=None):
        xml_text="""<?xml version='1.0' encoding='UTF-8'?>
        <TransferredValueTxn>
        <TransferredValueTxnReq>
        <ReqCat>TransferredValue</ReqCat>
        <ReqAction>StatInq</ReqAction>
        <Date></Date>
        <Time></Time>
        <PartnerName>Flare Entertainment</PartnerName>
                <CardActionInfo>
                <PIN>7489807526</PIN>
                <AcctNum></AcctNum>
                <SrcRefNum></SrcRefNum>
        </CardActionInfo>
        </TransferredValueTxnReq>
        </TransferredValueTxn>"""
        r=urllib2.Request("https://milws4-test.incomm.com/transferedvalue/gateway",data=xml_text,headers={'Content-Type': 'application/xml'})
        u = urllib2.urlopen(r)
        response = u.read()
        print "responseresponseresponseresponse",response
        xml1 = xml.dom.minidom.parseString(response)
        pretty_xml_as_string = xml1.toprettyxml()
        print "pretttyyyyyyyyyyyyyyyyyyy",pretty_xml_as_string
#        incomm_cred_obj=self.pool.get('incomm.cred.details')
#        config_ids = incomm_cred_obj.search(cr,uid,[])
#        print "config_idsconfig_idsconfig_ids",config_ids
#        if config_ids:
#            config_obj = incomm_cred_obj.browse(cr,uid,config_ids[0])
#            print "config_objconfig_obj",config_obj
#            date='20130806'
#            time='085800'
#            partner_name='Flare Entertainment'
#            pin='7232140658'
#            acc_num='6262722235'
#            src_refnum='0000006262722235'
#            self.call(cr, uid, config_obj, 'gift_card_stat_inq',date,time,partner_name,pin,acc_num,src_refnum)
#            self.call(cr, uid, config_obj, 'gift_card_redemption',date,time,partner_name,pin,acc_num,src_refnum)
#            self.call(cr, uid, config_obj, 'gift_card_reversal',date,time,partner_name,pin,acc_num,src_refnum)

    def call(self, cr, uid, obj, method, *arguments):
        print "methodmethod",method,obj.server_url
        if method == 'gift_card_stat_inq':
            gp = GiftCardStatInq(obj.server_url)
            print "gppppppppppppppppppppp",gp,arguments,obj.server_url
            result = gp.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5])
            return result
#            print"result",result
        elif method=='gift_card_redemption':
            gcr= GiftCardRedemption(obj.server_url)
            print "gppppppppppppppppppppp",gcr,arguments
            result = gcr.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5])
            return result
            
        elif method=='gift_card_reversal':
            gcre= GiftCardReversal(obj.server_url)
            print "gppppppppppppppppppppp",gcre,arguments
            result = gcre.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5])
            return result
            
    _columns = {
       	'partner_id': fields.many2one('res.partner','Partner'),
        'gift_card_details':fields.char('Gift Card',size=256)
    }

gift_card_validate_call()

