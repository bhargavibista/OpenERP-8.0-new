# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import random
import string
#from openerp.addons.base_external_referentials.external_osv import ExternalSession

class magento_data_export(osv.osv_memory):
    _name = 'magento.data.export'
    _rec_name = 'type'
    _columns={
     'type':fields.selection([('cust_export', 'Customer Export'),('sale_order_export', 'Sale Order Export'),('recurring_export', 'Recurring Export'),('service_export', 'Service Export'),('service_update', 'Service Update'),('status_update', 'Status Update')],'Type'),
     'website_id':fields.many2one('external.shop.group', 'Website'),
     'shop_id':fields.many2one('sale.shop', 'Shop ID'),
     'active_customers': fields.many2many('res.partner', 'res_partner_export_id', 'partner_id', 'wizard_id', 'Active Customers'),
     'recurring_invoices': fields.many2many('account.invoice', 'account_invoice_export_id', 'invoice_id', 'wizard_id', 'Recurring Invoices'),
     'exporting_so': fields.many2many('sale.order', 'sale_order_export_id', 'order_id', 'wizard_id', 'Sale Orders'),
    }
    def onchange_type(self,cr,uid,ids,type,context={}):
        result = {}
        if type and type in ('cust_export','service_export'):
            cr.execute("select id from res_partner where id in (select agmnt_partner from res_partner_policy where active_service=True)")
            active_partner_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#            if active_partner_ids:
#                result['active_customers'] = list(set(active_partner_ids))
        return {'value':result}
    def address_data(self,cr,uid,addr_id,customer_id_obj,magento_cust_id,website_id,context):
        if addr_id:
            so_obj = self.pool.get('sale.order')
            conn = context.get('conn_obj')
            if conn:
                address_obj = self.pool.get('res.partner')
                address_id_obj = address_obj.browse(cr,uid,addr_id)
                region_name = (address_id_obj.state_id.name if address_id_obj.state_id else '')
                region_id = (address_id_obj.state_id.region_id if address_id_obj.state_id else '')
                add_data = {}
                firstname,lastname = address_obj.func_customer_name(address_id_obj.name)
                if address_id_obj.street2:
                    street = address_id_obj.street+'\n'+' '+ address_id_obj.street2
                else:
                    street  = address_id_obj.street
                add_data.update({'firstname': firstname,
                'lastname' : lastname,
                'country_id' : address_id_obj.country_id.code,
                'region_name' : region_name,
                'region_id' : region_id,
                'company' : customer_id_obj.name,
                'city'  : address_id_obj.city,
                'street' : street,
                'telephone' : address_id_obj.phone,
                'postcode': address_id_obj.zip,
                'fax': address_id_obj.fax,
                })
                if context.get('is_default_billing',''):
                    add_data.update({'is_default_billing':'True'})
                if context.get('is_default_shipping',''):
                    add_data.update({'is_default_shipping':'True'})
                mag_add_id = conn.call('customer_address.create',[magento_cust_id,add_data])

    def perform_action(self,cr,uid,ids,context={}):
        ids_obj = self.browse(cr,uid,ids[0])
        partner_obj = self.pool.get('res.partner')
        so_obj = self.pool.get('sale.order')
        invoice_obj = self.pool.get('account.invoice')
        model_data_obj = self.pool.get('ir.model.data')
        if ids_obj.type == 'recurring_export':
            recurring_invoices = ids_obj.recurring_invoices
            for each_inv in recurring_invoices:
                partner_obj.export_recurring_profile(cr,uid,[each_inv.id],context)
	elif ids_obj.type == 'status_update':
            exporting_sale_order = ids_obj.exporting_so
            if exporting_sale_order:
                for each_so_brw in exporting_sale_order:
                    if each_so_brw.magento_incrementid:
                        referential_id_obj = each_so_brw.shop_id.referential_id
                        try:
                            attr_conn = referential_id_obj.external_connection(True)
                            attr_conn.call('sales_order.status_change',[each_so_brw.magento_incrementid,'complete','complete'])
                        except Exception, e:
                            print "error string",e
        elif ids_obj.type == 'sale_order_export':
            exporting_sale_order = ids_obj.exporting_so
            if exporting_sale_order:
                for each_so_brw in exporting_sale_order:
                    if not each_so_brw.magento_exported:
                        magento_shop_brw = each_so_brw.shop_id
                        context['shop_id'] = magento_shop_brw
                        data = so_obj.export_sale_order(cr,uid,[each_so_brw.id],context)
                        external_session = ExternalSession(magento_shop_brw.referential_id, magento_shop_brw)
                        conn = magento_shop_brw.referential_id.external_connection(True)
                        context['conn_obj'] = conn
                        if data:
                            api_response = data.get('api_response')
                            increment_id = api_response.get('increment_id')
                            if each_so_brw.cox_sales_channels == 'retail':
                                cr.execute("select id from account_invoice where recurring = False and id in (select invoice_id from sale_order_invoice_rel where order_id = %d)"%(each_so_brw.id))
                                invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                                for each_invoice in invoice_ids:
                                    context = {'main_lang':'en_US','lang':'en_US','active_model':'account.invoice','active_id':each_invoice}#this line is very important because other wise invoice doesnot gets exporte
                                    invoice_obj._export_one_resource(cr, uid, external_session, each_invoice, context=context)
                                if api_response:
                                    payment_id = api_response.get('payment_id')
                                    increment_id = api_response.get('increment_id')
                                    return_val = conn.call('sales_order.process_invoice', [payment_id,increment_id,'authorizenetcim'])
                                    magento_incrementid = api_response.get('increment_id')
                                if data.get('new_customer',False):
                                        so_obj.email_to_customer(cr,uid,each_so_brw.partner_id,'res.partner','welcome_email',each_so_brw.partner_id.emailid,context)
                            if data.get('service_data',{}):
                                external_session.connection.call('sales_order.recurring_services',['export',data.get('service_data',{}),increment_id])
                            if api_response and api_response.get('db_id'):
                                if each_so_brw.cox_sales_channels == 'call_center':
                                    so_obj.email_to_customer(cr, uid, each_so_brw,'sale.order','account_set_up',each_so_brw.partner_id.emailid,context)
        elif ids_obj.type == 'service_export':
            active_customers = ids_obj.active_customers
            service_obj = self.pool.get('res.partner.policy')
            for each_cust in active_customers:
                cr.execute("select id from res_partner_policy where active_service=True and agmnt_partner=%d"%(each_cust.id))
                active_service_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                magento_incrementid = False
                for each_service in active_service_ids:
                    service_id_obj = service_obj.browse(cr,uid,each_service)
                    sale_id = so_obj.search(cr,uid,[('name','=',service_id_obj.sale_order)])
                    if sale_id:
                            so_id_brw = so_obj.browse(cr,uid,sale_id[0])
                            origin = so_id_brw.origin
                            if not so_id_brw.magento_so_id:
                                magento_shop_brw = so_id_brw.shop_id
                                context['shop_id'] = magento_shop_brw
                                data = so_obj.export_sale_order(cr,uid,sale_id,context)
                                if data:
                                    external_session = ExternalSession(magento_shop_brw.referential_id, magento_shop_brw)
                                    cr.execute("select id from account_invoice where recurring = False and id in (select invoice_id from sale_order_invoice_rel where order_id = %d)"%(sale_id[0]))
                                    invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                                    for each_invoice in invoice_ids:
                                        context = {'lang':'en_US','active_model':'account.invoice','active_id':each_invoice}#this line is very important because other wise invoice doesnot gets exporte
                                        invoice_obj._export_one_resource(cr, uid, external_session, each_invoice, context=context)
                                    api_response = data.get('api_response')
                                    if api_response:
                                        payment_id = api_response.get('payment_id')
                                        increment_id = api_response.get('increment_id')
                                        return_val = conn.call('sales_order.process_invoice', [payment_id,increment_id,'authorizenetcim'])
                                        magento_incrementid = api_response.get('increment_id')
                    if not magento_incrementid:
                        cr.execute("select magento_incrementid from sale_order where name='%s'"%(origin))
                        magento_incrementid = filter(None, map(lambda x:x[0], cr.fetchall()))
                    service_data={'customer_id': each_cust.ref,
                    'order_id': magento_incrementid,
                    'product_id' : service_id_obj.product_id.magento_product_id,
                    'name': service_id_obj.service_name,
                    'desc': service_id_obj.service_name,
                    'status':1
                    }
                    try:
                        service_id = conn.call('sales_order.export_services',[service_data])
                    except Exception, e:
                        print e
	elif ids_obj.type == 'service_update':
             cr.execute("select * from res_partner_policy where (create_date >= '2013-10-31') and active_service= False and sale_line_id is not null and agmnt_partner is not null")
             search_inactive_policy = filter(None, map(lambda x:x[0], cr.fetchall()))
#             search_inactive_policy = [1603]
             if search_inactive_policy:
                 so_obj = self.pool.get('sale.order')
                 need_to_update_data = []
                 for inactive_each in self.pool.get('res.partner.policy').browse(cr,uid,search_inactive_policy):
                        if inactive_each.agmnt_partner.ref:
                            sale_id_brw = so_obj.browse(cr,uid,inactive_each.sale_id)
                            data = {'customer_id':inactive_each.agmnt_partner.ref,
                                'order_id':sale_id_brw.magento_so_id}
                            if 'mag' not in sale_id_brw.name:
                                data.update({'product_id': inactive_each.product_id.magento_product_id})
                            need_to_update_data.append(data)
                 if need_to_update_data:
                    external_session = ExternalSession(sale_id_brw.shop_id.referential_id, sale_id_brw.shop_id)
                    result = external_session.connection.call('sales_order.recurring_services', ['update',need_to_update_data,''])
        elif ids_obj.type == 'cust_export':
            website_id = ids_obj.website_id
            website_mag_id = self.pool.get('external.shop.group').oeid_to_extid(cr, uid, website_id,website_id.id)#will give Website magento ID
            active_customers = ids_obj.active_customers
            magento_shop_brw = ids_obj.shop_id
            conn = magento_shop_brw.referential_id.external_connection(True)
            context['conn_obj'] = conn
            for cust_id_obj in active_customers:
                customer_id = conn.call('ol_customer.customerExists',[cust_id_obj.emailid,website_mag_id,cust_id_obj.name])
                #print "customer_id",customer_id
                if not customer_id:
                    name=(cust_id_obj.name.lstrip().rstrip() if cust_id_obj.name else '')
                    firstname,lastname = partner_obj.func_customer_name(name)
                    group_id = so_obj.magento_id(cr,uid,ids,'res.partner.category',cust_id_obj.group_id.id)
                    password=''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
                    dict_cust = {'firstname': firstname,
                        'lastname' : lastname,
                        'email'  : cust_id_obj.emailid,
                        'password' :str(password),
                        'store_id' :ids_obj.shop_id.default_storeview_integer_id,
                        'website_id':website_mag_id,
                        'taxvat': cust_id_obj.mag_vat,
                        'group_id': group_id}
                    customer_id = conn.call('customer.create',[dict_cust])
                    if customer_id:
                        cr.execute("update res_partner set ref='%s',magento_pwd='%s' where id=%d"%(customer_id,password,cust_id_obj.id))
                        id_val = partner_obj.extid_to_existing_oeid(cr, uid, ids_obj.shop_id.referential_id.id,customer_id,context)
                        if not id_val:
                            model_data_ids = model_data_obj.search(cr, uid,
                            [('res_id', '=', cust_id_obj.id),
                             ('model', '=', 'res.partner'),
                             ('referential_id', '=', website_id.referential_id.id)], context=context)
                            if model_data_ids:
                                model_data_obj.write(cr,uid,model_data_ids[0],{'name':'res_partner/%s'%(customer_id)})
                            else:
                                partner_obj.create_external_id_vals(cr,uid,cust_id_obj.id,customer_id,website_id.referential_id.id)
                        addr = partner_obj.address_get(cr, uid, [cust_id_obj.id], ['delivery', 'invoice','default'])
                        if addr.get('invoice',''):
                            context['is_default_billing'] = True
                            if addr.get('delivery','') == addr.get('invoice',''):
                                context['is_default_shipping'] = True
                            self.address_data(cr,uid,addr.get('invoice',''),cust_id_obj,customer_id,website_id,context)
                        if addr.get('delivery','') != addr.get('invoice',''):
                            context['is_default_shipping'] = True
                            context['is_default_billing'] = False
                            self.address_data(cr,uid,addr.get('delivery',''),cust_id_obj,customer_id,website_id,context)
                        if cust_id_obj.customer_profile_id:
                            mag_profile_id = conn.call('sales_order.magento_Authorize_profile',[customer_id,cust_id_obj.customer_profile_id])
#                        so_obj.email_to_customer(cr,uid,cust_id_obj,'res.partner','welcome_email',cust_id_obj.emailid,context)
                else:
                    if customer_id.get('Id',False):
                        cr.execute("update res_partner set ref=%s where id =%d"%(customer_id.get('Id',False),cust_id_obj.id))
        return {'type': 'ir.actions.act_window_close'}

magento_data_export()
