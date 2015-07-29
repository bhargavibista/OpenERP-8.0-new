# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import osv, fields
import csv
import cStringIO
import base64
import datetime
import time
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
        invoice_obj = self.pool.get('account.invoice')
        self_obj=self.browse(cr,uid,ids[0])
        invoice_id_list,search_so=[],[]
        if self_obj.date_from and self_obj.date_to:
            search_so = so_obj.search(cr,uid,[('date_confirm','>=',self_obj.date_from),('date_confirm','<=',self_obj.date_to),('create_date','>','2013-10-29'),('invoiced','=',True)])
        elif self_obj.date_from:
            search_so = so_obj.search(cr,uid,[('date_confirm','>=',self_obj.date_from),('create_date','>','2013-10-29'),('invoiced','=',True)])
        elif self_obj.date_to:
            search_so = so_obj.search(cr,uid,[('date_confirm','<=',self_obj.date_to),('create_date','>','2013-10-29'),('invoiced','=',True)])
        else:
            search_so = so_obj.search(cr,uid,[('create_date','>','2013-10-29'),('invoiced','=',True)])
        if search_so:
            datas = ["Sale No.","Customer Name","Customer No","Street",
            "City","State","Zip","Email ID","Phone Number","Date",
            "Order State","Promo Code","Sales Channel","Location Name",
            "Offer/Product Name","Device","Device Price(in this offer)","Service","Service Price(in this offer","Free/Paid",
            "Quantity","Offer Price","Sales Tax","User",]
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            datas = []
            count=0
            for so_id_obj in so_obj.browse(cr,uid,search_so):
#                cr.execute("select id from account_invoice where state='paid' and id in (select invoice_id from sale_order_invoice_rel where order_id = %d)"%(so_id_obj.id))
#                invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#                if invoice_ids:
                count+=1
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
                    city = so_id_obj.partner_invoice_id.city
                    zip = so_id_obj.partner_invoice_id.zip
                    phone = so_id_obj.partner_invoice_id.phone
                    if so_id_obj.partner_invoice_id.state_id:
                        country_state = so_id_obj.partner_invoice_id.state_id.name
                for line in so_id_obj.order_line:
                    return_line_id_obj,line_ids,prod_ids,date_list,cancel_return_reason,cancel_date,return_reason,return_date = False,[],[],[],'','','',''
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
                    if line.sub_components:
                        count=len(line.sub_components)
                        pro_name,ser_name,pro_price,serv_price='','',0.0,0.0
                        for prod_obj in line.sub_components:
                            if prod_obj.product_id and prod_obj.product_id.type=="product":
                                pro_name += prod_obj.product_id.name+'\n'
                                pro_price +=prod_obj.price
                            if prod_obj.product_id and prod_obj.product_id.type=="service":
                                ser_name += prod_obj.product_id.name+'\n'
                                serv_price +=prod_obj.price
                            if len(line.sub_components)>=2:
                                count=count-1
                                if count==0:
                                    pro_name=(pro_name.strip('\n'))
                                    ser_name=(ser_name.strip('\n'))
                                    datas.append(pro_name)
                                    datas.append(pro_price if pro_name else '')
                                    datas.append(ser_name)
                                    datas.append(serv_price if ser_name else '')
                                    if ((pro_name and pro_price==0.0) and (ser_name and serv_price==0.0)) and (line.product_id.list_price==0.00):
#                                        print"'Both are Free''Both are Free''Both are Free'"
                                        datas.append('Both are Free')
                                    elif pro_name and pro_price==0.0:
                                        datas.append('Free Device')
                                    elif ser_name and serv_price==0.0:
                                        datas.append('Free Service')
                                    else:
                                        datas.append('Paid')
                            elif len(line.sub_components)==1:
                                count=count-1
                                if count==0:
                                    pro_name=(pro_name.strip('\n'))
                                    ser_name=(ser_name.strip('\n'))
                                    datas.append(pro_name)
                                    datas.append(pro_price if pro_name else '')
                                    datas.append(ser_name)
                                    datas.append(serv_price if ser_name else '')
                                    if (pro_name and pro_price==0.0) and (line.product_id.list_price==0.00):
                                        datas.append('Free Device')
                                    elif (ser_name and serv_price==0.0) and (line.product_id.list_price==0.00):
                                        datas.append('Free Service')
                                    else:
                                        datas.append('Paid')
                    else:
                        datas.append(line.product_id.name if line.product_id and line.product_id.type=="product" else '')
                        datas.append(line.price_subtotal if line.product_id and line.product_id.type=="product" else '')
                        datas.append(line.product_id.name if ((line.product_id and line.product_id.type=="service") and (line.product_id.default_code!='SHIP'))else '')
                        datas.append(line.price_subtotal if ((line.product_id and line.product_id.type=="service") and (line.product_id.default_code!='SHIP')) else '')
                        if (line.price_subtotal==0.00):
                            datas.append('Free')
                        else:
                            datas.append('Paid')
                    datas.append(float(line.product_uom_qty))
                    datas.append(float(line.price_subtotal))
                    if sales_tax == 0.0 :
                        if so_id_obj.amount_tax >= 0.0:
                            sales_tax = so_id_obj.amount_tax
                            datas.append(sales_tax)
                    else:
                        datas.append(0.0)
                    datas.append((so_id_obj.user_id.name if so_id_obj.user_id else ''))

                    pls_write = writer.writerow(datas)
                    datas = []
#                    ##To Search Recurring billing for the Sale Order
#                    cr.execute("select id from account_invoice where recurring = True and state='paid' and id in (select invoice_id from sale_order_invoice_rel where order_id = %d)"%(so_id_obj.id))
#                    invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#                    if invoice_ids:
#                    
#                        amount_tax = 0.0
#                        for invoice_id_obj in invoice_obj.browse(cr,uid,invoice_ids):
##                            if invoice_id_obj.recurring==True:
#                            if invoice_id_obj.id in invoice_id_list:
#                                pass
#                            else:
#                                invoice_id_list.append(invoice_id_obj.id)
#                                inv_street,inv_city,inv_zip,inv_phone,inv_co_state = '','','','',''
#                                if invoice_id_obj.partner_id:
#                                    inv_street = str(invoice_id_obj.partner_id.street) + (str(invoice_id_obj.partner_id.street2) if (invoice_id_obj.partner_id.street2) else '')
#                                    inv_city = invoice_id_obj.partner_id.city
#                                    inv_zip = invoice_id_obj.partner_id.zip
#                                    inv_phone =  invoice_id_obj.partner_id.zip
#                                    if invoice_id_obj.partner_id.state_id:
#                                        inv_co_state = invoice_id_obj.partner_id.state_id.name
#                                for invoice_line in invoice_id_obj.invoice_line:
#                                    datas.append(invoice_id_obj.number)
#                                    datas.append(invoice_id_obj.partner_id.name)
#                                    datas.append(invoice_id_obj.partner_id.ref)
#                                    datas.append(inv_street)
#                                    datas.append(inv_city)
#                                    datas.append(inv_co_state)
#                                    datas.append(inv_zip)
#                                    datas.append(invoice_id_obj.partner_id.emailid)
#                                    datas.append(inv_phone)
#                                    datas.append(invoice_id_obj.date_invoice)
#                                    datas.append(invoice_id_obj.state)
#                                    datas.append('-')
#                                    datas.append('-')
#                                    datas.append('-')
#                                    datas.append(invoice_line.name)
#                                    datas.extend(['','','','','Paid'])
#                                    datas.append(invoice_line.quantity)
#                                    datas.append(invoice_line.price_subtotal)
#                                    if amount_tax == 0.0 :
#                                        if invoice_id_obj.amount_tax >=0.0:
#                                            amount_tax = invoice_id_obj.amount_tax
#                                            datas.append(amount_tax)
#                                    else:
#                                        datas.append(0.0)
#                                    datas.append(invoice_id_obj.user_id.name)
#                                    datas.extend(['-','-',0.0,0.0,0.0])
#                                    pls_write = writer.writerow(datas)
#                                    datas = []
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


    def export_cancel_order (self,cr,uid,ids,policy_id):
        sale_obj=self.pool.get('sale.order')
        return_obj=self.pool.get('return.order')
        policy_obj=self.pool.get('res.partner.policy')
        policy_brw=policy_obj.browse(cr,uid,policy_id)
        sale_id=policy_brw.sale_id
        datas=""
        cr.execute("select id from credit_service_line where service_id in (select id from res_partner_policy where active_service=False and id=%s)"%(policy_id))
        credit_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
        if credit_line_id:
            if policy_brw.active_service==False:
                credit_line_brw=self.pool.get('credit.service.line').browse(cr,uid,credit_line_id)
                for line in credit_line_brw:
                    if line.order_id.state=='done':
                        sale_brw=sale_obj.browse(cr,uid,line.service_id.sale_id)
                        phone,sales_tax,return_tax ='',0.0,0.0
                        line_ids,prod_ids,cancel_return_reason = [],[],''
                        datas +=str((line.service_id.sale_order if line.service_id else line.name))+","+str(line.order_id.name if line.order_id else '')+"\
                                ,"+str((line.order_partner_id.name.replace(',','') if line.order_partner_id else '' ))+","+str((line.order_partner_id.ref if line.order_partner_id.ref else ''))+"\
                                ,"+str((line.order_partner_id.emailid if line.order_partner_id.emailid else ''))+","+str(line.service_id.agmnt_partner.phone if line.service_id.agmnt_partner else '')+"\
                                ,"+str(line.order_id.state if line.order_id else '')+","+str('')+"\
                                ,"+str((line.product_id.name.replace(',','') if line.service_id else line.name))+"\
                                ,"+str(line.product_uom_qty)+","+str(line.price_subtotal)
                        if sales_tax == 0.0 :
                            if line.order_id.amount_tax >= 0.0:
                                sales_tax = line.order_id.amount_tax
                                datas += ","+str(sales_tax)
                        else:
                            datas += ","+str('0.0')
                        datas +=","+str((line.order_id.user_id.name.replace(',','') if line.order_id.user_id else ''))+","+str('Inactive')+"\
                                ,"+str((line.order_id.date_order if line.order_id.date_order else ''))+","+str((sale_brw.date_order if line.service_id.sale_id else '' ))+"\
                                ,"+str((sale_brw.location_id.name.replace(',','') if line.service_id.sale_id else ''))+"\n"
        else:
            return_id=return_obj.search(cr,uid,[('linked_sale_order','=',sale_id),('state','=','done')])
            if return_id:
                datas=self.export_return_order(cr,uid,ids,sale_id)
            elif policy_brw.sale_order:
                active_service=policy_brw.active_service
                datas=self.export_suspension_orders(cr,uid,ids,policy_brw.sale_order,active_service)
            else:
                pass
        return datas
    def export_return_order(self,cr,uid,ids,sale_id):
        datas = ""
        return_obj = self.pool.get('return.order')
        return_id = return_obj.search(cr,uid,[('linked_sale_order','=',sale_id),('state','=','done')])
        if return_id:
            return_brw=return_obj.browse(cr,uid,return_id[0])
            purchase_date=return_brw.linked_sale_order.date_order
            location=return_brw.linked_sale_order.location_id.name

            for line in return_obj.browse(cr,uid,return_id[0]).order_line:
                if return_id[0]:
                    phone,return_type,sales_tax,return_tax ='','',0.0,0.0
                if return_brw.return_type=='car_return':
                    return_type = 'Credit Return'
                if line.product_id.name!='Shipping costs':
                    datas +=str((return_brw.linked_sale_order.name if return_brw.linked_sale_order else ''))+","+str(return_brw.name)+"\
                            ,"+str((return_brw.partner_id.name.replace(',','')))+","+str((return_brw.partner_id.ref if return_brw.partner_id.ref else ''))+"\
                            ,"+str((return_brw.partner_id.emailid))+","+str((return_brw.partner_id.phone.replace(';','') if return_brw.partner_id else ''))+"\
                            ,"+str(return_brw.state)+","+str(return_type)+"\
                            ,"+str((line.product_id.name.replace(',','') if line.product_id else line.name))+","+str((line.product_uom_qty))+"\
                            ,"+str(line.price_subtotal)
                    if sales_tax == 0.0 :
                        if return_brw.amount_tax >= 0.0:
                            sales_tax = return_brw.amount_tax
                            datas += ","+str(sales_tax)
                    else:
                        datas += ","+str('0.0')
                    datas +=","+str((return_brw.user_id.name.replace(',','') if return_brw.user_id else ''))+","+str('Inactive')+"\
                            ,"+str(return_brw.date_order or '')+","+str(purchase_date)+"\
                            ,"+str(location.replace(',',''))+"\n"
            return datas
    def export_suspension_orders(self,cr,uid,ids,sale_ref,active_service):
        datas=""
        payment_obj=self.pool.get('partner.payment.error')
        sale_obj=self.pool.get('sale.order')
        acc_inv_obj=self.pool.get('account.invoice')
        sale_id=sale_obj.search(cr,uid,[('name','=',sale_ref)])
        if sale_id:
            sale_brw=sale_obj.browse(cr,uid,sale_id[0])
            purchase_date=sale_brw.date_order
            location=sale_brw.location_id.name
        sale_reference='RB'+sale_ref
        cr.execute("select id,invoice_date from partner_payment_error where invoice_name = '%s' order by invoice_date desc"%(sale_reference),)
        exceptions = filter(None, map(lambda x:x[0], cr.fetchall()))
        if exceptions:
#            print "exceptionsexceptionsexceptionsexceptions",exceptions
            street,city,zip,phone,country_state,return_type,sales_tax,return_tax ='','','','','','',0.0,0.0
            payment_brw=payment_obj.browse(cr,uid,exceptions[0])
            inv_id=acc_inv_obj.search(cr,uid,[('origin','=',sale_reference),('state','=','draft')])
            if inv_id:
                for inv_id in acc_inv_obj.browse(cr,uid,inv_id):
                    for each_line in inv_id.invoice_line:
                        datas +=str(sale_ref if sale_ref else '')+","+str(sale_reference if sale_reference else '')+"\
                            ,"+str((payment_brw.partner_id.name.replace(',','') if payment_brw.partner_id else ''))+","+str((payment_brw.partner_id.ref if payment_brw.partner_id.ref else ''))+"\
                            ,"+str((payment_brw.partner_id.emailid if payment_brw.partner_id else '' ))+","+str((payment_brw.partner_id.phone if payment_brw.partner_id else ''))+"\
                            ,"+str(inv_id.state if inv_id else '')+","+str('')
                        if each_line.product_id.name!='Shipping costs':
                            datas += ","+str((each_line.product_id.name.replace(',','') if each_line.product_id else ''))+","+str(each_line.quantity if each_line.product_id else '')+"\
                            ,"+str((each_line.price_subtotal if each_line.product_id else ''))
                        if sales_tax == 0.0 :
                            if inv_id.amount_tax >= 0.0:
                                sales_tax = inv_id.amount_tax
                                datas += ","+str(sales_tax)
                            else:
                                datas += ","+str('0.0')
                        datas += ","+str((inv_id.user_id.name.replace(',','') if inv_id.user_id else ''))
                        if (active_service==True):
                            active_inactive='Active'
                        else:
                            active_inactive='Inactive'
                        datas += ","+str((active_inactive))+","+str(inv_id.date_invoice if inv_id else '')+"\
                            ,"+str(purchase_date if purchase_date else'' )+","+str(location.replace(',','') if location else '' )+"\n"
                return datas

    def export_cancel_service_csv(self,cr,uid,ids,context={}):
        list_sale_policy_ids = [] ## list to store all the appended sale ids from policy
        policy_obj = self.pool.get('res.partner.policy')
        f = open('/tmp/Churn Report.csv','w')
        self_obj=self.browse(cr,uid,ids[0])
        datas = ""
        datas = "Sale No"+","+"Return No/Credit No"+","+"Customer Name"+","+"Customer No"+","+"Email ID"+","+"Phone Number"+","+"Order State"+","+"Return Type"+","+"Product Name"+","+"ReturnQuantity"+","+"Revenue"+","+"Returns Tax"+","+"User"+","+"Active/Inactive"+","+"Cancel/Return Date"+","+"Purchase Date"+","+"Location"+"\n"
        f.write(datas)
        datas = ""
        if (self_obj.date_from and self_obj.date_to):
            cr.execute("select id from res_partner_policy where (return_date between '%s' and '%s') or (suspension_date between '%s' and '%s') or (cancel_date between '%s' and '%s')"%(self_obj.date_from,self_obj.date_to,self_obj.date_from,self_obj.date_to,self_obj.date_from,self_obj.date_to))
            policy_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            for policy_brw in policy_obj.browse(cr,uid,policy_ids):
                sale_id=policy_brw.sale_id
                return_date=policy_brw.return_date
                suspension_date=policy_brw.suspension_date
                cancel_date=policy_brw.cancel_date
                if return_date and sale_id:
                    if policy_brw.active_service==False:
                        datas=self.export_return_order(cr,uid,ids,sale_id)
                elif cancel_date:
                    if policy_brw.sale_id and policy_brw.sale_id in list_sale_policy_ids:
                        pass
                    else:
                        datas=self.export_cancel_order(cr,uid,ids,policy_brw.id)
                        list_sale_policy_ids.append(policy_brw.sale_id)
                elif suspension_date and policy_brw.sale_order:
                    active_service=policy_brw.active_service
                    datas=self.export_suspension_orders(cr,uid,ids,policy_brw.sale_order,active_service)
                if datas:
                    f.write(datas)
                    datas=""
                else:
                    continue
            f = open("/tmp/Churn Report.csv","rb")
            bytes = f.read()
            out = base64.encodestring(bytes)
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
export_cancel_service_csv()
