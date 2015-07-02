# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import osv, fields
import csv
import cStringIO
import base64
from dateutil import parser

class export_csv(osv.osv_memory):
    """ Export Module """
    _name = "export.csv"
    _description = "Export CSV"
    _columns = {
        'name' : fields.char('Name',size=32),
        'csv_file' : fields.binary('CSV file'),
		'date_from':fields.date('From'),
        'date_to':fields.date('To'),
    }
    def export_offer_index(self,cr,uid,ids,context={}):
        product_obj = self.pool.get('product.product')
        search_offers = product_obj.search(cr,uid,[('active','=',True)])
        if search_offers:
            datas = []
            datas.append("Unique Offer ID")
            datas.append("Offer Name")
            datas.append("Start Date")
            datas.append("End Date")
            datas.append("Post Month Recurring Charges")
            datas.append("Tiers/Service Name")
            datas.append("Product")
            datas.append("Discount Code")
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            datas = []
            for each_prod in product_obj.browse(cr,uid,search_offers):
                if each_prod.ext_prod_config:
                    datas.append(each_prod.unique_offer_id if each_prod.unique_offer_id else '')
                    datas.append(each_prod.name)
                    cr.execute("select min(create_date) from sale_order_line where product_id = %s"%(each_prod.id))
                    min_create_date = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if min_create_date:
                        min_create_date = parser.parse(min_create_date[0])
                        min_create_date = min_create_date.strftime('%Y-%m-%d')
                        datas.append(min_create_date)
                    else:
                        datas.append('')
                    datas.append('')
                    if each_prod.free_trail_days == 0:
                        datas.append(1)
                    else:
                        datas.append(each_prod.free_trail_days)
                    child_service_name,child_product_name = '',''
                    for each_config in each_prod.ext_prod_config:
                        if each_config.comp_product_id.type == 'service':
                            child_service_name = child_service_name+' ' + each_config.comp_product_id.name
                        if each_config.comp_product_id.type == 'product':
                            child_product_name = child_product_name+' ' + each_config.comp_product_id.name
                    datas.append(child_service_name)
                    datas.append(child_product_name)
                    pls_write = writer.writerow(datas)
                    datas = []
            out=base64.encodestring(buf.getvalue())
            buf.close()
            self.write(cr, uid, ids, {'csv_file':out,'name': 'Offers Index.csv'})
            return {
              'name':_("Offers Index"),
              'view_mode': 'form',
              'view_id': False,
              'view_type': 'form',
              'res_model': 'export.csv',
              'res_id': ids[0],
              'type': 'ir.actions.act_window',
              'nodestroy': True,
              'target': 'new',
              'context': context,
            } 	
    def demo_account_list(self,cr,uid,ids,context):
        policy_obj = self.pool.get('res.partner.policy')
        cr.execute("select * from res_partner_policy where (create_date is null or create_date >= '2013-10-31') and sale_id is null")
        search_active_policy = filter(None, map(lambda x:x[0], cr.fetchall()))
	search_active_policy.sort(reverse=True)	
#        print"search_active_policy",search_active_policy
        if search_active_policy:
            datas = []
            datas.append("Customer Name")
            datas.append("Email")
            datas.append("Street")
            datas.append("City")
            datas.append("State")
            datas.append("Zip")
            datas.append("Phone Number")
            datas.append("Product Name")
            datas.append("Start Date")
            datas.append("Free Trail Date")
            datas.append("Return/Cancellation Date")
            datas.append("Price")
            datas.append("Active/Inactive")
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            datas = []
            for each_policy in policy_obj.browse(cr,uid,search_active_policy):
                if each_policy.agmnt_partner:
                    active_inactive = 'Inactive'
                    datas.append(each_policy.agmnt_partner.name)
                    datas.append(each_policy.agmnt_partner.emailid)
                    datas.append(each_policy.agmnt_partner.street)
                    datas.append(each_policy.agmnt_partner.city)
                    datas.append(each_policy.agmnt_partner.state_id.name if each_policy.agmnt_partner.state_id else '')
                    datas.append(each_policy.agmnt_partner.zip)
                    datas.append(each_policy.agmnt_partner.phone)
                    datas.append(each_policy.product_id.name if each_policy.product_id else '')
                    datas.append(each_policy.start_date if each_policy.start_date else '')
                    datas.append(each_policy.free_trial_date if each_policy.free_trial_date else '')
                    datas.append(each_policy.cancel_date if each_policy.cancel_date else '')
                    datas.append(each_policy.product_id.list_price if each_policy.product_id else '')
                    if each_policy.active_service:
                        active_inactive = 'Active'
                    datas.append(active_inactive)
                    pls_write = writer.writerow(datas)
                    datas = []
            out=base64.encodestring(buf.getvalue())
            buf.close()
            self.write(cr, uid, ids, {'csv_file':out,'name': 'Demo Accounts.csv'})
            return {
              'name':_("Export Demo List"),
              'view_mode': 'form',
              'view_id': False,
              'view_type': 'form',
              'res_model': 'export.csv',
              'res_id': ids[0],
              'type': 'ir.actions.act_window',
              'nodestroy': True,
              'target': 'new',
              'context': context,
            }
    def export_subscription(self,cr,uid,ids,context):
        policy_obj = self.pool.get('res.partner.policy')
        so_obj = self.pool.get('sale.order')
	partner_obj = self.pool.get('res.partner')
        cr.execute("select * from res_partner_policy where (create_date is null or create_date >= '2013-10-31') and sale_id is not null")
        search_active_policy = filter(None, map(lambda x:x[0], cr.fetchall()))
#        print"search_active_policy",search_active_policy
        if search_active_policy:
            datas = []
            datas.append("Customer Name")
            datas.append("Email")
            datas.append("Street")
            datas.append("City")
            datas.append("State")
            datas.append("Zip")
            datas.append("Phone Number")
            datas.append("SO Number")
            datas.append("Magento Number")
            datas.append("Sales Channel")
            datas.append("Product Name")
            datas.append("Start Date")
            datas.append("Free Trail Date")
            datas.append("Return/Cancellation Date")
            datas.append("Price")
            datas.append("Active/Inactive")
	    datas.append("Cancel Source")
            datas.append("Cancel/Return Reason")
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            datas = []
            for each_policy in policy_obj.browse(cr,uid,search_active_policy):
                if each_policy.agmnt_partner:
                    street,country_state,sales_channel,active_inactive = '','','','Inactive'
                    datas.append(each_policy.agmnt_partner.name)
                    datas.append(each_policy.agmnt_partner.emailid)
                    if each_policy.sale_id:
                        so_id_obj = so_obj.browse(cr,uid,each_policy.sale_id)
                        if so_id_obj.partner_invoice_id:
                            street = str(so_id_obj.partner_invoice_id.street) + (str(so_id_obj.partner_invoice_id.street2) if (so_id_obj.partner_invoice_id.street2) else '')
                            datas.append(street)
                            datas.append(so_id_obj.partner_invoice_id.city if so_id_obj.partner_invoice_id else '')
                            if so_id_obj.partner_invoice_id.state_id:
                                country_state = so_id_obj.partner_invoice_id.state_id.name
                                datas.append(country_state)
			    else:
				datas.append('') 	
                            datas.append(so_id_obj.partner_invoice_id.zip if so_id_obj.partner_invoice_id else '')
                            datas.append(so_id_obj.partner_invoice_id.phone if so_id_obj.partner_invoice_id else '')
                        datas.append(so_id_obj.name)
                        datas.append(so_id_obj.magento_so_id if so_id_obj.magento_so_id else '')
                        if so_id_obj.cox_sales_channels:
                            if so_id_obj.cox_sales_channels =='call_center':
                                sales_channel = 'Call Center'
                            elif so_id_obj.cox_sales_channels =='ecommerce':
                                sales_channel = 'Ecommerce'
                            elif so_id_obj.cox_sales_channels =='retail':
                                sales_channel = 'Retail Store'
                            elif so_id_obj.cox_sales_channels =='amazon':
                                sales_channel = 'Third Party Product'
                    else:
                        datas.append(street)
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                    datas.append(sales_channel)
                    datas.append(each_policy.product_id.name if each_policy.product_id else '')
                    datas.append(each_policy.start_date if each_policy.start_date else '')
                    datas.append(each_policy.free_trial_date if each_policy.free_trial_date else '')
                    datas.append(each_policy.cancel_date if each_policy.cancel_date else '')
                    datas.append(each_policy.product_id.list_price if each_policy.product_id else '')
                    if each_policy.active_service:
                        active_inactive = 'Active'
                    datas.append(active_inactive)
		    if each_policy.additional_info:
                        additional_info_dict = partner_obj.return_cancel_reason_extract(each_policy.additional_info)
                        cancel_return_reason = additional_info_dict.get('cancel_return_reason')
                        cancel_source = additional_info_dict.get('source')
                        datas.append(cancel_source)
                        datas.append(cancel_return_reason)
                    else:
                        datas.append('')
                        datas.append('') 
                    pls_write = writer.writerow(datas)
                    datas = []
            out=base64.encodestring(buf.getvalue())
            buf.close()
            self.write(cr, uid, ids, {'csv_file':out,'name': 'Subscription.csv'})
            return {
              'name':_("Export Subscription Report"),
              'view_mode': 'form',
              'view_id': False,
              'view_type': 'form',
              'res_model': 'export.csv',
              'res_id': ids[0],
              'type': 'ir.actions.act_window',
              'nodestroy': True,
              'target': 'new',
              'context': context,
            }

            
    def export_csv(self,cr,uid,ids,context={}):
        so_obj = self.pool.get('sale.order')
        partner_obj = self.pool.get('res.partner')
        so_line_obj = self.pool.get('sale.order.line')
        return_line_obj = self.pool.get('return.order.line')
        policy_obj = self.pool.get('res.partner.policy')
        self_obj=self.browse(cr,uid,ids[0])
        search_so=[]
       	if self_obj.date_from and self_obj.date_to:
            search_so = so_obj.search(cr,uid,[('date_order','>=',self_obj.date_from),('date_order','<=',self_obj.date_to),('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
       	elif self_obj.date_from:
            search_so = so_obj.search(cr,uid,[('date_order','>=',self_obj.date_from),('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
        elif self_obj.date_to:
            search_so = so_obj.search(cr,uid,[('date_order','<=',self_obj.date_to),('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
        else:
            search_so = so_obj.search(cr,uid,[('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
#        cr.execute("select id from sale_order where state in ('progress','done') and create_date >= '2013-10-29' and invoiced = True")
#        search_so = filter(None, map(lambda x:x[0], cr.fetchall()))
#        search_so = [1503]
        if search_so:
            datas = ["Sale No.","Customer Name","Customer No","Street",
            "City","State","Zip","Email ID","Phone Number","Date",
            "Order State","Promo Code","Sales Channel","Location Name",
            "Product Name","Quantity","Revenue","Sales Tax","User",
            "Return No.","Return Order Date","Return Product Name",
            "Return Quantity","Return Amount","Return Tax","Return Reason",
            "Active/Inactive","Cancel/Return Date"]
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            datas = []
            count=0
            for so_id_obj in so_obj.browse(cr,uid,search_so):
                print"so_id_obj",so_id_obj
                count+=1
                print"counttttttttttt",count
                street,city,zip,phone,country_state,sales_channel,sales_tax,return_tax ='','','','','','',0.0,0.0
                if so_id_obj.cox_sales_channels:
                    if so_id_obj.cox_sales_channels =='call_center':
                        sales_channel = 'Call Center'
                    elif so_id_obj.cox_sales_channels =='ecommerce':
                        sales_channel = 'Ecommerce'
                    elif so_id_obj.cox_sales_channels =='retail':
                        sales_channel = 'Retail Store'
                    elif so_id_obj.cox_sales_channels =='amazon':
                        sales_channel = 'Third Party Product'
                if so_id_obj.partner_invoice_id:
                    street = str(so_id_obj.partner_invoice_id.street) + (str(so_id_obj.partner_invoice_id.street2) if (so_id_obj.partner_invoice_id.street2) else '')
                    city = so_id_obj.partner_invoice_id.city
                    zip = so_id_obj.partner_invoice_id.zip
                    phone = so_id_obj.partner_invoice_id.phone
                    if so_id_obj.partner_invoice_id.state_id:
                        country_state = so_id_obj.partner_invoice_id.state_id.name
                for line in so_id_obj.order_line:
                    return_line_id_obj,line_ids,prod_ids,cancel_return_reason = False,[],[],''
                    datas.append(so_id_obj.name)
                    datas.append(so_id_obj.partner_id.name)
		    datas.append(so_id_obj.partner_id.ref if so_id_obj.partner_id.ref else '')	
                    datas.append(street)
                    datas.append(city)
                    datas.append(country_state)
                    datas.append(zip)
                    datas.append(so_id_obj.partner_id.emailid)
                    datas.append(phone)
                    datas.append(so_id_obj.date_confirm)
                    datas.append(so_id_obj.state)
                    datas.append(so_id_obj.promo_code if so_id_obj.promo_code else '')
                    datas.append(sales_channel)
                    datas.append((so_id_obj.location_id.name if so_id_obj.location_id else ''))
                    datas.append((line.product_id.name if line.product_id else line.name))
                    datas.append(float(line.product_uom_qty))
                    datas.append(float(line.price_subtotal))
                    if sales_tax == 0.0 :
                        if so_id_obj.amount_tax >= 0.0:
                            sales_tax = so_id_obj.amount_tax
                            datas.append(sales_tax)
                    else:
                        datas.append(0.0)
                    datas.append((so_id_obj.user_id.name if so_id_obj.user_id else ''))
                    line_ids.append(line.id)
                    prod_ids.append(line.product_id.id if line.product_id else '')
                    search_child_so_line_id = so_line_obj.search(cr,uid,[('parent_so_line_id','in',line_ids)])
                    if search_child_so_line_id:
                        for each_child in  so_line_obj.browse(cr,uid,search_child_so_line_id):
                            line_ids.append(each_child.id)
                            if each_child.product_id:
                                prod_ids.append(each_child.product_id.id)
                    result_return = return_line_obj.search(cr,uid,[('sale_line_id','in',line_ids)])
                    if result_return:
                        roname,rodate, rolinename,qty,line_subtotal,roamount_tax = '','','',0.0,0.0,0
                        for return_line_id_obj in return_line_obj.browse(cr,uid,result_return):
                            if (return_line_id_obj.order_id.state != 'draft') and (return_line_id_obj.order_id.return_type == 'car_return'):
                              roname += (return_line_id_obj.order_id.name if return_line_id_obj.order_id else '-')
                              rodate += return_line_id_obj.order_id.date_order
                              rolinename += (return_line_id_obj.name if return_line_id_obj.name else '-')
                              if (return_line_id_obj.product_id.type =='product'):
                                  qty += (float(return_line_id_obj.product_uom_qty))
                              else:
                                if (return_line_id_obj.product_id.type =='service') and ( not return_line_id_obj.product_id.recurring_service):
                                    qty += (float(return_line_id_obj.product_uom_qty))
                              line_subtotal += float(return_line_id_obj.price_subtotal)
                            else:
                                return_line_id_obj = False
                            if return_line_id_obj:
                                if return_line_id_obj.order_id.amount_tax >= 0.0 :
                                    return_tax = return_line_id_obj.order_id.amount_tax
                                    if return_line_id_obj.order_id.amount_tax != roamount_tax:
                                        roamount_tax += float(return_tax)
                        datas.append(roname)
                        datas.append(rodate)
                        datas.append(rolinename)
                        datas.append('-'+str(qty))
                        datas.append('-'+str(line_subtotal))
                        datas.append('-'+str(roamount_tax))
                    if not result_return:
                        datas.extend(['-','-','-',0.0,0.0,0.0])
                    if line_ids and prod_ids:
                        search_partner_policy = policy_obj.search(cr,uid,[('sale_line_id','in',line_ids),('product_id','in',prod_ids)])
                        if search_partner_policy:
                            search_partner_policy.sort()
                            policy_brw = policy_obj.browse(cr,uid,search_partner_policy[-1])
			    if policy_brw.additional_info:
                                cancel_return_reason = partner_obj.return_cancel_reason_extract(policy_brw.additional_info)
                                cancel_return_reason = cancel_return_reason.get('cancel_return_reason','') 
                            active_inactive = ('Inactive' if not policy_brw.active_service else 'Active')
                            cancel_date = policy_brw.cancel_date
			    datas.append(cancel_return_reason)	
                            datas.append(active_inactive)
                            datas.append(cancel_date if cancel_date else '')
                    print"dataaaaaaaaa",datas
                    pls_write = writer.writerow(datas)
                    datas = []
                ##To Search Recurring billing for the Sale Order
                cr.execute("select id from account_invoice where recurring = True and state='paid' and id in (select invoice_id from sale_order_invoice_rel where order_id = %d)"%(so_id_obj.id))
                invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                if invoice_ids:
                    invoice_obj = self.pool.get('account.invoice')
                    amount_tax = 0.0
                    for invoice_id_obj in invoice_obj.browse(cr,uid,invoice_ids):
                        inv_street,inv_city,inv_zip,inv_phone,inv_co_state = '','','','',''
                        if invoice_id_obj.partner_id:
                            inv_street = str(invoice_id_obj.partner_id.street) + (str(invoice_id_obj.partner_id.street2) if (invoice_id_obj.partner_id.street2) else '')
                            inv_city = invoice_id_obj.partner_id.city
                            inv_zip = invoice_id_obj.partner_id.zip
                            inv_phone =  invoice_id_obj.partner_id.zip
                            if invoice_id_obj.partner_id.state_id:
                                inv_co_state = invoice_id_obj.partner_id.state_id.name
                        for invoice_line in invoice_id_obj.invoice_line:
                            datas.append(invoice_id_obj.number)
                            datas.append(invoice_id_obj.partner_id.name)
			    datas.append(invoice_id_obj.partner_id.ref)	
                            datas.append(inv_street)
                            datas.append(inv_city)
                            datas.append(inv_co_state)
                            datas.append(inv_zip)
                            datas.append(invoice_id_obj.partner_id.emailid)
                            datas.append(inv_phone)
                            datas.append(invoice_id_obj.date_invoice)
                            datas.append(invoice_id_obj.state)
                            datas.append('-')
                            datas.append('-')
                            datas.append('-')
                            datas.append(invoice_line.name)
                            datas.append(invoice_line.quantity)
                            datas.append(invoice_line.price_subtotal)
#                            print"datassssssssssssssssss",datas
                            if amount_tax == 0.0 :
                                if invoice_id_obj.amount_tax >=0.0:
                                    amount_tax = invoice_id_obj.amount_tax
                                    datas.append(amount_tax)
                            else:
                                datas.append(0.0)
                            datas.append(invoice_id_obj.user_id.name)
                            datas.extend(['-','-',0.0,0.0,0.0])
                            pls_write = writer.writerow(datas)
                            datas = []
            out=base64.encodestring(buf.getvalue())
            buf.close()
            self.write(cr, uid, ids, {'csv_file':out,'name': 'Sales Report.csv'})
            return {
              'name':_("Export Sale Report"),
              'view_mode': 'form',
              'view_id': False,
              'view_type': 'form',
              'res_model': 'export.csv',
              'res_id': ids[0],
              'type': 'ir.actions.act_window',
              'nodestroy': True,
              'target': 'new',
              'domain': '[]',
              'context': context,
            }
export_csv()


class export_cancel_service_csv(osv.osv_memory):
    """ Export Module """
    _name = "export.cancel.service.csv"
    _description = "Export CSV"
    _columns = {
        'name' : fields.char('Name',size=32),
        'csv_file' : fields.binary('CSV file'),
        'date_from':fields.date('From',required=True),
        'date_to':fields.date('To',required=True),
    }



    def export_cancel_service_csv(self,cr,uid,ids,context={}):
        so_obj = self.pool.get('sale.order')
        acc_inv_obj=self.pool.get('account.invoice')
	partner_obj = self.pool.get('res.partner')
        so_line_obj = self.pool.get('sale.order.line')
        return_line_obj = self.pool.get('return.order.line')
        return_obj = self.pool.get('return.order')
        payment_obj = self.pool.get('partner.payment.error')
        credit_obj = self.pool.get('credit.service')
        credit_line_obj = self.pool.get('credit.service.line')
        policy_obj = self.pool.get('res.partner.policy')
        self_obj=self.browse(cr,uid,ids[0])
        search_so=[]
        datas = []
        active_inactive=''
        buf=cStringIO.StringIO()
        writer=csv.writer(buf, 'UNIX')
        if (self_obj.date_from and self_obj.date_to):
            print "self_obj.date_from",self_obj.date_from,self_obj.date_to
            payment_exceptions = payment_obj.search(cr,uid,[('invoice_date','>=',self_obj.date_from),('invoice_date','<=',self_obj.date_to),('active_payment','=',False)])
            print "payment_exceptionspayment_exceptions",payment_exceptions
            return_orders = return_obj.search(cr,uid,[('date_order','>=',self_obj.date_from),('date_order','<=',self_obj.date_to),('state','=','done'),('return_type','=','car_return')])
            credit_orders = credit_obj.search(cr,uid,[('date_order','>=',self_obj.date_from),('date_order','<=',self_obj.date_to),('state','=','done')])
            print "return_ordersreturn_ordersreturn_orders",return_orders,len(return_orders)
        if return_orders:
            datas = ["Sale No.","Return No/Credit No","Customer Name","Customer No","Street",
            "City","State","Zip","Email ID","Phone Number",
            "Order State","Return Type",
            "Product Name"," ReturnQuantity","Revenue","Returns Tax","User",
            "Active/Inactive","Cancel/Return Date"]
            pls_write = writer.writerow(datas)
            datas = []
            count=0
            date_cancel=''
            count=0
            print "cpoijsvbghdfhgvf",count
            for return_id_obj in return_obj.browse(cr,uid,return_orders):
                count+=1
                sale_ref=return_id_obj.linked_sale_order.id
                policy_id = policy_obj.search(cr,uid,[('sale_id','=',sale_ref)])
                if policy_id:
                    policy_brw=policy_obj.browse(cr,uid,policy_id[0])
                    active_inactive=policy_brw.active_service
                    if (active_inactive==True):
                        active_inactive='Active'
                    else:
                        active_inactive='Inactive'
                    date_cancel=policy_brw.cancel_date
#                count+=1
                street,city,zip,phone,country_state,return_type,sales_tax,return_tax ='','','','','','',0.0,0.0
                if return_id_obj.return_type:
                    if return_id_obj.return_type =='car_return':
                        return_type = 'Credit Return'
                if return_id_obj.partner_id:
                    street = str(return_id_obj.partner_id.street) + (str(return_id_obj.partner_id.street2) if (return_id_obj.partner_id.street2) else '')
                    city = return_id_obj.partner_id.city
                    zip = return_id_obj.partner_id.zip
                    phone = return_id_obj.partner_id.phone
                    if return_id_obj.partner_id.state_id:
                        country_state = return_id_obj.partner_id.state_id.name
                for line in return_id_obj.order_line:
#                    count+=1
                    return_line_id_obj,line_ids,prod_ids,cancel_return_reason = False,[],[],''
                    datas.append(return_id_obj.linked_sale_order.name)
                    datas.append(return_id_obj.name)
                    datas.append(return_id_obj.partner_id.name)
		    datas.append(return_id_obj.partner_id.ref if return_id_obj.partner_id.ref else '')
                    datas.append(street)
                    datas.append(city)
                    datas.append(country_state)
                    datas.append(zip)
                    datas.append(return_id_obj.partner_id.emailid)
                    datas.append(phone)
                    datas.append(return_id_obj.state)
                    datas.append(return_type)
                    datas.append((line.product_id.name if line.product_id else line.name))
                    datas.append(float(line.product_uom_qty))
                    datas.append(float(line.price_subtotal))
                    if sales_tax == 0.0 :
                        if return_id_obj.amount_tax >= 0.0:
                            sales_tax = return_id_obj.amount_tax
                            datas.append(sales_tax)
                    else:
                        datas.append(0.0)
                    datas.append((return_id_obj.user_id.name if return_id_obj.user_id else ''))
                    datas.append(active_inactive)
                    datas.append(date_cancel or '')
                    pls_write = writer.writerow(datas)
                    datas = []
#                print "cpountttttttttttttttttttt",count
        if credit_orders:
            for credit_id_obj in credit_obj.browse(cr,uid,credit_orders):
                count+=1
                street,city,zip,phone,country_state,return_type,sales_tax,return_tax ='','','','','','',0.0,0.0
                if credit_id_obj.partner_id:
                    street = str(credit_id_obj.partner_id.street) + (str(credit_id_obj.partner_id.street2) if (credit_id_obj.partner_id.street2) else '')
                    city = credit_id_obj.partner_id.city
                    zip = credit_id_obj.partner_id.zip
                    phone = credit_id_obj.partner_id.phone
                    if credit_id_obj.partner_id.state_id:
                        country_state = credit_id_obj.partner_id.state_id.name
                for line in credit_id_obj.order_line:
                    credit_line_obj,line_ids,prod_ids,cancel_return_reason = False,[],[],''
                    datas.append((line.service_id.sale_order if line.service_id else line.name))
                    datas.append(credit_id_obj.name)
                    datas.append(credit_id_obj.partner_id.name)
                    datas.append(credit_id_obj.partner_id.ref if credit_id_obj.partner_id.ref else '')
                    datas.append(street)
                    datas.append(city)
                    datas.append(country_state)
                    datas.append(zip)
                    datas.append(credit_id_obj.partner_id.emailid)
                    datas.append(phone)
                    datas.append(credit_id_obj.state)
                    datas.append('')
                    datas.append((line.service_id.product_id.name if line.service_id else line.name))
                    datas.append(float(line.product_uom_qty))
                    datas.append(float(line.price_subtotal))
                    if sales_tax == 0.0 :
                        if credit_id_obj.amount_tax >= 0.0:
                            sales_tax = credit_id_obj.amount_tax
                            datas.append(sales_tax)
                    else:
                        datas.append(0.0)
                    datas.append((credit_id_obj.user_id.name if credit_id_obj.user_id else ''))
                    if line.service_id:
                        if line.service_id.active_service==True:
                            active_inactive='Active'
                        else:
                            active_inactive='Inactive'
                    datas.append((active_inactive))
                    datas.append((line.service_id.cancel_date if line.service_id else ''))
                    pls_write = writer.writerow(datas)
                    print "datas old...................",datas
                    datas = []
        if payment_exceptions:
            street,city,zip,phone,country_state,return_type,sales_tax,return_tax ='','','','','','',0.0,0.0
            for paymnet_id_obj in payment_obj.browse(cr,uid,payment_exceptions):
                count+=1
                street,city,zip,phone,country_state,return_type,sales_tax,return_tax ='','','','','','',0.0,0.0
                if paymnet_id_obj.partner_id:
                    invoice_exception=acc_inv_obj.search(cr,uid,[('origin','=',paymnet_id_obj.invoice_name),('state','=','draft')])
                    street = str(paymnet_id_obj.partner_id.street) + (str(paymnet_id_obj.partner_id.street2) if (paymnet_id_obj.partner_id.street2) else '')
                    city = paymnet_id_obj.partner_id.city
                    zip = paymnet_id_obj.partner_id.zip
                    phone = paymnet_id_obj.partner_id.phone
                    source=paymnet_id_obj.invoice_name
                    message=paymnet_id_obj.message
                    inv_date=paymnet_id_obj.invoice_date
		    if "RB" in source:
                   	 so_ref=source.split('B')[1]
                    if paymnet_id_obj.partner_id.state_id:
                        country_state = paymnet_id_obj.partner_id.state_id.name
                    if invoice_exception:
                        for inv_id in acc_inv_obj.browse(cr,uid,invoice_exception):
                            for each_line in inv_id.invoice_line:
                                datas.append(so_ref if source else '')
                                datas.append(source if source else '')
                                datas.append(paymnet_id_obj.partner_id.name if paymnet_id_obj.partner_id else '' )
                                datas.append(paymnet_id_obj.partner_id.ref if paymnet_id_obj.partner_id.ref else '')
                                datas.append(street if street else '')
                                datas.append(city if city else '')
                                datas.append(country_state if country_state else '')
                                datas.append(zip if zip else '')
                                datas.append(paymnet_id_obj.partner_id.emailid if paymnet_id_obj.partner_id else '' )
                                datas.append(phone if phone else '')
                                datas.append(inv_id.state if inv_id else '')
                                datas.append('')
                                datas.append((each_line.product_id.name if each_line.product_id else ''))
                                datas.append(float(each_line.quantity if each_line.product_id else ''))
                                datas.append(float(each_line.price_subtotal if each_line.product_id else ''))
                                if sales_tax == 0.0 :
                                    if inv_id.amount_tax >= 0.0:
                                        sales_tax = inv_id.amount_tax
                                        datas.append(sales_tax)
                                    else:
                                        datas.append(0.0)
                                datas.append((inv_id.user_id.name if inv_id.user_id else ''))
                                datas.append(inv_id.date_invoice if inv_id else '')
                                pls_write = writer.writerow(datas)
                                datas = []
            pls_write = writer.writerow(datas)
            datas = []
            out=base64.encodestring(buf.getvalue())
            buf.close()
            self.write(cr, uid, ids, {'csv_file':out,'name': 'Churn Report.csv'})
            return {
              'name':_("Export Cancel services Report"),
              'view_mode': 'form',
              'view_id': False,
              'view_type': 'form',
              'res_model': 'export.cancel.service.csv',
              'res_id': ids[0],
              'type': 'ir.actions.act_window',
              'nodestroy': True,
              'target': 'new',
              'domain': '[]',
              'context': context,
            }
export_csv()

