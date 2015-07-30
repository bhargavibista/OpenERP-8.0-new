# -*- encoding: utf-8 -*-
import logging
from openerp.osv import osv, fields
import datetime
from openerp.tools.translate import _
from openerp import netsvc
from dateutil.relativedelta import relativedelta
#from openerp.addons.magentoerpconnect import magerp_osv
import calendar
from calendar import monthrange
import ast
import logging
_logger = logging.getLogger(__name__)

class res_partner(osv.osv):
    _inherit="res.partner"
    
    def recurring_billing(self,cr,uid,context={}):
        partner_ids,payment_profile_id,start_date=[],False,''
        sale_obj=self.pool.get('sale.order')
	exception_obj=self.pool.get('partner.payment.error')
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
        if len(partner_ids)==0:
            partner_ids = self.search(cr, uid, [('billing_date','=',str(today))])
        for partner_id in partner_ids:
            partner_obj=self.browse(cr,uid,partner_id)       
#            nextmonth=datetime.datetime.strptime(nextmonth, "%Y-%m-%d").date()
            maerge_invoice_data=[]
            cr.execute('select id from res_partner_policy where  active_service = True and no_recurring=False and  agmnt_partner = %s  and (next_billing_date <= (select billing_date from res_partner where id=%s))'% (partner_id,partner_id))
            #cr.execute('select id from res_partner_policy where  active_service = True and agmnt_partner = %s  and ((free_trial_date is null) or free_trial_date <= (select billing_date from res_partner where id=%s))'% (partner_id,partner_id))
            policies = filter(None, map(lambda x:x[0], cr.fetchall()))
            _logger.info('policies---------------- %s', policies)
            if policies:
                nextmonth = today + relativedelta(months=1)
                if len(policies)==1:
                    cr.execute("select start_date from res_partner_policy where id =%s"%(policies[0]))
                    start_date=cr.fetchone()
                elif len(policies)>1:
                    cr.execute("select start_date from res_partner_policy where free_trial_date=(select min(free_trial_date) from res_partner_policy where id in %s)"%(tuple(policies),))
                    start_date=cr.fetchone()
                if start_date and start_date[0]:
                    start_date=datetime.datetime.strptime(start_date[0], "%Y-%m-%d")
                    if start_date.day==31:
                        nextmonth=str(nextmonth.year)+'-'+str(nextmonth.month)+'-'+str(days_nextmonth)
                        nextmonth=datetime.datetime.strptime(nextmonth, "%Y-%m-%d").date()
                    elif today.month==2:
                        nextmonth=str(nextmonth.year)+'-'+str(nextmonth.month)+'-'+str(start_date.day)
                        nextmonth=datetime.datetime.strptime(nextmonth, "%Y-%m-%d").date()
            partner_policy = self.pool.get('res.partner.policy')
            for policy_brw in partner_policy.browse(cr,uid,policies):
                #Extra Code for Checking whether service is cancelled or not
                #Starts here
                cr.execute('select id from cancel_service where sale_id = %s and sale_line_id = %s and partner_policy_id=%s and cancelled=False'%(policy_brw.sale_id,policy_brw.sale_line_id,policy_brw.id))
                policies = filter(None, map(lambda x:x[0], cr.fetchall()))
                ##Ends here
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
                        search_payment_exception =exception_obj.search(cr,uid,[('active_payment','=',True),('partner_id','=',partner_id),('invoice_name','ilike',invoice_name)])
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
                    if sale_info:
                        maerge_invoice_data+=[sale_info]
            if len(maerge_invoice_data)!=0:
                cr.execute("select profile_id from partner_profile_ids where partner_id='%s'"%(str(partner_obj.id)))
                result=cr.dictfetchall()
                if result:
                    partner_profile_id=result[0].get('profile_id')
                    cr.execute("select id,profile_id,credit_card_no from custmer_payment_profile where customer_profile_id='%s' and active_payment_profile=True"%(str(partner_obj.customer_profile_id)))
                    payment_profile_data=cr.dictfetchall()
                    if payment_profile_data:
                        for each in payment_profile_data:
                            payment_profile_id=each.get('profile_id')
                            profile_id=each.get('id')
                            if profile_id==partner_profile_id:
                                context['cc_number'] = each.get('credit_card_no')
                context['partner_id_obj'] = partner_obj
                context['recurring_billing']=True
                res_id=sale_obj.action_invoice_merge(cr, uid, maerge_invoice_data, today, nextmonth, start_date,payment_profile_id, context=context)
                if res_id:
                    if partner_obj.payment_policy=='pro':
                        partner_obj.write({'auto_import':True,'billing_date':str(nextmonth)},context=context)
                        for each_policy in maerge_invoice_data:
                            policy_brw = each_policy.get('policy_id_brw',False)
                            policy_brw.write({'next_billing_date':str(nextmonth)})
                    invoice_id_obj = invoice_obj.browse(cr,uid,res_id)
                    sale_obj.email_to_customer(cr,uid,invoice_id_obj,'account.invoice','',partner_obj.emailid,context)
                    self.cal_next_billing_amount(cr,uid,partner_id)
                    if partner_obj.ref:
                        try:
                            self.export_recurring_profile(cr,uid,[res_id],context)
                        except Exception, e:
                            _logger.info('error string--------------- %s', e)
                else:
                    for service_data in maerge_invoice_data:
                        policy_brw = service_data.get('policy_id_brw',False)
                        app_id=policy_brw.product_id.id
                        rental_result = user_auth_obj.rental_playjam(cr,uid,partner_id,app_id,0)
                        if ast.literal_eval(str(rental_result)).has_key('body') and ast.literal_eval(str(rental_result)).get('body')['result'] == 4113:
                            #4113 is the result response value for successfull rental update
                            additional_info = {'source':'COX','cancel_return_reason':'Credit Card Not on File.'}
                            cancel_reason = return_obj.additional_info(cr,uid,additional_info)
                            cr.execute("update res_partner_policy set active_service = False,return_cancel_reason='Credit Card Not on File.',cancel_date=%s,additional_info=%s where id = %s",(today,cancel_reason,policy_brw.id))
                            sale_obj.email_to_customer(cr,uid,pay_error,'partner.payment.error','cancel_service',partner_obj.emailid,context)
        return True
    def magento_connection(self,cr,uid,context={}):
        referential_obj = self.pool.get('external.referential')
        website_obj = self.pool.get('external.shop.group')
        partner_obj = self.pool.get('res.partner')
        search_referential = referential_obj.search(cr,uid,[])
        if search_referential:
            attr_conn = False
            referential_id_obj = referential_obj.browse(cr,uid,search_referential[0])

    def prodid_from_pkgid(self,cr,uid,package_id):
        prod_brw = False
        product_obj = self.pool.get('product.product')
        if package_id and 'service' in str(package_id):
            split_val = str(package_id).split('service')
            if split_val:
                magento_prod_id = split_val[-1]
                if magento_prod_id:
                    search_oe_prod_id = product_obj.search(cr,uid,[('magento_product_id','=',magento_prod_id)])
                    if search_oe_prod_id:
                        prod_brw = product_obj.browse(cr,uid,search_oe_prod_id[0])
        return prod_brw

    def makeSubscriptionPurchase(self,cr,uid,subscription_data):
        if subscription_data and subscription_data.get('user_name','') or subscription_data.get('customer_id',''):
            username = subscription_data.get('user_name','')
            customer_id = subscription_data.get('customer_id','')
            package_id = subscription_data.get('package_id','')
            start_date = subscription_data.get('start_date','')
            from_package_id = subscription_data.get('from_package_id','')
            up_down_service = subscription_data.get('upgrade_downgrade','')
            previous_package_prorated_price = subscription_data.get('previous_package_prorated_price','')
            new_package_prorated_price = subscription_data.get('new_package_prorated_price','')
            previous_package_price = subscription_data.get('previous_package_price','')
            new_package_price = subscription_data.get('new_package_price','')
	    from_openerp=subscription_data.get('from_openerp','')
            partner_obj = self.pool.get('res.partner')
            partner_policy = self.pool.get('res.partner.policy')
            up_down_obj=self.pool.get('upgrade.downgrade.policy')
            return_obj = self.pool.get('return.order')
            product_obj=self.pool.get('product.product')
            partner_id=False
            if customer_id:
                partner_id = partner_obj.search(cr,uid,[('ref','=',customer_id)])
            elif username:
                partner_id = partner_obj.search(cr,uid,[('emailid','ilike',username)])
            if partner_id and package_id and start_date and from_package_id:
                partner_brw = partner_obj.browse(cr,uid,partner_id[0])
                oe_prod_brw = product_obj.search(cr,uid,[('default_code','=',from_package_id)])
                if from_package_id=='service91':
                    return "You can not downgrade"
                if oe_prod_brw:
                    search_old_policy = partner_policy.search(cr,uid,[('product_id','=',oe_prod_brw.id),('active_service','=',True),('agmnt_partner','in',partner_id)])
		    if not partner_brw.customer_profile_id:
                        res='Customer Payment Profile does not exist.'
                        return res
                    if search_old_policy:
                        old_policy_brw = partner_policy.browse(cr,uid,search_old_policy[0])
		        free_trial_date,flag,source='',False,''
                        source=('gcluster' if uid==72  else 'COX')
		        billing_dt_obj = datetime.datetime.strptime(partner_brw.billing_date, '%Y-%m-%d').date()
		        start_dt_current_service=datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
		        old_free_trial_date=datetime.datetime.strptime(old_policy_brw.free_trial_date, "%Y-%m-%d").date()
#			additional_info = {'source':source,'cancel_return_reason':up_down_service}
                        ######## cox gen2 changes by yogita
                        additional_info = {'source':source,'cancel_return_reason':'downgrade'}
			cancel_reason = return_obj.additional_info(cr,uid,additional_info)
	                cr.execute("update res_partner_policy set return_cancel_reason='downgrade',active_service = False,cancel_date=%s,additional_info=%s where id = %s",(start_date,cancel_reason,old_policy_brw.id))
			if (old_free_trial_date>start_dt_current_service):
                            if (start_dt_current_service.month==2 and billing_dt_obj.day in(31,30)) or (billing_dt_obj.day==31) :
                                days_month=calendar.monthrange(start_dt_current_service.year,start_dt_current_service.month)[1]
                                new_billing_date=str(start_dt_current_service.year)+'-'+str(start_dt_current_service.month)+'-'+str(days_month)
                            else:
                                new_billing_date=str(start_dt_current_service.year)+'-'+str(start_dt_current_service.month)+'-'+str(billing_dt_obj.day)
                            new_billing_date=datetime.datetime.strptime(new_billing_date, "%Y-%m-%d").date()
                            if start_dt_current_service>=new_billing_date:
                                new_billing_date=new_billing_date + relativedelta(months=1)
                            if new_billing_date<billing_dt_obj:
                                billing_dt_obj=new_billing_date
                                flag=True
                                free_trial_date=billing_dt_obj-relativedelta(days=1)
                            elif start_dt_current_service<old_free_trial_date and old_free_trial_date>billing_dt_obj:
                                free_trial_date=billing_dt_obj-relativedelta(days=1)
                            else:
                                free_trial_date=old_free_trial_date
#                                            free_trial_date=datetime.datetime.strptime(str(free_trial_date), "%Y-%m-%d").date()
                        elif(old_free_trial_date<start_dt_current_service):
                            free_trial_date=billing_dt_obj-relativedelta(days=1)
                        else:
                            free_trial_date=old_free_trial_date
                        free_trial_date=datetime.datetime.strptime(str(free_trial_date), "%Y-%m-%d").date()
                        new_pack_oe_brw = self.prodid_from_pkgid(cr,uid,package_id)
                        if new_pack_oe_brw:
		            if billing_dt_obj<start_dt_current_service:
	#                                        billing_dt_obj=billing_dt_obj+relativedelta(months=1)
		                days_left =(billing_dt_obj+relativedelta(months=1)) - start_dt_current_service
		            else:
		                days_left = billing_dt_obj - start_dt_current_service
                            policy_id=partner_policy.create(cr,uid,{
                            'service_name':new_pack_oe_brw.name,
                            'active_service':True,
                            'sale_id': old_policy_brw.sale_id,
                            'start_date': start_date,
                            'agmnt_partner':partner_id[0],
                            'product_id': new_pack_oe_brw.id,
                            'from_package_id':old_policy_brw.id,
                            'up_down_service':up_down_service,
			    'free_trial_date': free_trial_date if free_trial_date else False,
#                            'free_trial_date': old_policy_brw.free_trial_date,
                            'sale_line_id':old_policy_brw.sale_line_id,
                            'extra_days': (days_left.days if days_left else 0),
                            'sale_order':old_policy_brw.sale_order,
                            'previous_package_prorated_price':previous_package_prorated_price,
                            'new_package_prorated_price':new_package_prorated_price,
                            'previous_package_price':previous_package_price,
                            'new_package_price':new_package_price,
                            'source':source,
                            'no_recurring':False,
                            })
			    if flag==True:
                                result=partner_brw.write({'billing_date':billing_dt_obj})
                            if from_openerp!=True:
                                result1=up_down_obj.create(cr,uid,{
                                'partner_id':partner_id[0],
                                'old_policy_id':old_policy_brw.id,
                                'product_id':new_pack_oe_brw.id,
                                'date_create':start_date,
                                'up_down_service':'upgrade' if 'up' in up_down_service.lower() else 'downgrade',
                                'start_date':start_date,
                                'free_trial_date':free_trial_date if free_trial_date else old_policy_brw.free_trial_date,
                                'source':source,
                                'state':'done',
                                'new_policy_id':policy_id,
                                'previous_package_prorated_price':previous_package_prorated_price,
                                'new_package_prorated_price':new_package_prorated_price,
                                'previous_package_price':previous_package_price,
                                'new_package_price':new_package_price,
                                })
                            else:
                                return free_trial_date,policy_id

		        return True
	return False
    
res_partner()

class res_partner_policy(osv.osv):
    _inherit = "res.partner.policy"
    _columns = {
    'previous_package_prorated_price' : fields.float('Previous Package Prorated Price'),
    'new_package_prorated_price' : fields.float('New Package Prorated Price'),
    'previous_package_price':fields.float('Previous Package Original Price'),
    'new_package_price':fields.float('New Package Original Price'),
    'last_amount_charged':fields.float('Last Amount Charged'),
    'source': fields.char('Upgrade/Downgrade Source'),
    'from_package_id': fields.many2one('res.partner.policy','From Pacakge ID'),
    'up_down_service': fields.char('Upgrade/Downgrade',size=256),
    'up_down_id':fields.many2one('upgrade.downgrade.policy','Updown Policy')
    }
    def up_down_charges_gcluster(self,cr,uid,original_service,current_service,context):
        last_amount_paid = original_service.last_amount_charged
        previous_package_prorated_price = current_service.previous_package_prorated_price
        new_package_prorated_price = current_service.new_package_prorated_price
        addition = previous_package_prorated_price + new_package_prorated_price
        if last_amount_paid > addition:
            final_charges =  last_amount_paid - addition
        else:
            final_charges =  addition - last_amount_paid
        return final_charges
 
    def up_down_charges(self,cr,uid,original_service,current_service,date_inv,context):
        adv_paid=0.0
        if not context:
            context={}
        start_dt_current_service = datetime.datetime.strptime(str(current_service.start_date), '%Y-%m-%d')
        old_free_trial_date=datetime.datetime.strptime(str(original_service.free_trial_date), "%Y-%m-%d")
        inv_dt_obj = datetime.datetime.strptime(str(date_inv), '%Y-%m-%d')
        days_in_month=calendar.monthrange(inv_dt_obj.year,inv_dt_obj.month)[1]
        days_left = inv_dt_obj - start_dt_current_service
        current_price = current_service.product_id.list_price
        diff_days=inv_dt_obj-old_free_trial_date
        original_price=original_service.last_amount_charged
        days_left_old=days_left
        if old_free_trial_date > start_dt_current_service:
            if (diff_days.days)>1:
                adv_paid=original_price
            original_price=0.0
            if (original_service.extra_days and original_service.extra_days>0):
                days_left_old = start_dt_current_service-old_free_trial_date
                original_price=0.0
        if context and context.get('cancel_date',False):
            cancel_date=datetime.datetime.strptime(str(original_service.cancel_date), "%Y-%m-%d")
            days_left_old=inv_dt_obj-cancel_date
        cr.execute('update res_partner_policy set last_amount_charged=%s where id =%s'%(current_price,current_service.id))
        if original_service.last_amount_charged<original_service.product_id.list_price and original_service.last_amount_charged!=0.0:
            days_left_old =(start_dt_current_service-old_free_trial_date)
            original_subscription_charges =  (original_price * ((days_left_old.days)/float(days_in_month)))
        else:
		original_subscription_charges =  (original_price * ((days_in_month- days_left_old.days)/float(days_in_month)))
        current_subscription_charges =  (current_price * (days_left.days/float(days_in_month)))
        addition = original_subscription_charges + current_subscription_charges
        if original_price > addition:
            final_charges =  original_price - addition
        else:
            final_charges =  addition - original_price
        if adv_paid<final_charges:
            final_charges=final_charges-adv_paid
        else:
            final_charges=adv_paid-final_charges
	cr.commit()
        return final_charges

    def invoice_line_up_down(self,cr,uid,policy_brw,unit_price,context):
        invoice_lines  = context.get('invoice_lines',[])
        sale_line_obj = self.pool.get('sale.order.line')
        vals = {'name': (context.get('name') if context else policy_brw.product_id.name),
            'price_unit': unit_price,
            'discount':0.0,
            'invoice_line_tax_id':[],
            'line_id': policy_brw.sale_line_id
            }
        line_id_brw = sale_line_obj.browse(cr,uid,policy_brw.sale_line_id)
        vals = sale_line_obj._prepare_invoice_line_cox(cr, uid, line_id_brw, False,vals, context)
        if vals:
                invoice_lines.append(vals)
        return invoice_lines
    
    def service_tier_calculation(self,cr,uid,policy_brw,new_price,date_inv,context):
        original_service =  policy_brw.from_package_id
        current_service = policy_brw
        upgrade_downgrade = policy_brw.up_down_service
        extra_days=0
        days=calendar.monthrange(date_inv.year,date_inv.month)[1]
        start_dt_current_service = datetime.datetime.strptime(str(current_service.start_date), '%Y-%m-%d')
        invoice_lines  =context.get('invoice_lines',[])
        if original_service.from_package_id:
            extra_days=original_service.extra_days
            while extra_days>0:
                context['cancel_date']=True
                start_current_service = datetime.datetime.strptime(str(original_service.start_date), '%Y-%m-%d')
                cancel_date=datetime.datetime.strptime(str(original_service.cancel_date), "%Y-%m-%d")
                extra_days_old=cancel_date-start_current_service
                extra_charges_old=(original_service.product_id.list_price/days)*int(extra_days_old.days)
                if extra_charges_old>0.0:
                    context['name'] = original_service.product_id.name + '(Extra Charges of Previous Service)'
                    context['new_pacakge_id'] = original_service.product_id
                    lines  = self.invoice_line_up_down(cr,uid,original_service,extra_charges_old,context)
                    invoice_lines += lines
                upgrade_downgrade=original_service.up_down_service
                original_service=original_service.from_package_id if original_service.from_package_id else original_service
                extra_days=original_service.extra_days if original_service.from_package_id else 0
        old_free_trial_date=datetime.datetime.strptime(str(original_service.free_trial_date), "%Y-%m-%d")
        billing_date=datetime.datetime.strptime(str(date_inv), "%Y-%m-%d")
        unit_price = policy_brw.product_id.list_price
        extra_charges = self.up_down_charges(cr,uid,original_service,current_service,date_inv,context)
        invoice_lines  =context.get('invoice_lines',[])
        context['new_pacakge_id'] = policy_brw.product_id
        #In case of upgrade new charges need to charged
        if (upgrade_downgrade and 'up' in upgrade_downgrade.lower()):
            context['name'] = policy_brw.product_id.name+ '(Upgrade Adjustment Charges)'
            lines  = self.invoice_line_up_down(cr,uid,policy_brw,unit_price,context)
            invoice_lines += lines

        if (upgrade_downgrade and 'down' in upgrade_downgrade.lower()) and  ((original_service.extra_days and original_service.extra_days>0)):
            context['name'] = policy_brw.product_id.name+'(Downgrade Adjustment Charges)'
            lines  = self.invoice_line_up_down(cr,uid,policy_brw,unit_price,context)
            invoice_lines += lines
        #Extra Charges :
        if extra_charges > 0.0:
            if ((upgrade_downgrade and 'down' in upgrade_downgrade.lower()) and (original_service.last_amount_charged>0.00 and (not original_service.extra_days))):
                extra_charges=unit_price-extra_charges
                inv_line_desc=policy_brw.product_id.name+'(with previous month adjustments)'
            else:
                inv_line_desc=policy_brw.product_id.name+'(Extra Charges of Upgrade/Downgrade)'
            context['name'] = inv_line_desc
            lines  = self.invoice_line_up_down(cr,uid,policy_brw,extra_charges,context)
            invoice_lines += lines
        if (original_service.extra_days and original_service.extra_days>0) and ((old_free_trial_date < start_dt_current_service)):
            cancel_date=datetime.datetime.strptime(str(original_service.cancel_date), "%Y-%m-%d")
            extra_days_old=cancel_date-old_free_trial_date
            extra_charges_old=(original_service.product_id.list_price/days)*int(extra_days_old.days)
            context['name'] = original_service.product_id.name + '(Extra Charges of Previous Service)'
            context['new_pacakge_id'] = original_service.product_id
            lines  = self.invoice_line_up_down(cr,uid,original_service,extra_charges_old,context)
            invoice_lines += lines
        return invoice_lines
res_partner_policy()

########class for upgrade_downgrade
class upgrade_downgrade_policy(osv.osv):
    _name='upgrade.downgrade.policy'
    
    _columns={
        'name':fields.char('Name',size=128),
        'partner_id':fields.many2one('res.partner','Partner Id',readonly=True,states={'draft': [('readonly', False)]}),
        'email' : fields.related('partner_id','emailid',type="char",size=64,string="Email"),
        'old_policy_id':fields.many2one('res.partner.policy','Previous Policy',readonly=True,states={'draft': [('readonly', False)]}),
        'new_policy_id':fields.many2one('res.partner.policy','New Policy'),
        'product_id':fields.many2one('product.product','New Service',readonly=True,states={'draft': [('readonly', False)]}),
        'up_down_service':fields.selection([('upgrade','Upgrade'),('downgrade','Downgrade')],'Upgrade/Downgrade',readonly=True,states={'draft': [('readonly', False)]}),
        'start_date':fields.date('Start Date',readonly=True,states={'draft': [('readonly', False)]}),
        'date_create':fields.date('Date'),
        'free_trial_date':fields.date('Free Trial Date',readonly=True,states={'draft': [('readonly', False)]}),
#        'free_trial_end':fields.date('Free Trial End',readonly=True,states={'draft': [('readonly', False)]}),
        'source':fields.char('Source',size=128,readonly=True,states={'draft': [('readonly', False)]}),
        'user_id':fields.many2one('res.users','Sales Person',readonly=True,states={'draft': [('readonly', False)]}), 
        'state':fields.selection([('draft','Draft'),('done','Done')],'Policy State',select=True),
        'new_package_price':fields.float('New Package Price'),
        'previous_package_price':fields.float('Previous Package Price'),
        'new_package_prorated_price':fields.float('New Package Prorated Price'),
        'previous_package_prorated_price':fields.float('Previous Package Prorated Price'),
    }
    _defaults={
         'user_id': lambda obj, cr, uid, context: uid,
         'date_create':fields.date.context_today,
         'source':'COX',
         'state':'draft',
         'name': lambda obj, cr, uid, context: '/',

    }
    def create(self,cr,uid,vals,context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'upgrade.downgrade.policy') or '/'
        new_id = super(upgrade_downgrade_policy, self).create(cr, uid, vals, context=context)
        return new_id
    def onchange_partner_id(self,cr,uid,ids,partner_id,context=None):
        res,res['value'] = {},{}
        if partner_id:
            res['value'].update({'product_id':False,'old_policy_id':False,'up_down_service':False})
        return res
    def onchange_product_id(self,cr,uid,ids,product_id,partner_id,old_policy_id,context=None):
        res,res['value'],res['warning'],message = {},{},{},''
#        existing_parent_services,existing_child_services,existing_parent_services2=[],[],[]
        old_prod_categ,old_prod_categ_parent,free_trial_date,flag,source=[],[],'',False,''
        if res.get('warning',{}):
            message = res.get('warning',{}).get('message','')
        if product_id and partner_id and old_policy_id:
            policy_obj=self.pool.get('res.partner.policy')
            product_obj = self.pool.get('product.product')
            old_policy_brw = policy_obj.browse(cr,uid,old_policy_id)
            new_pack_oe_brw =product_obj.browse(cr,uid,product_id)
            cr.execute('select product_id from res_partner_policy where active_service=True and return_cancel_reason is null and agmnt_partner= %s'%partner_id)
            product_ids=filter(None, map(lambda x:x[0], cr.fetchall()))
            if product_ids and new_pack_oe_brw.id in product_ids:
                message += message + '\n Customer already has same active subscription.'
                res['warning']['message'] = message
                res['value'].update({'product_id':False,'name':'','up_down_service':False})
                return res
            oe_categ_id=product_obj.browse(cr,uid,old_policy_brw.product_id.id).categ_id
            if oe_categ_id.parent_id:
                old_prod_categ_parent.append(oe_categ_id.parent_id.id)
            old_prod_categ.append(oe_categ_id.id)
            new_prod_categ=new_pack_oe_brw.categ_id
            if new_prod_categ.parent_id:
                if (new_prod_categ.parent_id.id not in old_prod_categ_parent) and (new_prod_categ.parent_id.id not in old_prod_categ) and (new_prod_categ.id not in old_prod_categ_parent):
                    message += message + '\n You can not Upgrade/Downgrade to this service'
                    res['warning']['message'] = message
                    res['value'].update({'product_id':False,'name':'','up_down_service':False})
                    return res
                elif (new_prod_categ.parent_id.id in old_prod_categ_parent) or (new_prod_categ.id in old_prod_categ_parent):
                    res['value'].update({'up_down_service':'upgrade'})
                else:
                    res['value'].update({'up_down_service':'downgrade'})
            elif (not new_prod_categ.parent_id):
                if (new_prod_categ.id not in old_prod_categ_parent) or (new_prod_categ.id in old_prod_categ):
                    message += message + '\n You can not Upgrade/Downgrade to this service'
                    res['warning']['message'] = message
                    res['value'].update({'product_id':False,'name':'','up_down_service':False})
                    return res
                elif new_prod_categ.id in old_prod_categ_parent:
                    res['value'].update({'up_down_service':'upgrade'})
            if old_policy_brw.from_package_id and old_policy_brw.extra_days>0:
                message += message + '\n Can not upgrade multiple times.'
                res['warning']['message'] = message
                res['value'].update({'product_id':False,'name':'','up_down_service':False})
                return res
        return res
    
    def upgrade_downgrade(self,cr,uid,id,context=None):
        self_obj=self.browse(cr,uid,id[0])
        if self_obj.partner_id:
            subscription_data={}
            start_date=fields.date.context_today(self, cr, uid, context=context)
            partner_obj=self.pool.get('res.partner')
            subscription_data.update({
                'CustomerId':self_obj.partner_id.id if self_obj.partner_id else '',
                'NewProductId':self_obj.product_id.id,
                'StartDate': start_date,
                'OldProductId':self_obj.old_policy_id.product_id.id,
                'from_openerp':True,
            })
            res=partner_obj.update_subscription(subscription_data)
            if ast.literal_eval(str(res)).has_key('body'):
                code=int(ast.literal_eval(str(res)).get('body')['code'])
                if code!=4113:
                    message =''
                    message += message + ast.literal_eval(str(res)).get('body')['message']
                    raise osv.except_osv(_('Error!!'), _('%s')%(message))
        return True
upgrade_downgrade_policy()

