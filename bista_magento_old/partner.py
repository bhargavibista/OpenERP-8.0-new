

from openerp.osv import osv, fields
import openerp.tools as tools
from random import randint
import os
import urllib
import requests
import json
import ast
from passlib.hash import pbkdf2_sha256
import time
import datetime
import ast


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


#function to create an order at a glance through magento online purchase order API Call
    def create_order_magento(self,cr,uid,dict,context):
        print "dict------------",dict
        result,dict_exist,vals,vals1,result,warning ={},{},{},{},{},{'code': 'False'}
        dict_exist = { 'magento_orderid':dict.get('MagentoOrderId'),'shipping_add':dict.get('ShippingAddress'),
                    'billing_info':dict.get('BillingInfo'),'lines':dict.get('OrderLine'),'partner_id':dict.get('CustomerId'),
                    }
        for key, value in dict_exist.iteritems():
            if value is '':
                print "None found4235434646!"
            else:
                today=datetime.date.today()
                partner_obj=self.pool.get('res.partner')
                sale_obj=self.pool.get("sale.order")
                total=dict.get('Total')
                location_id=12
                partner_brw=self.browse(cr,uid,dict_exist.get('partner_id'))
                partner_addr = partner_obj.address_get(cr, uid, [dict_exist.get('partner_id')],
                            ['default', 'invoice', 'delivery', 'contact'])
                shipping_add=dict_exist.get('shipping_add')
                if shipping_add.get('Street1') and shipping_add.get('Street2'):
                    street1=shipping_add.get('Street1')
                    street2=shipping_add.get('Street2')
                else:
                    street1 = shipping_add.get('Street1')
                    street2 = ''
                city=shipping_add.get('City')
                state=shipping_add.get('State')
                state_id=self.pool.get('res.country.state').search(cr,uid,[('name','=',state)])
                country_id=self.pool.get('res.country.state').browse(cr, uid, state_id[0], context).country_id.id
                zip=shipping_add.get('Zip')
                if state_id and country_id:
                    ship_add=partner_obj.search(cr,uid,[('street','ilike',street1),('street2','ilike',street2),('city','=',city),('zip','=',zip),('state_id','=',state_id[0]),('country_id','=',country_id)])
                    if not ship_add:
                        vals1 = {'parent_id': dict_exist.get('partner_id'),'name':partner_brw.name,'address_type': 'delivery','city':city,'phone': partner_brw.phone,'street':street1,'street2': street2 or '', 'state_id':state_id[0],'country_id':country_id}
                        ship_add=partner_obj.create(cr, uid, vals1, context=context)
                    else:
                        ship_add=ship_add[0]
                if 'PaymentProfileId' in dict_exist.get('billing_info'):
                    billing_info=dict_exist.get('billing_info')
                    payment_profile_id=billing_info.get('PaymentProfileId')
                vals = {'partner_id':dict_exist.get('partner_id'),'shop_id': 3,'amount_total':total,'magento_so_id':dict_exist.get('magento_orderid'),'pricelist_id': 1,'cox_sales_channels':'ecommerce','partner_invoice_id': partner_addr['invoice'],'partner_shipping_id': ship_add,'location_id':location_id,'date_order': today}
                new_id = sale_obj.create(cr, uid, vals, context=context)
                sale_brw=sale_obj.browse(cr,uid,new_id)
                for each in dict_exist.get('lines'):
                    each_param=dict_exist.get('lines').get(each)
                    price=each_param.get('Price')
                    sku=each_param.get('SKU')
                    product_id=self.pool.get("product.product").search(cr,uid,[('default_code','=',sku)])
                    if product_id:
                        cr.execute("select product_id from res_partner_policy where active_service =True and agmnt_partner = %s"%(dict_exist.get('partner_id')))
                        active_services = filter(None, map(lambda x:x[0], cr.fetchall()))
                        sub_components = self.pool.get('extra.prod.config').search(cr,uid,[('product_id','in',product_id)])
                        if sub_components:
                            for each_sub_comp in sub_components:
                                if each_sub_comp in active_services:
                                    warning.update({'message' : _('Subscription is already active for requested service')})
                                    result['warning'] = warning
                                    return json.dumps(result)
                                else:
                                    quantity=each_param.get('Qty')
                                    context.update({'active_model': 'sale.order','magento_orderid': dict_exist.get('magento_orderid'),'active_id':new_id})
                                    vals1 = {'order_id': new_id,'name':'Friends and Family offer - Free Device + 3 Months Service','price_unit': price,'product_uom_qty': quantity or 1.0,'product_uos_qty': quantity or 1.0,'product_id': product_id[0] or False,}
                            self.pool.get("sale.order.line").create(cr, uid, vals1, context=context)
                    else:
                        warning.update({'message' : _('Product Not Found!!!!')})
                        result['warning'] = warning
                        return json.dumps(result)
                so_name=sale_brw.name
                if payment_profile_id:
                    context['cust_payment_profile_id']=payment_profile_id
                    self.pool.get("charge.customer").charge_customer(cr,uid,[new_id],context)
                    result={'code':True,'OrderNo':so_name}
                elif billing_info.get('CreditCard'):
                    credit_card=billing_info.get('CreditCard')
                    context.update({'ccv': credit_card.get('CCV'),'exp_date': credit_card.get('ExpDate'),'action_to_do':'new_customer_profile','magento_orderid': dict_exist.get('magento_orderid'),'sale_id':[new_id],'cc_number':credit_card.get('CCNumber')})
                    self.pool.get('customer.profile.payment').charge_customer(cr,uid,[new_id],context)
                    result={'code':True,'OrderNo':so_name}
                else:
                    result={'code':False,'message':'Failure!!!!!!!!!!!'}
                return json.dumps(result)



            

    '''def create_update_customer(self,cr,uid,dict,context=None):
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
            cr.execute('select id from res_partner where emailid= %s', (emailid,))
            if_exist = filter(None, map(lambda x:x[0], cr.fetchall()))
            vals.update({'emailid':emailid})

        if dict.has_key('PrimaryGameProfileName'):
            game_profile_name=dict.get('PrimaryGameProfileName')
            vals.update({'game_profile_name':game_profile_name})

        if dict.has_key('Password'):
            password=dict.get('Password')
            vals.update({'password':password})

        if dict.has_key('DOB'):
            dob=dict.get('DOB')
            try:
                datetime.datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":False,'message': "Incorrect data format, should be YYYY-MM-DD",}})
            vals.update({'dob':dob})

        if dict.has_key('Gender'):
            gender=dict.get('Gender')
            if gender =='M' or gender =='F':
                vals.update({'gender':gender})
            else:               
                return json.dumps({"body":{"code":False,'message': "Incorrect Data for Gender",}})

        if dict.has_key('AgeRating'):
            age_rating=dict.get('AgeRating')
            vals.update({'age_rating':age_rating})

        if dict.has_key('AccountPIN'):
            account_pin=dict.get('AccountPIN')
            vals.update({'account_pin':account_pin})

        if dict.has_key('UseWallet'):
            use_wallet=dict.get('UseWallet')
            vals.update({'use_wallet':use_wallet})

        if customer_id:
            self.write(cr,uid,[customer_id],vals)
            return json.dumps({"body":{'code':True,'message':"Success","CustomerId":customer_id,}})
        else:
            if if_exist!=[]:
                return json.dumps({"body":{"code":False,'message': "The Email-id Already exists.",}})
            cust_id=self.create(cr,uid,vals)
            return json.dumps({"body":{'code':True,'message':"Success","CustomerId":cust_id,}})
        return True'''

    '''def create_update_customer(self,cr,uid,dict,context=None):
        print "dict----------------",dict,type(dict)
        customer_id=dict.get('CustomerId',False)
        pro_id=False
        name=""
        vals={}
        f_name,l_name='',''
        if dict.has_key('FirstName') or dict.has_key('LastName'):
            name=dict.get('FirstName','')+' '+dict.get('LastName','')
            vals.update({'name':name})

        if dict.has_key('Email'):
            emailid=dict.get('Email')
            cr.execute('select id from res_partner where emailid= %s', (emailid,))
            if_exist = filter(None, map(lambda x:x[0], cr.fetchall()))
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

        if dict.has_key('ProfileDetails'):
	    profile_vals={}
	    print "inside--------------",dict.get('ProfileDetails')
            dict_profile=dict.get('ProfileDetails')
            if dict_profile.has_key('Gender'):
                gender=dict_profile.get('Gender')
                if gender =='M' or gender =='F':
                    profile_vals.update({'gender':gender})
                else:
                    return json.dumps({"body":{"code":False,'message': "Incorrect Data for Gender",}})

            if dict_profile.has_key('DOB'):
                dob=dict_profile.get('DOB')
                try:
                    datetime.datetime.strptime(dob, '%Y-%m-%d')
                except ValueError:
                    return json.dumps({"body":{"code":False,'message': "Incorrect data format, should be YYYY-MM-DD",}})
                profile_vals.update({'dob':dob})

            if dict_profile.has_key('PlayerTag'):
                player_tag=dict_profile.get('PlayerTag')
                profile_vals.update({'player_tag':player_tag})

            if dict_profile.has_key('AgeRating'):
                age_rating=dict_profile.get('AgeRating')
                profile_vals.update({'age_rating':age_rating})

            pro_id=self.pool.get('user.profile').create(cr,uid,profile_vals)
	    print "proid-------------------------------------",pro_id



        if customer_id:
            self.write(cr,uid,[customer_id],vals)
            if pro_id:
                self.pool.get('user.profile').write(cr,uid,[pro_id],{'partner_id':int(customer_id)})
            return json.dumps({'code':True,'message':"Success","CustomerId":customer_id,})

        else:
            if if_exist!=[]:
                return json.dumps({"body":{"code":False,'message': "The Email-id Already exists.",}})
            cust_id=self.create(cr,uid,vals)
	    print "cust_id-----------------",cust_id
            if pro_id:
		
                self.pool.get('user.profile').write(cr,uid,[pro_id],{'partner_id':cust_id},context=context)
            return json.dumps({"body":{'code':True,'message':"Success","CustomerId":cust_id,}})'''


    def create_update_customer(self,cr,uid,dict,context=None):
        print "dict----------------",dict,type(dict)
        customer_id=dict.get('CustomerId',False)
        pro_id=False
        name=""
        profile_vals={}
        vals={}
        f_name,l_name='',''

	if customer_id:
            cr.execute('select id from res_partner where id= %s', (customer_id,))
            if_present = filter(None, map(lambda x:x[0], cr.fetchall()))
            if if_present==[]:
                return json.dumps({"body":{'code':False,'message':"CustomerId Not Present.",}})

            active=self.browse(cr,uid,customer_id).active
            if active != True:
                return json.dumps({'Code':False,'messsage':'The Customer is Deactivated.'})


        if dict.has_key('FirstName') or dict.has_key('LastName'):
            name=dict.get('FirstName','')+' '+dict.get('LastName','')
            vals.update({'name':name})

        if dict.has_key('Email'):
            emailid=dict.get('Email')
            cr.execute('select id from res_partner where emailid= %s', (emailid,))
            if_exist = filter(None, map(lambda x:x[0], cr.fetchall()))
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
                return json.dumps({"body":{"code":False,'message': "Incorrect data format, should be YYYY-MM-DD",}})
            vals.update({'dob':dob})


        if customer_id:
            self.write(cr,uid,[customer_id],vals)
            return json.dumps({'code':True,'message':"Success","CustomerId":customer_id,})

        else:
            if if_exist!=[]:
                return json.dumps({"body":{"code":False,'message': "The Email-id Already exists.",}})
            cust_id=self.create(cr,uid,vals)
            return json.dumps({"body":{'code':True,'message':"Success","CustomerId":cust_id,}})


    def create_update_profile(self,cr,uid,dict,context=None):
        print "dict----------------",dict,type(dict)
        pro_id=False
        name=""
        profile_vals={}

        profile_id=dict.get('ProfileId',False)

        customer_id=dict.get('CustomerId',False)

	if customer_id and not profile_id:

            user_profile_ids=self.browse(cr,uid,customer_id).user_profile_ids
            if user_profile_ids!=[]:
                return json.dumps({"body":{'code':False,'message':"Profile Already Created for this Customer.",}})


        if customer_id:

	    cr.execute('select id from res_partner where id= %s', (customer_id,))
            if_exist = filter(None, map(lambda x:x[0], cr.fetchall()))
            if if_exist==[]:
                return json.dumps({"body":{'code':False,'message':"CustomerId Not Present.",}})

	    active=self.browse(cr,uid,customer_id).active
            if active != True:
                return json.dumps({'Code':False,'messsage':'The Customer is Deactivated.'})


            profile_vals.update({'partner_id':customer_id})
        else:
            return json.dumps({"body":{'code':False,'message':"Please provide the CustomerId",}})
        
        
        if dict.has_key('PlayerTag'):
            player_tag=dict.get('PlayerTag')
            profile_vals.update({'player_tag':player_tag})
        if dict.has_key('DOB'):
            dob=dict.get('DOB')
            try:
                datetime.datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                return json.dumps({"body":{"code":False,'message': "Incorrect data format, should be YYYY-MM-DD",}})
            profile_vals.update({'dob':dob})


        if dict.has_key('Gender'):
            gender=dict.get('Gender')
            if gender =='M' or gender =='F' or gender =='O':
                profile_vals.update({'gender':gender})
            else:
                return json.dumps({"body":{"code":False,'message': "Incorrect Data for Gender",}})

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
            self.pool.get('user.profile').write(cr,uid,[profile_id],profile_vals)
            return json.dumps({'code':True,'message':"Success","ProfileId":profile_id,})

        else: 
            pro_id=self.pool.get('user.profile').create(cr,uid,profile_vals)
            return json.dumps({"body":{'code':True,'message':"Success","ProfileId":pro_id,}})




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
                return json.dumps({"body":{"code":True,"message":"Success","UserName": username, "Password": password, "CustomerId":partner_id[0],"FirstName":first_name,"LastName":last_name}})
            else:
                return json.dumps({"body":{"code":False,"message":"Incorrect Password"}})

#            return result
        return json.dumps({"body":{"code":False,"message":"Incorrect UserName"}})



    def get_account_info(self, cr, uid, dict, context=None):
        print "dict-----------------------",dict
        res={}
        if dict.get('CustomerId',False):
            cust_id=dict.get('CustomerId')
            print "cust_id-------------",cust_id
            pat_obj=self.browse(cr,uid,int(cust_id))
            if pat_obj:
		active=pat_obj.active
                if active != True:
                    return json.dumps({'Code':False,'messsage':'The Customer is Deactivated.'})
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
			    print "!!!!!!!!!!!!!!!!!!!!!!!!",each
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


    def update_billing_info(self, cr, uid, dict,context=None):
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
                vals.update({'state_id':state_id})

            if billing_add.has_key('Country'):
                country=billing_add.get('Country')
                cr.execute('select id from res_country where code = %s', (state,))
                country_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                vals.update({'country_id':country_id})

            if billing_add.has_key('Zip'):
                zip=billing_add.get('Zip')
                vals.update({'zip':zip})
            try:
                self.write(cr,uid,[customer_id],vals)
            except Exception ,e:
                return json.dumps({'Code':False,'messsage':'The Address is not valid.'})


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
        
        

        return json.dumps({'Code':True,'messsage':'Success.'})


    '''def update_billing_info(self, cr, uid, dict,context=None):
        print "dict----------",dict
        cust_profile_id=''
        customer_id=dict.get('CustomerId',False)
        if not customer_id:
            return json.dumps({"body":{'code':False,'message':"Please provide the CustomerId",}})
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
                vals.update({'state_id':state_id})

	    if billing_add.has_key('Country'):
                country=billing_add.get('Country')
                cr.execute('select id from res_country where code = %s', (state,))
                country_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                vals.update({'country_id':country_id})

            if billing_add.has_key('Zip'):
                zip=billing_add.get('Zip')
                vals.update({'zip':zip})

            try:
                self.write(cr,uid,[customer_id],vals)
            except Exception ,e:
                return json.dumps({'Code':False,'messsage':'The Address is not valid.'})

        return json.dumps({'Code':True,'messsage':'Success.'})'''


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

