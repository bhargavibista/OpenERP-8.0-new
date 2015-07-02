# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import random
import string
from datetime import date, datetime, timedelta

class demo_account_setup(osv.osv_memory):
    _name="demo.account.setup"
#    _rec_name = 'emailid'
    _columns={
    'password': fields.char('Passsword To be Set up',size=215),
    'emailid': fields.char('Email ID',size=215),
    'email_subject': fields.char('Subject',size=215),
    'email_body': fields.text('Email Body'),
    'magento_location': fields.many2one('external.referential','Magento Website'),
    'send_email': fields.boolean('Send Email'),
    'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),   #Preeti
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                       context=None, toolbar=False, submenu=False):
       res = super(demo_account_setup, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
       if context and context.get('active_id'):
           partner_brw = self.pool.get('res.partner').browse(cr,uid,context.get('active_id'))
#           if partner_brw.ref:
#               raise osv.except_osv(_('Warning !'),_('Account is already Setup'))
       return res
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(demo_account_setup, self).default_get(cr, uid, fields, context=context)
        if context and context.get('active_id'):
            emailid = self.pool.get('res.partner').browse(cr,uid,context.get('active_id')).emailid
            if emailid:
                res.update({'emailid':emailid})
            search_referential = self.pool.get('external.referential').search(cr,uid,[])
            if search_referential:
                res.update({'magento_location':search_referential})
        return res
    def onchange_password(self,cr,uid,ids,password,context):
        res= {}
        warning = {'title': _('Warning!')}
        if password:
            if len(password) <= 5:
                warning.update({'message' : _('Password should be Greater than 5 Characters')})
        if warning and warning.get('message'):
            res['value'] = {}
            res['value']['password'] = False
            res['warning'] = warning
        return res
    def onchange_send_email(self,cr,uid,ids,send_email,context):
        res  = {}
        if send_email:
            template_obj=self.pool.get('email.template')
            template_search = template_obj.search(cr,uid,[('model','=','res.partner'),('email_type','=','welcome_email')])
            #print "template_search",template_search
            if template_search:
                template_id_obj = template_obj.browse(cr,uid,template_search[0])
                content = template_id_obj.body_html
                subject= template_id_obj.subject
                res['email_body'] = content
                res['email_subject'] = subject
                res
        return {'value':res}
    def create_demo_account(self,cr,uid,ids,context):
        if context and context.get('active_id'):
            ids_brw = self.browse(cr,uid,ids[0])
            password = ids_brw.password
            partner_obj = self.pool.get('res.partner')
            model_data_obj = self.pool.get('ir.model.data')
            so_obj = self.pool.get('sale.order')
            website_obj = self.pool.get('external.shop.group')
            magento_export_obj = self.pool.get('magento.data.export')
            partner_brw = partner_obj.browse(cr,uid,context.get('active_id'))
            website_partner_id = partner_brw.website_id
            website_mag_part_id = website_obj.oeid_to_extid(cr, uid, website_partner_id,website_partner_id.id)#will give Website magento ID
            all_website = website_obj.search(cr,uid,[])
            website_ids = partner_obj.get_website_magento_id(cr,uid,all_website)
            try:
                conn = ids_brw.magento_location.external_connection(True)
                if conn:
                    context['conn_obj'] = conn
                    customer_id = conn.call('ol_customer.customerExists',[partner_brw.emailid,website_ids,partner_brw.name])
                    if not customer_id:
                        name=(partner_brw.name.lstrip().rstrip() if partner_brw.name else '')
                        firstname,lastname = partner_obj.func_customer_name(name)
                        group_id = so_obj.magento_id(cr,uid,ids,'res.partner.category',partner_brw.group_id.id)
                        if not ids_brw.password:
                            password=''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
                        dict_cust = {'firstname': firstname,
                            'lastname' : lastname,
                            'email'  : partner_brw.emailid,
                            'password' :str(password),
                            #'store_id' :website_partner_id.default_shop_id.default_storeview_integer_id,
                            'website_id':website_mag_part_id,
                            'taxvat': partner_brw.mag_vat,
                            'group_id': group_id}
                        customer_id = conn.call('customer.create',[dict_cust])
                        if customer_id:
                            cr.execute("update res_partner set ref='%s',magento_pwd='%s' where id=%d"%(customer_id,password,partner_brw.id))
                            id_val = partner_obj.extid_to_existing_oeid(cr, uid, ids_brw.magento_location.id,customer_id,context)
                            if not id_val:
                                model_data_ids = model_data_obj.search(cr, uid,
                                [('res_id', '=', partner_brw.id),
                                ('model', '=', 'res.partner'),
                                ('referential_id', '=', ids_brw.magento_location.id)], context=context)
                                if model_data_ids:
                                    model_data_obj.write(cr,uid,model_data_ids[0],{'name':'res_partner/%s'%(customer_id)})
                                else:
                                    partner_obj.create_external_id_vals(cr,uid,partner_brw.id,customer_id,website_partner_id.referential_id.id)
                            addr = partner_obj.address_get(cr, uid, [partner_brw.id], ['delivery', 'invoice','default'])
                            if addr.get('invoice',''):
                                context['is_default_billing'] = True
                                if addr.get('delivery','') == addr.get('invoice',''):
                                    context['is_default_shipping'] = True
                                magento_export_obj.address_data(cr,uid,addr.get('invoice',''),partner_brw,customer_id,website_partner_id,context)
                            if addr.get('delivery','') != addr.get('invoice',''):
                                context['is_default_shipping'] = True
                                context['is_default_billing'] = False
                                magento_export_obj.address_data(cr,uid,addr.get('delivery',''),partner_brw,customer_id,website_partner_id,context)
                            if partner_brw.customer_profile_id:
                                mag_profile_id = conn.call('sales_order.magento_Authorize_profile',[customer_id,partner_brw.customer_profile_id])
                            if ids_brw.send_email:
                                message_obj = self.pool.get('mail.compose.message')
                                smtp_obj = self.pool.get('email.smtpclient')
                                smtpserver_id = smtp_obj.search(cr,uid,[('pstate','=','running'),('active','=',True)])
                                if smtpserver_id:
                                    content = message_obj.render_template(cr, uid, ids_brw.email_body, 'res.partner', partner_brw.id)
                                    subject=message_obj.render_template(cr, uid, ids_brw.email_subject, 'res.partner', partner_brw.id)
                                    queue_id = smtp_obj.send_email(cr, uid, smtpserver_id[0], ids_brw.emailid, subject, content,[])
                                    if queue_id:
                                        result=smtp_obj._my_check_queue(cr,uid,queue_id)
                    else:
                        if customer_id.get('Id',False):
                            cr.execute("update res_partner set ref=%s where id =%d"%(customer_id.get('Id',False),partner_brw.id))
		    current_time = datetime.now()
                    service_start_dt = current_time.strftime("%Y-%m-%d")
		    cr.execute("select product_id from res_partner_policy where agmnt_partner=%s and active_service = True"%(partner_brw.id))  #Preeti
                    existing_pack_id = filter(None, map(lambda x:x[0], cr.fetchall()))   #Preeti
                    if ids_brw.product_id.id not in existing_pack_id:
                        cr.execute("insert into res_partner_policy (service_name,product_id,active_service,agmnt_partner,start_date) values('%s',%s,True,%s,'%s')"%(ids_brw.product_id.name,ids_brw.product_id.id,partner_brw.id,service_start_dt))   #Preeti
                    else:
                        raise osv.except_osv(_('Warning !'),_('Account is already Setup'))                     
#                    cr.execute("insert into res_partner_policy (service_name,product_id,active_service,agmnt_partner,start_date) values('Flare Play Game Service',27,True,%s,'%s')"%(partner_brw.id,service_start_dt))
            except Exception, e:
                print "error string",e
		raise osv.except_osv(_('Warning !'),_('Account is already Setup'))
        return True
demo_account_setup()
