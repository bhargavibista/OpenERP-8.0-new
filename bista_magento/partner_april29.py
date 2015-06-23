
from openerp.osv import fields, osv
import datetime
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
import calendar
from openerp.tools.misc import attrgetter
from openerp.addons.base_external_referentials.external_osv import ExternalSession
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




class res_partner(osv.osv):
    '''Voucher related details'''
    _inherit = 'res.partner'
    _columns={

        'user_name':fields.char('User Name', size=100),
        'password':fields.text('Password'),
        'gender':fields.selection([
            ('M', 'Male'),
            ('F', 'Female')
            ], 'Gender'),
        'dob':fields.date('DOB'),
        'age_rating':fields.char('Age Rating'),
        'player_tag':fields.char('Player Tag'),
        'game_profile_name':fields.char('Game Profile Name'),
        'account_pin':fields.char('Account Pin'),
        'use_wallet':fields.char('Use Wallet'),

    }
    _sql_constraints = [('username_uniq', 'unique(u_name)', 'A partner already exists with this User Name')]

    def create(self, cr, uid, vals, context={}):
        print "password----------------",vals.get('password')
        if vals.has_key('password'):
            pwd=vals.get('password')
            hash = pbkdf2_sha256.encrypt(str(pwd), rounds=200, salt_size=16)
            vals['password']=str(hash)

        res = super(res_partner, self).create(cr, uid, vals, context)

        return res

    def write(self, cr, uid, ids, vals, context={}):
        print "password----------------",vals.get('password')
        if vals.has_key('password'):
            pwd=vals.get('password')
            hash = pbkdf2_sha256.encrypt(str(pwd), rounds=200, salt_size=16)
            vals['password']=str(hash)

        res = super(res_partner, self).write(cr, uid, ids, vals, context)

        return res


#    {"ApiId":"123","DBName":"cox_db_12jan","CustomerId": "","FirstName": "abc","LastName": "pqr","Email": "abc@gmail.co", "PrimaryGameProfileName":"ab",
#"Password": "pqr","DOB":"1991-01-30","Gender":"M/F/O","AgeRating":14 , "AccountPIN":"123","UseWallet":True}


#    wallet processing
#    function to Top up the wallet using  CC
    def wallet_topup(self,cr,uid,dict,context):
        count=0
#        dict={'BillingInfo': {'PaymentProfileId': '29720861','BillingAddress': {'Street1': '581 Telegraph Canyon Rd', 'Street2': '', 'State': 'CA', 'Zip': '91910-6436', 'City': 'Chula Vista'}, 'CreditCard': {'CCNumber': '510510493671000', 'CCV': '123', 'ExpDate': '122020'}}, 'FillAmount': 10.0, 'ApiId': '123', 'PaymentType': 'CC', 'CustomerId': 6,'DBName': 'april_26th_final_test'}
#        dict_old={ 'BillingInfo': {'PaymentProfileId': '','BillingAddress': {'Street1': '581 Telegraph Canyon Rd', 'Street2': '', 'State': 'California', 'Zip': '91910-6436', 'City': 'Chula Vista'}, 'CreditCard': {'CCNumber': '510510493671000', 'CCV': '123', 'ExpDate': '122020'}}, 'FillAmount': 10.0, 'ApiId': '123', 'PaymentType': 'CC', 'CustomerId': 4543,'DBName': 'local_stable_7_test'}
        dict_wallet = { 'fill_amount':dict.get('FillAmount'),'payment_type':dict.get('PaymentType'),
                    'billing_info':dict.get('BillingInfo'),'api_id':dict.get('ApiId'),'partner_id':dict.get('CustomerId'),
                    }
        authorize_net_config = self.pool.get('authorize.net.config')
        journal_pool = self.pool.get('account.journal')
        account_voucher_obj=self.pool.get('account.voucher')
        partner_obj=self.pool.get('res.partner')
        user_auth_obj=self.pool.get('user.auth')
        account_obj=self.pool.get('account.account')
        transaction_id=''
        act_model='res.partner'
        transaction_type='profileTransAuthCapture'
        today=datetime.date.today()
        for key, value in dict_wallet.iteritems():
            if value is '':
                result={"body":{ 'code':False, 'message':"('%s Not found')"%(key)}}
                return json.dumps(result)
        #if the payment needs to be processed using CC
        auth_config_ids = authorize_net_config.search(cr,uid,[])
        credit_card=dict_wallet.get('billing_info').get('CreditCard')
        if credit_card:
            ccn=credit_card.get('CCNumber')
            ccv=credit_card.get('CCV')
            exp_date=credit_card.get('ExpDate')
        active_id=dict_wallet.get('partner_id')
        partner_brw=partner_obj.browse(cr,uid,active_id)
        if dict_wallet.get('billing_info').has_key('PaymentProfileId') and auth_config_ids:
            billing_info=dict_wallet.get('billing_info')
            payment_profile_id=billing_info.get('PaymentProfileId')
            config_obj = authorize_net_config.browse(cr,uid,auth_config_ids[0])
            amount=dict_wallet.get('fill_amount')
            bank_journal_ids = journal_pool.search(cr, uid, [('type', '=', 'bank')])
            account_id=account_obj.search(cr, uid, [('name', 'ilike', 'Advance Payment')])
            voucher_data = {'account_id': account_id[0],'partner_id': active_id,'journal_id':bank_journal_ids[0],'amount': amount,'type':'receipt','state': 'draft','pay_now': 'pay_later','name': '','date': today,'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher',context=None),'payment_option': 'without_writeoff','comment': _('Write-Off')}
            voucher_id=account_voucher_obj.create(cr,uid,voucher_data, context=context)
            context.update({'reference': voucher_id,'description':'Wallet Top-Up','captured_api':True})
#        call to create transaction in case of existine payment profile
            try:
                if payment_profile_id:
                    cust_profile_Id=partner_brw.customer_profile_id
                    numberstring=payment_profile_id
    #        call to create profile if there is no existing payment profile at Authorize end
                else: 
                    maxmind_response=self.pool.get('customer.profile.payment').maxmind_call(cr,uid,ccn)
                    if maxmind_response:
                        email=partner_brw.emailid
                        response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileOnly',email)
                        if response and 'cust_profile_id' in response:
                            cust_profile_Id = response.get('cust_profile_id')
                            if cust_profile_Id:
            #                                   //if success is False
                                if not response.get('success'):
                                    profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',cust_profile_Id)
                                    if not profile_info.get('payment_profile'):
                                      response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,active_id,partner_brw,partner_brw,cust_profile_Id,ccn,exp_date,ccv,act_model)
                                      numberstring = response.get('customerPaymentProfileId',False)
                                    else:
                                        profile_info = profile_info.get('payment_profile')
                                        if ccn[-4:] in profile_info.keys():
                                            numberstring =  profile_info[ccn[-4:]]
                                        else:
                                            response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,active_id,partner_brw,partner_brw,cust_profile_Id,ccn,exp_date,ccv,act_model)
                                            numberstring = response.get('customerPaymentProfileId',False)
            #                                   //if success is True
                                else:
                                    response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,active_id,partner_brw,partner_brw,cust_profile_Id,ccn,exp_date,ccv,act_model)
                                    numberstring = response.get('customerPaymentProfileId',False)
                if cust_profile_Id and numberstring:
                    payment_profile_val = {ccn[-4:]: numberstring}
                    partner_obj.cust_profile_payment(cr,uid,active_id,cust_profile_Id,payment_profile_val,exp_date,context)
                    if dict_wallet.get('fill_amount')>0.0:
                        amount=dict_wallet.get('fill_amount')
                        context['customer_profile_id']=cust_profile_Id
                        response =authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',active_id,transaction_type,amount,cust_profile_Id,numberstring,transaction_id,ccv,act_model,'',context)
                        transaction_id = response.get('response').split(',')[6]
                        if response.get('resultCode') == 'Ok':
                            wallet_response=user_auth_obj.wallet_playjam(cr, uid, 'FLARE1124', amount, context=None)
#                            retry 5 attempts in case if wallet update fails at playjam end
                            while count<5:
                                print "while cinrehvjkfdhjfdhb234567",count
                                if ast.literal_eval(wallet_response).get("body") and ast.literal_eval(wallet_response).get("body").get('result')==4129:
                                    quantity=ast.literal_eval(wallet_response).get("body").get('quantity')
                                    result={"body":{"code":True, "message":"Success", "WalletBalance":quantity}}
                                    partner_obj.write(cr,uid,active_id,{'wal_bal':quantity})
                                    account_voucher_obj.write(cr,uid,voucher_id,{'state':'posted'})
                                    account_voucher_obj.api_response(cr,uid,voucher_id,response.get('response'),numberstring,transaction_type,context)
                                     #Add Journal Entries
                                    account_voucher_obj.action_move_line_create(cr,uid,[voucher_id])
                                    count=6
                                else:
                                    count+=1
                            if count==5:
                                authorize_net_config.call(cr,uid,config_obj,'VoidTransaction',cust_profile_Id,numberstring,transaction_id)
                                result={"body":{ "code":False, "message":"Failed to update wallet at Playjam end"}}
            except Exception, e:
                result={'code':False,'message':'Failed to create order because %s'%(e)}
            return json.dumps(result)
#    giftcard        
    def redeem_gift_card(self,cr,uid,dict,context):
        maerge_invoice_data,result,sale_info=[],{},{}
        today=datetime.date.today()
        nextmonth = today + relativedelta(months=1)
        invoice_obj=self.pool.get('account.invoice')
        exception_obj=self.pool.get('partner.payment.error')
        sale_obj=self.pool.get('sale.order')
        gift_card_obj=self.pool.get('gift.card.validate.call')
        tru_obj=self.pool.get('tru.subscription.options')
        policy_obj=self.pool.get('res.partner.policy')
#        dict={"ApiId":"123","DBName":"april_26th_final_test","CustomerId":"6","GiftCardNumber": "7528681124"}
        print "dict....................",dict
        dict_gift_card={'api_id':dict.get('ApiId'),'partner_id':dict.get('CustomerId'),'card_no':dict.get('GiftCardNumber')}
#        for reversal of card value
#        gift_card_reversal=gift_card_obj.api_call_toincomm_reversal(cr,uid,dict_gift_card.get('card_no'),context=context)
#        return True
        for key, value in dict_gift_card.iteritems():
            if value is '':
                result={"body":{ "code":False, "message":"('%s Not found')"%(key)}}  
                return json.dumps(result)
        try:
            partner_brw=self.pool.get('res.partner').browse(cr,uid,int(dict.get('CustomerId')))
            billing_date=partner_brw.billing_date
            billing_date=datetime.datetime.strptime(billing_date, '%Y-%m-%d')
            if billing_date:
                nextmonth=billing_date + relativedelta(months=1)
            gift_card_response=gift_card_obj.api_call_toincomm_statinq(cr,uid,dict_gift_card.get('card_no'),context=context)
            resp_code_statinq=gift_card_response.getElementsByTagName("RespCode")[0].childNodes[0].nodeValue
            print "resp_code_statinqresp_code_statinq",resp_code_statinq
            if resp_code_statinq=='4001':
                face_value=gift_card_response.getElementsByTagName("FaceValue")[0].childNodes[0].nodeValue
                print "face_valueface_valueface_value",face_value
                partner_obj=self.pool.get('res.partner').browse(cr,uid,int(dict.get('CustomerId')))
                if face_value>0.0:
                    subscription_id=tru_obj.search(cr,uid,[('sales_channel_tru','=','tru')])
                    if subscription_id:
                        subscrption_service=tru_obj.browse(cr,uid,subscription_id[0]).product_id
                        print "subscrption_servicesubscrption_service",subscrption_service
                        cr.execute("select product_id from res_partner_policy where active_service =True and agmnt_partner = %s"%(int(dict_gift_card.get('partner_id'))))
                        active_services = filter(None, map(lambda x:x[0], cr.fetchall()))
                        print "active_servicesactive_services",active_services,subscrption_service.id
                        if active_services and subscrption_service.id in active_services:
                            policy_id = policy_obj.search(cr,uid,[('product_id','=',subscrption_service.id)])
                            print "policy id...............",policy_id
                            policy_brw=policy_obj.browse(cr,uid,policy_id[0])
                            print "policy_brwpolicy_brwpolicy_brw",policy_brw
                            #Extra Code for Checking whether service is cancelled or not
                            cr.execute('select id from cancel_service where sale_id = %s and sale_line_id = %s and partner_policy_id=%s and cancelled=False'%(policy_brw.sale_id,policy_brw.sale_line_id,policy_brw.id))
                            policies = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if not policies:
                                sale_info={}
                                cr.execute(
                                    "select id from sale_order_line where parent_so_line_id in(\
                                    select sale_line_id from return_order_line where order_id = \
                                    (select id from return_order where state= 'email_sent' and return_type='car_return' and linked_sale_order = %s ))\
                                    or id in(\
                                    select sale_line_id from return_order_line where order_id = \
                                    (select id from return_order where state= 'email_sent' and return_type='car_return' and linked_sale_order = %s ))\
                                    "%(policy_brw.sale_id,policy_brw.sale_id)
                                    )
                                so_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                                if not policy_brw.sale_line_id in so_line_id:
                                    invoice_name = '%'+policy_brw.sale_order+'%'
                                    print "invoice_nameinvoice_name",invoice_name
                                    search_payment_exception =exception_obj.search(cr,uid,[('active_payment','=',True),('partner_id','=',int(dict.get('CustomerId'))),('invoice_name','ilike',invoice_name)])
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
                                redemption_details=gift_card_obj.api_call_toincomm_redemption(cr,uid,dict_gift_card.get('card_no'),context=context)
                                print "redemption_detailsredemption_detailsredemption_details",redemption_details
                                resp_code=redemption_details.getElementsByTagName("RespCode")[0].childNodes[0].nodeValue
                                
                                if resp_code=='0':
                                    if sale_info:
                                        maerge_invoice_data+=[sale_info]
                            if len(maerge_invoice_data)!=0:
                                cr.execute("select profile_id from partner_profile_ids where partner_id='%s'"%(int(dict.get('CustomerId'))))
                                result_profile=cr.dictfetchall()
                                if result_profile:
                                    partner_profile_id=result_profile[0].get('profile_id')
                                    cr.execute("select id,profile_id,credit_card_no from custmer_payment_profile where customer_profile_id='%s' and active_payment_profile=True"%(str(partner_obj.customer_profile_id)))
                                    payment_profile_data=cr.dictfetchall()
                                    if payment_profile_data:
                                        for each in payment_profile_data:
                                            payment_profile_id=each.get('profile_id')
                                            profile_id=each.get('id')
                                            print "profile_id",profile_id,partner_profile_id
                                            if profile_id==partner_profile_id:
                                                context['cc_number'] = each.get('credit_card_no')
                                context.update({'partner_id_obj': partner_obj,'captured_api': True,'giftcard':True,'facevalue': facevalue})
                                res_id=sale_obj.action_invoice_merge(cr, uid, maerge_invoice_data, today, nextmonth, policy_brw.start_date,payment_profile_id, context=context)
                                if res_id:
                                    if partner_obj.payment_policy=='pro':
                                        partner_obj.write({'auto_import':True,'billing_date':str(nextmonth)},context)
                                    invoice_id_obj = invoice_obj.browse(cr,uid,res_id)
                                    sale_obj.email_to_customer(cr,uid,invoice_id_obj,'account.invoice','',partner_obj.emailid,context)
                                    if partner_obj.ref:
                                        try:
                                            self.export_recurring_profile(cr,uid,[res_id],context)
                                        except Exception, e:
                                            print "error string",e
                                    result={"body":{"code":True, "message":"Success"}}
                                else:
                                    gift_card_reversal=gift_card_obj.api_call_toincomm_reversal(cr,uid,dict_gift_card.get('card_no'),context=context)
                                    result={"body":{ "code":False, "message":"Card Reversed"}}
                            else:
                                result={"body":{ "code":False, "message":"Service is Already Cancelled"}}        
                        else:
                            result={"body":{ "code":False, "message":"Subscription is not active for the customer"}}  
            elif resp_code_statinq=='4003':
                result={"body":{ "code":False, "message":"Card is already Redeemed"}}
            elif resp_code_statinq=='4006':
                result={"body":{ "code":False, "message":"Card not Found"}}
        except Exception, e:
            result={'code':False,'message':'Failed to create order because %s'%(e)}
        return json.dumps(result)
#online purchase order
##function to create an order at a glance through magento online purchase order API Call
    def create_order_magento(self,cr,uid,dict,context):
        vals,dict_exist,line_data,so_data,vals1,vals2,result,street1_inv,street2_inv,street1,street2 ={},{},{},{},{},'','','',''
        product_obj=self.pool.get("product.product")
#        dict_old={"ApiId":"123","DBName":"local_stable_7_test","CustomerId":"4570","Email":"wallettest3@gmail.com","MagentoOrderId":"3423435345","BillingInfo":{ "PaymentProfileId":"","CreditCard":{"CCNumber":"378282246310005","ExpDate":"122020","CCV":"123",},"BillingAddress": { "Street1": "581 Telegraph Canyon Rd","Street2": "","City": "Chula Vista","State": "CA","Zip": "91910-6436",}},"ShippingAddress": { "Street1": "581 Telegraph Canyon Rd", "Street2": "", "City": "Chula Vista", "State": "CA", "Zip": "91910-6436" },"OrderLine":{'line1':{"SKU":"freindsfamiliyoffer","ProductId":41,"Qty":"1.0","Price":"10.00"}},"Subtotal":6.00,"Discount":2.00,"Tax":2.00,"Shipping":5.00,"Total":11.00,}
#        dict={"ApiId":"123","DBName":"april_26th_final_test","CustomerId":"6","Email":"yogita.paghdar@bistasolutions.com","MagentoOrderId":"3423565345","BillingInfo":{ "PaymentProfileId":"","CreditCard":{"CCNumber":"378734493671000","ExpDate":"122020","CCV":"123",},"BillingAddress": { "Street1": "1401","Street2": "795 Hammond Dr","City": "Atlanta","State": "GA","Zip": "30328-5517",}},"ShippingAddress": { "Street1": "1401", "Street2": "795 Hammond Dr", "City": "Atlanta", "State": "GA", "Zip": "30328-5517" },"OrderLine":{'line1':{"SKU":"Disney Bundle","ProductId":13,"Qty":"1.0","Price":"10.00"}},"Subtotal":6.00,"Discount":2.00,"Tax":2.00,"Shipping":5.00,"Total":11.00,}
        dict_exist = { 'magento_orderid':dict.get('MagentoOrderId'),'shipping_add':dict.get('ShippingAddress'),
                    'billing_info':dict.get('BillingInfo'),'lines':dict.get('OrderLine'),'partner_id':dict.get('CustomerId'),
                    }
        for key, value in dict_exist.iteritems():
            if value is '':
                result={"body":{ 'code':False, 'message':"('%s Not found')"%(key)}}
                return json.dumps(result)
        try:
            today=datetime.date.today()
            partner_obj=self.pool.get('res.partner')
            sale_obj=self.pool.get("sale.order")
            total=dict.get('Total')
            location_id=1
            sale_shop=self.pool.get("sale.shop")
            partner_brw=partner_obj.browse(cr,uid,int(dict_exist.get('partner_id')))
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
            state_id=self.pool.get('res.country.state').search(cr,uid,[('code','=',state)])
            state_id_inv=self.pool.get('res.country.state').search(cr,uid,[('code','=',state_inv)])
            country_id=self.pool.get('res.country.state').browse(cr, uid, state_id[0], context).country_id.id
            country_id_inv=self.pool.get('res.country.state').browse(cr, uid, state_id_inv[0], context).country_id.id
            shop_id=sale_shop.search(cr,uid,[('name','ilike','company')])
            zip=shipping_add.get('Zip')
            zip_inv=inv_add.get('Zip')
            print state_id,state_id_inv,country_id,country_id_inv,shop_id,zip,zip_inv
            if state_id and country_id:
                print street1,street2,zip
                ship_add=partner_obj.search(cr,uid,[('parent_id','=',int(dict_exist.get('partner_id'))),('street','ilike',street1),('street2','ilike',street2),('city','=',city),('zip','=',zip),('state_id','=',state_id[0]),('country_id','=',country_id)])
                if not ship_add:
                    vals1 = {'parent_id': int(dict_exist.get('partner_id')),'name':partner_brw.name,'address_type': 'contact','city':city,'phone': partner_brw.phone,'street':street1,'street2': street2 or '', 'state_id':state_id[0],'country_id':country_id,'zip':zip}
                    ship_add=partner_obj.create(cr, uid, vals1, context=context)
                else:
                    ship_add=ship_add[0]
            if state_id_inv and country_id_inv:
                print street1_inv,street2_inv,city_inv
                invoice_add=partner_obj.search(cr,uid,[('id','=',int(dict_exist.get('partner_id'))),('street','ilike',street1_inv),('street2','ilike',street2_inv),('city','=',city_inv),('zip','=',zip_inv),('state_id','=',state_id_inv[0]),('country_id','=',country_id_inv)])
                if not invoice_add:
                    vals2 = {'city':city,'street':street1_inv,'street2': street2_inv or '', 'state_id':state_id[0],'country_id':country_id}
                    partner_obj.write(cr, uid,int(dict_exist.get('partner_id')), vals2)
                    invoice_add=int(dict_exist.get('partner_id'))
                else:
                    invoice_add=invoice_add[0]
            if 'PaymentProfileId' in dict_exist.get('billing_info'):
                billing_info=dict_exist.get('billing_info')
                payment_profile_id=billing_info.get('PaymentProfileId')
            so_data = {'partner_id':int(dict_exist.get('partner_id')),'shop_id': shop_id[0],'amount_total':total,'magento_so_id':dict_exist.get('magento_orderid'),'pricelist_id': pricelist,'cox_sales_channels':'ecommerce','partner_invoice_id': invoice_add,'partner_shipping_id': ship_add,'location_id':location_id,'date_order': today}
            new_id = sale_obj.create(cr, uid, so_data, context=context)
            sale_brw=sale_obj.browse(cr,uid,new_id)
            for each in dict_exist.get('lines'):
                each_param=dict_exist.get('lines').get(each)
                price=each_param.get('Price')
                productid=each_param.get('ProductId')
                product_id=product_obj.search(cr,uid,[('id','=',productid)])
                if product_id:
                    prdct_name=str(product_obj.browse(cr,uid,productid).name)
                    cr.execute("select product_id from res_partner_policy where active_service =True and agmnt_partner = %s"%(int(dict_exist.get('partner_id'))))
                    active_services = filter(None, map(lambda x:x[0], cr.fetchall()))
                    print "active_services",active_services
#                    sub_components = self.pool.get('extra.prod.config').search(cr,uid,[('product_id','=',product_id)])
                    quantity=each_param.get('Qty')
                    context.update({'active_model': 'sale.order','magento_orderid': dict_exist.get('magento_orderid'),'active_id':new_id})
                    line_data = {'order_id': new_id,'name':prdct_name,'price_unit': price,'product_uom_qty': quantity or 1.0,'product_uos_qty': quantity or 1.0,'product_id': product_id[0] or False,'actual_price':0.0}
                    sale_line_id=self.pool.get("sale.order.line").create(cr, uid, line_data, context=context)
                    sub_components = product_obj.browse(cr,uid,product_id[0]).ext_prod_config
                    print "sub_componentssub_components",sub_components,product_id
                    if sub_components:
                        for each_sub_comp in sub_components:
                            comp_prod_id=each_sub_comp.comp_product_id.id
                            price=each_sub_comp.comp_product_id.price
                            print "comp_prod_idcomp_prod_id",comp_prod_id
                            product_type=product_obj.browse(cr,uid,comp_prod_id).type
                            print "product_typeproduct_type",product_type
                            if product_type=='service':
                                if comp_prod_id in active_services:
                                    result={"body":{ 'code':'False', 'message':"Subscription is already active for requested service"}}
                                    return result
                            sub_comp_data=({'name':each_sub_comp.comp_product_id.name,'qty_uom':1.0,'product_id':comp_prod_id,'price':price,'so_line_id':sale_line_id,'product_type':product_type,'uom_id':each_sub_comp.product_id.uom_id.id or 1})
                            sub_comp_id=self.pool.get('sub.components').create(cr,uid,sub_comp_data,context=context)
                else:
                    result={"body":{ 'code':False, 'message':"Product Not Found!!!!"}}
                    return json.dumps(result)
            so_name=sale_brw.name
    #        call at Authorize end for an existing profile
            if payment_profile_id:
                context.update({'cust_payment_profile_id':payment_profile_id,'captured_api':True})
                exis_pay_profile=self.pool.get('charge.customer').charge_customer(cr,uid,[new_id],context)
                result={"body":{ 'code':True, 'message':"Success",'OrderNo':so_name}}
    #        call at Authorize for a new profile creation
            elif billing_info.get('CreditCard'):
                credit_card=billing_info.get('CreditCard')
                context.update({'ccv': credit_card.get('CCV'),'exp_date': credit_card.get('ExpDate'),'action_to_do':'new_customer_profile','magento_orderid': dict_exist.get('magento_orderid'),'sale_id':[new_id],'cc_number':credit_card.get('CCNumber')})
                new_pay_prfl=self.pool.get('customer.profile.payment').charge_customer(cr,uid,[new_id],context)
                result={"body":{ 'code':True, 'message':"Success",'OrderNo':so_name}}
        except Exception, e:
            result={'code':False,'message':'Failed to create order because %s'%(e)}
        return json.dumps(result)
    



##function to create an order at a glance through magento online purchase order API Call
#    def create_order_magento(self,cr,uid,dict,context):
#        print "dict------------",dict
#        result,dict_exist,vals,vals1,result,warning ={},{},{},{},{},{'code': 'False'}
#        dict_exist = { 'magento_orderid':dict.get('MagentoOrderId'),'shipping_add':dict.get('ShippingAddress'),
#                    'billing_info':dict.get('BillingInfo'),'lines':dict.get('OrderLine'),'partner_id':dict.get('CustomerId'),
#                    }
#        for key, value in dict_exist.iteritems():
#            if value is '':
#                print "None found4235434646!"
#            else:
#                today=datetime.date.today()
#                partner_obj=self.pool.get('res.partner')
#                sale_obj=self.pool.get("sale.order")
#                total=dict.get('Total')
#                location_id=12
#                partner_brw=self.browse(cr,uid,dict_exist.get('partner_id'))
#                partner_addr = partner_obj.address_get(cr, uid, [dict_exist.get('partner_id')],
#                            ['default', 'invoice', 'delivery', 'contact'])
#                shipping_add=dict_exist.get('shipping_add')
#                if shipping_add.get('Street1') and shipping_add.get('Street2'):
#                    street1=shipping_add.get('Street1')
#                    street2=shipping_add.get('Street2')
#                else:
#                    street1 = shipping_add.get('Street1')
#                    street2 = ''
#                city=shipping_add.get('City')
#                state=shipping_add.get('State')
#                state_id=self.pool.get('res.country.state').search(cr,uid,[('name','=',state)])
#                country_id=self.pool.get('res.country.state').browse(cr, uid, state_id[0], context).country_id.id
#                zip=shipping_add.get('Zip')
#                if state_id and country_id:
#                    ship_add=partner_obj.search(cr,uid,[('street','ilike',street1),('street2','ilike',street2),('city','=',city),('zip','=',zip),('state_id','=',state_id[0]),('country_id','=',country_id)])
#                    if not ship_add:
#                        vals1 = {'parent_id': dict_exist.get('partner_id'),'name':partner_brw.name,'address_type': 'delivery','city':city,'phone': partner_brw.phone,'street':street1,'street2': street2 or '', 'state_id':state_id[0],'country_id':country_id}
#                        ship_add=partner_obj.create(cr, uid, vals1, context=context)
#                    else:
#                        ship_add=ship_add[0]
#                if 'PaymentProfileId' in dict_exist.get('billing_info'):
#                    billing_info=dict_exist.get('billing_info')
#                    payment_profile_id=billing_info.get('PaymentProfileId')
#                vals = {'partner_id':dict_exist.get('partner_id'),'shop_id': 3,'amount_total':total,'magento_so_id':dict_exist.get('magento_orderid'),'pricelist_id': 1,'cox_sales_channels':'ecommerce','partner_invoice_id': partner_addr['invoice'],'partner_shipping_id': ship_add,'location_id':location_id,'date_order': today}
#                new_id = sale_obj.create(cr, uid, vals, context=context)
#                sale_brw=sale_obj.browse(cr,uid,new_id)
#                for each in dict_exist.get('lines'):
#                    each_param=dict_exist.get('lines').get(each)
#                    price=each_param.get('Price')
#                    sku=each_param.get('SKU')
#                    product_id=self.pool.get("product.product").search(cr,uid,[('default_code','=',sku)])
#                    if product_id:
#                        cr.execute("select product_id from res_partner_policy where active_service =True and agmnt_partner = %s"%(dict_exist.get('partner_id')))
#                        active_services = filter(None, map(lambda x:x[0], cr.fetchall()))
#                        sub_components = self.pool.get('extra.prod.config').search(cr,uid,[('product_id','in',product_id)])
#                        if sub_components:
#                            for each_sub_comp in sub_components:
#                                if each_sub_comp in active_services:
#                                    warning.update({'message' : _('Subscription is already active for requested service')})
#                                    result['warning'] = warning
#                                    return json.dumps(result)
#                                else:
#                                    quantity=each_param.get('Qty')
#                                    context.update({'active_model': 'sale.order','magento_orderid': dict_exist.get('magento_orderid'),'active_id':new_id})
#                                    vals1 = {'order_id': new_id,'name':'Friends and Family offer - Free Device + 3 Months Service','price_unit': price,'product_uom_qty': quantity or 1.0,'product_uos_qty': quantity or 1.0,'product_id': product_id[0] or False,}
#                            self.pool.get("sale.order.line").create(cr, uid, vals1, context=context)
#                    else:
#                        warning.update({'message' : _('Product Not Found!!!!')})
#                        result['warning'] = warning
#                        return json.dumps(result)
#                so_name=sale_brw.name
#                if payment_profile_id:
#                    context['cust_payment_profile_id']=payment_profile_id
#                    self.pool.get("charge.customer").charge_customer(cr,uid,[new_id],context)
#                    result={'code':True,'OrderNo':so_name}
#                elif billing_info.get('CreditCard'):
#                    credit_card=billing_info.get('CreditCard')
#                    context.update({'ccv': credit_card.get('CCV'),'exp_date': credit_card.get('ExpDate'),'action_to_do':'new_customer_profile','magento_orderid': dict_exist.get('magento_orderid'),'sale_id':[new_id],'cc_number':credit_card.get('CCNumber')})
#                    self.pool.get('customer.profile.payment').charge_customer(cr,uid,[new_id],context)
#                    result={'code':True,'OrderNo':so_name}
#                else:
#                    result={'code':False,'message':'Failure!!!!!!!!!!!'}
#                return json.dumps(result)
#


            

    def create_update_customer(self,cr,uid,dict,context=None):
        print "dict----------------",dict,type(dict)
        customer_id=dict.get('CustomerId',False)
        
        name=""
        vals={}
        f_name,l_name='',''
        if dict.has_key('FirstName') or dict.has_key('LastName'):
            name=dict.get('FirstName','')+' '+dict.get('LastName','')
            vals.update({'name':name})

        if dict.has_key('Email'):
            emailid=dict.get('Email')
            vals.update({'emailid':emailid})

        if dict.has_key('PrimaryGameProfileName'):
            game_profile_name=dict.get('PrimaryGameProfileName')
            vals.update({'game_profile_name':game_profile_name})

        if dict.has_key('Password'):
            password=dict.get('Password')
            vals.update({'password':password})

        if dict.has_key('DOB'):
            dob=dict.get('DOB')
            vals.update({'dob':dob})

        if dict.has_key('AgeRating'):
            age_rating=dict.get('AgeRating')
            vals.update({'age_rating':age_rating})

        if dict.has_key('AccountPIN'):
            account_pin=dict.get('AccountPIN')
            vals.update({'account_pin':account_pin})

        if dict.has_key('UseWallet'):
            use_wallet=dict.get('UseWallet')
            vals.update({'use_wallet':age_rating})

        if customer_id:
            self.write(cr,uid,[customer_id],vals)
            return json.dumps({'code':True,'message':"Success","CustomerId":customer_id,})
        else:
            cust_id=self.create(cr,uid,vals)
            return json.dumps({'code':True,'message':"Success","CustomerId":cust_id,})


#        ero
        return True


    def login_magento(self,cr,uid,username,password,context=None):
        cr.execute('select id from res_partner where emailid = %s', (username,))
        partner_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        print "partner_id-------",partner_id
#        ero
        if partner_id:
            pat_obj=self.browse(cr,uid,partner_id[0])
            hash=pat_obj.password
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
                return json.dumps({"code":True,"message":"Success","UserName": username, "Password": password, "CustomerId":partner_id[0],"FirstName":first_name,"LastName":last_name})
            else:
                return json.dumps({"code":False,"message":"Incorrect Password"})

#            return result
        return json.dumps({"code":False,"message":"Incorrect UserName"})



    def get_account_info(self, cr, uid, dict, context=None):
        print "dict-----------------------",dict
        res={}
        if dict.get('CustomerId',False):
            cust_id=dict.get('CustomerId')
            print "cust_id-------------",cust_id
            pat_obj=self.browse(cr,uid,int(cust_id))
            if pat_obj:
                print "test----------",pat_obj
                res.update({'CustomerId':cust_id})
                game_profile_name=pat_obj.game_profile_name
                if game_profile_name:
                    res.update({'PrimaryGameProfileName':game_profile_name})
                password=pat_obj.password
                if password:
                    res.update({'Password':password})
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
                wal_bal_body=ua_obj.wallet_playjam(cr,uid,cust_id,0)
                wal_bal_body = ast.literal_eval(str(wal_bal_body))
                if wal_bal_body.has_key('body') and (wal_bal_body.get('body')).has_key('quantity'):
                    quantity=wal_bal_body['body']['quantity']
                    res.update({'WalletBalance':quantity})

                user_auth_ids=pat_obj.user_auth_ids
                if user_auth_ids:
                    dev_ids=[]
                    for each in user_auth_ids:
                        dev_id=each.device_id
                        dev_ids.append(dev_id)


                    res.update({'Devices':dev_ids})

                policy_ids=pat_obj.agreement_policy
                if policy_ids:
                    subscription_list=[]
                    for each in policy_ids:
                        sub={}
                        
                        if each.active_service:
                            sub.update({'SKU':each.product_id.default_code,'SubscriptionDetail':each.service_name,'Price':each.recurring_price,'StartDate':each.start_date,'FreeTrialDate':each.free_trial_date})
                            subscription_list.append(sub)
                    res.update({'Subscription':subscription_list})
                    
                bill_info={}
                if pat_obj.profile_ids:
                    for each in pat_obj.profile_ids:
                        if each.active_payment_profile==True:
                            bill_info.update({'PaymentProfileId':each.profile_id})
                            bill_info.update({'CreditCard':{'CCNumber':each.credit_card_no,'ExpDate':each.exp_date}})
#                            bill_info.update({'CreditCard':{'CCNumber':each.credit_card_no,}})

                partner_addr = self.pool.get('res.partner').address_get(cr, uid, [int(cust_id)],['invoice',])
                if partner_addr:
                    inv_add_id=partner_addr.get('invoice')
                    add_obj=self.pool.get('res.partner').browse(cr,uid,inv_add_id)
                    bill_info.update({'BillingAddress':{'Street1':add_obj.street,'Street2':add_obj.street2,'City':add_obj.city,'State':add_obj.state_id.name,'Zip':add_obj.zip}})

                res.update({'BillingInfo':bill_info})
                res.update({'Code':True,'messsage':'Success'})


                return json.dumps(res)

            return json.dumps({'Code':False,'messsage':'No CustomerId Given.'})





    def get_transactions_magento(self,cr,uid,dict,context=None):
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
                return json.dumps({ "code":True, "message":"Success", "Transactions":transactions})
        
        return json.dumps({ "code":False, "message":"Error!!"})
    
    
        





res_partner()

