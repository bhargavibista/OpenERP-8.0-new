# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import datetime
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
import calendar
from openerp.tools.misc import attrgetter
from openerp.addons.base_external_referentials.external_osv import ExternalSession
from openerp.addons.magentoerpconnect import magerp_osv
DEBUG = True
from openerp.tools.translate import _
import random
from openerp import netsvc
import string
import ast
import uuid
from validate_email import validate_email
import md5
import logging
import re
_logger = logging.getLogger(__name__)
class res_partner(magerp_osv.magerp_osv):
    _inherit="res.partner"
    _columns = {
    'email': fields.char('Email', size=240,required=False),
#    'name': fields.char('Name', size=128, select=True),
#    'zip': fields.related('address', 'zip', type='char', size=256, string='ZIP'),
#    'phone_no': fields.related('address', 'phone', type='char', size=256, string='Phone Number'),
    'agreement_policy':fields.one2many('res.partner.policy','agmnt_partner','Agreement'),
    'billing_date':fields.date('Billing Date'),
    'start_date':fields.date('Start Date'),
    'payment_policy': fields.selection([
            ('pro', 'Pro Rate'),
            ('eom', 'End of Month')
            ], 'Payment Policy', help="Pro-Reta option generates invoice after one month from current date.\n End of month policy generates \n invoices at every end of month. "),
    'check_all': fields.boolean('Check All'),
    'high_speed_internet': fields.selection([
            ('yes', 'Yes'),
            ('no', 'No')
            ], 'CHSI'),
    'cable': fields.selection([
            ('yes', 'Yes'),
            ('no', 'No')
            ], 'Essential Tier Cox Cable'),
    'ref': fields.char('Customer No', size=64, select=1),
#    'cable': fields.boolean('Essential Tier Cox Cable'),
#    'flare_account': fields.boolean('Flare Account'),
    }

    def update_policy_datas(self,cr,uid,ids,context):
        policy_obj=self.pool.get("res.partner.policy")
        return_obj=self.pool.get("return.order")
        error_obj=self.pool.get("partner.payment.error")
        sale_obj=self.pool.get("sale.order")
#        inactive_services=policy_obj.search(cr,uid,[('active_service','=',False)])
        cr.execute("select id from res_partner_policy where active_service =False and create_date >= '2013-11-01'")
        inactive_services = filter(None, map(lambda x:x[0], cr.fetchall()))
        print"inactive_services--------",len(inactive_services)
        for each in policy_obj.browse(cr,uid,inactive_services):
#            print"eachhhhhhhhhhhh---",each.agmnt_partner
            print"sale_order---",each.sale_order
#            print"cance_date---",each.cancel_date
            
#            return_order=return_obj.search(cr,uid,[('partner_id','=',each.agmnt_partner.id),('return_type','=','car_return')])
#            payment_error=error_obj.search(cr,uid,[('partner_id','=',each.agmnt_partner.id),('active_payment','=',False)])
            if each.sale_order:
                sale_id=sale_obj.search(cr,uid,[('name','=',each.sale_order)])
                print"sale_id--------------",sale_id
                return_order=return_obj.search(cr,uid,[('linked_sale_order','=',sale_id[0]),('return_type','=','car_return')])
                
                if return_order:
                    print"return_order-========",return_order
                    for each_return in return_obj.browse(cr,uid,return_order):
    #                    print"each_error----",each_error
                        if each_return.date_order :
    #                        print"hi------------",each_error,each_error.invoice_date
                            date_order=each_return.date_order
                            return_date=datetime.datetime.strptime(date_order, '%Y-%m-%d').date()
    #                        print"typweeeeeee",type(suspension_date)
                            each.write({'return_date':date_order})
                payment_error=error_obj.search(cr,uid,[('invoice_name','ilike',each.sale_order),('active_payment','=',False)])
                
                if payment_error:
                    print"payment_error-========+++",payment_error
                    for each_error in error_obj.browse(cr,uid,payment_error):
    #                    print"each_error----",each_error
                        if each_error.invoice_id and each_error.invoice_id.state!="paid":
    #                        print"hi------------",each_error,each_error.invoice_date
                            invoice_date=each_error.invoice_date
                            suspension_date=datetime.datetime.strptime(invoice_date, '%Y-%m-%d').date() + relativedelta(months=1)
    #                        print"typweeeeeee",type(suspension_date)
                            each.write({'suspension_date':suspension_date})
            
                
            
#        fdfsdsd
        return True

    def return_cancel_reason_extract(self,string):
        string = string.replace("\\",'')
#        string = string.replace("\'",'')
        dict_val = ast.literal_eval(string)
        return dict_val 
    def show_serial_number(self,cr,uid,ids,context):
        if ids:
            search_contacts = self.search(cr,uid,[('parent_id','in',ids)])
            if search_contacts:
                ids += search_contacts
            if len(ids) > 1:
                cr.execute("select production_lot from stock_move_lot where stock_move_id in (select id from stock_move where picking_id in (select id from stock_picking where partner_id in %s))"%(tuple(ids),))
            else:
                cr.execute("select production_lot from stock_move_lot where stock_move_id in (select id from stock_move where picking_id in (select id from stock_picking where partner_id =%s))"%(ids[0]))
            lot_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if lot_ids:
                res = self.pool.get('ir.model.data')
                tree_res = res.get_object_reference(cr, uid, 'stock', 'view_production_lot_tree')
                tree_id = tree_res and tree_res[1] or False
                form_res = res.get_object_reference(cr, uid, 'stock', 'view_production_lot_form')
                form_id = form_res and form_res[1] or False
                return {
                        'name': _('Serial Numbers'),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'stock.production.lot',
                        'res_id': False,
                        'view_id': False,
                        'views': [(tree_id, 'tree'), (form_id, 'form')],
                        'target': 'current',
                        'type': 'ir.actions.act_window',
                        'domain': [('id','in',lot_ids)]
                        }	
    def onchange_name(self,cr,uid,ids,name,context={}):
       res={}
       warning = {'title': _('Warning!')}
       if name:
           name=name.split(' ')
           if len(name) < 2:
               warning.update({'message' : _('Please enter the last name')})
	   elif len(name) >= 2 and name[1]=='':
              warning.update({'message' : _('Please enter the last name')})
           if warning and warning.get('message'):
               res['warning'] = warning
	       res['value'] = {}
	       res['value']['name'] = False	 
	      
       return res
    def onchange_emailid(self,cr,uid,ids,emailid,context={}):
        res,res['value'],res['warning']={},{},{}
        warning = {'title': _('Warning!')}
        if emailid:
            if len(emailid) > 7:
		if not re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", emailid):
                    warning = {
                    'title': _('Invalid Email'),
                    'message' : _('Please enter a valid email address.......')
                    }
                    res['value']['emailid'] =False
                    res['warning'] = warning
                cr.execute("select id from res_partner where emailid ilike '%s'"%(emailid))
                duplicate_email = map(lambda x: x[0], cr.fetchall())
                if duplicate_email:
                    warning.update({'message' : _('Email Already Exists..............................')})
                    res['warning'] = warning
                    res['value']['emailid'] = False
        return res

    def get_website_magento_id(self,cr,uid,oe_website_ids):
        if len(oe_website_ids) > 1:
            cr.execute("select name from ir_model_data where model = 'external.shop.group' and res_id in %s"%(tuple(oe_website_ids),))
        else:
            cr.execute("select name from ir_model_data where model = 'external.shop.group' and res_id = %s"%(oe_website_ids[0]))
        website_magento_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if website_magento_id:
            website_magento_id = [int(name.split('/')[1]) for name in website_magento_id if '/' in name]
        return website_magento_id
    
    def subscriber_list(self,cr,uid):
        policy_obj = self.pool.get('res.partner.policy')
        partner_obj = self.pool.get('res.partner')
        line_obj = self.pool.get('sale.order.line')
        result = {}
        search_partner = partner_obj.search(cr,uid,['|',('ref','!=',''),('ref','!=',False)],order='id')
        print"search_partner-----",search_partner
	_logger.info('Create a with vals kuldeeeeeepppppp %s', len(search_partner))
#        search_partner = [4525]
        search_partner.sort()
        if search_partner:
            for each_partner in partner_obj.browse(cr,uid,search_partner):
                cr.execute("select id from res_partner_policy where (create_date is null or create_date >= '2013-10-31') and (do_not_show=False or do_not_show is null) and service_name not ilike '%s' and agmnt_partner=%s order by id desc"%('%casual%',each_partner.id))
                search_active_policy = filter(None, map(lambda x:x[0], cr.fetchall()))
                print "search_active_policy",search_active_policy
                if search_active_policy:
                    for each_policy in policy_obj.browse(cr,uid,search_active_policy):
                        price,subscription_data,cancel_return_reason,cancel_source,line_id_brw = 0.0,[],'','',False
                        emailid =  each_partner.emailid
                        is_valid = validate_email(emailid)
                        if is_valid:
                            if each_policy.sale_line_id:
                                line_id_brw = line_obj.browse(cr,uid,each_policy.sale_line_id)
                                price = (line_id_brw.product_id.list_price) * (line_id_brw.product_uom_qty)
                            status = ('Active' if each_policy.active_service else 'Inactive')
                            additional_info = each_policy.additional_info
                            if additional_info:
                                string,cancel_source = "\\'",'COX'
                                additional_info = str(additional_info).replace(string,"'").replace("\\\"","'")
                                additional_info = ast.literal_eval(additional_info)
                                if isinstance(additional_info, (dict)):
                                    cancel_return_reason = additional_info.get('cancel_return_reason','')
                            subscription_data.append({
                            'email':emailid,
                            'package_name':each_policy.service_name,
                            #Extra Code
                            'from_package_id':('service'+ str(each_policy.from_package_id.product_id.magento_product_id) if each_policy.from_package_id else ''),
                            ###
                            'package_id':('service'+str(each_policy.product_id.magento_product_id) if each_policy.product_id else each_policy.service_name),
                            'price':float(price),
                            'customer_id' : each_partner.ref,
                            'status':status,
                            'demo_account':(False if line_id_brw else True),
                            'start_date':each_policy.start_date,
                            'suspension_date':(each_policy.suspension_date if each_policy.suspension_date else ''),
                            'return_date':(each_policy.return_date if each_policy.return_date else ''),
                            'cancel_date':(each_policy.cancel_date if each_policy.cancel_date else ''),
                            'cancel_reason':cancel_return_reason,
                            'cancel_source' : cancel_source,
                            })
                            if str(each_partner.ref) not in result.iterkeys():
                                if line_id_brw and not each_policy.start_date:
                                    continue
                                result[str(each_partner.ref)] = subscription_data
                            else:
                                value = result[str(each_partner.ref)]
                                if line_id_brw and not each_policy.start_date:
                                    continue
                                result[str(each_partner.ref)]  = value + subscription_data
        print "resulut",result                                
        return result

    def forgot_password(self,cr,uid,user_id,customerId):
        referential_obj = self.pool.get('external.referential')
        website_obj = self.pool.get('external.shop.group')
        partner_obj = self.pool.get('res.partner')
        sale_obj = self.pool.get('sale.order')
        search_referential = referential_obj.search(cr,uid,[])
        customer_id,partner_id='',''
        if search_referential:
            attr_conn = False
            referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
            try:
                attr_conn = referential_id_obj.external_connection(True)
                search_default_website = website_obj.search(cr,uid,[])
                if search_default_website:
                    website_ids = self.get_website_magento_id(cr,uid,search_default_website)
                    if customerId:
                        customer_id=customerId
                        partner_id = self.pool.get('res.partner').search(cr,uid,[('ref','=',customer_id)])
                    elif user_id:
                        result = attr_conn.call('ol_customer.customerExists',[user_id,website_ids])
                        if result.get('Id'):
                            customer_id  =  result.get('Id')
                            partner_id = partner_obj.search(cr,uid,[('ref','=',result.get('Id'))])
                    if partner_id:
                        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
                        salt = uuid.uuid4()
                        hash_string = md5.md5(str(salt)[:2]+password).hexdigest()
                        password_hash = hash_string + ':' + str(salt)[:2]
                        data = {'password_hash': password_hash}
                        attr_conn.call('customer.update',[customer_id,data])
                        cr.execute("update res_partner set magento_pwd = '%s' where id=%d"%(password,partner_id[0]))
                        cr.commit()
                        partner_id_obj = partner_obj.browse(cr,uid,partner_id[0])
                        sale_obj.email_to_customer(cr,uid,partner_id_obj,'res.partner','forgot_password',partner_id_obj.emailid,{})
                        return True
            except Exception, e:
                #print "str",e
                return False
    def getsubscriptioninfo(self,cr,uid,emailid,customerId):
        if emailid or customerId:
            policy_obj = self.pool.get('res.partner.policy')
            partner_obj = self.pool.get('res.partner')
            line_obj = self.pool.get('sale.order.line')
            result = {}
            customer_id,partner_id='',''
            referential_obj = self.pool.get('external.referential')
            search_referential = referential_obj.search(cr,uid,[])
            if search_referential:
                attr_conn = False
                referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
                try:
                    attr_conn = referential_id_obj.external_connection(True)
                except Exception, e:
                    print "Error in URLLIB with connection",str(e)
#
                if attr_conn:
#                    partner_id = self.pool.get('res.partner').search(cr,uid,[('emailid','ilike',emailid)])
#                    ids_obj=self.pool.get('res.partner').browse(cr,uid,partner_id[0])
                    search_default_website = self.pool.get('external.shop.group').search(cr,uid,[])
                    print"websites---------------",search_default_website
                    website_ids = self.get_website_magento_id(cr,uid,search_default_website)
#                    website_id = self.pool.get('external.shop.group').oeid_to_extid(cr, uid, websites,websites)#will give Website magento ID
                    if customerId:
                        customer_id=customerId
                        partner_id = self.pool.get('res.partner').search(cr,uid,[('ref','=',customer_id)])
                    elif emailid:
                        customer_id = attr_conn.call('ol_customer.customerExists',[emailid,website_ids])
                        if customer_id:
                            customer_id  =  customer_id.get('Id')
                            partner_id = self.pool.get('res.partner').search(cr,uid,[('ref','=',customer_id)])
                    print"Partner_id",partner_id,customer_id
                    if partner_id:
                        search_services = policy_obj.search(cr,uid,[('agmnt_partner','in',partner_id),('do_not_show','=',False),('service_name','not ilike','%casual%')])
        #		search_services = policy_obj.search(cr,uid,[('agmnt_partner','in',partner_id),('service_name','ilike','%play%')])
                        if search_services:
                            search_services.sort()
                            for each_policy in policy_obj.browse(cr,uid,search_services):
                                price,subscription_data,cancel_return_reason,cancel_source,line_id_brw = 0.0,[],'','',False
                                if each_policy.sale_line_id:
                                    line_id_brw = line_obj.browse(cr,uid,each_policy.sale_line_id)
                                    price = (line_id_brw.product_id.list_price) * (line_id_brw.product_uom_qty)
				else:
                                   price = (each_policy.product_id.list_price)
                                status = ('Active' if each_policy.active_service else 'Inactive')
                                additional_info = each_policy.additional_info
                                if additional_info:
                                    string,cancel_source = "\\'",'COX'
                                    additional_info = str(additional_info).replace(string,"'").replace("\\\"","'")
                                    additional_info = ast.literal_eval(additional_info)
                                    if isinstance(additional_info, (dict)):
                                        cancel_return_reason = additional_info.get('cancel_return_reason','')
                                subscription_data.append({
                                'email':emailid if emailid else partner_obj.browse(cr,uid,partner_id[0]).emailid,
                                'package_name':each_policy.service_name,
                                #Extra Code
                                        'from_package_id':('service'+ str(each_policy.from_package_id.product_id.magento_product_id) if each_policy.from_package_id else ''),
                                ###
                                'package_id':('service'+ str(each_policy.product_id.magento_product_id) if each_policy.product_id else each_policy.service_name),
                                'price':float(price),
                                'customer_id' : customer_id,
                                'status':status,
                                'demo_account':(False if line_id_brw else True),
                                'start_date':each_policy.start_date,
                                'suspension_date':(each_policy.suspension_date if each_policy.suspension_date else ''),
                                'return_date':(each_policy.return_date if each_policy.return_date else ''),
                                'cancel_date':(each_policy.cancel_date if each_policy.cancel_date else ''),
                                'cancel_reason':cancel_return_reason,
                                'cancel_source' : cancel_source,
                                })
                                if customer_id not in result.iterkeys():
                                    if line_id_brw and not each_policy.start_date:
                                        continue
                                    result[customer_id] = subscription_data
                                else:
                                    value = result[customer_id]
                                    if line_id_brw and not each_policy.start_date:
                                        continue
                                    result[customer_id]  = value + subscription_data
            return result

    def getsubsriptionstatus(self,cr,uid,user_id):
        if user_id:
            partner_obj = self.pool.get('res.partner')
            service_obj = self.pool.get('res.partner.policy')
            partner_id = partner_obj.search(cr,uid,[('emailid','ilike',user_id)])
            response = {}
            response['service_level'] = 'basic'
            if partner_id:
                search_services = service_obj.search(cr,uid,[('agmnt_partner','=',partner_id[0]),('active_service','=',True)])
                if search_services:
                    service_brw = service_obj.browse(cr,uid,search_services)
                    for each_service in service_brw:
                        response['status'] = 'active'
                        lower_service_name = each_service.service_name.lower()
                        if 'advance' in lower_service_name:
                            response['service_level'] = 'advance'
                        elif 'basic' in lower_service_name:
                            if response.get('service_level') != 'advance':
                                response['service_level'] = 'basic'
                else:
                    response['status'] = 'inactive'
            return response
    def authenticate_user(self,cr,uid,user_id,password,hash_pwd):
        result  = []
	vals={}
        referential_obj = self.pool.get('external.referential')
        website_obj = self.pool.get('external.shop.group')
        partner_obj = self.pool.get('res.partner')
	partner_log_obj=self.pool.get('res.partner.auth.log')
        search_referential = referential_obj.search(cr,uid,[])
	search_partner = partner_obj.search(cr,uid,[('emailid','ilike',user_id)])
	login_time=datetime.datetime.today() 
        if search_referential:
            attr_conn = False
            referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
	    _logger.info("Tried to login with EmailId %s and Password %s", user_id,password)
            try:
                attr_conn = referential_id_obj.external_connection(True)
                search_default_website = website_obj.search(cr,uid,[])
                if search_default_website:
                    website_ids = self.get_website_magento_id(cr,uid,search_default_website)
#		    search_partner = partner_obj.search(cr,uid,[('emailid','ilike',user_id)])
#		    if search_partner:
#			result={'encrypted_password': 'ZmwyNDc2', 'customer_id': '', 'username_match': True, 'password_match': True}	
#		    else:
#			result = {'encrypted_password': '', 'customer_id': '', 'username_match': False, 'password_match': False}	
                    result = attr_conn.call('ol_customer.authenticate_customer',[user_id,password,website_ids,hash_pwd])
		    if result:
                        vals={
                            'partner_id':search_partner[0] if search_partner else False,
                            'user_id':user_id,
                            'username_match':result.get('username_match',False),
                            'password_match':result.get('password_match',False),
                            'encrypted_password':result.get('encrypted_password',False),
                            'login_time':login_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'customer_id':result.get('customer_id',False),
			    'response_result':result,
                        }
                        partner_log_obj.create(cr,uid,vals)
                        _logger.info("Sucessful login with Emailid %s ", user_id)
#                    if result.get('customer_id'):
#                        partner_id = partner_obj.search(cr,uid,[('ref','=',result.get('customer_id'))])
#                        if partner_id:
#                            cr.execute("update res_partner set emailid = '%s' where id=%d"%(user_id,partner_id[0]))
#                            cr.commit()
                    return result
            except Exception, e:
		_logger.info("Error occured %s",str(e))
                #print "e",str(e)
#		search_partner = partner_obj.search(cr,uid,[('emailid','ilike',user_id)])
        	if search_partner:
              		result={'encrypted_password': 'ZmwyNDc2', 'customer_id': '', 'username_match': True, 'password_match': True}
	        else:
        	        result = {'encrypted_password': '', 'customer_id': '', 'username_match': False, 'password_match': False}
		if result:
                    vals={
                                'partner_id':search_partner[0] if search_partner else False,
                                'user_id':user_id,
                                'username_match':result.get('username_match',False),
                                'password_match':result.get('password_match',False),
                                'encrypted_password':result.get('encrypted_password',False),
                                'login_time':login_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'customer_id':result.get('customer_id',False),
                                'login_error':str(e),
				'response_result':result,
                            }
                    partner_log_obj.create(cr,uid,vals)
                    _logger.info("Sucessful login with Emailid %s ", user_id)
        return result
    #Function is inherited because want to change email id if it gets changed in OE it should 
    #change on magento side also.
    def write(self,cr,uid,ids,vals,context={}):
        updated,new_emailid,ids_obj = False,'',False
	#authorize_net_config = self.pool.get('authorize.net.config')
        #config_ids =authorize_net_config.search(cr,uid,[])
        if ids:
            if type(ids) in [int, long]:
                ids = [ids]
            if vals.get('emailid','') and not vals.get('auto_import',False):
                ids_obj = self.browse(cr,uid,ids[0])
                if ids_obj.ref:
                    referential_obj = self.pool.get('external.referential')
                    search_referential = referential_obj.search(cr,uid,[])
                    if search_referential:
                        attr_conn = False
                        referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
                        try:
                            attr_conn = referential_id_obj.external_connection(True)
                        except Exception, e:
                            #print "Error in URLLIB",str(e)
#                            self.log(cr,uid,ids[0],'Error while connecting with Magento')
                            vals.update({'emailid':ids_obj.emailid})
                        if attr_conn:
                            website_id = self.pool.get('external.shop.group').oeid_to_extid(cr, uid, ids_obj.website_id,ids_obj.website_id.id)#will give Website magento ID
                            customer_id = attr_conn.call('ol_customer.customerExists',[vals.get('emailid',''),website_id,ids_obj.name])
                            if customer_id:
                                raise osv.except_osv(_('Error !'),_('Customer with these Email ID already Exists On Magento'))
                            return_val = attr_conn.call('customer.update',[ids_obj.ref,{'email':vals.get('emailid','')}])
                            updated = True
                            new_emailid = vals.get('emailid','')
                        
        res = super(res_partner, self).write(cr, uid, ids,vals, context=context)
        if updated == True:
            if (new_emailid) and (ids_obj):
		#config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                #print "config_objconfig_objconfig_obj",config_obj
                #profile_id=ids_obj.customer_profile_id
                #if profile_id:
		   # print"profile idddddddddddddddddddd",profile_id 
                    #auth_resp=authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',profile_id)
                    #if auth_resp:
                      #  auth_email_id=auth_resp.get('email')
		 #	print"responseeeeeeeeeeeeeeeeeeeeeeeeee",auth_resp,auth_email_id
                  #      if auth_email_id:
                   #         if (new_emailid==auth_email_id):
		#		print"idsssssssssssssssssssssssssssssss",new_emailid,auth_email_id
                 #               warning.update({'message' : _('Email Already Exists.at Authorize end.Enter different emailid.')})
                  #              res['warning'] = warning
                   #             res['value']['emailid'] = False
                    #        else:
                     #           res=authorize_net_config.call(cr,uid,config_obj,'updateCustomerProfileRequest',new_emailid,profile_id)
                                #print "responseresponseresponseresponse.......",res
                self.pool.get('sale.order').email_to_customer(cr,uid,ids_obj,'res.partner','email_change',new_emailid,context)
        return res
        
    #Function is inherited to get openerp partner id based on the email id
    def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None, mapping=None, mapping_id=None, context=None):
        """
        Used in _record_external_resources
        The resource will converted into OpenERP data by using the function _transform_external_resources
        And then created or updated, and an external id will be added into the table ir.model.data

        :param dict resource: resource to convert into OpenERP data
        :param int referential_id: external referential id from where we import the resource
        :param dict defaults: defaults value
        :return: dictionary with the key "create_id" and "write_id" which containt the id created/written
        """
        mapping, mapping_id = self._init_mapping(cr, uid, external_session.referential_id.id, mapping=mapping, mapping_id=mapping_id, context=context)
        written = created = False
        vals = self._transform_one_resource(cr, uid, external_session, 'from_external_to_openerp', resource, mapping=mapping, mapping_id=mapping_id, defaults=defaults, context=context)
        if not vals:
            # for example in the case of an update on existing resource if update is not wanted vals will be {}
            return {}
        referential_id = external_session.referential_id.id
        external_id = vals.get('external_id')
        external_id_ok = not (external_id is None or external_id is False)
        alternative_keys = mapping[mapping_id]['alternative_keys']
        alternative_keys = [] ## Extra Coding because it was searching partner by website_id which is wrong
        existing_rec_id = False
        existing_ir_model_data_id = False
        if external_id_ok:
            del vals['external_id']
        existing_ir_model_data_id, existing_rec_id = self._get_oeid_from_extid_or_alternative_keys\
                (cr, uid, vals, external_id, referential_id, alternative_keys, context=context)

        if not (external_id_ok or alternative_keys):
            external_session.logger.warning(_("The object imported need an external_id, maybe the mapping doesn't exist for the object : %s" %self._name))
        #Extra code Starts here
        if vals.get('emailid'):
            if not existing_rec_id:
                existing_rec_id = self.search(cr, uid, [('emailid','=',vals.get('emailid'))])
        ##Ends here
        if existing_rec_id:
            if isinstance(existing_rec_id, list):
                existing_rec_id = existing_rec_id[0]
        if existing_rec_id:
            if not self._name in context.get('do_not_update', []):
                if self.oe_update(cr, uid, external_session, existing_rec_id, vals, resource, defaults=defaults, context=context):
                    written = True
        else:
            existing_rec_id = self.oe_create(cr, uid,  external_session, vals, resource, defaults, context=context)
            created = True
        if external_id_ok:
            if existing_ir_model_data_id:
                if created:
                    # means the external ressource is registred in ir.model.data but the ressource doesn't exist
                    # in this case we have to update the ir.model.data in order to point to the ressource created
                    self.pool.get('ir.model.data').write(cr, uid, existing_ir_model_data_id, {'res_id': existing_rec_id}, context=context)
            else:
                ir_model_data_vals = \
                self.create_external_id_vals(cr, uid, existing_rec_id, external_id, referential_id, context=context)
                if not created:
                    # means the external resource is bound to an already existing resource
                    # but not registered in ir.model.data, we log it to inform the success of the binding
                    external_session.logger.info("Bound in OpenERP %s from External Ref with "
                                                "external_id %s and OpenERP id %s successfully" %(self._name, external_id, existing_rec_id))

        if created:
            if external_id:
                external_session.logger.info(("Created in OpenERP %s from External Ref with"
                                        "external_id %s and OpenERP id %s successfully" %(self._name, external_id_ok and str(external_id), existing_rec_id)))
            elif alternative_keys:
                external_session.logger.info(("Created in OpenERP %s from External Ref with"
                                        "alternative_keys %s and OpenERP id %s successfully" %(self._name, external_id_ok and str (vals.get(alternative_keys)), existing_rec_id)))
            return {'create_id' : existing_rec_id}
        elif written:
            if external_id:
                external_session.logger.info(("Updated in OpenERP %s from External Ref with"
                                        "external_id %s and OpenERP id %s successfully" %(self._name, external_id_ok and str(external_id), existing_rec_id)))
            elif alternative_keys:
                external_session.logger.info(("Updated in OpenERP %s from External Ref with"
                                        "alternative_keys %s and OpenERP id %s successfully" %(self._name, external_id_ok and str (vals.get(alternative_keys)), existing_rec_id)))
            return {'write_id' : existing_rec_id}
        return {}
    #Function is inherited from the Authorize.net becasue to make current payment profile as active
    #and make another payment profile as inactive from Openerp and also from Magento site
    def cust_profile_payment(self,cr,uid,ids,profile_id,payment_profile_data,context={}):
        ids =int(ids)
        cr.execute("UPDATE res_partner SET customer_profile_id='%s' where id=%d"%(profile_id,ids))
        payment_obj = self.pool.get('custmer.payment.profile')
        active_payment_profile_id = []
        for cc_number in payment_profile_data.iterkeys():
            each_profile = payment_profile_data[cc_number]
            search_payment_profile = payment_obj.search(cr,uid,[('profile_id','=',each_profile),('credit_card_no','=',cc_number)])
            if not search_payment_profile:
                create_payment = payment_obj.create(cr,uid,{'active_payment_profile':True,'profile_id':each_profile,'credit_card_no':cc_number,'customer_profile_id':profile_id})
                active_payment_profile_id.append(create_payment)
                cr.execute('INSERT INTO partner_profile_ids \
                        (partner_id,profile_id) values (%s,%s)', (ids, create_payment))
            else:
                active_payment_profile_id.append(search_payment_profile[0])
        if active_payment_profile_id:
            payment_obj.write(cr,uid,active_payment_profile_id,{'active_payment_profile':True})
            cr.execute("select profile_id from partner_profile_ids where partner_id=%s and profile_id not in %s",(ids,tuple(active_payment_profile_id),))
            in_active_payment_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if in_active_payment_ids:
                payment_obj.write(cr,uid,in_active_payment_ids,{'active_payment_profile':False})
        return True
    def get_magento_group_id(self,cr,uid,context):
        search_general_group = self.pool.get('res.partner.category').search(cr, uid, [('name','ilike','general')])
        if search_general_group:
            return search_general_group[0]
    def get_magento_website_id(self,cr,uid,context):
        search_website = self.pool.get('external.shop.group').search(cr, uid, [])
        if search_website:
            return search_website[0]
    def get_tax_schedule_id(self,cr,uid,context):
        search_tax_schedule = self.pool.get('tax.schedule').search(cr, uid, [])
        if search_tax_schedule:
            return search_tax_schedule[0]
    _defaults={
    'payment_policy':'pro',
    'group_id':get_magento_group_id,
    'website_id':get_magento_website_id,
    'tax_schedule_id':get_tax_schedule_id
    }
    #To Search partner name by Customer Name,Email Id and ZIP
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        search_by_name = []
        if not args:
            args = []
        if name:
            search_by_name = self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
            search_by_emailid = self.search(cr, user, args + [('emailid',operator,name)], limit=limit, context=context)
            search_by_zip = self.search(cr, user, args + [('zip',operator,name)], limit=limit, context=context)
            if search_by_emailid:
                search_by_name = search_by_name + search_by_emailid
            if search_by_zip:
                search_by_name = search_by_name + search_by_zip
        else:
            search_by_name = self.search(cr, user, args, limit=limit, context=context)
        search_by_name = list(set(search_by_name))
        result = self.name_get(cr, user, search_by_name, context=context)
        return result

    def onchange_check_all(self, cr,uid,ids,check_all_data,context=None):
        if check_all_data:
            return {'value':{'high_speed_internet':'yes','cable':'yes','flare_account':check_all_data}}
        else:
            return {'value':{'high_speed_internet':'no','cable':'no','flare_account':check_all_data}}

#    def create(self, cr, uid, vals, context=None):
#        if vals.get('address',False):
#            if vals['address'][0]:
#                defaul_address=vals['address'][0][2]
#                name=''
#                if defaul_address.get('firstname',''):
#                    name=defaul_address.get('firstname')
#                if defaul_address.get('lastname',''):
#                    name=name+' '+defaul_address.get('lastname')
#                if len(name)!=0:
#                    vals['name']=name
#        res = super(res_partner, self).create(cr, uid, vals, context=context)
#        return res

    def export_recurring_profile(self,cr,uid,ids,context={}):
        if ids:
            invoice_id_obj = self.pool.get('account.invoice').browse(cr,uid,ids[0])
            partner_magento_id = invoice_id_obj.partner_id.ref
            referential_obj = self.pool.get('external.referential')
            search_referential = referential_obj.search(cr,uid,[])
            if search_referential:
                referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])
                attr_conn = referential_id_obj.external_connection(DEBUG)
                if attr_conn:
                    billing_data,billing_prod_det,billing_address_info,return_val,magento_incrementid = {},[],'',False,False
                    #Billing Information
                    billing_data['customer_id'] = partner_magento_id
                    billing_data['customer_name'] = invoice_id_obj.partner_id.name
                    billing_data['email'] = invoice_id_obj.partner_id.emailid
                    billing_data['group'] = (invoice_id_obj.partner_id.group_id.name if invoice_id_obj.partner_id.group_id else '')
                    if invoice_id_obj.partner_id:
                        billing_address_info  = (invoice_id_obj.partner_id.street if invoice_id_obj.partner_id.street else '')
                        billing_address_info  += "," + (invoice_id_obj.partner_id.city if invoice_id_obj.partner_id.city else '')
                        billing_address_info  += "," + (invoice_id_obj.partner_id.state_id.name if invoice_id_obj.partner_id.state_id else '')
                        billing_address_info  += "," +(invoice_id_obj.partner_id.zip if invoice_id_obj.partner_id.zip else '')
                        billing_address_info  += "," + (invoice_id_obj.partner_id.country_id.name if invoice_id_obj.partner_id.country_id else '')
                        billing_address_info  += "," + (invoice_id_obj.partner_id.phone if invoice_id_obj.partner_id.phone else '')
                    billing_data['billing_address'] = billing_address_info[:-1]
                    billing_data['status'] = 'Active'
                    billing_data['payment_information'] = 'Authorize.Net'
                    billing_data['next_payment_date'] = ( str(invoice_id_obj.partner_id.billing_date)+" 00:00:00" if invoice_id_obj.partner_id.billing_date else '')
                    billing_data['order_date'] = ( str(invoice_id_obj.date_invoice)+" 00:00:00" if invoice_id_obj.date_invoice else '')
                    #To Set OrderId in the Recurring billing
                    origin = invoice_id_obj.origin
		    origin = str(origin).replace('RB','')
                    if str(origin).find('|') == -1:
                        cr.execute("select magento_incrementid from sale_order where name='%s'"%(origin))
                        magento_incrementid = filter(None, map(lambda x:x[0], cr.fetchall()))
                    else:
                        split_data = str(origin).split('|')
                        cr.execute("select magento_incrementid from sale_order where name in %s"%(tuple(split_data),))
                        magento_incrementid = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if magento_incrementid:
                        order_id = '|'.join(magento_incrementid)
                        if order_id:
                            billing_data['order_id'] = order_id
                    #Billing Product Information
                    for each_line in invoice_id_obj.invoice_line:
                        billing_prod_det.append({'sku':each_line.product_id.default_code,
                        'product_name':each_line.name,
                        'qty':each_line.quantity,
                        'price':each_line.price_unit,
                        'price_subtotal':each_line.price_subtotal,
                        'product_id': each_line.product_id.magento_product_id
                        })
                    billing_data['product_details'] = billing_prod_det
                    try:
                        return_val = attr_conn.call('sales_order.create_recurring_billing', [billing_data])
                    except Exception, e:
                        return e
                    return return_val

    def recurring_billing(self,cr,uid,context={}):
	#print "in recurring billing"
        partner_ids,payment_profile_id,start_date=[],False,''
        sale_obj=self.pool.get('sale.order')
        invoice_obj = self.pool.get('account.invoice')
        if context is None:
            context={}
        if context.get('billing_date',False) and context.get('partner_ids',False):
            today=context.get('billing_date','')
            today=datetime.datetime.strptime(today, "%Y-%m-%d").date()
            partner_ids=context.get('partner_ids')
        else:
            today=datetime.date.today()
        nextmonth = today + relativedelta(months=1)
        days_nextmonth=calendar.monthrange(nextmonth.year,nextmonth.month)[1]
#        days=calendar.monthrange(today.year,today.month)[1]
        if len(partner_ids)==0:
            partner_ids = self.search(cr, uid, [('billing_date','=',str(today))])
        for partner_id in partner_ids:
            partner_obj=self.browse(cr,uid,partner_id)
	    if partner_obj.start_date:	
	            start_date=datetime.datetime.strptime(partner_obj.start_date, "%Y-%m-%d").date()
#        	    print "start_date",start_date
	            if start_date and start_date.day==31:
        	        nextmonth=str(nextmonth.year)+'-'+str(nextmonth.month)+'-'+str(days_nextmonth)
                	nextmonth=datetime.datetime.strptime(nextmonth, "%Y-%m-%d").date()
	            if today.month==2:
        	        nextmonth=str(nextmonth.year)+'-'+str(nextmonth.month)+'-'+str(start_date.day)
                	nextmonth=datetime.datetime.strptime(nextmonth, "%Y-%m-%d").date()
#            nextmonth=datetime.datetime.strptime(nextmonth, "%Y-%m-%d").date()
            maerge_invoice_data=[]
            cr.execute('select id from res_partner_policy where  active_service = True and agmnt_partner = %s  and ((free_trial_date is null) or free_trial_date < (select billing_date from res_partner where id=%s))'% (partner_id,partner_id))
            policies = filter(None, map(lambda x:x[0], cr.fetchall()))
            #print policies
            partner_policy = self.pool.get('res.partner.policy')
            for policy_brw in partner_policy.browse(cr,uid,policies):
                #Extra Code for Checking whether service is cancelled or not
                #Starts here
                cr.execute('select id from cancel_service where sale_id = %s and sale_line_id = %s and partner_policy_id=%s and cancelled=False'%(policy_brw.sale_id,policy_brw.sale_line_id,policy_brw.id))
                policies = filter(None, map(lambda x:x[0], cr.fetchall()))
                ##Ends here
                if not policies:
                    sale_info={}
                    sale_info.update(
                        {'sale_id':policy_brw.sale_id,
                        'line_id':policy_brw.sale_line_id,
                        'order_name': policy_brw.sale_order,
                        'free_trial_date':policy_brw.free_trial_date,
                        'extra_days':policy_brw.extra_days,
                        'policy_id':policy_brw.id
                        })
                    if sale_info:
                        maerge_invoice_data+=[sale_info]
            if len(maerge_invoice_data)!=0:
                cr.execute("select profile_id,credit_card_no from custmer_payment_profile where customer_profile_id='%s' and active_payment_profile=True"%(str(partner_obj.customer_profile_id)))
                payment_profile_data=cr.dictfetchall()
                if payment_profile_data:
                    payment_profile_id=payment_profile_data[0].get('profile_id')
                    context['cc_number'] = payment_profile_data[0].get('credit_card_no')
                context['partner_id_obj'] = partner_obj
		#print "action_invoice_merge",sale_info	
                res_id=sale_obj.action_invoice_merge(cr, uid, maerge_invoice_data, today, nextmonth, start_date,payment_profile_id, context=context)
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
        return True
res_partner()

'''class res_partner_address(osv.osv):
    _inherit="res.partner"
    def _get_default_country(self, cr, uid, context=None):
        country_id = self.pool.get('res.country').search(cr,uid,[('code','ilike','US')])
        if country_id:
            return country_id[0]

    def _get_default_state(self, cr, uid, context=None):
        state_id = self.pool.get('res.country.state').search(cr,uid,[('code','ilike','CA')])
        if state_id:
            return state_id[0]
    
    _columns = {
    'email': fields.char('E-Mail', size=240),
    }
    _defaults= {
    'type':'default',
    'country_id': _get_default_country,
    'state_id': _get_default_state
    }
    def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None, mapping=None, mapping_id=None, context=None):
        """
        Used in _record_external_resources
        The resource will converted into OpenERP data by using the function _transform_external_resources
        And then created or updated, and an external id will be added into the table ir.model.data
        :param dict resource: resource to convert into OpenERP data
        :param int referential_id: external referential id from where we import the resource
        :param dict defaults: defaults value
        :return: dictionary with the key "create_id" and "write_id" which containt the id created/written
        """
        mapping, mapping_id = self._init_mapping(cr, uid, external_session.referential_id.id, mapping=mapping, mapping_id=mapping_id, context=context)
        written = created = False
        vals = self._transform_one_resource(cr, uid, external_session, 'from_external_to_openerp', resource, mapping=mapping, mapping_id=mapping_id, defaults=defaults, context=context)
        if not vals:
            # for example in the case of an update on existing resource if update is not wanted vals will be {}
            return {}
        referential_id = external_session.referential_id.id
        external_id = vals.get('external_id')
        external_id_ok = not (external_id is None or external_id is False)
        alternative_keys = mapping[mapping_id]['alternative_keys']
        alternative_keys = [] ## Extra Coding because it was searching partner by website_id which is wrong
        existing_rec_id = False
        existing_ir_model_data_id = False
        if external_id_ok:
            del vals['external_id']
        existing_ir_model_data_id, existing_rec_id = self._get_oeid_from_extid_or_alternative_keys\
                (cr, uid, vals, external_id, referential_id, alternative_keys, context=context)

        if not (external_id_ok or alternative_keys):
            external_session.logger.warning(_("The object imported need an external_id, maybe the mapping doesn't exist for the object : %s" %self._name))
        #Extra code Starts here
        vals['auto_import'] = True
        if existing_rec_id:
            existing_rec_id = existing_rec_id[0]
        if existing_rec_id:
            if not self._name in context.get('do_not_update', []):
                if self.oe_update(cr, uid, external_session, existing_rec_id, vals, resource, defaults=defaults, context=context):
                    written = True
        else:
            existing_rec_id = self.oe_create(cr, uid,  external_session, vals, resource, defaults, context=context)
            created = True
        if external_id_ok:
            if existing_ir_model_data_id:
                if created:
                    # means the external ressource is registred in ir.model.data but the ressource doesn't exist
                    # in this case we have to update the ir.model.data in order to point to the ressource created
                    self.pool.get('ir.model.data').write(cr, uid, existing_ir_model_data_id, {'res_id': existing_rec_id}, context=context)
            else:
                ir_model_data_vals = \
                self.create_external_id_vals(cr, uid, existing_rec_id, external_id, referential_id, context=context)
                if not created:
                    # means the external resource is bound to an already existing resource
                    # but not registered in ir.model.data, we log it to inform the success of the binding
                    external_session.logger.info("Bound in OpenERP %s from External Ref with "
                                                "external_id %s and OpenERP id %s successfully" %(self._name, external_id, existing_rec_id))
        if created:
            if external_id:
                external_session.logger.info(("Created in OpenERP %s from External Ref with"
                                        "external_id %s and OpenERP id %s successfully" %(self._name, external_id_ok and str(external_id), existing_rec_id)))
            elif alternative_keys:
                external_session.logger.info(("Created in OpenERP %s from External Ref with"
                                        "alternative_keys %s and OpenERP id %s successfully" %(self._name, external_id_ok and str (vals.get(alternative_keys)), existing_rec_id)))
            return {'create_id' : existing_rec_id}
        elif written:
            if external_id:
                external_session.logger.info(("Updated in OpenERP %s from External Ref with"
                                        "external_id %s and OpenERP id %s successfully" %(self._name, external_id_ok and str(external_id), existing_rec_id)))
            elif alternative_keys:
                external_session.logger.info(("Updated in OpenERP %s from External Ref with"
                                        "alternative_keys %s and OpenERP id %s successfully" %(self._name, external_id_ok and str (vals.get(alternative_keys)), existing_rec_id)))
            return {'write_id' : existing_rec_id}
        return {}
    
    def write(self, cr, uid, ids, vals, context=None):
        if ids:
            name=''
            if type(ids) in [int, long]:
                ids = [ids]
            address_obj=self.browse(cr, uid, ids[0])
            ids=super(res_partner_address, self).write(cr, uid, ids, vals, context=context)
            if 'firstname' in vals and 'lastname' in vals:
                name=vals.get('firstname','')+' '+vals.get('lastname','')
            elif 'firstname' in vals:
                name=vals.get('firstname','')+' '+address_obj.lastname
            elif 'lastname' in vals:
                name=(address_obj.firstname if address_obj.firstname else '')+' '+vals.get('lastname','')
            else:
                name=(address_obj.firstname if address_obj.firstname else '')+' '+(address_obj.lastname if address_obj.firstname else '')
            if address_obj.type=='default':
                partner_id=address_obj.partner_id.id
                self.pool.get('res.partner').write(cr,uid,[partner_id],{'name':name},context)
        return ids
    
res_partner_address()'''

class res_partner_policy(osv.osv):
    _name = "res.partner.policy"
    _rec_name = 'service_name'
    _order = 'start_date desc' 	
    _columns = {
    'sale_order': fields.char('Sale Order Number', size=32),
    'active_service': fields.boolean('Active Service',select=True),
    'product_id' : fields.many2one('product.product','Selected Service'),
    'service_name':fields.related('product_id','name_template',type='char',string='Service Name',store=True),
#    'sale_order_related':fields.many2one('sale.order','Sale Order'),
#    'auth_transaction_id' :fields.related('sale_order_related','auth_transaction_id',type='char',string='Transaction ID',store=True,readonly=True),
#    'cc_number' :fields.related('sale_order_related','cc_number',type='char',string='Credit Card Number',store=True,readonly=True),
#    'authorization_code': fields.related('sale_order_related','authorization_code',type='char',string='Authorization Code',store=True,readonly=True),
#    'customer_payment_profile_id': fields.related('sale_order_related','customer_payment_profile_id',type='char',string='Payment Profile ID',store=True,readonly=True),
    'start_date': fields.date('Start Date', select=True, help="Date on which service is created."),
    'next_billing_date': fields.datetime('Next Billing Date', select=True, help="Date on which next Payment will be generated."),
    'end_date': fields.date('End Date', select=True, help="Date on which service is closed."),
    'free_trial_date': fields.date('Free Trial Date', select=True, help="Date till which free trial is given"),
    'agmnt_partner':fields.many2one('res.partner','Partner'),
    'sale_id':fields.integer('Sale Order Id',help="Sale order id."),
    'sale_line_id':fields.integer('Sale Order Line Id',help="sale order line id."),
    'free_trail_days':fields.integer('Free Trial Months'),
    'extra_days':fields.integer('Extra Days'),
    'cancel_date': fields.date('Cancel Date'),
    'suspension_date': fields.date('Cancel Date'),
    'return_date': fields.date('Cancel Date'),
    'additional_info': fields.text('Additional Information'),
    'last_amount_charged':fields.float('Last Amount Charged'),
    'return_cancel_reason': fields.text('Return/Cancellation Reason'),
    'do_not_show': fields.boolean('Active Service',select=True),
#    'recurring_price':fields.float('Recurring Price'),
    'no_recurring':fields.boolean('No Recurring'),
    'recurring_reminder':fields.boolean('Recurring Reminder'),
    }
########## function to set cancel_date for all customers whose no_recurring is true
    def cancellation_for_no_recurring(self,cr,uid,ids,context=None):
        today=datetime.datetime.now()
#        today='2015-03-01 00:00:00'
#        today=datetime.datetime.strptime(str(today), "%Y-%m-%d %H:%M:%S")
        free_trial_end=today+relativedelta(months=1)
#        policy_ids=self.search(cr,uid,[('no_recurring','=',True),('free_trial_date','>=',today.strftime("%Y-%m-%d")),('free_trial_date','<=',last_day.strftime("%Y-%m-%d"))])
        cr.execute("select id from res_partner_policy where active_service=True and no_recurring=True and recurring_reminder=False\
                and cancel_date is null and return_date is null and suspension_date is null \
                and free_trial_date<='%s'"%(free_trial_end))
        policy_ids=filter(None, map(lambda x:x[0], cr.fetchall()))
#        policy_ids=self.search(cr,uid,[('no_recurring','=',True),('free_trial_date','<=',free_trial_end),('recurring_reminder','=',False),('cancel_date','=','')])
        if policy_ids:
            cancel_service = self.pool.get('cancel.service')
#            context['cancellation_reason']='Recurring Billing is not active'
            for each_policy in self.browse(cr,uid,policy_ids):
                free_trial_date=datetime.datetime.strptime(each_policy.free_trial_date, "%Y-%m-%d")
                #print "free_trial_datefree_trial_date",free_trial_date
                cancellation_date= free_trial_date + relativedelta(days=1)
                #print "cancellation_datecancellation_date",cancellation_date
                cancellation_reason='Opt Out for Recurring Billing.'
                if (not each_policy.cancel_date):
                    cancel_service.create(cr,uid,{'service_name':each_policy.service_name,
                'sale_id': each_policy.sale_id,
                'sale_line_id': each_policy.sale_line_id,
                'partner_policy_id': each_policy.id,
                'cancellation_date': cancellation_date,
				'cancellation_reason': cancellation_reason,
                'cancelled': False
                })
		cr.execute("update res_partner_policy set cancel_date=%s,additional_info=%s,return_cancel_reason=%s where id=%s",(cancellation_date,cancellation_reason,cancellation_reason,each_policy.id))
                email_to = each_policy.agmnt_partner.emailid
                res=self.pool.get('sale.order').email_to_customer(cr, uid, each_policy,'res.partner.policy','recurring_service_alert',email_to,context)
                if res:
                    each_policy.write({'recurring_reminder':True})
        return True
res_partner_policy()

class CountryState(osv.osv):
    _inherit='res.country.state'
    _columns={
        'region_id':fields.char('Region ID',size=120),
    }
CountryState()

class users(osv.osv):
    _inherit = 'res.users'
    _columns={
        'src_location_id' : fields.many2one('stock.location','Source Location'),
        'mag_store_id' : fields.many2one('sale.shop','Magento Store'),
    } 
    def create(self, cr, uid, vals, context={}):
        gid = super(users, self).create(cr, uid, vals, context)
        cr.commit()
        smtp_obj=self.pool.get('email.smtpclient')
        smtp_id=smtp_obj.search(cr,uid,[])
        for each_smtp in smtp_id:
	        cr.execute('''
        	        insert into res_smtpserver_group_rel values(%s,%s)
	            '''%(each_smtp,gid))
        return gid	
users()

class company(osv.osv):
    _inherit='res.company'
    def onchange_reminder_day(self,cr,uid,ids,days,context={}):
        res = {}
        if days:
            if days >= 30:
                res['warning'] = {}
                res['warning']['message'] = 'Days should be less then 30'
                res['value'] = {}
                res['value']['eula_accpt_days'] = 0

        return res
    def call_center_update(self,cr,uid,ids,context={}):
	#Patch for separting of reasons and source from one field
        policy_obj = self.pool.get('res.partner.policy')
        partner_obj = self.pool.get('res.partner')
        search_partner_policy = policy_obj.search(cr,uid,[('additional_info','!=','null')])
        #print "lenght",len(search_partner_policy)

        if search_partner_policy:
            for each_policy in policy_obj.browse(cr,uid,search_partner_policy):
         #       print "each_policy",each_policy
	#	print "eachfdfddsfdsfffffffffffffffff",each_policy.additional_info
                if each_policy.additional_info:
			additional_info_dict = partner_obj.return_cancel_reason_extract(each_policy.additional_info)
	#		print "eachfdfddsfdsf",each_policy.additional_info
			
        	        cancel_return_reason = additional_info_dict.get('cancel_return_reason')
	                cancel_return_source = additional_info_dict.get('source')
        	        policy_obj.write(cr,uid,each_policy.id,{'return_cancel_reason':cancel_return_reason,'source':cancel_return_source})
        return True
#        data = {'partner_id':1,'store_id':1}
#        self.pool.get('schedular.function').eula_reminder(cr,uid,context)
#        search_sale_order = self.pool.get('sale.order').search(cr, uid, [])
#        for each in search_sale_order:
#            self.pool.get('sale.order').write(cr,uid,each,{})
#        context['do_not_update'] = True
#        search_id = self.pool.get('return.order').search(cr,uid,[('id','=',7)])
#        print "search_id",search_id
#        fdf
        result =  self.pool.get('res.partner').subscriber_list(cr,uid)
        print result
        fdfsd
#        self.pool.get('schedular.function').agreement_status(cr,uid,{})
        magento_shop_brw = self.pool.get('sale.shop').browse(cr,uid,2)
        attr_conn = magento_shop_brw.referential_id.external_connection(True)

        result = attr_conn.call('sales_order.new_credit_card', [])
        print "result",result
        fdf
#        result = attr_conn.call('ol_customer.authenticate_customer',['poonam.dafal@bistasolutions.com','solutions','1'])
#        print "result",result
#        service_data= [{'order_id':'100000113','customer_id':'29','product_id':'20'},{'order_id':'100000114','customer_id':'29','product_id':'20'}]
#        deactived_services = attr_conn.call('sales_order.recurring_services', ['update',service_data,''])
#        print "deactived_services",deactived_services
#        fdfs
        increment_ids = ['2','33']
        return_val = attr_conn.call('sales_order.agreement_acceptance_check', [increment_ids])
        #print "return_val",return_val
        fdf
        invoice_id_obj = self.pool.get('account.invoice').browse(cr,uid,12)
        date_invoice = invoice_id_obj.date_invoice
        #print "ffdfdfd",invoice_id_obj.partner_id.billing_date
        #print date_invoice
        val = ( str(invoice_id_obj.partner_id.billing_date)+" 00:00:00" if invoice_id_obj.partner_id.billing_date else '')
        #print "val",type(val),val
        new_val = ( str(invoice_id_obj.date_invoice)+" 00:00:00" if invoice_id_obj.date_invoice else '')
        #print "new_val",new_val
        fdefdfd
        cr.execute("select name from ir_model_data where model='%s' and res_id=%d and name like '%s'"%('res.partner',3,'%/%'))
        id = filter(None, map(lambda x:x[0], cr.fetchall()))
        #print "id",id
        fdf
#        sale_object = self.pool.get('sale.order').browse(cr,uid,102)
#        magento_shop_brw = sale_object.shop_id
        magento_shop_brw = self.pool.get('sale.shop').browse(cr,uid,2)
        attr_conn = magento_shop_brw.referential_id.external_connection(True)
#        return True
    _columns={
        'flare_watch_tou_agmt': fields.text('Agreement'),
        'fanhanttan_toa_agmt': fields.text('Agreement'),
        'privacy_policy_agmt': fields.text('Agreement'),
        'fanhanttan_privacy_policy_agmt': fields.text('Agreement'),
        'eula_accpt_days': fields.integer('EULA Reminder'),
    }
company()

class partner_payment_error(osv.osv):
    _name='partner.payment.error'
    _rec_name = 'partner_id'
    _columns={
    'partner_id': fields.many2one('res.partner','Partner Name'),
    'invoice_id': fields.many2one('account.invoice','Invoice ID'),
    'invoice_name':fields.char('Source Document',size=64),
    'invoice_date':fields.date('Invoice Date'),
    'message':fields.text('Error Message'),
    'status':fields.related('invoice_id','capture_status',type='char',size=64,string='Capture Status'),
    'email_id':fields.related('partner_id','emailid',type='char',size=256,string='Email Id',store=True),
    'phone_no': fields.related('partner_id', 'phone', type='char', size=256, string='Phone Number',store=True),
    'cc_update_date': fields.datetime('CC Updated Date'),  
    'source':fields.char('Exception Source',size=64),
    'active_payment': fields.boolean('Active'),
    'next_retry_date':fields.date('Next retry Date'),
    }
    #    function to charge weekly all the payment exceptions
    def weekly_exceptions_charge(self,cr,uid,ids):
        wf_service = netsvc.LocalService("workflow")
        payment_obj=self.pool.get('partner.payment.error')
        exception_brw=payment_obj.browse(cr,uid,ids)
        billing_date=exception_brw.partner_id.billing_date
        context={}
        today=datetime.date.today()
        nextmonth = datetime.datetime.strptime(billing_date, "%Y-%m-%d") + relativedelta(months=1)
        nextmonth = nextmonth.strftime("%Y-%m-%d")
        res_obj=self.pool.get('res.partner')
        authorize_net_config = self.pool.get('authorize.net.config')
        partner_obj=self.pool.get('res.partner')
        so_obj=self.pool.get('sale.order')
        acc_obj=self.pool.get('account.invoice')
        act_model = context.get('active_model',False)
        transaction_id=''
        invoice_id=exception_brw.invoice_id.id
        if invoice_id:
            amount=acc_obj.browse(cr,uid,invoice_id).amount_total
        partner_id=exception_brw.partner_id.id
        act_model = 'account.invoice'
        context['recurring_billing']=True
        transaction_type = 'profileTransAuthCapture'
        config_ids = authorize_net_config.search(cr,uid,[])
        if partner_id:
            customer_profile_id=res_obj.browse(cr,uid,partner_id).customer_profile_id
            cr.execute("select profile_id from custmer_payment_profile where customer_profile_id='%s' and active_payment_profile=True"%(customer_profile_id))
            payment_profile_data=filter(None, map(lambda x:x[0], cr.fetchall()))
            if payment_profile_data:
                cust_payment_profile_id=payment_profile_data[0]
            if config_ids and customer_profile_id:
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                transaction_details =authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',invoice_id,transaction_type,amount,customer_profile_id,cust_payment_profile_id,transaction_id,act_model,'',context)
                cr.execute("select credit_card_no from custmer_payment_profile where profile_id='%s'"%(cust_payment_profile_id))
                cc_number = filter(None, map(lambda x:x[0], cr.fetchall()))
                if cc_number:
                    cc_number = cc_number[0]
                if context.get('recurring_billing'):
                    transaction_response = transaction_details.get('response','')
                else:
                    transaction_response = transaction_details
                if transaction_details and transaction_details.get('resultCode',False) == 'Ok' and act_model=='account.invoice':
                    context['cc_number'] ='XXXX'+cc_number
                    context['customer_profile_id'] = customer_profile_id
                    if exception_brw.invoice_id.state =='draft':
                        cr.execute("UPDATE account_invoice SET capture_status='captured',date_invoice='%s',next_billing_date='%s' where id=%d"%(today,nextmonth,invoice_id))
                        wf_service.trg_validate(uid, 'account.invoice',invoice_id,'invoice_open', cr)
                        self.pool.get(act_model).make_payment_of_invoice(cr, uid, [invoice_id], context=context)
                        so_obj.email_to_customer(cr,uid,exception_brw.invoice_id,'account.invoice','',exception_brw.invoice_id.partner_id.emailid,context)
                        sale_name=exception_brw.invoice_name.replace('RB','').split('|')
#                    code to update suspension date to False when payment is done
                        if sale_name:
                            for each_name in sale_name:
                                cr.execute("update res_partner_policy set suspension_date= Null where sale_order='%s'"%(str(each_name)))
                                partner_obj.write(cr,uid,exception_brw.partner_id.id,{'billing_date':nextmonth})
                acc_obj.api_response(cr,uid,invoice_id,transaction_response,cust_payment_profile_id,transaction_type,context)
                return transaction_details,invoice_id

        # function to charge daily all the payment exceptions in true state
    def charge_weekly_exceptions(self,cr,uid,ids,context):
        policy_obj=self.pool.get('res.partner.policy')
        today=datetime.date.today()
        inv_id_list=[]
        active_exceptions = self.search(cr,uid,[('active_payment','=',True),('next_retry_date','=',today)])
        if active_exceptions:
            for each_exception in self.browse(cr,uid,active_exceptions):
                next_retry_date=each_exception.next_retry_date
                next_retry_date=datetime.datetime.strptime(next_retry_date, "%Y-%m-%d")
                cmpr_date=''
                invoice_origin=each_exception.invoice_name
                inv_id=each_exception.invoice_id.id
                if invoice_origin:
                    so_name=invoice_origin.replace('RB','').split('|')
                    policy_id = policy_obj.search(cr,uid,[('sale_order','in',so_name),('active_service','=',True)])
                    if policy_id:
                        for each in policy_obj.browse(cr,uid,policy_id):
                            cancel_date=each.cancel_date
                            sus_date=each.suspension_date
                            if cancel_date and sus_date:
                                if cancel_date<=sus_date:
                                    cmpr_date=datetime.datetime.strptime(cancel_date, "%Y-%m-%d")
                                else:
                                    cmpr_date=datetime.datetime.strptime(sus_date, "%Y-%m-%d")
                            elif cancel_date and not sus_date:
                                cmpr_date=datetime.datetime.strptime(cancel_date, "%Y-%m-%d")
                            elif sus_date and not cancel_date:
                                cmpr_date=datetime.datetime.strptime(sus_date, "%Y-%m-%d")
                            else:
                                cmpr_date=next_retry_date
                            if next_retry_date<=cmpr_date and inv_id not in inv_id_list:
                                transaction_details,invoice_id=self.weekly_exceptions_charge(cr,uid,each_exception.id)
                                inv_id_list.append(invoice_id)
                                if transaction_details and transaction_details.get('resultCode',False) == 'Ok':
                                    self.write(cr,uid,each_exception.id,{'active_payment':False,'next_retry_date':False})
                                else:
                                    transaction_message=transaction_details.get('message',False)
                                    next_try_date=next_retry_date+datetime.timedelta(weeks=1)
                                    if cmpr_date==next_retry_date:
                                        next_try_date= next_try_date
                                    elif next_try_date<=cmpr_date:
                                        next_try_date= next_try_date
                                    else:
                                        next_try_date=False
                                    self.write(cr,uid,each_exception.id,{'next_retry_date':next_try_date,'message':str(transaction_message)})
                    else:
                        self.write(cr,uid,each_exception.id,{'active_payment':False,'next_retry_date':False})
        
#        function to update the retry date of exceptions whose active payment is true
    def next_retry_update(self,cr,uid,ids,context):
        policy_obj=self.pool.get('res.partner.policy')
	today=datetime.date.today()
        active_exceptions = self.search(cr,uid,[('active_payment','=',True),('next_retry_date','<',today)])
        if active_exceptions:
            for each_exception in self.browse(cr,uid,active_exceptions):
                date_of_invoice=each_exception.invoice_date
                current_time = datetime.datetime.today()
                cmpr_date=''
                invoice_origin=each_exception.invoice_name
                if invoice_origin:
                    so_name=invoice_origin.replace('RB','').split('|')
                if date_of_invoice:
                    invoice_date=datetime.datetime.strptime(date_of_invoice, "%Y-%m-%d")
                    policy_id = policy_obj.search(cr,uid,[('sale_order','in',so_name),('active_service','=',True)])
                    if policy_id:
                        policy_brw=policy_obj.browse(cr,uid,policy_id[0])
                        cancel_date=policy_brw.cancel_date
                        sus_date=policy_brw.suspension_date
                        if cancel_date and sus_date:
                            if cancel_date<=sus_date:
                                cmpr_date=datetime.datetime.strptime(cancel_date, "%Y-%m-%d")
                            else:
                                cmpr_date=datetime.datetime.strptime(sus_date, "%Y-%m-%d")
                        elif cancel_date and not sus_date:
                            cmpr_date=datetime.datetime.strptime(cancel_date, "%Y-%m-%d")
                        elif sus_date and not cancel_date:
                            cmpr_date=datetime.datetime.strptime(sus_date, "%Y-%m-%d")
                        else:
                            cmpr_date=invoice_date
                        if invoice_date<=cmpr_date:
                            while (invoice_date<current_time):
                                new_invoice_date=invoice_date+datetime.timedelta(weeks=1)
                                invoice_date=new_invoice_date
                                if invoice_date>current_time:
                                    self.write(cr,uid,each_exception.id,{'next_retry_date':invoice_date})
            return invoice_date
    
    def cc_update_time_exceptions(self,cr,uid,partner_id,context):
        if partner_id:
            payment_exception_obj = self.pool.get('partner.payment.error')
            search_exceptions =  payment_exception_obj.search(cr,uid,[('partner_id','in',partner_id)])
            if search_exceptions:
                current_time = datetime.datetime.today()
                payment_exception_obj.write(cr,uid,search_exceptions,{'cc_update_date':current_time})

    def capture_pending_payment(self,cr,uid,ids,context=None):
        if context is None:
            context={}
        for entity in self.browse(cr,uid,ids):
            billing_date=entity.invoice_date
            patrner_id=entity.partner_id.id
	    cr.execute("select active_service from res_partner_policy where agmnt_partner=%s"%(patrner_id))
            policy_active_inactive = filter(None, map(lambda x:x[0], cr.fetchall()))
	    if True in policy_active_inactive:		
	            invoice_id=entity.invoice_id.id
        	    invoice_date=datetime.datetime.strptime(billing_date, "%Y-%m-%d")
	            nextmonth = invoice_date + relativedelta(months=1)
		    nextmonth = nextmonth.strftime("%Y-%m-%d")
	            context.update({'source': entity.source,'payment_exception_id': entity.id,'recurring_billing':True,'billing_date':billing_date,'partner_id':patrner_id,'active_model':'account.invoice','active_ids':[invoice_id],'active_id':invoice_id,'sale_id':[invoice_id],'nextmonth':str(nextmonth)})
        	    if invoice_id:
                	context['action_to_do'] = 'new_payment_profile'
	                context['call_from'] = 'function'
        	        return {
                	    'name': ('New Customer and Payment Profile'),
	                    'view_type': 'form',
        	            'view_mode': 'form',
	                    'res_model': 'profile.transaction',
        	            'view_id': False,
	                    'type': 'ir.actions.act_window',
        	            'target': 'new',
	                     'context': context
        	        }	
            else:
                raise osv.except_osv(_('Warning !'),_('Not having any Active service ')) 

    def cancel_service_not_paid(self,cr,uid,ids,context={}):
        sale_obj = self.pool.get("sale.order")
        return_obj= self.pool.get('return.order')
        policy_obj = self.pool.get("res.partner.policy")
        today = datetime.date.today()
        lastMonth = today + relativedelta(months=-1)
#	print"lastMonth-------",lastMonth
        so_name=[]
        final_dict,service_to_cancel = {},[]
        payment_exce = self.search(cr, uid, [('invoice_date','<=',lastMonth),('active_payment','=',True),('status','=',False)])
        self_obj=self.browse(cr, uid, ids)
        for pay_error in self.browse(cr, uid, payment_exce):
            invoice_origin=pay_error.invoice_name
            so_name=invoice_origin.replace('RB','').split('|')
            if so_name:
                for each_name in so_name:
                    sale_ids = sale_obj.search(cr, uid, [('name','=',each_name)])
#                    policy_id = policy_obj.search(cr, uid, [('sale_order','=',each_name)])
                    cr.execute("select id from res_partner_policy where cancel_date is null and sale_order=%s",(each_name,))
                    policy_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                    policy_brw=policy_obj.browse(cr, uid, policy_id[0])
                    if sale_ids and policy_id:
                        each_rec = sale_obj.browse(cr,uid,sale_ids[0])
                        if each_rec and each_rec.order_line:
                            need_to_update_data = []
                            #Code to write cancellation data and marking service as deactive
                            additional_info = str({'source':'COX','cancel_return_reason':"Recurring Charges not Paid."})
#                            cancellation_data = return_obj.additional_info(cr,uid,additional_info)
                            cr.execute("update res_partner_policy set active_service=False,additional_info=%s,suspension_date=%s,return_cancel_reason='Recurring Charges not Paid.' where id=%s",(additional_info,today,policy_id[0]))
                            return_obj.update_billing_date(cr,uid,pay_error.partner_id.id,pay_error.partner_id.billing_date,policy_brw.sale_line_id)
                            sale_obj.email_to_customer(cr,uid,pay_error,'partner.payment.error','cancel_service',each_rec.partner_id.emailid,context)
                            ######################
                            if each_rec.magento_so_id:
                                data={}
                                data = {'customer_id':each_rec.partner_id.ref,
                                'order_id':each_rec.magento_so_id}
                                if 'mag' not in each_name:
                                    data.update({'product_id': policy_obj.browse(cr, uid, policy_id[0]).product_id.magento_product_id})
                                if data:
                                    need_to_update_data.append(data)
                                if not each_rec.shop_id.referential_id.id in final_dict.iterkeys():
                                    final_dict[each_rec.shop_id.referential_id.id] = need_to_update_data
                                else:
                                    value = final_dict[each_rec.shop_id.referential_id.id]
                                    new_value = value + need_to_update_data
                                    final_dict[each_rec.shop_id.referential_id.id] = new_value
            self.write(cr,uid,pay_error.id,{'active_payment':False,'next_retry_date':False})
        if final_dict:
            referential_obj = self.pool.get('external.referential')
            for each_key in final_dict.iterkeys():
                value = final_dict[each_key]
                referential_id_obj = referential_obj.browse(cr,uid,each_key)
                attr_conn = referential_id_obj.external_connection(True)
                deactived_services = attr_conn.call('sales_order.recurring_services', ['update',value,''])

partner_payment_error()

class res_partner_auth_log(osv.osv):
    _name = "res.partner.auth.log"
    _columns={
        'partner_id':fields.many2one('res.partner','Partner'),
        'user_id':fields.char('User Name',size=256),
        'username_match':fields.boolean('User Name Match'),
        'password_match':fields.boolean('Password Match'),
        'encrypted_password':fields.char('Encrypted Password',size=256),
        'login_time':fields.datetime('Login Time'),
        'customer_id':fields.char('Customer No',size=64,select=1),
        'login_error':fields.text('Login Error'),
        'response_result':fields.text('Result Response'),

    }

    def create(self,cr,uid,vals,context=None):
        cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        res=super(res_partner_auth_log,self).create(cr,uid,vals,context)
        return res

    ####function to export log data to csv file
    def export_auth_log(self,cr,uid,ids,context=None):
        datas=""
        append_ids=[]
        today = datetime.datetime.today() 
        lastmonth = today + relativedelta(months=-1)
        f = open('/opt/cox_auth_log/Auth Logs%s.csv'% today.strftime('%Y-%m-%d'),'at')
        auth_ids=self.search(cr,uid,[('login_time','<=',today.strftime('%Y-%m-%d')),('login_time','>=',lastmonth.strftime('%Y-%m-%d'))])
        if auth_ids:
            datas="Customer Name"+","+"Customer No"+","+"User Name"+","+"Encrypted Password"+"\
            ,"+"User Name Match"+","+"Password Match"+","+"Login Time"+","+"Response Result"+","+"Login Error"+"\n"
            f.write(datas)
            datas=""
            for  each_id in self.browse(cr,uid,auth_ids):
                 datas=str(each_id.partner_id.name.replace(',','') if (each_id.partner_id) else '')+","+str(each_id.customer_id)+","+str(each_id.user_id)+"\
                 ,"+str(each_id.encrypted_password.replace(',','') if each_id.encrypted_password else '')+","+str(each_id.username_match)+","+str(each_id.password_match)+"\
                 ,"+str(each_id.login_time)+","+str(each_id.response_result.replace(',','') if each_id.response_result else '')+","+str(each_id.login_error)+"\n"
                 f.write(datas)
                 append_ids.append(each_id.id)
                 datas=""
                 
        if len(auth_ids)==len(append_ids):
            self.unlink(cr,uid,append_ids)
        return True
res_partner_auth_log()

#########to keep track of rb activation
class recurring_billing_activation(osv.osv):
    _name='recurring.billing.activation'
    _rec_name='partner_id'
    _columns={
        'partner_id':fields.many2one('res.partner','Partner ID'),
        'policy_id':fields.many2one('res.partner.policy','Policy ID'),
        'rb_activation_date':fields.date('Activation Date'),
        'user_id':fields.many2one('res.users','User ID'),
    }
recurring_billing_activation()
