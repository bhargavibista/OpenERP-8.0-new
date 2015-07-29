from openerp.osv import fields, osv
import datetime 
import sys
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
import calendar
from openerp.tools.misc import attrgetter
#from openerp.addons.base_external_referentials.external_osv import ExternalSession
#from openerp.addons.magentoerpconnect import magerp_osv
DEBUG = True
from openerp.tools.translate import _
import random
from openerp import netsvc
import string
import time
import ast
from validate_email import validate_email
import md5
import logging
import re
import uuid
from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
import urllib
import requests
import json
import ast
from passlib.hash import pbkdf2_sha256
from openerp import models, fields, api, _
from openerp.http import request
from openerp import SUPERUSER_ID
import random
import string

#~ from datetime import datetime


class res_partner(models.Model):
    '''Voucher related details'''
    _inherit = 'res.partner'
#    _columns={
#
#        'user_name':fields.char('User Name', size=100),
#        'password':fields.text('Password'),
#        'gender':fields.selection([
#            ('M', 'Male'),
#            ('F', 'Female'),
#	    ('O', 'Other')
#            ], 'Gender'),
#        'dob':fields.date('DOB'),
#        'age_rating':fields.char('Age Rating'),
#        'player_tag':fields.char('Player Tag'),
#        'game_profile_name':fields.char('Game Profile Name'),
#        'account_pin':fields.char('Account Pin'),
#        'use_wallet':fields.char('Use Wallet'),
#	
#
#    }
    user_name = fields.Char(string ='User Name',size=100)
    password = fields.Text(string='Password')
    magento_pwd =fields.Char('Password',size=128)
    gender = fields.Selection([('M', 'Male'),
            ('F', 'Female'),
	    ('O', 'Other')],string='Gender')
    dob = fields.Date(string='DOB')
    age_rating = fields.Char(string='Age Rating',size=100)
    player_tag = fields.Char(string='Player Tag',size=100)
    game_profile_name = fields.Char(string='Game Profile Name',size=100)
    account_pin = fields.Char(string='Account Pin',size=100)
    use_wallet = fields.Char(string='Use Wallet',size=100)
    pay_profile_id = fields.Char('Payment Profile')    
    
#    _sql_constraints = [('username_uniq', 'unique(name)', 'A partner already exists with this User Name')]

    _defaults={
    'magento_pwd':'ZmwyNDc2',
    'password':'ZmwyNDc2'
    }
    def create(self,cr,uid, vals, context={}):
        print "password--233435--------------",vals.get('password')
        if vals.has_key('password'):
            pwd=vals.get('password')
            hash = pbkdf2_sha256.encrypt(str(pwd), rounds=200, salt_size=16)
            vals['password']=str(hash)

        res = super(res_partner, self).create(cr, uid, vals, context)

        return res

    def write(self, cr,uid,ids, vals, context={}):
        print "password----------------",vals.get('password')
	print "ids-----------------------------------",ids,type(ids)
	res=True
	#if tyoe(ids)==str:
	    #ids=int(ids)
	if isinstance(ids,(int,str)) :
	    ids=int(ids)
            ids = [ids]
#	else:
#	    ids=int(ids)
  	print "ids......................878787...",ids
        if vals.has_key('password'):
            pwd=vals.get('password')
            hash = pbkdf2_sha256.encrypt(str(pwd), rounds=200, salt_size=16)
            vals['password']=str(hash)        
	res = super(res_partner, self).write(cr, uid, ids, vals, context)
        #if vals.has_key('password'):
         #   pwd=vals.get('password')
          #  hash = pbkdf2_sha256.encrypt(str(pwd), rounds=200, salt_size=16)
           # vals['password']=str(hash)
        if ids:
	 #   print "ids--------------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^-----------",ids
	    if isinstance(ids,(int)) :
		ids = [ids]
	#	res = super(res_partner, self).write(cr, uid, ids, vals, context)
	    x=ids[0]
            print "x.................................",x,type(x)
            playjam_exported=self.browse(cr,uid,int(x)).playjam_exported
            if playjam_exported:
                playjam_update_vals={'mode':'U'}
                if vals.has_key('account_pin'):
                    account_pin=vals.get('account_pin')
                    playjam_update_vals.update({'accountPin':account_pin})
                if vals.has_key('name'):
                    name=vals.get('name')
                    x=name.find('')
                    name=name.replace(" ","")
                    first_name=name[:x]
                    last_name=name[x:]
                    playjam_update_vals.update({'name':first_name,'surname':last_name})
                if vals.has_key('emailid'):
                    emailid=vals.get('emailid')
                    playjam_update_vals.update({'email':emailid})
                if vals.has_key('dob'):
                    dob=vals.get('dob')
                    if dob:
                        date_object = datetime.datetime.strptime(dob, '%Y-%m-%d')
                        dob=date_object.strftime('%Y/%m/%d')
                        playjam_update_vals.update({'dob':dob})
                if vals.has_key('active'):
                    active=vals.get('active')
                    playjam_update_vals.update({'active':active})
		playjam_update_vals.update({'uid':int(x)})
		print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",x
		length=len(playjam_update_vals)
		print "length-----------------------------",length
		if int(x)!=0 and length>2:
                    response=self.pool.get('user.auth').account_playjam(playjam_update_vals)
                    print"res----account---------",response,type(response)
                    dict_res=ast.literal_eval(response)
                    if dict_res.has_key('body') and (dict_res.get('body')).has_key('result'):
                        if dict_res['body']['result']!=4098:
                            raise osv.except_osv('Error!!', 'Account Not Updated At Playjam!')
        return res


#    {"ApiId":"123","DBName":"cox_db_12jan","CustomerId": "","FirstName": "abc","LastName": "pqr","Email": "abc@gmail.co", "PrimaryGameProfileName":"ab",
#"Password": "pqr","DOB":"1991-01-30","Gender":"M/F/O","AgeRating":14 , "AccountPIN":"123","UseWallet":True}

#    wallet processing
#    function to Top up the wallet using  CC
    def wallet_topup(self,dict,context=None):
        count=0
        context_maxmind={}
#        dict={'BillingInfo': {'PaymentProfileId': '29720861','BillingAddress': {'Street1': '581 Telegraph Canyon Rd', 'Street2': '', 'State': 'CA', 'Zip': '91910-6436', 'City': 'Chula Vista'}, 'CreditCard': {'CCNumber': '510510493671000', 'CCV': '123', 'ExpDate': '122020'}}, 'FillAmount': 10.0, 'ApiId': '123', 'PaymentType': 'CC', 'CustomerId': 6,'DBName': 'april_26th_final_test'}
#        dict_old={ 'BillingInfo': {'PaymentProfileId': '','BillingAddress': {'Street1': '581 Telegraph Canyon Rd', 'Street2': '', 'State': 'California', 'Zip': '91910-6436', 'City': 'Chula Vista'}, 'CreditCard': {'CCNumber': '510510493671000', 'CCV': '123', 'ExpDate': '122020'}}, 'FillAmount': 10.0, 'ApiId': '123', 'PaymentType': 'CC', 'CustomerId': 4543,'DBName': 'local_stable_7_test'}
        dict_wallet = { 'fill_amount':dict.get('FillAmount'),'payment_type':dict.get('PaymentType'),
                    'billing_info':dict.get('BillingInfo'),'api_id':dict.get('ApiId'),'partner_id':dict.get('CustomerId'),
                    }
        authorize_net_config = self.pool.get('authorize.net.config')
        journal_pool = self.pool.get('account.journal')
        account_voucher_obj=self.pool.get('account.voucher')
        prepaid_obj=self.pool.get('prepaid.cards.rejected')
        payment_obj=self.pool.get('custmer.payment.profile')
        partner_obj=self.pool.get('res.partner')
        user_auth_obj=self.pool.get('user.auth')
        inv_obj=self.pool.get('account.invoice')
        transaction_id=''
        act_model='res.partner'
        transaction_type='profileTransAuthCapture'
        today=datetime.date.today()
        for key, value in dict_wallet.iteritems():
            if value is '':
                result={"body":{ 'code':'-5634', 'message':"Invalid Request Data"}}
                return json.dumps(result)
        customer_id=partner_obj.search(request.cr,SUPERUSER_ID,[('id','=',int(dict_wallet.get('partner_id')))])

        print "customer_idcustome343546r_id",customer_id
        if not customer_id:
            result={"body":{ 'code':'-5555', 'message':"Missing or Invalid Customer ID"}}
            return json.dumps(result)
        #if the payment needs to be processed using CC
        auth_config_ids = authorize_net_config.search(request.cr,SUPERUSER_ID,[])
        credit_card=dict_wallet.get('billing_info').get('CreditCard')
        if credit_card:
            ccn=credit_card.get('CCNumber')
            ccv=credit_card.get('CCV')
            exp_date=credit_card.get('ExpDate')
            exp_date = exp_date[-4:] + '-' + exp_date[:2]
        active_id=int(dict_wallet.get('partner_id'))
        partner_brw=partner_obj.browse(request.cr,SUPERUSER_ID,active_id)
        playjam_exported=partner_brw.playjam_exported
        if not playjam_exported:
            result={"body":{ 'code':False, 'message':"Customer not present at Playjam End"}}
            return json.dumps(result)
        if dict_wallet.get('billing_info').has_key('PaymentProfileId') and auth_config_ids:
            billing_info=dict_wallet.get('billing_info')
            payment_profile_id=billing_info.get('PaymentProfileId')
            config_obj = authorize_net_config.browse(request.cr,SUPERUSER_ID,auth_config_ids[0])
            amount=dict_wallet.get('fill_amount')
            bank_journal_ids = journal_pool.search(request.cr,SUPERUSER_ID, [('type', '=', 'bank')])
            account_data = inv_obj.get_accounts(request.cr,SUPERUSER_ID,active_id,bank_journal_ids[0])
            print "account_dataaccount_data",account_data,account_data['value']['account_id']
            voucher_data = {'account_id':account_data['value']['account_id'],'partner_id': active_id,'journal_id':bank_journal_ids[0],'amount': amount,'type':'receipt','state': 'draft','pay_now': 'pay_later','name': '','date': today,'company_id': self.pool.get('res.company')._company_default_get(request.cr,SUPERUSER_ID, 'account.voucher',context=None),'payment_option': 'without_writeoff','comment': _('Write-Off')}
            print "voucher data,,,,,,,,,,,,,,,,,,,,,,,",voucher_data
            voucher_id=account_voucher_obj.create(request.cr,SUPERUSER_ID,voucher_data, context=context)
            context.update({'reference': voucher_id,'description':'Wallet Top-Up','captured_api':True})
#        call to create transaction in case of existine payment profile
            try:
                if payment_profile_id:
                    cust_profile_Id=partner_brw.customer_profile_id
                    print "cust_profile_Id",cust_profile_Id
                    request.cr.execute("select credit_card_no from custmer_payment_profile where profile_id='%s'"%(payment_profile_id))
                    ccn = filter(None, map(lambda x:x[0], request.cr.fetchall()))
    #                ccn = ['1111']
                    print "cccn.................",ccn
                    if ccn:
                        ccn = ccn[0]
                    numberstring=payment_profile_id
                    print "numberstringnumberstring",numberstring
    #        call to create profile if there is no existing payment profile at Authorize end
                else: 
                    maxmind_response,context_maxmind=self.pool.get('customer.profile.payment').maxmind_call(cr,uid,ccn,int(dict_wallet.get('partner_id')))
                    if maxmind_response:
                        email=partner_brw.emailid
                        response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerProfileOnly',email)
                        if response and 'cust_profile_id' in response:
                            cust_profile_Id = response.get('cust_profile_id')
                            if cust_profile_Id:
            #                                   //if success is False
                                if not response.get('success'):
                                    profile_info = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'GetCustomerProfile',cust_profile_Id)
                                    if not profile_info.get('payment_profile'):
                                      response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',False,active_id,partner_brw,partner_brw,cust_profile_Id,ccn,exp_date,ccv,act_model)
                                      numberstring = response.get('customerPaymentProfileId',False)
                                    else:
                                        profile_info = profile_info.get('payment_profile')
                                        if ccn[-4:] in profile_info.keys():
                                            numberstring =  profile_info[ccn[-4:]]
                                        else:
                                            response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',False,active_id,partner_brw,partner_brw,cust_profile_Id,ccn,exp_date,ccv,act_model)
                                            numberstring = response.get('customerPaymentProfileId',False)
            #                                   //if success is True
                                else:
                                    response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',False,active_id,partner_brw,partner_brw,cust_profile_Id,ccn,exp_date,ccv,act_model)
                                    numberstring = response.get('customerPaymentProfileId',False)
                if cust_profile_Id and numberstring:
                    payment_profile_val = {ccn[-4:]: numberstring}
                    if dict_wallet.get('fill_amount')>0.0:
                        amount=dict_wallet.get('fill_amount')
                        present_amt_playjam_req=user_auth_obj.wallet_playjam(request.cr,SUPERUSER_ID,active_id, 0.0, context=None)
                        print "present_amt_playjampresent_amt_playjam",present_amt_playjam_req
			if ast.literal_eval(str(present_amt_playjam_req)).has_key('body') and ast.literal_eval(str(present_amt_playjam_req)).get('body')['result']==4129: 
                            present_amt_playjam=float(ast.literal_eval(present_amt_playjam_req).get("body").get('quantity'))
                            add_amt=present_amt_playjam+amount
                            if amount>500.0 or add_amt>500.0:
                                 x=500.0-float(present_amt_playjam)
                                 print "x....................................",x
                                 result={"body":{ 'code':'-55', 'message':"Maximum TopUp Amount Reached"}}
                                 return json.dumps(result) 
			    print"resultttttttttttttttttttttttttttttttttttttttttttttttttttT"
                            context['customer_profile_id']=cust_profile_Id
                            response =authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerProfileTransaction',active_id,transaction_type,amount,cust_profile_Id,numberstring,transaction_id,ccv,act_model,'',context)
                            transaction_id = response.get('response').split(',')[6]
                            prepaid_id_search=prepaid_obj.search(request.cr,SUPERUSER_ID,[('card_no','=',ccn[-4:])])
                            print "transaction_id//////////////////",transaction_id,prepaid_id_search
                            if context_maxmind and context_maxmind.get('prepaid'):
                                payment_id=payment_obj.search(cr,uid,[('credit_card_no','=',ccn[-4:])])
                                print "payment_idpayment_idpayment_id",payment_id
                                if payment_id:
                                    for each in payment_id:
                                        payment_obj.write(request.cr,SUPERUSER_ID,each,{'prepaid':True})
                            if prepaid_id_search:
                                prepaid_obj.write(cr,uid,prepaid_id_search[0],{'transaction_id':transaction_id})
                            if response.get('resultCode') == 'Ok':
                                wallet_response=user_auth_obj.wallet_playjam(request.cr,SUPERUSER_ID, active_id, amount, context=None)
                                print "wallet_responsewallet_response",wallet_response
        #                            retry 5 attempts in case if wallet update fails at playjam end
                                while count<6:
                                    print "while cinrehvjkfdhjfdhb234567",count
                                    if ast.literal_eval(wallet_response).get("body") and ast.literal_eval(wallet_response).get("body").get('result')==4129:
                                        quantity=ast.literal_eval(wallet_response).get("body").get('quantity')
                                        partner_obj.cust_profile_payment(request.cr,SUPERUSER_ID,active_id,cust_profile_Id,payment_profile_val,exp_date,context)
                                        result={"body":{"code":'49', "message":"TopUp Successful", "WalletBalance":quantity}}
                                        partner_obj.write(request.cr,SUPERUSER_ID,active_id,{'wal_bal':quantity})
                                        account_voucher_obj.write(request.cr,SUPERUSER_ID,voucher_id,{'state':'posted'})
                                        account_voucher_obj.api_response(request.cr,SUPERUSER_ID,voucher_id,response.get('response'),numberstring,transaction_type,context)
                                        context['wallet_top_up']=True
                                         #Add Journal Entries
                                        account_voucher_obj.action_move_line_create(request.cr,SUPERUSER_ID,[voucher_id],context)
                                        return json.dumps(result)
                                        count=7
                                    else:
                                        count+=1
                                if count==6:
				    if transaction_id:

                                        authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'VoidTransaction',cust_profile_Id,numberstring,transaction_id)
                                    result={"body":{ "code":'-49', "message":"TopUp Failed"}}
                            else:
                                result={"body":{ "code":'-49', "message":"TopUp Failed"}} 
			else:
			    result={"body":{ "code":'-49', "message":"TopUp Failed"}}
                    else:
                        result={"body":{ "code":False, "message":"Please top up with amount greater than 0"}}         
                else:
                    result={"body":{ "code":'-50', "message":"Credit Card Details not found"}} 
            except Exception, e:
                if transaction_id:
                    authorize_net_config.call(cr,uid,config_obj,'VoidTransaction',cust_profile_Id,numberstring,transaction_id)
                result={"body":{ 'code':'-5633','message':"Technical problem"}}
            return json.dumps(result)
#    giftcard        
    def redeem_gift_card(self,dict,context=None):
        maerge_invoice_data,result,sale_info=[],{},{}
        today=datetime.datetime.today()
        nextmonth = today + relativedelta(months=1)
        invoice_obj=self.pool.get('account.invoice')
        exception_obj=self.pool.get('partner.payment.error')
        account_obj=self.pool.get('account.account')
        sale_obj=self.pool.get('sale.order')
        gift_card_obj=self.pool.get('gift.card.validate.call')
        tru_obj=self.pool.get('tru.subscription.options')
        policy_obj=self.pool.get('res.partner.policy')
#        dict={"ApiId":"123","DBName":"april_26th_final_test","CustomerId":"6","GiftCardNumber": "7528681124"}
        print "dict....................",dict
        dict_gift_card={'api_id':dict.get('ApiId'),'partner_id':dict.get('CustomerId'),'card_no':dict.get('GiftCardNumber')}
        for key, value in dict_gift_card.iteritems():
            if value is '':
                result={"body":{ "code":'-5634', "message":"Invalid Request Data"}}  
                return json.dumps(result)
        #gift_card_obj.api_call_toincomm_reversal(cr,uid,dict_gift_card.get('card_no'),context=context)
        #return True
        try:
            customer_id=self.pool.get('res.partner').search(request.cr,SUPERUSER_ID,[('id','=',int(dict_gift_card.get('partner_id')))])
            print "customer_idcustomer_id",customer_id
            if not customer_id:
                result={"body":{ 'code':'-5555', 'message':"Missing or Invalid Customer ID"}}
                return json.dumps(result)
            partner_brw=self.pool.get('res.partner').browse(request.cr,SUPERUSER_ID,int(dict.get('CustomerId')))
            billing_date=partner_brw.billing_date
#            billing_date=datetime.datetime.strptime(billing_date, '%Y-%m-%d')
	    billing_date=datetime.datetime.strptime(billing_date, '%Y-%m-%d')
            if billing_date:
                nextmonth=billing_date + relativedelta(months=1)
            gift_card_response=gift_card_obj.api_call_toincomm_statinq(request.cr,SUPERUSER_ID,dict_gift_card.get('card_no'),context=context)
            resp_code_statinq=gift_card_response.getElementsByTagName("RespCode")[0].childNodes[0].nodeValue
            print "resp_code_statinqresp_code_statinq",resp_code_statinq
#            code 4001 response is for "Card is Active"
            if resp_code_statinq=='4001':
                face_value=gift_card_response.getElementsByTagName("FaceValue")[0].childNodes[0].nodeValue
                print "face_valueface_valueface_value",face_value
                partner_obj=self.pool.get('res.partner').browse(request.cr,SUPERUSER_ID,int(dict.get('CustomerId')))
                if face_value>0.0:
                    subscription_id=tru_obj.search(request.cr,SUPERUSER_ID,[('sales_channel_tru','=','tru')])
                    print "subscription_idsubscription_id",subscription_id
                    if not subscription_id:
                        result={"body":{ "code":False, "message":"No Subscription is stipulated for TRU"}}
                    else:
                        subscrption_service=tru_obj.browse(request.cr,SUPERUSER_ID,subscription_id[0]).product_id
                        print "subscrption_servicesubscrption_service",subscrption_service
                        request.cr.execute("select product_id from res_partner_policy where active_service =True and agmnt_partner = %s"%(int(dict_gift_card.get('partner_id'))))
                        active_services = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                        print "active_servicesactive_services",active_services,subscrption_service.id
                        if active_services and subscrption_service.id in active_services:
                            policy_id = policy_obj.search(request.cr,SUPERUSER_ID,[('product_id','=',subscrption_service.id),('agmnt_partner','=',int(dict_gift_card.get('partner_id'))),('active_service','=',True)])
                            print "policy id...............",policy_id
                            if policy_id:
				policy_brw=policy_obj.browse(request.cr,SUPERUSER_ID,policy_id[0])
				print "policy_brwpolicy_brwpolicy_brw",policy_brw
                                so_id=policy_brw.sale_id
                                sale_brw=sale_obj.browse(request.cr,SUPERUSER_ID,so_id)
                                sale_channel=sale_brw.cox_sales_channels
                            #Extra Code for Checking whether service is cancelled or not
                            request.cr.execute('select id from cancel_service where sale_id = %s and sale_line_id = %s and partner_policy_id=%s and cancelled=False'%(policy_brw.sale_id,policy_brw.sale_line_id,policy_brw.id))
                            policies = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                            if not policies:
                                sale_info={}
                                request.cr.execute(
                                    "select id from sale_order_line where parent_so_line_id in(\
                                    select sale_line_id from return_order_line where order_id = \
                                    (select id from return_order where state= 'email_sent' and return_type='car_return' and linked_sale_order = %s ))\
                                    or id in(\
                                    select sale_line_id from return_order_line where order_id = \
                                    (select id from return_order where state= 'email_sent' and return_type='car_return' and linked_sale_order = %s ))\
                                    "%(policy_brw.sale_id,policy_brw.sale_id)
                                    )
                                so_line_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                                if not policy_brw.sale_line_id in so_line_id:
                                    invoice_name = '%'+policy_brw.sale_order+'%'
                                    print "invoice_nameinvoice_name",invoice_name
                                    search_payment_exception =exception_obj.search(request.cr,SUPERUSER_ID,[('active_payment','=',True),('partner_id','=',int(dict.get('CustomerId'))),('invoice_name','ilike',invoice_name)])
                                    if not search_payment_exception:
                                            sale_info.update(
                                                {'sale_id':policy_brw.sale_id,
                                                'line_id':policy_brw.sale_line_id,
                                                'order_name': policy_brw.sale_order,
                                                'free_trial_date':policy_brw.free_trial_date,
                                                'extra_days':policy_brw.extra_days,
                                                'policy_id':policy_brw.id,
                                               'policy_id_brw':policy_brw## Extra Code
                                                })
                                    else:
                                        result={"body":{ "code":False, "message":"Payment Exception is generated for the same service"}}        
                                        return json.dumps(result)
                                redemption_details=gift_card_obj.api_call_toincomm_redemption(request.cr,SUPERUSER_ID,dict_gift_card.get('card_no'),context=context)
                                print "redemption_detailsredemption_detailsredemption_details",redemption_details
                                resp_code=redemption_details.getElementsByTagName("RespCode")[0].childNodes[0].nodeValue
#                                code 0 is for Success
    #In case of failure of redemption reateemt for 3 times limit to redeem the card 
#                                resp_code='43'
                                if resp_code=='0':
                                    if sale_info:
                                        maerge_invoice_data+=[sale_info]
                                        if len(maerge_invoice_data)!=0:
#defining account prepaid revenue or service revenue depending on redemption before the free trial or after free trial correspondingly
                                            free_trail=policy_brw.free_trial_date
                                            free_trail=datetime.datetime.strptime(free_trail, '%Y-%m-%d')
                                            print "today and free tril................",today,free_trail
                                            if today<free_trail:
                                                account_id=account_obj.search(request.cr,SUPERUSER_ID, [('name', 'ilike', 'Advance Payment')])
                                                account_id=account_id[0]
                                            else:
                                                account_id=False
                                            context.update({'partner_id_obj': partner_obj,'captured_api': True,'giftcard':True,'facevalue': face_value,'account_id':account_id})
                                            res_id=sale_obj.action_invoice_merge(request.cr,SUPERUSER_ID, maerge_invoice_data, today, nextmonth, policy_brw.start_date,'', context=context)
                                            if res_id:
						if len(active_services)==1:
							self.pool.get('res.partner').write(request.cr,SUPERUSER_ID,int(dict_gift_card.get('partner_id')),{'billing_date':str(nextmonth)}) 
						policy_obj.write(request.cr,SUPERUSER_ID,policy_id[0],{'next_billing_date':str(nextmonth)})
                                                invoice_id_obj = invoice_obj.browse(cr,uid,res_id)
                                                invoice_obj.write(request.cr,SUPERUSER_ID,res_id,{'gift_card_no':dict_gift_card.get('card_no')})
                                                sale_obj.email_to_customer(cr,uid,invoice_id_obj,'account.invoice','',partner_obj.emailid,context)
						result={"body":{"code":'4543', "message":"Redeem Successful"}}
                                                #    try:
                                                 #       self.export_recurring_profile(cr,uid,[res_id],context)
                                                  #  except Exception, e:
                                                   #     print "error string",e
                                                
#result={"body":{"code":True, "message":"Success"}}
                                            else:
                                                gift_card_reversal=gift_card_obj.api_call_toincomm_reversal(request.cr,SUPERUSER_ID,dict_gift_card.get('card_no'),context=context)
						result={"body":{ "code":False, "message":"Technical Problem(Invoice not created)"}}
                                elif resp_code=='43':
                                        result={"body":{ "code":'-4543', "message":"Missing or Invalid card"}}        
                                elif resp_code=='46':
                                        result={"body":{ "code":'-4545', "message":"Card Is Not Active"}}        
                                elif resp_code=='38':
                                        result={"body":{ "code":'-4544', "message":"Card is already Redeemed"}}        
                                else:
					result={"body":{'code':'-5633','message':'Technical problem from Incomm end'}}
                            else:
                                    result={"body":{ "code":'-4546', "message":"Subscription is Inactive or Cancelled"}}        
                        else:
                            result={"body":{ "code":False, "message":"Subscription is not active for the customer"}}  
            elif resp_code_statinq=='4002':
                result={"body":{ "code":'-4545', "message":"Card Is Not Active"}}
            elif resp_code_statinq=='4003':
                result={"body":{ "code":'-4544', "message":"Card is already Redeemed"}}
            elif resp_code_statinq=='4006':
                result={"body":{ "code":'-4543', "message":"Missing or Invalid Card"}}
            else:
		result={"body":{'code':'-5633','message':'Technical problem from Incomm end'}}
                                                    
        except Exception, e:
            print 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)
            gift_card_reversal=gift_card_obj.api_call_toincomm_reversal(request.cr,SUPERUSER_ID,dict_gift_card.get('card_no'),context=context)
            result={"body":{'code':'-5633','message':'Technical problem'}}
        return json.dumps(result)
#    giftcard        
#    def redeem_gift_card(self,cr,uid,dict,context):
#        maerge_invoice_data,result,sale_info=[],{},{}
#        today=datetime.datetime.today()
#        nextmonth = today + relativedelta(months=1)
#        invoice_obj=self.pool.get('account.invoice')
#        exception_obj=self.pool.get('partner.payment.error')
#        account_obj=self.pool.get('account.account')
#        sale_obj=self.pool.get('sale.order')
#        gift_card_obj=self.pool.get('gift.card.validate.call')
#        tru_obj=self.pool.get('tru.subscription.options')
#        policy_obj=self.pool.get('res.partner.policy')
##        dict={"ApiId":"123","DBName":"april_26th_final_test","CustomerId":"6","GiftCardNumber": "7528681124"}
#        print "dict....................",dict
#        dict_gift_card={'api_id':dict.get('ApiId'),'partner_id':dict.get('CustomerId'),'card_no':dict.get('GiftCardNumber')}
#        for key, value in dict_gift_card.iteritems():
#            if value is '':
#                result={"body":{ "code":False, "message":"('%s Not found')"%(key)}}  
#                return json.dumps(result)
##        gift_card_obj.api_call_toincomm_reversal(cr,uid,dict_gift_card.get('card_no'),context=context)
##        return True
#        try:
#            customer_id=self.pool.get('res.partner').search(cr,uid,[('id','=',int(dict_gift_card.get('partner_id')))])
#            print "customer_idcustomer_id",customer_id
#            if not customer_id:
#                result={"body":{ 'code':False, 'message':"Customer not found!!!!"}}
#                return json.dumps(result)
#            partner_brw=self.pool.get('res.partner').browse(cr,uid,int(dict.get('CustomerId')))
#            billing_date=partner_brw.billing_date
#            billing_date=datetime.datetime.strptime(billing_date, '%Y-%m-%d')
#            if billing_date:
#                nextmonth=billing_date + relativedelta(months=1)
#            gift_card_response=gift_card_obj.api_call_toincomm_statinq(cr,uid,dict_gift_card.get('card_no'),context=context)
#            resp_code_statinq=gift_card_response.getElementsByTagName("RespCode")[0].childNodes[0].nodeValue
#            print "resp_code_statinqresp_code_statinq",resp_code_statinq
##            code 4001 response is for "Card is Active"
#            if resp_code_statinq=='4001':
#                face_value=gift_card_response.getElementsByTagName("FaceValue")[0].childNodes[0].nodeValue
#                print "face_valueface_valueface_value",face_value
#                partner_obj=self.pool.get('res.partner').browse(cr,uid,int(dict.get('CustomerId')))
#                if face_value>0.0:
#                    subscription_id=tru_obj.search(cr,uid,[('sales_channel_tru','=','tru')])
#                    print "subscription_idsubscription_id",subscription_id
#                    if not subscription_id:
#                        result={"body":{ "code":False, "message":"No Subscription is stipulated for TRU"}}
#                    else:
#                        subscrption_service=tru_obj.browse(cr,uid,subscription_id[0]).product_id
#                        print "subscrption_servicesubscrption_service",subscrption_service
#                        cr.execute("select product_id from res_partner_policy where active_service =True and agmnt_partner = %s"%(int(dict_gift_card.get('partner_id'))))
#                        active_services = filter(None, map(lambda x:x[0], cr.fetchall()))
#                        print "active_servicesactive_services",active_services,subscrption_service.id
#                        if active_services and subscrption_service.id in active_services:
#                            policy_id = policy_obj.search(cr,uid,[('product_id','=',subscrption_service.id)])
#                            print "policy id...............",policy_id
#                            policy_brw=policy_obj.browse(cr,uid,policy_id[0])
#                            print "policy_brwpolicy_brwpolicy_brw",policy_brw
#                            #Extra Code for Checking whether service is cancelled or not
#                            cr.execute('select id from cancel_service where sale_id = %s and sale_line_id = %s and partner_policy_id=%s and cancelled=False'%(policy_brw.sale_id,policy_brw.sale_line_id,policy_brw.id))
#                            policies = filter(None, map(lambda x:x[0], cr.fetchall()))
#                            if not policies:
#                                sale_info={}
#                                cr.execute(
#                                    "select id from sale_order_line where parent_so_line_id in(\
#                                    select sale_line_id from return_order_line where order_id = \
#                                    (select id from return_order where state= 'email_sent' and return_type='car_return' and linked_sale_order = %s ))\
#                                    or id in(\
#                                    select sale_line_id from return_order_line where order_id = \
#                                    (select id from return_order where state= 'email_sent' and return_type='car_return' and linked_sale_order = %s ))\
#                                    "%(policy_brw.sale_id,policy_brw.sale_id)
#                                    )
#                                so_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
#                                if not policy_brw.sale_line_id in so_line_id:
#                                    invoice_name = '%'+policy_brw.sale_order+'%'
#                                    print "invoice_nameinvoice_name",invoice_name
#                                    search_payment_exception =exception_obj.search(cr,uid,[('active_payment','=',True),('partner_id','=',int(dict.get('CustomerId'))),('invoice_name','ilike',invoice_name)])
#                                    if not search_payment_exception:
#                                            sale_info.update(
#                                                {'sale_id':policy_brw.sale_id,
#                                                'line_id':policy_brw.sale_line_id,
#                                                'order_name': policy_brw.sale_order,
#                                                'free_trial_date':policy_brw.free_trial_date,
#                                                'extra_days':policy_brw.extra_days,
#                                                'policy_id':policy_brw.id,
#                                               'policy_id_brw':policy_brw## Extra Code
#                                                })
#                                    else:
#                                        result={"body":{ "code":False, "message":"Payment Exception is generated for the same service"}}        
#                                        return json.dumps(result)
#                                redemption_details=gift_card_obj.api_call_toincomm_redemption(cr,uid,dict_gift_card.get('card_no'),context=context)
#                                print "redemption_detailsredemption_detailsredemption_details",redemption_details
#                                resp_code=redemption_details.getElementsByTagName("RespCode")[0].childNodes[0].nodeValue
##                                code 0 is for Success
#                                if resp_code=='0':
#                                    if sale_info:
#                                        maerge_invoice_data+=[sale_info]
#                                if len(maerge_invoice_data)!=0:
##defining account prepaid revenue or service revenue depending on redemption before the free trial or after free trial correspondingly
#                                    free_trail=policy_brw.free_trial_date
#                                    free_trail=datetime.datetime.strptime(free_trail, '%Y-%m-%d')
#                                    print "today and free tril................",today,free_trail
#                                    if today<free_trail:
#                                        account_id=account_obj.search(cr, uid, [('name', 'ilike', 'Advance Payment')])
#                                        account_id=account_id[0]
#                                    else:
#                                        account_id=False
#                                    context.update({'partner_id_obj': partner_obj,'captured_api': True,'giftcard':True,'facevalue': face_value,'account_id':account_id})
#                                    res_id=sale_obj.action_invoice_merge(cr, uid, maerge_invoice_data, today, nextmonth, policy_brw.start_date,'', context=context)
#                                    if res_id:
#                                        if partner_obj.payment_policy=='pro':
#                                            partner_obj.write({'auto_import':True,'billing_date':str(nextmonth)},context)
#                                        invoice_obj.write(cr,uid,res_id,{'gift_card_no':dict_gift_card.get('card_no')})
#                                        invoice_id_obj = invoice_obj.browse(cr,uid,res_id)
#                                        sale_obj.email_to_customer(cr,uid,invoice_id_obj,'account.invoice','',partner_obj.emailid,context)                                                                                                                                                                         
#                                        result={"body":{"code":True, "message":"Success"}}
#                        
#                                    else:
#                                        gift_card_reversal=gift_card_obj.api_call_toincomm_reversal(cr,uid,dict_gift_card.get('card_no'),context=context)
#                                        result={"body":{ "code":False, "message":"Card Reversed"}}
#                            else:
#                                result={"body":{ "code":False, "message":"Service is Already Cancelled"}}        
#                        else:
#                            result={"body":{ "code":False, "message":"Subscription is not active for the customer"}}  
#            elif resp_code_statinq=='4003':
#                result={"body":{ "code":False, "message":"Card is already Redeemed"}}
#            elif resp_code_statinq=='4006':
#                result={"body":{ "code":False, "message":"Card not Found"}}
#        except Exception, e:
#            gift_card_reversal=gift_card_obj.api_call_toincomm_reversal(cr,uid,dict_gift_card.get('card_no'),context=context)
#            result={'code':False,'message':'Failed to redeem gift card because %s'%(e)}
#        return json.dumps(result)
#online purchase order
##function to create an order at a glance through magento online purchase order API Call
    def create_order_magento(self,dict,context=None):
        if context==None:
            context={}
        vals,dict_exist,line_data,so_data,vals1,vals2,result,street1_inv,street2_inv,street1,street2,payment_profile_id  ={},{},{},{},{},{},{},'','','','',''
        product_obj=self.pool.get("product.product")
        warehouse_obj = self.pool.get('stock.warehouse')
#        dict_old={"ApiId":"123","DBName":"local_stable_7_test","CustomerId":"4570","Email":"wallettest3@gmail.com","MagentoOrderId":"3423435345","BillingInfo":{ "PaymentProfileId":"","CreditCard":{"CCNumber":"378282246310005","ExpDate":"122020","CCV":"123",},"BillingAddress": { "Street1": "581 Telegraph Canyon Rd","Street2": "","City": "Chula Vista","State": "CA","Zip": "91910-6436",}},"ShippingAddress": { "Street1": "581 Telegraph Canyon Rd", "Street2": "", "City": "Chula Vista", "State": "CA", "Zip": "91910-6436" },"OrderLine":{'line1':{"SKU":"freindsfamiliyoffer","ProductId":41,"Qty":"1.0","Price":"10.00"}},"Subtotal":6.00,"Discount":2.00,"Tax":2.00,"Shipping":5.00,"Total":11.00,}
#        dict={"ApiId":"123","DBName":"april_26th_final_test","CustomerId":"6","Email":"yogita.paghdar@bistasolutions.com","MagentoOrderId":"3423565345","BillingInfo":{ "PaymentProfileId":"","CreditCard":{"CCNumber":"378734493671000","ExpDate":"122020","CCV":"123",},"BillingAddress": { "Street1": "1401","Street2": "795 Hammond Dr","City": "Atlanta","State": "GA","Zip": "30328-5517",}},"ShippingAddress": { "Street1": "1401", "Street2": "795 Hammond Dr", "City": "Atlanta", "State": "GA", "Zip": "30328-5517" },"OrderLine":{'line1':{"SKU":"Disney Bundle","ProductId":13,"Qty":"1.0","Price":"10.00"}},"Subtotal":6.00,"Discount":2.00,"Tax":2.00,"Shipping":5.00,"Total":11.00,}
        dict_exist = { 'magento_orderid':dict.get('MagentoOrderId'),'shipping_add':dict.get('ShippingAddress'),
                    'billing_info':dict.get('BillingInfo'),'lines':dict.get('OrderLine'),'partner_id':dict.get('CustomerId'),
                    }
        print "dict...4756768678................",dict
        if dict.has_key('tru') or dict.has_key('wallet_purchase'):
            print "dict_existdict_existdict_existdict_exist",dict_exist
#            if dict.get('tru'):
            dict_exist.pop('magento_orderid')
#            context['tru']=True
#            context['wallet_purchase']=True
        for key, value in dict_exist.iteritems():
            if value is '':
                result={"body":{ 'code':'-5634', 'message':"Invalid Request Data"}}
                return json.dumps(result)
        try:
            today=datetime.date.today()
            print"today",today
            partner_obj=self.pool.get('res.partner')
            sale_obj=self.pool.get("sale.order")
            billing_info=dict_exist.get('billing_info')
            total=dict.get('Total')
	    sale_shop=self.pool.get("sale.shop")
            customer_id=partner_obj.search(request.cr,SUPERUSER_ID,[('id','=',int(dict_exist.get('partner_id')))])
            print "customer_idcustomer_id",customer_id
            if not customer_id:
                result={"body":{ 'code':'-5555', 'message':"Missing or Invalid Customer ID"}}
                return json.dumps(result)
            warehouse_id=warehouse_obj.search(request.cr,SUPERUSER_ID,[('name','ilike','company')])
            warehouse_brw = warehouse_obj.browse(request.cr, SUPERUSER_ID, warehouse_id[0])
            if warehouse_brw and warehouse_brw.lot_stock_id:
                location_id= warehouse_brw.lot_stock_id.id
                print "location_idlocation_id",location_id
            partner_brw=partner_obj.browse(request.cr,SUPERUSER_ID,int(dict_exist.get('partner_id')))
            pricelist = partner_brw.property_product_pricelist.id or False
            shipping_add=dict_exist.get('shipping_add')
            inv_add=dict_exist.get('billing_info').get('BillingAddress')
            if inv_add.get('Street1') and inv_add.get('Street2'):
                street1_inv=inv_add.get('Street1')
                street2_inv=inv_add.get('Street2')
            else:
                street1_inv=inv_add.get('Street1')
            if shipping_add.get('Street1') and shipping_add.get('Street2'):
                street1=shipping_add.get('Street1')
                street2=shipping_add.get('Street2')
            else:
                street1=shipping_add.get('Street1')
            city=shipping_add.get('City')
            state=shipping_add.get('State')
            city_inv=inv_add.get('City')
            state_inv=inv_add.get('State')
            state_id=self.pool.get('res.country.state').search(request.cr,SUPERUSER_ID,[('code','=',state)])
            state_id_inv=self.pool.get('res.country.state').search(request.cr,SUPERUSER_ID,[('code','=',state_inv)])
            country_id=self.pool.get('res.country.state').browse(request.cr, SUPERUSER_ID, state_id[0], context).country_id.id
            country_id_inv=self.pool.get('res.country.state').browse(request.cr, SUPERUSER_ID, state_id_inv[0], context).country_id.id
            zip=shipping_add.get('Zip')
            zip_inv=inv_add.get('Zip')
            print state_id,state_id_inv,country_id,country_id_inv,zip,zip_inv
            if state_id and country_id:
                print street1,street2,zip
                ship_add=partner_obj.search(request.cr,SUPERUSER_ID,[('id','=',int(dict_exist.get('partner_id'))),('street','ilike',street1),('street2','ilike',street2),('city','=',city),('zip','=',zip),('state_id','=',state_id[0]),('country_id','=',country_id)])
                if not ship_add:
                    vals1 = {'parent_id': int(dict_exist.get('partner_id')),'name':partner_brw.name,'address_type': 'delivery','city':city,'phone': partner_brw.phone,'street':street1,'street2': street2 or '', 'state_id':state_id[0],'country_id':country_id,'zip':zip}
                    ship_add=partner_obj.create(request.cr, SUPERUSER_ID, vals1, context=context)
                    print "ship addd--------------------",ship_add
                else:
                    ship_add=ship_add[0]
                    print "else ship add-----------------",ship_add
            if state_id_inv and country_id_inv:
                print street1_inv,street2_inv,city_inv,state_id_inv,country_id_inv
                invoice_add=partner_obj.search(request.cr,SUPERUSER_ID,[('id','=',int(dict_exist.get('partner_id'))),('street','ilike',street1_inv),('street2','ilike',street2_inv),('city','=',city_inv),('zip','=',zip_inv),('state_id','=',state_id_inv[0]),('country_id','=',country_id_inv)])
                if not invoice_add:
                    print "no invoice address found.................."
                    vals2 = {'city':city_inv,'street':street1_inv,'street2': street2_inv or '', 'state_id':state_id_inv[0],'country_id':country_id_inv,'zip':zip_inv}
                    print "vals22------------------",vals2,int(dict_exist.get('partner_id'))
                    new_inv_add=partner_obj.write(request.cr,SUPERUSER_ID,int(dict_exist.get('partner_id')), vals2)
                    print "new_inv_addnew_inv_add",new_inv_add
                    invoice_add=int(dict_exist.get('partner_id'))
                else:
                    invoice_add=invoice_add[0]
                print "invoice_addinvoice_addfound----------",invoice_add
            if 'PaymentProfileId' in dict_exist.get('billing_info'):
                payment_profile_id=billing_info.get('PaymentProfileId')
            if dict.get('tru'):
                sales_channel='tru'
            elif dict.get('wallet_purchase'):
                sales_channel='playjam'
            else:
                sales_channel='ecommerce'
            fpos = partner_brw.property_account_position and  partner_brw.property_account_position.id or False
    #        print"fpos",fpos
            so_data = {'partner_id':int(dict_exist.get('partner_id')),'amount_total':total,'magento_so_id':dict_exist.get('magento_orderid'),'pricelist_id': pricelist,'cox_sales_channels':sales_channel,'partner_invoice_id': invoice_add,'partner_shipping_id': ship_add,'location_id':location_id,'date_order': today, 'fiscal_position':fpos}
            print"so_data",so_data
            new_id = sale_obj.create(request.cr,SUPERUSER_ID, so_data, context=context)
            print"new_id",new_id
            sale_brw=sale_obj.browse(request.cr,SUPERUSER_ID,new_id)
            print "dict_exist.get('lines')---------------------",dict_exist.get('lines')
            for each in dict_exist.get('lines'):
                print "each!!!!!!!!!!!!!!!!!!!!!!!---------------------!!!!!!!!!!!!!!1",each
                each_param=dict_exist.get('lines').get(each)
                dict_price=float(each_param.get('Price'))
                productid=each_param.get('ProductId')
                product_id=product_obj.search(request.cr,SUPERUSER_ID,[('id','=',productid)])
                print"product_id",product_id
                if product_id:
                    price=product_obj.browse(request.cr,SUPERUSER_ID,productid).list_price
                    print"price",price,dict_price
                    if dict_price!=price:
                        result={"body":{ 'code':'False', 'message':"Price of the product doesnt match with the list price defined"}}
                        return json.dumps(result) 
                    prdct_name=str(product_obj.browse(request.cr,SUPERUSER_ID,productid).name)
                    request.cr.execute("select product_id from res_partner_policy where active_service =True and agmnt_partner = %s"%(int(dict_exist.get('partner_id'))))
                    active_services = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                    print "active_services",active_services
    #                    sub_components = self.pool.get('extra.prod.config').search(cr,uid,[('product_id','=',product_id)])
                    quantity=each_param.get('Qty')
                    print "quantityquantityquantity",quantity
                    context.update({'active_model': 'sale.order','magento_orderid': dict_exist.get('magento_orderid'),'active_id':new_id})
                    line_data = {'order_id': new_id,'name':prdct_name,'price_unit': price,'product_uom_qty': quantity or 1.0,'product_uos_qty': quantity or 1.0,'product_id': product_id[0] or False,'actual_price':0.0}
                    print "line data........................................",line_data
                    sale_line_id=self.pool.get("sale.order.line").create(request.cr, SUPERUSER_ID, line_data, context=context)
                    print "sale line id...............................",sale_line_id
#                    if dict.get('Shipping') and dict.get('Shipping')>0.0:
#                        print "shipping line needs to be added//////////////////////"
#                        ship_product_id=product_obj.search(request.cr,SUPERUSER_ID,[('default_code','=','SHIP')])
#                        if ship_product_id:
#                            ship_dict_price=float(dict.get('Shipping'))
#                            ship_list_price=product_obj.browse(request.cr,SUPERUSER_ID,ship_product_id[0]).list_price
#                            if ship_list_price!=ship_dict_price:
#                                print "shipping price updated////////////////////////////"
#                                product_obj.write(request.cr, SUPERUSER_ID,ship_product_id[0],{'list_price':float(dict.get('Shipping'))})
#                                cr.commit()
#                            ship_prdct_name=str(product_obj.browse(request.cr,SUPERUSER_ID,ship_product_id[0]).name)
#                            ship_line_data = {'order_id': new_id,'name':ship_prdct_name,'price_unit': ship_dict_price,'product_uom_qty': quantity or 1.0,'product_uos_qty': quantity or 1.0,'product_id': ship_product_id[0] or False,'actual_price':0.0}
#                            ship_so_line_id=self.pool.get("sale.order.line").create(request.cr, SUPERUSER_ID, ship_line_data, context=context)
                    sub_components = product_obj.browse(request.cr,SUPERUSER_ID,product_id[0]).ext_prod_config
                    print "sub_componentssub_components",sub_components,product_id
                    print "sub_componentssub_components",sub_components,product_id
                    if sub_components:
                        for each_sub_comp in sub_components:
                            comp_prod_id=each_sub_comp.comp_product_id.id
                            price=each_sub_comp.price
                            print "pricepricepricepriceof each subcomponent.................",price
                            print "comp_prod_idcomp_prod_id",comp_prod_id
                            product_type=product_obj.browse(request.cr,SUPERUSER_ID,comp_prod_id).type
                            print "product_typeproduct_type",product_type
                            if product_type=='service':
                                if comp_prod_id in active_services:
                                    result={"body":{ 'code':'-1114', 'message':"Duplicated Subscription"}}
                                    return json.dumps(result)
                            sub_comp_data=({'name':each_sub_comp.comp_product_id.name,'qty_uom':float(quantity) or 1.0,'product_id':comp_prod_id,'price':price,'so_line_id':sale_line_id,'product_type':product_type,'uom_id':each_sub_comp.product_id.uom_id.id or 1})
                            sub_comp_id=self.pool.get('sub.components').create(request.cr,SUPERUSER_ID,sub_comp_data,context=context)
                else:
                    result={"body":{ 'code':'-1112', 'message':"Missing or Invalid Product ID"}}
                    return json.dumps(result)
            so_name=sale_brw.name
    #        call at Authorize end for an existing profile
	    if dict.get('Shipping') and dict.get('Shipping')>0.0:
		print "shipping line needs to be added//////////////////////"
		ship_product_id=product_obj.search(request.cr,SUPERUSER_ID,[('default_code','=','SHIP')])
		if ship_product_id:
		    ship_dict_price=float(dict.get('Shipping'))
		    ship_list_price=product_obj.browse(cr,uid,ship_product_id[0]).list_price
		    if ship_list_price!=ship_dict_price:
		        print "shipping price updated////////////////////////////"
			product_obj.write(cr,uid,ship_product_id[0],{'list_price':float(dict.get('Shipping'))})
			cr.commit()
		    ship_prdct_name=str(product_obj.browse(cr,uid,ship_product_id[0]).name)
		    ship_line_data = {'order_id': new_id,'name':ship_prdct_name,'price_unit': ship_dict_price,'product_uom_qty': quantity or 1.0,'product_uos_qty': quantity or 1.0,'product_id': ship_product_id[0] or False,'actual_price':0.0}
		    ship_so_line_id=self.pool.get("sale.order.line").create(cr, uid, ship_line_data, context=context)
		    print "ship so line id////////////////////////////////////",ship_so_line_id
            if payment_profile_id:
                print"payment_profile_id",payment_profile_id
                context.update({'cust_payment_profile_id':payment_profile_id,'captured_api':True})
                exis_pay_profile=self.pool.get('charge.customer').charge_customer(request.cr,SUPERUSER_ID,[new_id],context)
                print"exis_pay_profile",exis_pay_profile
                result={"body":{ 'code':'1111', 'message':"Order Created Successfully",'OrderNo':so_name}}
            elif dict.has_key('tru') or dict.has_key('wallet_purchase') or dict.has_key('free_subscription'):
                new_pay_prfl=self.pool.get('customer.profile.payment').charge_customer(request.cr,SUPERUSER_ID,[new_id],context)
                print "new pay profile.......................",new_pay_prfl
                if dict.has_key('wallet_purchase'):
                    #amount_deduct=float(new_pay_prfl.get('context').get('default_amount'))
                    exist_wallet_quantity=partner_brw.wal_bal
		    print "exist_wallet qunatity////////////////////////////////",exist_wallet_quantity
 #                   if amount_deduct:
                    if exist_wallet_quantity:
                        amnt_after_deduction=float(exist_wallet_quantity)-float(sale_brw.amount_total)
                    else:
                        amnt_after_deduction=float(sale_brw.amount_total)
		    print "amount afterd ecdededbkjhfnkjfdhkjvfdgjknb",amnt_after_deduction
                    partner_obj.write(cr,uid,int(dict_exist.get('partner_id')),{'wal_bal':amnt_after_deduction})
                result={"body":{ 'code':'1111', 'message':"Order Created Successfully",'OrderNo':so_name}}
    #        call at Authorize for a new profile creation
            elif billing_info.get('CreditCard'):
                credit_card=billing_info.get('CreditCard')
                if not (credit_card.get('CCV') or credit_card.get('CCNumber') or credit_card.get('ExpDate')):
                    result={"body":{ 'code':'-1113', 'message':"Missing Credit Card Info"}}
                    return json.dumps(result)
                else:
                    context.update({'ccv': credit_card.get('CCV'),'exp_date': credit_card.get('ExpDate'),'action_to_do':'new_customer_profile','magento_orderid': dict_exist.get('magento_orderid'),'sale_id':[new_id],'cc_number':credit_card.get('CCNumber')})
                    new_pay_prfl=self.pool.get('customer.profile.payment').charge_customer(request.cr,SUPERUSER_ID,[new_id],context)
                    result={"body":{ 'code':'1111', 'message':"Order Created Successfully",'OrderNo':so_name}}
        except Exception, e:
           result={"body":{'code':False,'message':'Failed to create order because %s'%(e)}}
        return json.dumps(result)
    
######## Update Subscription API to upgrade/downgrade service by yogita
    def update_subscription(self,subscription_data,context=None):
	print "subscription data-----",subscription_data
        tmpl_obj = self.pool.get('product.template')
        if subscription_data and subscription_data.get('CustomerId',''):
            dict_exist = { 'CustomerId':subscription_data.get('CustomerId'),'NewProductId':subscription_data.get('NewProductId'),
            'StartDate':subscription_data.get('StartDate'),'OldProductId':subscription_data.get('OldProductId'),
            }
            for key, value in dict_exist.iteritems():
                if not value:
                    result={"body":{ 'code':'-5634', 'message':'Invalid Request Data'}}
                    return json.dumps(result)
            customer_id = subscription_data.get('CustomerId','')
            new_product_id = subscription_data.get('NewProductId','')
            start_date = subscription_data.get('StartDate','')
            old_product_id = subscription_data.get('OldProductId','')
	    from_openerp=subscription_data.get('from_openerp','')
            partner_obj = self.pool.get('res.partner')
            partner_policy = self.pool.get('res.partner.policy')
            up_down_obj=self.pool.get('upgrade.downgrade.policy')
            return_obj = self.pool.get('return.order')
            product_obj=self.pool.get('product.product')
            user_auth_obj = self.pool.get('user.auth')
            partner_id=False
            print"customer_id",customer_id,new_product_id,old_product_id,start_date
            if customer_id:
                partner_id = partner_obj.search(request.cr,SUPERUSER_ID,[('id','=',customer_id)])
            if not partner_id:
                return json.dumps({'body':{'code':'-5555','message':'Invalid or Missing Customer ID'}})
            if start_date:
                start_dt_current_service=datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                if start_dt_current_service<datetime.date.today():
                    return json.dumps({'body':{'code':'-4116','message':'Invalid Start Date'}})
            old_pack_oe_id=product_obj.search(request.cr,SUPERUSER_ID,[('id','=',old_product_id)])
            print old_pack_oe_id
            if not old_pack_oe_id:
                return json.dumps({'body':{'code':'-4114','message':'Invalid or Missing Product ID'}})
            new_pack_oe_id=product_obj.search(request.cr,SUPERUSER_ID,[('id','=',new_product_id)])
            print new_pack_oe_id
            if not new_pack_oe_id:
                return json.dumps({'body':{'code':'-4114','message':'Invalid or Missing Product ID'}})
            try:
                partner_brw = partner_obj.browse(request.cr,SUPERUSER_ID,partner_id[0])
                if not partner_brw.customer_profile_id:
                        return json.dumps({'body':{'code':'-4118','message':'No Payment Profile'}})
                if not partner_brw.playjam_exported:
                    return json.dumps({'body':{'code':'-51','message':'Customer Profile does not exist on playjam side.'}})
                request.cr.execute('select product_id from res_partner_policy where active_service=True and return_cancel_reason is null and agmnt_partner= %s'%partner_id[0])
                product_ids=filter(None, map(lambda x:x[0], request.cr.fetchall()))
                if product_ids and new_pack_oe_id[0] in product_ids:
                    return json.dumps({'body':{'code':'-4117','message':'Duplicate Subscription'}})
                search_old_policy = partner_policy.search(request.cr,SUPERUSER_ID,[('product_id','=',old_pack_oe_id[0]),('active_service','=',True),('agmnt_partner','in',partner_id)])
    #                search_old_policy = partner_policy.search(request.cr,SUPERUSER_ID,[('active_service','=',True),('agmnt_partner','in',partner_id)])
                print"search_old_policysearch_old_policysearch_old_policy",search_old_policy
                if search_old_policy:
    #                        new_pack_id = product_obj.search(request.cr,SUPERUSER_ID,[('default_code','=ilike',new_sku)])
                    new_pack_oe_brw=product_obj.browse(request.cr,SUPERUSER_ID,new_pack_oe_id[0])
                    print"new_pack_oe_brw",new_pack_oe_brw,new_pack_oe_brw.product_type,tmpl_obj.browse(request.cr,SUPERUSER_ID,new_pack_oe_brw.product_tmpl_id.id).product_type
                    if new_pack_oe_brw.product_tmpl_id and tmpl_obj.browse(request.cr,SUPERUSER_ID,new_pack_oe_brw.product_tmpl_id.id).product_type!='service':
                        return json.dumps({'body':{'code':'-4114','message':'Invalid or Missing Product ID'}})
                    old_prod_categ,old_prod_categ_parent,free_trial_date,flag,source=[],[],'',False,''
                    old_policy_brw = partner_policy.browse(request.cr,SUPERUSER_ID,search_old_policy[0])
                   
                    exception_obj=self.pool.get('partner.payment.error')
                    invoice_name = '%'+old_policy_brw.sale_order+'%'
                    search_payment_exception =exception_obj.search(cr,uid,[('active_payment','=',True),('partner_id','=',partner_id[0]),('invoice_name','ilike',invoice_name)])
                    if search_payment_exception:
                        return json.dumps({"body":{ "code":'-4548', "message":"Payment Exception is generated for the same service"}})
                    print"old_policy_brw",old_policy_brw
                    if old_policy_brw.from_package_id and old_policy_brw.extra_days>0:
                        print"old_policy_brw.from_package_idold_policy_brw.from_package_idold_policy_brw.from_package_id",old_policy_brw.from_package_id,old_policy_brw.from_package_id.extra_days,old_policy_brw.extra_days
                        return json.dumps({'body':{'code':'-4119','message':'Can not upgrade multiple times'}})
    #                    if new_pack_oe_brw.id==old_policy_brw.product_id.id:
    #                        return json.dumps({'body':{'code':False,'message':'You can not Upgrade/Downgrade to the same active subscription.'}})
                    oe_categ_id=product_obj.browse(request.cr,SUPERUSER_ID,old_product_id).categ_id
                    if oe_categ_id.parent_id:
                        old_prod_categ_parent.append(oe_categ_id.parent_id.id)
                    old_prod_categ.append(oe_categ_id.id)
                    source='COX'
                    billing_dt_obj = datetime.datetime.strptime(partner_brw.billing_date, '%Y-%m-%d').date()
                    print"old_policy_brw.free_trial_date",old_policy_brw.free_trial_date
                    old_free_trial_date=datetime.datetime.strptime(old_policy_brw.free_trial_date, "%Y-%m-%d").date()
                    if (old_free_trial_date>start_dt_current_service):
                        if (start_dt_current_service.month==2 and billing_dt_obj.day in(31,30)) or (billing_dt_obj.day==31) :
                            days_month=calendar.monthrange(start_dt_current_service.year,start_dt_current_service.month)[1]
                            new_billing_date=str(start_dt_current_service.year)+'-'+str(start_dt_current_service.month)+'-'+str(days_month)
                        else:
                            new_billing_date=str(start_dt_current_service.year)+'-'+str(start_dt_current_service.month)+'-'+str(billing_dt_obj.day)
                        new_billing_date=datetime.datetime.strptime(new_billing_date, "%Y-%m-%d").date()
                        print"new_billing_datenew_billing_datenew_billing_date",new_billing_date
                        if start_dt_current_service>=new_billing_date:
                            new_billing_date=new_billing_date + relativedelta(months=1)
                            print"new_billing_datenew_billing_datenew_billing_date",new_billing_date
                        if new_billing_date<billing_dt_obj:
                            billing_dt_obj=new_billing_date
                            free_trial_date=billing_dt_obj-relativedelta(days=1)
                            flag=True
                            print"billing_dt_objbilling_dt_obj--------------------------",billing_dt_obj
                        elif start_dt_current_service<old_free_trial_date and old_free_trial_date>billing_dt_obj:
                            free_trial_date=billing_dt_obj-relativedelta(days=1)
                        else:
                            free_trial_date=old_free_trial_date
                    elif(old_free_trial_date<start_dt_current_service):
                        free_trial_date=billing_dt_obj-relativedelta(days=1)
                    else:
                        free_trial_date=old_free_trial_date
                    free_trial_date=datetime.datetime.strptime(str(free_trial_date), "%Y-%m-%d").date()
    #                            new_pack_id = product_obj.search(request.cr,SUPERUSER_ID,[('default_code','=ilike',new_sku)])
    #                            new_pack_oe_brw=product_obj.browse(request.cr,SUPERUSER_ID,new_pack_id[0])
                    new_prod_categ=new_pack_oe_brw.categ_id
                    updown_service=''
                    if new_prod_categ.parent_id:
                        if (new_prod_categ.parent_id.id not in old_prod_categ_parent) and (new_prod_categ.parent_id.id not in old_prod_categ) and (new_prod_categ.id not in old_prod_categ_parent):
                            return json.dumps({'body':{'code':'-4114','message':'Invalid or Missing Product ID'}})
                        elif (new_prod_categ.parent_id.id in old_prod_categ_parent) or (new_prod_categ.id in old_prod_categ_parent):
                            updown_service='upgrade'
                        else:
                            updown_service='downgrade'
                    elif (not new_prod_categ.parent_id):
    #                                or (new_prod_categ.id in old_prod_categ_parent):
                        if (new_prod_categ.id not in old_prod_categ_parent) or (new_prod_categ.id in old_prod_categ):
                            return json.dumps({'body':{'code':'-4114','message':'You can not Upgrade/Downgrade to this service.'}})
                        elif new_prod_categ.id in old_prod_categ_parent:
                            updown_service='upgrade'
                    if billing_dt_obj<start_dt_current_service:
                        days_left =(billing_dt_obj+relativedelta(months=1)) - start_dt_current_service
                    else:
                        days_left = billing_dt_obj - start_dt_current_service
                    #TODO call Rental API
    #                                    user_id='FLARE1124'
                    print"billing_dt_objbilling_dt_objbilling_dt_objbilling_dt_obj",billing_dt_obj
                    user_id=partner_id[0]
                    app_id=new_pack_oe_brw.product_tmpl_id.app_id
                    today=datetime.date.today()
                    end_date=today+relativedelta(months=60)
                    expiry_epoch=time.mktime(end_date.timetuple())
#                    expiry_epoch=time.mktime(datetime.datetime.strptime(str('2050-12-31'), "%Y-%m-%d").timetuple())
                    expiry_epoch=int(expiry_epoch)
                    print"expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1",expiry_epoch
                    new_policy_result = user_auth_obj.rental_playjam(cr,uid,user_id,app_id,expiry_epoch)
                    print "voucher_return-------------++++++++++++++",new_policy_result
#                        if result==4113:
                    if ast.literal_eval(str(new_policy_result)).has_key('body') and ast.literal_eval(str(new_policy_result)).get('body')['result'] == 4113:
                        app_id=old_policy_brw.product_id.product_tmpl_id.app_id
        #                                    app_id=284
                        print "user_id---------",user_id
                        print "app_id---------",app_id
                        print "expiry_epoch---------",start_date
                        print"datetime.datetime.today()",datetime.datetime.today()
#                        today =  str(datetime.datetime.today()).split(' ')[0]
#                        expiry_epoch=time.mktime(datetime.datetime.now().timetuple())
#                        print"expiry_epochexpiry_epochexpiry_epochexpiry_epoch",expiry_epoch
#                        expiry_epoch1=(int(expiry_epoch)+3600)
#                        print"expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1",expiry_epoch1
                        old_policy_result = user_auth_obj.rental_playjam(user_id,app_id,0)
                        print "voucher_return----------",old_policy_result
                        if ast.literal_eval(str(old_policy_result)).has_key('body') and ast.literal_eval(str(old_policy_result)).get('body')['result'] == 4113:
                            #4113 is the result response value for successfull rental update
                            additional_info = {'source':source,'cancel_return_reason':'downgrade'}
                            cancel_reason = return_obj.additional_info(request.cr,SUPERUSER_ID,additional_info)
                            request.cr.execute("update res_partner_policy set active_service = False,return_cancel_reason='downgrade',cancel_date=%s,additional_info=%s where id = %s",(start_date,cancel_reason,old_policy_brw.id))
#                            app_id=new_pack_oe_brw.app_id
        #                                    app_id=284
    #                        expiry_epoch=time.mktime(datetime.datetime.strptime(str('2050-12-31'), "%Y-%m-%d").timetuple())
    #			expiry_epoch=int(expiry_epoch)
    #                        print"expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1expiry_epoch1",expiry_epoch
    #                        new_policy_result = user_auth_obj.rental_playjam(cr,uid,user_id,app_id,expiry_epoch)
    #                        print "voucher_return-------------++++++++++++++",new_policy_result
    ##                        if result==4113:
    #                        if ast.literal_eval(str(new_policy_result)).has_key('body') and ast.literal_eval(str(new_policy_result)).get('body')['result'] == 4113:
                                #4113 is the result response value for successfull rental update
                            policy_id=partner_policy.create(request.cr,SUPERUSER_ID,{
                            'service_name':new_pack_oe_brw.name,
                            'active_service':True,
                            'sale_id': old_policy_brw.sale_id,
                            'start_date': start_date,
                            'agmnt_partner':partner_id[0],
                            'product_id': new_pack_oe_brw.id,
                            'from_package_id':old_policy_brw.id,
                            'up_down_service':updown_service,
                            'free_trial_date': free_trial_date if free_trial_date else False,
                            'sale_line_id':old_policy_brw.sale_line_id,
                            'extra_days': (days_left.days if days_left else 0),
                            'sale_order':old_policy_brw.sale_order,
                            'source':source,
                            'no_recurring':False,
                            'next_billing_date':billing_dt_obj,
                            })
                            if flag==True:
                                result1=partner_brw.write({'billing_date':billing_dt_obj})
                            if from_openerp!=True:
                                up_down_id=up_down_obj.create(request.cr,SUPERUSER_ID,{
                                'partner_id':partner_id[0],
                                'old_policy_id':old_policy_brw.id,
                                'product_id':new_pack_oe_brw.id,
                                'up_down_service':updown_service,
                                'start_date':start_date,
                                'free_trial_date':free_trial_date if free_trial_date else old_policy_brw.free_trial_date,
                                'source':source,
                                'state':'done',
                                'new_policy_id':policy_id,
                                })
                                partner_policy.write(request.cr,SUPERUSER_ID,policy_id,{'up_down_id':up_down_id})
                            else:
                                up_down_id=up_down_obj.search(request.cr,SUPERUSER_ID,[('partner_id','=',partner_id[0]),('old_policy_id','=',search_old_policy[0])])
                                if up_down_id:
                                    up_down_obj.write(request.cr,SUPERUSER_ID,up_down_id,{'start_date':start_date,'free_trial_date':free_trial_date if free_trial_date else old_policy_brw.free_trial_date,'state':'done','new_policy_id':policy_id})
                            partner_obj.cal_next_billing_amount(request.cr,SUPERUSER_ID,partner_id[0])
                            if policy_id:
                                    return json.dumps({'body':{'code':'4113','message':'Subscription Updated'}})
                        else:
                            new_policy_cancel_result = user_auth_obj.rental_playjam(user_id,new_pack_oe_brw.app_id,expiry_epoch)
                            print "new_policy_cancel_resultnew_policy_cancel_resultnew_policy_cancel_result",new_policy_cancel_result
			    return json.dumps({'body':{'code':'-4113','message':'Subscription Update Failed'}})
                    else:
                            return json.dumps({'body':{'code':'-4113','message':'Subscription Update Failed'}})
                else:
                        return json.dumps({'body':{'code':'-4120','message':'No Subscription Active'}})
            except Exception, e:
                return json.dumps({'body':{'code':'-5633','message':'Technical problem'}})
	return json.dumps({'body':{'code':'-5634', 'message':'Invalid Request Data'}}) 

    def create_update_customer(self,dict,context=None):
        print "dict----------------",dict,type(dict)
        customer_id=dict.get('CustomerId',False)
        pro_id=False
        name=""
        profile_vals={}
        vals={}
        f_name,l_name='',''
	if_exist=[]
	if customer_id:
            request.cr.execute('select id from res_partner where id= %s', (customer_id,))
            if_present = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            if if_present==[]:
                return json.dumps({"body":{'code':'-5555','message':'Missing or Invalid Customer ID'}})

            active=self.browse(request.cr,SUPERUSER_ID,int(customer_id)).active
            if active != True:
                return json.dumps({"body":{'Code':'-5555','message':'Missing or Invalid Customer ID'}})


        if dict.has_key('FirstName') or dict.has_key('LastName'):
            name=dict.get('FirstName','')+' '+dict.get('LastName','')
            vals.update({'name':name})

        if dict.has_key('Email'):
            emailid=dict.get('Email')
            request.cr.execute('select id from res_partner where emailid= %s', (emailid,))
            if_exist = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            vals.update({'emailid':emailid})
        if dict.has_key('Password'):
            password=dict.get('Password')
            vals.update({'password':password})
        
        if dict.has_key('AccountPIN'):
            account_pin=dict.get('AccountPIN')
            vals.update({'account_pin':account_pin})

        if dict.has_key('UseWallet'):
            use_wallet=dict.get('UseWallet')
            vals.update({'use_wallet':use_wallet})

        if dict.has_key('DOB'):
            dob=dict.get('DOB')
            try:
                datetime.datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":"-4094",'message': "Missing or Invalid DOB",}})
            vals.update({'dob':dob})


        if customer_id:
            self.write(request.cr,SUPERUSER_ID,[customer_id],vals)
            return json.dumps({"body":{'code':'4097','message':"Account Created","CustomerId":customer_id,}})

        else:
            if if_exist!=[]:
                return json.dumps({"body":{"code":"-4093",'message': "Duplication Email on update or create",}})

	    
            request.cr.execute('select id from res_country_state where code = %s', ('GA',))
            state_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))

            request.cr.execute('select id from res_country where code = %s', ('US',))
            country_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))

            vals.update({'street':'1401','street2':'795 Hammond Dr','city':'Atlanta','state_id':state_id[0],'country_id':country_id[0],"zip":"30328-5517"})
            print "vals----------",vals


            cust_id=self.create(request.cr,SUPERUSER_ID,vals)
            return json.dumps({"body":{'code':'4097','message':"Account Created","CustomerId":cust_id,}})


    def create_update_profile(self,dict,context=None):
        print "dict----------------",dict,type(dict),self
	print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",dict
        pro_id=False
        name=""
        profile_vals={}

        profile_id=dict.get('ProfileId',False)

        customer_id=int(dict.get('CustomerId',False))
        #if customer_id:

	 #   request.cr.execute('select id from res_partner where id= %s', (customer_id,))
          #  if_exist = filter(None, map(lambda x:x[0], request.cr.fetchall()))
           # if if_exist==[]:
            #    return json.dumps({"body":{'code':False,'message':"CustomerId Not Present.",}})

	if customer_id and not profile_id:

            user_profile_ids=self.browse(request.cr,SUPERUSER_ID,int(customer_id)).user_profile_ids
	    print "user_profile_ids--------------",user_profile_ids
            if user_profile_ids:
                return json.dumps({"body":{'code':'-4225','message':"Duplicate player tag",}})


        if customer_id:

	    request.cr.execute('select id from res_partner where id= %s', (customer_id,))
            if_exist = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            if if_exist==[]:
                return json.dumps({"body":{'code':'-5555','message':"Missing or Invalid Customer ID",}})

	    active=self.browse(request.cr,SUPERUSER_ID,int(customer_id)).active
	    print "active---------------",active
	    print "customer_id-------",customer_id
            if active == False:
                return json.dumps({"body":{'Code':'4228','message':'Profile Deleted'}})


            profile_vals.update({'partner_id':customer_id})
        else:
            return json.dumps({"body":{'code':'-5555','message':"Missing or Invalid Customer ID",}})
        
        
        if dict.has_key('PlayerTag'):
            player_tag=dict.get('PlayerTag')
            profile_vals.update({'player_tag':player_tag})
        if dict.has_key('DOB'):
            dob=dict.get('DOB')
            try:
                datetime.datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":'-4228','message': "Missing or Invalid DOB",}})
            profile_vals.update({'dob':dob})


        if dict.has_key('Gender'):
            gender=dict.get('Gender')
            if gender =='M' or gender =='F' or gender =='O':
                profile_vals.update({'gender':gender})
            else:
                return json.dumps({"body":{"code":'-4229','message': "Missing or Invalid gender"}})

        if dict.has_key('ProfilePIN'):
            pin=dict.get('ProfilePIN')
            profile_vals.update({'pin':pin})

        if dict.has_key('AvatarId'):
            avatar_id=dict.get('AvatarId')
            profile_vals.update({'avatar_id':avatar_id})

        if dict.has_key('AgeRating'):
            age_rating=dict.get('AgeRating')
            profile_vals.update({'age_rating':age_rating})




        if profile_id:
            self.pool.get('user.profile').write(request.cr,SUPERUSER_ID,[profile_id],profile_vals)
            return json.dumps({"body":{'code':'4227','message':"Profile Updated","ProfileId":profile_id,}})

        else: 
	    print"profile_vals==========",profile_vals
            pro_id=self.pool.get('user.profile').create(request.cr,SUPERUSER_ID,profile_vals)
            return json.dumps({"body":{'code':'4225','message':"Profile Created","ProfileId":pro_id,}})




    def login_magento(self,username,password,context=None):
        print"username",username
        request.cr.execute('select id from res_partner where emailid = %s', (username,))
        partner_id = filter(None, map(lambda x:x[0], request.cr.fetchall())) 
        print "partner_id-------",partner_id
#        ero
        if partner_id:
            pat_obj=self.browse(request.cr,SUPERUSER_ID,partner_id[0])
            hash=pat_obj.password
	    print "hash--------------",hash
	    if not hash:
		return json.dumps({"body":{"code":False,"message":"Password Not Present."}})
#            hash = '$pbkdf2-sha256$200$cO59T2ltDWFMCYFwrnVuLQ$i6Kg0RD0sTr2.U7waZDFjzg8LCzmNEMHclldMXWhl3'
            print type(hash),type(password)
            password = str(password)
            hash= str(hash)
            print type(hash),type(password),hash,password
            result=pbkdf2_sha256.verify(password, hash)
            if result:
                name=pat_obj.name
                pos=name.find(' ')
                name=name.replace(' ','')
                first_name=name[:pos]
                last_name=name[pos:]
                return json.dumps({"body":{"code":'2222',"message":"Login Success","UserName": username, "Password": password, "CustomerId":partner_id[0],"FirstName":first_name,"LastName":last_name}})
            else:
                return json.dumps({"body":{"code":'-2223',"message":"Incorrect UserName or Password"}})

#            return result
        return json.dumps({"body":{"code":'-2223',"message":"Incorrect UserName or Password"}})





    def get_account_info(self, dict, context=None):
        print "dict-----------------------",dict
        res={}
        if dict.get('CustomerId',False):
            cust_id=dict.get('CustomerId')
	    cust_id=int(cust_id)
	    request.cr.execute('select id from res_partner where id= %s', (cust_id,))
            if_present = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            if if_present==[]:
                return json.dumps({"body":{'code':'-5555','message':'Missing or Invalid Customer ID'}})
            print "cust_id-------------",cust_id
            pat_obj=self.browse(request.cr,SUPERUSER_ID,int(cust_id))
            if pat_obj:
		active=pat_obj.active
                if active != True:
                    return json.dumps({"body":{'code':'-5555','message':'Missing or Invalid Customer ID'}})
                print "test----------",pat_obj
                res.update({'CustomerId':cust_id})
		game_profile_name=pat_obj.user_profile_ids
                if game_profile_name:
                    print"game_profile_name",game_profile_name
                    res.update({'PrimaryGameProfileName':game_profile_name[0].player_tag})
                #game_profile_name=pat_obj.game_profile_name
                #if game_profile_name:
                    #res.update({'PrimaryGameProfileName':game_profile_name})

		name=pat_obj.name
                f_name=''
                l_name=''
                if name:
                    x=name.find(' ')
                    name=name.replace(' ','')
                    f_name=name[:x]
                    l_name=name[x:]
                res.update({'FirstName':f_name,'LastName':l_name})
                email_id=pat_obj.emailid
                if email_id:
                    res.update({'EmailId':email_id})

                password=pat_obj.password
                if password:
                    res.update({'Password':"xxxx"})
                dob=pat_obj.dob
                if dob:
                    res.update({'DOB':dob})

                gender=pat_obj.gender
                if gender:
                    res.update({'Gender':gender})

                age_rating=pat_obj.age_rating
                if age_rating:
                    res.update({'AgeRating':age_rating})

                account_pin=pat_obj.account_pin
                if account_pin:
                    res.update({'AccountPIN':account_pin})
                
                ua_obj=self.pool.get('user.auth')
                wal_bal_body=ua_obj.wallet_playjam(cust_id,0)
                wal_bal_body = ast.literal_eval(str(wal_bal_body))
                if wal_bal_body.has_key('body') and (wal_bal_body.get('body')).has_key('quantity') and (wal_bal_body.get('body')).get('result')==4129:
                    quantity=wal_bal_body['body']['quantity']
                    res.update({'WalletBalance':quantity})

		else:
#                    return json.dumps({"body":{'Code':False,'message':'Unable to get the updated Wallet balance.'}})
                    res.update({'WalletBalance':0.0})

                user_auth_ids=pat_obj.user_auth_ids
		print "user_auth_ids-----check----",user_auth_ids
                if user_auth_ids:
                    dev_ids=[]
                    for each in user_auth_ids:
                        dev_id=each.serial_no.name
                        dev_ids.append(dev_id)


                    res.update({'Devices':dev_ids})

                policy_ids=pat_obj.agreement_policy
                if policy_ids:
                    subscription_list=[]
                    for each in policy_ids:
			print "each-------------",each
                        sub={}
                        
                        if each.active_service:
                            sub.update({'ProductId':each.product_id.id,'SKU':each.product_id.default_code,'SubscriptionDetail':each.service_name,'Price':each.recurring_price,'StartDate':each.start_date,'FreeTrialDate':each.free_trial_date})
                            subscription_list.append(sub)
                    res.update({'Subscription':subscription_list})
                    
                bill_info={}
                if pat_obj.profile_ids:
                    for each in pat_obj.profile_ids:
                        if each.active_payment_profile==True:
                            name=pat_obj.name
                            f_name=''
                            l_name=''
                            if name:
                                x=name.find(' ')
                                name=name.replace(' ','')
                                f_name=name[:x]
                                l_name=name[x:]
                            bill_info.update({'FirstName':f_name,'LastName':l_name})
                            if pat_obj.child_ids:
                                request.cr.execute('select id from res_partner where parent_id = %s and pay_profile_id = %s', (pat_obj.id,each.profile_id))
                                active_contact = filter(None, map(lambda x:x[0], request.cr.fetchall()))
                                if active_contact:
                                    name=self.browse(request.cr,SUPERUSER_ID,active_contact[0]).name
                                    f_name=''
                                    l_name=''
                                    if name:
                                        x=name.find(' ')
                                        name=name.replace(' ','')
                                        f_name=name[:x]
                                        l_name=name[x:]
                            bill_info.update({'FirstName':f_name,'LastName':l_name})                            
                            bill_info.update({'PaymentProfileId':each.profile_id})
			    print "!!!!!!!!!!!!!!!!!!!!!!!!",each
                            bill_info.update({'CreditCard':{'CCNumber':each.credit_card_no,'ExpDate':each.exp_date}})
#                            bill_info.update({'CreditCard':{'CCNumber':each.credit_card_no,}})

                profile_details={}
                if pat_obj.user_profile_ids:
                    profile_obj=pat_obj.user_profile_ids[0]
                    profile_details.update({'ProfileId':profile_obj.id})
                    if profile_obj.player_tag:
                        profile_details.update({'PlayerTag':profile_obj.player_tag})
                    if profile_obj.dob:
                        profile_details.update({'DOB':profile_obj.dob})
                    if profile_obj.gender:
                        profile_details.update({'Gender':profile_obj.gender})
                    if profile_obj.age_rating:
                        profile_details.update({'AgeRating':profile_obj.age_rating})
                    
                res.update({'ProfileDetails':profile_details})

                partner_addr = self.pool.get('res.partner').address_get(request.cr,SUPERUSER_ID, [int(cust_id)],['invoice',])
                if partner_addr:
                    inv_add_id=partner_addr.get('invoice')
                    add_obj=self.pool.get('res.partner').browse(request.cr,SUPERUSER_ID,inv_add_id)
                    bill_add_info={'BillingAddress':{'Street1':add_obj.street,'Street2':add_obj.street2,'City':add_obj.city,'State':add_obj.state_id.name,'Zip':add_obj.zip}}
		    if add_obj.street=='1401' and (add_obj.city=='Atlanta' or add_obj.city=='Brookhaven') and add_obj.state_id.code=='GA' and add_obj.zip=='30328-5517':
			bill_add_info={}
		    bill_info.update(bill_add_info)
                res.update({'BillingInfo':bill_info})
                res.update({'code':'5632','message':'Success'})


                return json.dumps({"body":res})

            return json.dumps({"body":{'code':'-5555','message':'Missing or Invalid Customer ID'}})




    '''def update_billing_info(self, dict,context=None):
        print "dict---$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$-------",dict
	#eroooooooo
        cust_profile_id=''
        customer_id=dict.get('CustomerId',False)
        if not customer_id:
            return json.dumps({"body":{'code':False,'message':"Please provide the CustomerId",}})
	customer_id=int(customer_id)
        if ('BillingInfo' in dict) and ('BillingAddress' in dict.get('BillingInfo')):
            print"iffffffffff"
            vals={}
            billing_add= (dict.get('BillingInfo')).get('BillingAddress')
	    print "billing addd-----------",billing_add
	    #ero
            if 'Street1' in billing_add:
                street=billing_add.get('Street1')
                vals.update({'street':street})
            if  'Street2' in billing_add:
                street2=billing_add.get('Street2')
                vals.update({'street2':street2})
            if 'Street1' in billing_add:
                street=billing_add.get('Street1')
                vals.update({'street':street})
            if 'City' in billing_add:
                city=billing_add.get('City')
                vals.update({'city':city})
            if 'State' in billing_add:
                state=billing_add.get('State')
                request.cr.execute('select id from res_country_state where code = %s', (state,))
                state_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
		if state_id:
                    vals.update({'state_id':state_id[0]})
		else:
		    return json.dumps({"body":{'code':False,'message':"Incorrect State Code",}})

            if 'Country' in billing_add:
                country=billing_add.get('Country')
                request.cr.execute('select id from res_country where code = %s', ('US',))
                country_id = filter(None, map(lambda x:x[0], request.cr.fetchall()))
		if state_id:
                    vals.update({'country_id':country_id[0]})
                else:
                    return json.dumps({"body":{'code':False,'message':"Incorrect Country Code",}})
                

            if  'Zip' in billing_add:
                zip=billing_add.get('Zip')
                vals.update({'zip':zip})
            print "valssssss-------------",vals
            try:
                self.write(request.cr,SUPERUSER_ID,[customer_id],vals)
                #cr.commit()
            except Exception ,e:
		print"eeeeeeeeee",e
                return json.dumps({"body":{'code':False,'message':'The Address is not valid.'}})



        #ero
        if ('CreditCard' in dict.get('BillingInfo')):
            cc_info=(dict.get('BillingInfo')).get('CreditCard')
            print "ccinfo------------------------",cc_info
            if ('CCNumber' in cc_info) and  ('ExpDate' in cc_info) and ('CCV' in  cc_info):
                ccn=cc_info.get('CCNumber')
                exp_date=cc_info.get('ExpDate')
                exp_date = exp_date[-4:] + '-' + exp_date[:2]
                ccv=cc_info.get('CCV')
            else:
                return json.dumps({"body":{'code':False,'message':'Incomplete Credit card Details.'}})


            cust_profile_id,numberstring=False,False
            act_model='res.partner'
            partner_obj=self.browse(request.cr,SUPERUSER_ID,customer_id)
            cust_profile_id=partner_obj.customer_profile_id
	    print "custproid--------------------------------",cust_profile_id
            email=partner_obj.emailid
            authorize_net_config=self.pool.get('authorize.net.config')
            config_ids =authorize_net_config.search(request.cr,SUPERUSER_ID,[])
            print "config_ids-----------------------",config_ids
            if config_ids:
                config_obj = authorize_net_config.browse(request.cr,SUPERUSER_ID,config_ids[0])

                if cust_profile_id:
                    try:
                        profile_info = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'GetCustomerProfile',cust_profile_id)
                        print "profile_info----------------",profile_info
                        response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn, exp_date, ccv,act_model)
                        numberstring = response.get('customerPaymentProfileId',False)
			print" numberstring numberstring numberstring", numberstring
                    except Exception ,e:
                        print"eeeeeeeeee",e
                        return json.dumps({"body":{'Code':False,'message':'The call to Authorize.Net Failed.'+str(e)}})
                else:
                    print "insideeeeeeeeeeee"
                    try:
                        res = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerProfileOnly',email)
                        print "res------------",res
                        cust_profile_id=res.get('cust_profile_id')
                        print "cust_profile_id-------------",cust_profile_id
                        #response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn,ccv,exp_date,act_model)
                        response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn, exp_date, ccv,act_model)
                        numberstring=response.get('customerPaymentProfileId')
                    except Exception ,e:
                        print"eeeeeeeeee",e
                        return json.dumps({"body":{'code':False,'message':'The call to Authorize.Net Failed.'+str(e)}})

                    print "response------------------",response
                if cust_profile_id and numberstring:
                           payment_profile_val = {ccn[-4:]: numberstring}
                           self.pool.get('res.partner').cust_profile_payment(cr,uid,customer_id,cust_profile_id,payment_profile_val,exp_date,context)

        

        return json.dumps({"body":{'code':True,'message':'Success.'}})'''
        
    def update_billing_info(self, dict,context=None):
        print "dict---$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$-------",dict
	#eroooooooo
        cust_profile_id=''
        customer_id=dict.get('CustomerId',False)
        if not customer_id:
            return json.dumps({"body":{'code':'-5555','message':"Missing or Invalid Customer ID",}})
	customer_id=int(customer_id)
        contact_id=False
        
        if dict.get('FirstName',False) and dict.get('LastName'):
            name=self.browse(cr,uid,customer_id).name
            x=name.find('')
            name=name.replace(" ","")
            first_name=name[:x]
            last_name=name[x:]

            if first_name!= dict.get('FirstName') and last_name!= dict.get('LastName'):

                contact_id=self.create(cr,uid,{'name':dict.get('FirstName')+" "+dict.get('LastName'),'parent_id':customer_id})
                cr.commit()
                
                
        if ('BillingInfo' in dict) and ('BillingAddress' in dict.get('BillingInfo')):
            vals={}
            billing_add= (dict.get('BillingInfo')).get('BillingAddress')
	    print "billing addd-----------",billing_add
	    #ero
            if 'Street1' in billing_add:
                street=billing_add.get('Street1')
                vals.update({'street':street})
            if  'Street2' in billing_add:
                street2=billing_add.get('Street2')
                vals.update({'street2':street2})
            
            if 'City' in billing_add:
                city=billing_add.get('City')
                vals.update({'city':city})
            if 'State' in billing_add:
                state=billing_add.get('State')
                cr.execute('select id from res_country_state where code = %s', (state,))
                state_id = filter(None, map(lambda x:x[0], cr.fetchall()))
		if state_id:
                    vals.update({'state_id':state_id[0]})
		else:
		    return json.dumps({"body":{'code':'-3224','message':"Missing or Invalid Address",}})

            if 'Country' in billing_add:
                country=billing_add.get('Country')
                cr.execute('select id from res_country where code = %s', ('US',))
                country_id = filter(None, map(lambda x:x[0], cr.fetchall()))
		if state_id:
                    vals.update({'country_id':country_id[0]})
                else:
                    return json.dumps({"body":{'code':'-3224','message':"Missing or Invalid Address",}})
                

            if  'Zip' in billing_add:
                zip=billing_add.get('Zip')
                vals.update({'zip':zip})
            print "valssssss-------------",vals
            try:
                self.write(request.cr,SUPERUSER_ID,[customer_id],vals)
                #cr.commit()
            except Exception ,e:
		print"eeeeeeeeee",e
                return json.dumps({"body":{'code':'-3224','message':'Missing or Invalid Address'}})
        #ero
        if ('CreditCard' in dict.get('BillingInfo')):
            cc_info=(dict.get('BillingInfo')).get('CreditCard')
            print "ccinfo------------------------",cc_info
            if ('CCNumber' in cc_info) and  ('ExpDate' in cc_info) and ('CCV' in  cc_info): 
                ccn=cc_info.get('CCNumber')
                exp_date=cc_info.get('ExpDate')
                exp_date = exp_date[-4:] + '-' + exp_date[:2]
                ccv=cc_info.get('CCV')
            else:
                return json.dumps({"body":{'code':'-3222','message':'Missing or Incomplete Credit card Details'}})


            cust_profile_id,numberstring=False,False
            act_model='res.partner'
            partner_obj=self.browse(request.cr,SUPERUSER_ID,customer_id)
            cust_profile_id=partner_obj.customer_profile_id
	    print "custproid--------------------------------",cust_profile_id
            email=partner_obj.emailid
            authorize_net_config=self.pool.get('authorize.net.config')
            config_ids =authorize_net_config.search(request.cr,SUPERUSER_ID,[])
            print "config_ids-----------------------",config_ids
            if config_ids:
                config_obj = authorize_net_config.browse(request.cr,SUPERUSER_ID,config_ids[0])
                if cust_profile_id:
                    try:
                        profile_info = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'GetCustomerProfile',cust_profile_id)
                        print "profile_info----------------",profile_info
                        if not profile_info.get('payment_profile'):
                            response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,ccv,act_model)
                            numberstring = response.get('customerPaymentProfileId',False)
                        else:
                            profile_info = profile_info.get('payment_profile')
                            if ccn[-4:] in profile_info.keys():
                                numberstring =  profile_info[ccn[-4:]]
                            else:
                                #response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',active_id[0],False,False,False,cust_profile_Id,ccn,exp_date,ccv,act_model)
				response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn, exp_date, ccv,act_model)
                                numberstring = response.get('customerPaymentProfileId',False)
			print" numberstring numberstring numberstring", numberstring
                    except Exception ,e:
                        print"eeeeeeeeee",e
                        return json.dumps({"body":{'Code':'-3221','message':'The call to Authorize.Net Failed'}})
                else:
                    print "insideeeeeeeeeeee"
                    try:
                        res = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerProfileOnly',email)
                        print "res------------",res
                        cust_profile_id=res.get('cust_profile_id')
                        print "cust_profile_id-------------",cust_profile_id
                        #response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn,ccv,exp_date,act_model)
                        response = authorize_net_config.call(request.cr,SUPERUSER_ID,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn, exp_date, ccv,act_model)
                        numberstring=response.get('customerPaymentProfileId')
                    except Exception ,e:
                        print"eeeeeeeeee",e
                        return json.dumps({"body":{'Code':'-3221','message':'The call to Authorize.Net Failed'}})

                    print "response------------------",response
                if cust_profile_id and numberstring:
                           payment_profile_val = {ccn[-4:]: numberstring}
                           self.pool.get('res.partner').cust_profile_payment(request.cr,SUPERUSER_ID,customer_id,cust_profile_id,payment_profile_val,exp_date,context)
                           if contact_id:
                               self.write(request.cr,SUPERUSER_ID,[contact_id],{'pay_profile_id':numberstring})
        return json.dumps({"body":{'code':'3221','message':'Update Success'}})
        

        #return json.dumps({"body":{'code':True,'message':'Success.'}})



    '''def update_billing_info(self, cr, uid, dict,context=None):
        print "dict----------",dict
        cust_profile_id=''
        customer_id=dict.get('CustomerId',False)
        if not customer_id:
            return json.dumps({"body":{'code':False,'message':"Please provide the CustomerId",}})

        if dict.has_key('BillingAddress'):
            vals={}
            billing_add=dict.get('BillingAddress')
            if billing_add.has_key('Street1'):
                street=billing_add.get('Street1')
                vals.update({'street':street})
            if billing_add.has_key('Street2'):
                street2=billing_add.get('Street2')
                vals.update({'street2':street2})
            if billing_add.has_key('Street1'):
                street=billing_add.get('Street1')
                vals.update({'street':street})
            if billing_add.has_key('City'):
                city=billing_add.get('City')
                vals.update({'city':city})
            if billing_add.has_key('State'):
                state=billing_add.get('State')
                cr.execute('select id from res_country_state where code = %s', (state,))
                state_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                vals.update({'state_id':state_id[0]})

            if billing_add.has_key('Country'):
                country=billing_add.get('Country')
                cr.execute('select id from res_country where code = %s', ('US',))
                country_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                vals.update({'country_id':country_id[0]})

            if billing_add.has_key('Zip'):
                zip=billing_add.get('Zip')
                vals.update({'zip':zip})
            try:
                self.write(cr,uid,[customer_id],vals)
            except Exception ,e:
		print"eeeeeeeeee",e
                return json.dumps({"body":{'Code':False,'message':'The Address is not valid.'}})


        cust_profile_id=self.browse(cr,uid,customer_id).customer_profile_id
        if dict.has_key('CreditCard'):
            cr.execute('select id from custmer_payment_profile where active_payment_profile = True and ids in (select id from partner_profile_ids where partner_id = %s)', (customer_id,))
            active_profile_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if active_profile_ids != []:
                self.pool.get('custmer.payment.profile').write(cr,uid,active_profile_ids,{'active_payment_profile':False})

            cc_info=dict.get('CreditCard')
            if cc_info.has_key('CCNumber') and cc_info.has_key('ExpDate'):
                cc_num=cc_info.get('CCNumber')
                exp_date=cc_info.get('ExpDate')
                cpp_id=self.pool.get('custmer.payment.profile').create(cr,uid,{'credit_card_no':cc_num,'customer_profile_id':cust_profile_id,'exp_date':exp_date,'active_payment_profile':True})
                cr.execute('INSERT INTO partner_profile_ids \
                        (partner_id,profile_id) values (%s,%s)', (customer_id, cpp_id))
        
        

        return json.dumps({"body":{'Code':True,'message':'Success.'}})'''


    '''def update_billing_info(self, cr, uid, dict,context=None):
        print "dict---$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$-------",dict
        cust_profile_id=''
        customer_id=dict.get('CustomerId',False)
        if not customer_id:
            return json.dumps({"body":{'code':False,'message':"Please provide the CustomerId",}})

        if dict.has_key('BillingInfo') and (dict.get('BillingInfo')).has_key('BillingAddress'):
            vals={}
            billing_add= (dict.get('BillingInfo')).get('BillingAddress')
	    print "billing addd-----------",billing_add
	    #ero
            if billing_add.has_key('Street1'):
                street=billing_add.get('Street1')
                vals.update({'street':street})
            if billing_add.has_key('Street2'):
                street2=billing_add.get('Street2')
                vals.update({'street2':street2})
            if billing_add.has_key('Street1'):
                street=billing_add.get('Street1')
                vals.update({'street':street})
            if billing_add.has_key('City'):
                city=billing_add.get('City')
                vals.update({'city':city})
            if billing_add.has_key('State'):
                state=billing_add.get('State')
                cr.execute('select id from res_country_state where code = %s', (state,))
                state_id = filter(None, map(lambda x:x[0], cr.fetchall()))
		if state_id:
                    vals.update({'state_id':state_id[0]})
		else:
		    return json.dumps({"body":{'code':False,'message':"Incorrect State Code",}})

            if billing_add.has_key('Country'):
                country=billing_add.get('Country')
                cr.execute('select id from res_country where code = %s', ('US',))
                country_id = filter(None, map(lambda x:x[0], cr.fetchall()))
		if state_id:
                    vals.update({'country_id':country_id[0]})
                else:
                    return json.dumps({"body":{'code':False,'message':"Incorrect Country Code",}})
                

            if billing_add.has_key('Zip'):
                zip=billing_add.get('Zip')
                vals.update({'zip':zip})
            print "valssssss-------------",vals
            try:
                self.write(cr,uid,[customer_id],vals)
                #cr.commit()
            except Exception ,e:
		print"eeeeeeeeee",e
                return json.dumps({"body":{'Code':False,'message':'The Address is not valid.'}})




            if (dict.get('BillingInfo')).has_key('CreditCard'):
                cc_info=(dict.get('BillingInfo')).get('CreditCard')
		print "ccinfo------------------------",cc_info
                if cc_info.has_key('CCNumber') and cc_info.has_key('ExpDate') and cc_info.has_key('CCV'):
                    ccn=cc_info.get('CCNumber')
                    exp_date=cc_info.get('ExpDate')
                    exp_date = exp_date[-4:] + '-' + exp_date[:2]
                    ccv=cc_info.get('CCV')
                else:
                    return json.dumps({"body":{'Code':False,'message':'Incomplete Credit card Details.'}})


                cust_profile_id,numberstring=False,False
                act_model='res.partner'
                partner_obj=self.browse(cr,uid,customer_id)
                cust_profile_id=partner_obj.customer_profile_id
                email=partner_obj.emailid
                authorize_net_config=self.pool.get('authorize.net.config')
                config_ids =authorize_net_config.search(cr,uid,[])
		print "config_ids-----------------------",config_ids
                if config_ids:
                    config_obj = authorize_net_config.browse(cr,uid,config_ids[0])

                    if cust_profile_id:
                        try:
                            profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',cust_profile_id)
                            print "profile_info----------------",profile_info
                            #response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn, ccv, exp_date,act_model)
                            response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn, exp_date, ccv,act_model)
			    print "response------------------",response
                            numberstring=response.get('customerPaymentProfileId')
                        except Exception ,e:
                            print"eeeeeeeeee",e
                            return json.dumps({"body":{'Code':False,'message':'The call to Authorize.Net Failed.'}})
                    else:
                        print "insideeeeeeeeeeee"
                        try:
                            res = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileOnly',email)
                            print "res------------",res
                            cust_profile_id=res.get('cust_profile_id')
                            print "cust_profile_id-------------",cust_profile_id
                            #response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn,ccv,exp_date,act_model)
			    response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,int(customer_id),partner_obj,partner_obj,cust_profile_id,ccn, exp_date, ccv,act_model)
                            numberstring=response.get('customerPaymentProfileId')
                        except Exception ,e:
                            print"eeeeeeeeee",e
                            return json.dumps({"body":{'Code':False,'message':'The call to Authorize.Net Failed.'}})

                        print "response------------------",response
                    if cust_profile_id and numberstring:
                               payment_profile_val = {ccn[-4:]: numberstring}
                               self.pool.get('res.partner').cust_profile_payment(cr,uid,customer_id,cust_profile_id,payment_profile_val,exp_date,context)

        

        return json.dumps({"body":{'Code':True,'message':'Success.'}})'''




    '''def get_transactions_magento(self,cr,uid,dict,context=None):
        print "dict----------------",dict,type(dict)
        if dict.has_key('CustomerId') and dict.has_key('StartDate') and dict.has_key('EndDate'):
            cust_id=dict.get('CustomerId')
            start=dict.get('StartDate')
            end=dict.get('EndDate')
            start_unix=time.mktime(datetime.datetime.strptime(start, "%Y-%m-%d").timetuple())
            end_unix=time.mktime(datetime.datetime.strptime(end, "%Y-%m-%d").timetuple())
            response=self.pool.get('user.auth').obtaintransactions(cr,uid,cust_id,start_unix,end_unix)
            print "response----------------",response,type(response)
            dict_res = ast.literal_eval(str(response))
            print "dict_res",dict_res
            if dict_res.has_key('body') and (dict_res.get('body')).has_key('transactions'):
                transactions=dict_res['body']['transactions']
		


		date_object = datetime.datetime.strptime(str(start), '%Y-%m-%d')
                invoice_start_date=date_object.strftime('%m/%d/%Y')
                
                date_object2 = datetime.datetime.strptime(str(end), '%Y-%m-%d')
                invoice_end_date=date_object2.strftime('%m/%d/%Y')

		
                cr.execute("select id from account_invoice where partner_id=%s and date_invoice between '%s' and '%s'"%(cust_id,invoice_start_date,invoice_end_date))
                invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                if invoice_ids:
                    subscriptions=[]
                    invoice_obj=self.pool.get('account.invoice')
                    for each in invoice_ids:
                        inv_brw=invoice_obj.browse(cr,uid,each)
                        product_ids=[line.product_id for line in inv_brw.invoice_line]
                        descs=[line.name for line in inv_brw.invoice_line]

                        sub={'TrasactionDate':inv_brw.date_invoice,'TrasactionId':inv_brw.auth_transaction_id,'ProductId':product_ids,'Amount':inv_brw.amount_total}
                        subscriptions.append(sub)
                    print "subscriptions------------",subscriptions

                    return json.dumps({"body":{ "code":True, "message":"Success", "Transactions":transactions, "Subscriptions":subscriptions}})

                
        
        return json.dumps({"body":{ "code":False, "message":"Call To PlayjamServer Failed."}})'''


    def get_transactions_magento(self,dict,context=None):
        print "dict----------------",dict,type(dict)
        if 'CustomerId' in dict and 'StartDate' in dict  and 'EndDate' in dict:
            cust_id=dict.get('CustomerId')
	    cust_id=int(cust_id)
            start=dict.get('StartDate')
            end=dict.get('EndDate')

	    try:
                datetime.datetime.strptime(start, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":'-5635','message': "Invalid Date Format",}})

            try:
                datetime.datetime.strptime(end, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":'-5635','message': "Invalid Date Format",}})


            date_object = datetime.datetime.strptime(str(start), '%Y-%m-%d')
            invoice_start_date=date_object.strftime('%m/%d/%Y')

            date_object2 = datetime.datetime.strptime(str(end), '%Y-%m-%d')
            invoice_end_date=date_object2.strftime('%m/%d/%Y')


            request.cr.execute("select id from account_invoice where partner_id=%s and date_invoice between '%s' and '%s'"%(cust_id,invoice_start_date,invoice_end_date))
            invoice_ids = filter(None, map(lambda x:x[0], request.cr.fetchall()))
	    print "invoiceids id",invoice_ids
            if invoice_ids:
                subscriptions=[]
                invoice_obj=self.pool.get('account.invoice')
                for each in invoice_ids:
                    inv_brw=invoice_obj.browse(request.cr,SUPERUSER_ID,each)
		    product_info=[]
                    product_ids=[line.product_id for line in inv_brw.invoice_line]
		    for each in product_ids:
                        product_info.append({'ProductId':each.id,'SKU':each.default_code,'SubscriptionDetail':each.name})
                    descs=[line.name for line in inv_brw.invoice_line]

                    sub={'TrasactionDate':inv_brw.date_invoice,'TrasactionId':(inv_brw.auth_transaction_id or ""),'ProductInfo':product_info,'Amount':inv_brw.amount_total}
                    subscriptions.append(sub)
                print "subscriptions------------",subscriptions

                return json.dumps({"body":{ "code":'5632', "message":"Success", "Subscriptions" :subscriptions}})
        return json.dumps({"body":{ "code":'-5632', "message":"No results found"}})

    
    
        
    def get_order_info(self,dict,context=None):
        print "dict----------------",dict,type(dict)
        if ('CustomerId' in dict) and ('StartDate' in dict) and ('EndDate' in dict):
#        if dict.has_key('CustomerId') and dict.has_key('StartDate') and dict.has_key('EndDate'):
            cust_id=dict.get('CustomerId')
            start=dict.get('StartDate')
            end=dict.get('EndDate')
	    


	    if not cust_id or not start or not end:
		return json.dumps({"body":{ "code":'-5634', "message":"Invalid Request Data"}})

	    request.cr.execute('select id from res_partner where id= %s', (cust_id,))
            if_present = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            if if_present==[]:
                return json.dumps({"body":{'code':'-5555','message':"Missing or Invalid Customer ID",}})

            
            try:
                datetime.datetime.strptime(start, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":'-5635','message': "Invalid Date Format",}})

            try:
                datetime.datetime.strptime(end, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":'-5635','message': "Invalid Date Format",}})
    
            date_object = datetime.datetime.strptime(str(start), '%Y-%m-%d')
            order_start_date=date_object.strftime('%m/%d/%Y')

            date_object2 = datetime.datetime.strptime(str(end), '%Y-%m-%d')
            order_end_date=date_object2.strftime('%m/%d/%Y')
	    print "start and end daes-----------------",order_start_date,order_end_date

            request.cr.execute("select id from sale_order where partner_id=%s and date_order between '%s' and '%s'"%(cust_id,order_start_date,order_end_date))
            order_ids = filter(None, map(lambda x:x[0], request.cr.fetchall()))
            print "order_ids---------------",order_ids
            if order_ids:
                order_details=[]
                order_obj=self.pool.get('sale.order')
                for each in order_ids:
                    sale_brw=order_obj.browse(request.cr,SUPERUSER_ID,each)
                    sub={'OrderNo':sale_brw.name,'OrderDate':sale_brw.date_order,'TrackingNo':(sale_brw.tracking_no or ""),'Total':sale_brw.amount_total,'Subtotal':sale_brw.amount_total,'Discount':sale_brw.amount_total,'Tax':sale_brw.amount_total,'Shippping':0.0}
                    if sale_brw.order_line:
                        line_data=[]
                        for each in sale_brw.order_line:
                            linesub={'ProductId':each.product_id.id,"SKU":each.product_id.default_code,"Description":each.name,"Qty":each.product_uom_qty,"Price":(each.price_unit)*(each.product_uom_qty)}
                            line_data.append(linesub)
                        sub.update({"OrderLine":line_data})
                    order_details.append(sub)

                

                return json.dumps({"body":{ "code":'5632', "message":"Success", "OrderDetails":order_details}})
        return json.dumps({"body":{ "code":'-5632', "message":"No results found"}})




res_partner()
