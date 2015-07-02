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
        f = open('/tmp/Sales Report.csv','w')
        if self_obj.date_from and self_obj.date_to:
            search_so = so_obj.search(cr,uid,[('date_order','>=',self_obj.date_from),('date_order','<=',self_obj.date_to),('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
        elif self_obj.date_from:
            search_so = so_obj.search(cr,uid,[('date_order','>=',self_obj.date_from),('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
        elif self_obj.date_to:
            search_so = so_obj.search(cr,uid,[('date_order','<=',self_obj.date_to),('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
        else:
            search_so = so_obj.search(cr,uid,[('state','in',('progress','done')),('create_date','>','2013-10-29'),('invoiced','=',True)])
        if search_so:
            datas = "Sale No"+","+"Customer Name"+","+"Customer No"+","+"Street"+","+"City"+","+"State"+","+"Zip"+","+"Email ID"+","+"Phone Number"+","+"Date"+","+"Order State"+","+"Promo Code"+","+"Sales Channel"+","+"Location Name"+","+"Offer/Product Name"+","+"Device"+","+"Device Price(in this offer)"+","+"Service"+","+"Service Price(in this offer)"+","+"Free/Paid"+","+"Quantity"+","+"Offer Price"+","+"Sales Tax"+","+"User"+","+"Return No."+","+"Return Order Date"+","+"Return Product Name"+","+"Return Quantity"+","+"Return Amount"+","+"Return Tax"+","+"Return Reason"+","+"Active/Inactive"+","+"Cancel/Return Date"+ "\n"
            f.write(datas)
            datas = ""
            count=0
            i = 0
            while(i<len(search_so)):
                so_id_obj = so_obj.browse(cr, uid, search_so[i])
#            for so_id_obj in so_obj.browse(cr,uid,search_so):
#                print"so_id_objso_id_objso_id_objso_id_obj",so_id_obj
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
                    street = str(so_id_obj.partner_invoice_id.street) + (str(so_id_obj.partner_invoice_id.street2) if (so_id_obj.partner_invoice_id.street2) else '')
                    city = so_id_obj.partner_invoice_id.city
                    zip = so_id_obj.partner_invoice_id.zip
                    phone = so_id_obj.partner_invoice_id.phone
                    if so_id_obj.partner_invoice_id.state_id:
                        country_state = so_id_obj.partner_invoice_id.state_id.name
                for line in so_id_obj.order_line:
                    return_line_id_obj,line_ids,prod_ids,cancel_return_reason = False,[],[],''
                    datas += str(so_id_obj.name)+","+str(so_id_obj.partner_id.name)+"\
                                ,"+str((so_id_obj.partner_id.ref if so_id_obj.partner_id.ref else ''))+","+str(street)+"\
                                ,"+str(city)+","+str(country_state)+"\
                                ,"+str(zip)+","+str(so_id_obj.partner_id.emailid)+"\
                                ,"+str(phone)+","+str(so_id_obj.date_confirm)+"\
                                ,"+str(so_id_obj.state)+","+str((so_id_obj.promo_code if so_id_obj.promo_code else ''))+"\
                                ,"+str(sales_channel)+","+str((so_id_obj.location_id.name if so_id_obj.location_id else ''))+"\
                                ,"+str((line.product_id.name if line.product_id else line.name))
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
                                    datas += ","+str(pro_name)+","+str(pro_price if pro_name else '')+","+str(ser_name)+","+str(serv_price if ser_name else '')
                                    if ((pro_name and pro_price==0.0) and (ser_name and serv_price==0.0)) and (line.product_id.list_price==0.00):
#                                        print"'Both are Free''Both are Free''Both are Free'"
                                        datas += ","+'Both are Free'
                                    elif pro_name and pro_price==0.0:
                                        datas += ","+'Free Device'
                                    elif ser_name and serv_price==0.0:
                                        datas += ","+'Free Service'
                                    else:
                                        datas += ","+'Paid'
                            elif len(line.sub_components)==1:
                                count=count-1
                                if count==0:
                                    pro_name=(pro_name.strip('\n'))
                                    ser_name=(ser_name.strip('\n'))
                                    datas += ","+str(pro_name)+","+str(pro_price if pro_name else '')+"\
                                    ,"+str(ser_name)+","+str(serv_price if ser_name else '')
                                    if (pro_name and pro_price==0.0) and (line.product_id.list_price==0.00):
                                        datas += ","+'Free Device'
                                    elif (ser_name and serv_price==0.0) and (line.product_id.list_price==0.00):
                                        datas += ","+'Free Service'
                                    else:
                                        datas += ","+'Paid'
                    else:
                        datas += ","+str(line.product_id.name if line.product_id and line.product_id.type=="product" else '')+","+str(line.product_id.list_price if line.product_id and line.product_id.type=="product" else '')+"\
                                    ,"+str((line.product_id.name if ((line.product_id and line.product_id.type=="service") and (line.product_id.default_code!='SHIP'))else ''))+","+str((line.product_id.list_price if ((line.product_id and line.product_id.type=="service") and (line.product_id.default_code!='SHIP')) else ''))
                        if ((line.product_id and line.product_id.list_price==0.00) and (line.price_subtotal==0.00)) :
                            datas += ","+'Free'
                        else:
                            datas += ","+'Paid'
                    datas += ","+str(line.product_uom_qty)
                    datas += ","+str(line.price_subtotal)
                    if sales_tax == 0.0 :
                        if so_id_obj.amount_tax >= 0.0:
                            sales_tax = so_id_obj.amount_tax
                            datas += ","+str(sales_tax)
                    else:
                        datas += ","+'0.0'
                    datas += ","+str((so_id_obj.user_id.name if so_id_obj.user_id else ''))
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
                        datas += ","+str(roname)+","+str(rodate)+"\
                                ,"+str(rolinename)+"\
                                ,"+str(('-'+str(qty)))+","+str(('-'+str(line_subtotal)))+"\
                                ,"+str(('-'+str(roamount_tax)))
                    if not result_return:
                        datas += ","+str('-')+","+str('-')+"\
                                ,"+str('-')+"\
                                ,"+str('0.0')+","+str('0.0')+","+str('0.0')
                    if line_ids and prod_ids:
                        print"line_idsline_idsline_idsline_ids",so_id_obj,line_ids,prod_ids
                        search_partner_policy = policy_obj.search(cr,uid,[('sale_line_id','in',line_ids),('product_id','in',prod_ids)])
                        if search_partner_policy:
                            search_partner_policy.sort()
                            policy_brw = policy_obj.browse(cr,uid,search_partner_policy[-1])
                            if policy_brw.additional_info:
                                cancel_return_reason = partner_obj.return_cancel_reason_extract(policy_brw.additional_info)
                                cancel_return_reason = cancel_return_reason.get('cancel_return_reason','')
                            active_inactive = ('Inactive' if not policy_brw.active_service else 'Active')
                            cancel_date = policy_brw.cancel_date
                            datas += ","+str(cancel_return_reason)+","+str(active_inactive)+"\
                                ,"+str((cancel_date if cancel_date else ''))+"\n"
                        else:
                            datas += ","+str("-")+","+str("-")+"\
                                ,"+str(("-"))+"\n"
                f.write(datas)
                datas=""
                i+=1
#                    pls_write = writer.writerow(datas)
##                    datas = []
#                ##To Search Recurring billing for the Sale Order
                cr.execute("select id from account_invoice where recurring = True and state='paid' and id in (select invoice_id from sale_order_invoice_rel where order_id = %d)"%(so_id_obj.id))
                invoice_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                if invoice_ids:
                    j=0
                    invoice_obj = self.pool.get('account.invoice')
                    amount_tax = 0.0
                    while(j<len(invoice_ids)):

                        invoice_id_obj=invoice_obj.browse(cr,uid,invoice_ids[j])

#                    for invoice_id_obj in invoice_obj.browse(cr,uid,invoice_ids):
                        inv_street,inv_city,inv_zip,inv_phone,inv_co_state = '','','','',''
                        if invoice_id_obj.partner_id:
                            inv_street = str(invoice_id_obj.partner_id.street) + (str(invoice_id_obj.partner_id.street2) if (invoice_id_obj.partner_id.street2) else '')
                            inv_city = invoice_id_obj.partner_id.city
                            inv_zip = invoice_id_obj.partner_id.zip
                            inv_phone =  invoice_id_obj.partner_id.zip
                            if invoice_id_obj.partner_id.state_id:
                                inv_co_state = invoice_id_obj.partner_id.state_id.name
                        for invoice_line in invoice_id_obj.invoice_line:
                            datas +=str(invoice_id_obj.number)+","+str(invoice_id_obj.partner_id.name)+"\
                            ,"+str(invoice_id_obj.partner_id.ref)+","+str(inv_street)+"\
                            ,"+str(inv_city)+","+str(inv_co_state)+"\
                            ,"+str(inv_zip)+","+str(invoice_id_obj.partner_id.emailid)+"\
                            ,"+str(inv_phone)+","+str(invoice_id_obj.date_invoice)+"\
                            ,"+str(invoice_id_obj.state)+","+str('-')+","+str('-')+","+str('-')+","+str(invoice_line.name)+str('-')+"\
                            ,"+str(invoice_line.quantity)+","+str(invoice_line.price_subtotal)
                            if amount_tax == 0.0:
                                if invoice_id_obj.amount_tax >=0.0:
                                    amount_tax = invoice_id_obj.amount_tax
                                    datas += ","+str(amount_tax)+"\n"
                            else:
                                datas += ","+ str('0.0')+"\n"
                            f.write(datas)
                            datas=""
                            j+=1
##                            pls_write = writer.writerow(datas)
##                            datas = []
##                            datas=""
                    f.write(datas)
                    datas=""
            f = open("/tmp/Sales Report.csv","rb")
            bytes = f.read()
            out = base64.encodestring(bytes)
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
        acc_inv_obj=self.pool.get('account.invoice')
        return_obj = self.pool.get('return.order')
        payment_obj = self.pool.get('partner.payment.error')
        policy_obj = self.pool.get('res.partner.policy')
        sale_obj= self.pool.get('sale.order')
        self_obj=self.browse(cr,uid,ids[0])
        search_so=[]
        datas = []
        active_inactive=''
        buf=cStringIO.StringIO()
        writer=csv.writer(buf, 'UNIX')
        if (self_obj.date_from and self_obj.date_to):
            cancelled_orders=policy_obj.search(cr,uid,[('cancel_date','>=',self_obj.date_from),('cancel_date','<=',self_obj.date_to),('active_service','=',False)])
            return_orders=policy_obj.search(cr,uid,[('return_date','>=',self_obj.date_from),('return_date','<=',self_obj.date_to),('active_service','=',False)])
            suspended_orders=policy_obj.search(cr,uid,[('suspension_date','>=',self_obj.date_from),('suspension_date','<=',self_obj.date_to)])
#            print "cancelled_orderscancelled_orders",cancelled_orders
#            print "return_ordersreturn_ordersreturn_ordersreturn_orders",return_orders
            print "suspended_orderssuspended_orderssuspended_orders",suspended_orders
            datas = ["Sale No.","Return No/Credit No","Customer Name","Customer No",
           "Email ID","Phone Number",
            "Order State","Return Type",
            "Product Name"," ReturnQuantity","Revenue","Returns Tax","User",
            "Active/Inactive","Cancel/Return Date","Purchase Date","Location"]
            pls_write = writer.writerow(datas)
            datas = []
        if return_orders:
            count=0
            date_cancel=''
            count=0
            for return_policy in policy_obj.browse(cr,uid,return_orders):
                date_return=return_policy.return_date
                phone,return_type,sales_tax,return_tax ='','',0.0,0.0
                sale_ref=return_policy.sale_order
                sale_id=sale_obj.search(cr,uid,[('name','=',sale_ref)])
#                print "sale id................",sale_id
                sale_brw=sale_obj.browse(cr,uid,sale_id[0])
                return_id = return_obj.search(cr,uid,[('linked_sale_order','=',sale_ref),('state','=','done')])
                if return_id:
                    return_brw=return_obj.browse(cr,uid,return_id[0])
                    purchase_date=sale_brw.date_order
                    location=sale_brw.location_id.name
                    if return_brw.return_type:
                        if return_brw.return_type =='car_return':
                            return_type = 'Credit Return'
                    for line in return_obj.browse(cr,uid,return_id[0]).order_line:
                        if line.product_id.type =='product':
                            datas.append(sale_ref)
                            datas.append(return_brw.name)
                            datas.append(return_brw.partner_id.name)
                            datas.append(return_brw.partner_id.ref if return_brw.partner_id.ref else '')
                            datas.append(return_brw.partner_id.emailid)
                            datas.append(return_brw.partner_id.phone if return_brw.partner_id else '')
                            datas.append(return_brw.state)
                            datas.append(return_type)
                            datas.append((line.product_id.name if line.product_id else line.name))
                            datas.append(float(line.product_uom_qty))
                            datas.append(float(line.price_subtotal))
                            if sales_tax == 0.0 :
                                if return_brw.amount_tax >= 0.0:
                                    sales_tax = return_brw.amount_tax
                                    datas.append(sales_tax)
                            else:
                                datas.append(0.0)
                            datas.append((return_brw.user_id.name if return_brw.user_id else ''))
                            datas.append('Inactive')
                            datas.append(date_return or '')
                            datas.append(purchase_date)
                            datas.append(location)
                            count=count+1
                            pls_write = writer.writerow(datas)
                            datas = []

        if cancelled_orders:

#            print "lenghth of cancel purderssssssssssssss",len(cancelled_orders)
            for cancel_policy in policy_obj.browse(cr,uid,cancelled_orders):
                print "cancel_policycancel_policy",cancel_policy
                sale_ref=cancel_policy.sale_order
                print "sale_refsale_refsale_ref",sale_ref
                sale_id=sale_obj.search(cr,uid,[('name','=',sale_ref)])
#                print "sale id................",sale_id
                if sale_id:
                    sale_brw=sale_obj.browse(cr,uid,sale_id[0])
                    purchase_date=sale_brw.date_order
                    location=sale_brw.location_id.name
                suspension_date=cancel_policy.suspension_date
                cancel_date=cancel_policy.cancel_date
                if cancel_date and suspension_date:
                    if cancel_date < suspension_date:
                        cr.execute("select id from credit_service_line where service_id=%s"%(cancel_policy.id))
                        credit_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                        if credit_line_id:
                            credit_line_brw=self.pool.get('credit.service.line').browse(cr,uid,credit_line_id)
                            for line in credit_line_brw:
#                                print "lineeeeeeeeeeeeeeeeeee",line
                                phone,sales_tax,return_tax ='',0.0,0.0
                                line_ids,prod_ids,cancel_return_reason = [],[],''
                                datas.append((line.service_id.sale_order if line.service_id else line.name))
                                datas.append(line.order_id.name if line.order_id else '')
                                datas.append(line.order_partner_id.name if line.order_partner_id else '' )
                                datas.append(line.order_partner_id.ref if line.order_partner_id.ref else '')
                                datas.append(line.order_partner_id.emailid)
                                datas.append(cancel_policy.agmnt_partner.phone if cancel_policy.agmnt_partner else '')
                                datas.append(line.order_id.state)
                                datas.append('')
                                datas.append((line.product_id.name if line.service_id else line.name))
                                datas.append(float(line.product_uom_qty))
                                datas.append(float(line.price_subtotal))
                                if sales_tax == 0.0 :
                                    if line.order_id.amount_tax >= 0.0:
                                        sales_tax = line.order_id.amount_tax
                                        datas.append(sales_tax)
                                else:
                                    datas.append(0.0)
                                datas.append((line.order_id.user_id.name if line.order_id.user_id else ''))
                                datas.append('Inactive')
                                datas.append((line.service_id.cancel_date if line.service_id else ''))
                                datas.append(purchase_date)
                                datas.append(location)
                                pls_write = writer.writerow(datas)
                                datas = []
                elif cancel_date and not suspension_date:
                    cr.execute("select id from credit_service_line where service_id=%s"%(cancel_policy.id))
                    credit_line_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if credit_line_id:
                        credit_line_brw=self.pool.get('credit.service.line').browse(cr,uid,credit_line_id)
                        for line in credit_line_brw:
#                            print "lineeeeeeeeeeeeeeeeeee",line
                            phone,sales_tax,return_tax ='',0.0,0.0
                            line_ids,prod_ids,cancel_return_reason = [],[],''
                            datas.append((line.service_id.sale_order if line.service_id else line.name))
                            datas.append(line.order_id.name if line.order_id else '')
                            datas.append(line.order_partner_id.name if line.order_partner_id else '' )
                            datas.append(line.order_partner_id.ref if line.order_partner_id.ref else '')
                            datas.append(line.order_partner_id.emailid)
                            datas.append(cancel_policy.agmnt_partner.phone if cancel_policy.agmnt_partner else '')
                            datas.append(line.order_id.state)
                            datas.append('')
                            datas.append((line.product_id.name if line.service_id else line.name))
                            datas.append(float(line.product_uom_qty))
                            datas.append(float(line.price_subtotal))
                            if sales_tax == 0.0 :
                                if line.order_id.amount_tax >= 0.0:
                                    sales_tax = line.order_id.amount_tax
                                    datas.append(sales_tax)
                            else:
                                datas.append(0.0)
                            datas.append((line.order_id.user_id.name if line.order_id.user_id else ''))
                            datas.append('Inactive')
                            datas.append((line.service_id.cancel_date if line.service_id else ''))
                            datas.append(purchase_date)
                            datas.append(location)
                            pls_write = writer.writerow(datas)
                            datas = []
        if suspended_orders:

            street,city,zip,phone,country_state,return_type,sales_tax,return_tax ='','','','','','',0.0,0.0
            for suspension_obj in policy_obj.browse(cr,uid,suspended_orders):
                sale_ref=suspension_obj.sale_order
                sale_id=sale_obj.search(cr,uid,[('name','=',sale_ref)])
                if sale_id:
                    print "sale id................",sale_id
                    sale_brw=sale_obj.browse(cr,uid,sale_id[0])
                    purchase_date=sale_brw.date_order
                    location=sale_brw.location_id.name
                sus_date=suspension_obj.suspension_date
                cancel_date=suspension_obj.cancel_date
                if cancel_date and sus_date:
                    active_inactive=suspension_obj.active_service
                    if sus_date<cancel_date:
                        print "11111111111111111111111111111",sus_date,cancel_date
                        so_ref=suspension_obj.sale_order
                        sale_ref='RB'+suspension_obj.sale_order
                        print "sale_refsale_refsale_ref",sale_ref
                        cr.execute("select id,invoice_date from partner_payment_error where invoice_name = '%s' order by invoice_date desc"%(sale_ref),)
                        exceptions = filter(None, map(lambda x:x[0], cr.fetchall()))
                        print "exceptionsvexceptionsexceptions",exceptions
                        if exceptions:
                            payment_brw=payment_obj.browse(cr,uid,exceptions[0])
                            inv_id=acc_inv_obj.search(cr,uid,[('origin','=',sale_ref),('state','=','draft')])
                            if inv_id:
                                for inv_id in acc_inv_obj.browse(cr,uid,inv_id):
                                    print "invoice id...............",inv_id
                                    for each_line in inv_id.invoice_line:
#                                        if each_line.product_id.type =='product':
				    	datas.append(so_ref if so_ref else '')
					datas.append(sale_ref if sale_ref else '')
					datas.append(payment_brw.partner_id.name if payment_brw.partner_id else '' )
					datas.append(payment_brw.partner_id.ref if payment_brw.partner_id.ref else '')
					datas.append(payment_brw.partner_id.emailid if payment_brw.partner_id else '' )
					datas.append(payment_brw.partner_id.phone if payment_brw.partner_id else '')
					datas.append(inv_id.state if inv_id else '')
					datas.append('')
					if each_line.product_id.name!='Shipping costs':
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
					if (active_inactive==True):
                                            active_inactive='Active'
					else:
                                            active_inactive='Inactive'
					datas.append(active_inactive)
					datas.append(inv_id.date_invoice if inv_id else '')
					datas.append(purchase_date)
					datas.append(location)
#                                       print "datass of suspensionnnnnnnnnnnnnnnnn",datas
					pls_write = writer.writerow(datas)
					datas = []
                elif sus_date and not cancel_date:
                    so_ref=suspension_obj.sale_order
                    active_inactive=suspension_obj.active_service
                    sale_ref='RB'+suspension_obj.sale_order
                    print "sale_refsale_refsale_ref",sale_ref
                    exceptions=payment_obj.search(cr,uid,[('invoice_name','=',sale_ref),('partner_id','=',suspension_obj.agmnt_partner.name)])
                    print "exceptionsvexceptionsexceptions",exceptions
                    if exceptions:
                        print "exceptionsexceptionsexceptions",exceptions
                        for each in payment_obj.browse(cr,uid,exceptions):
                            inv_id=acc_inv_obj.search(cr,uid,[('origin','=',sale_ref),('state','=','draft')])
                            print "invoce id..............",inv_id
                            if inv_id:
                                for inv_id in acc_inv_obj.browse(cr,uid,inv_id):
                                    print "invoice id...............",inv_id
                                    for each_line in inv_id.invoice_line:
#                                        if each_line.product_id.type=='product':
                                        datas.append(so_ref if so_ref else '')
                                        datas.append(sale_ref if sale_ref else '')
                                        datas.append(each.partner_id.name if each.partner_id else '' )
                                        datas.append(each.partner_id.ref if each.partner_id.ref else '')
                                        datas.append(each.partner_id.emailid if each.partner_id else '' )
                                        datas.append(each.partner_id.phone if each.partner_id else '')
                                        datas.append(inv_id.state if inv_id else '')
                                        print "dats.................",datas
                                        datas.append('')
                                        if each_line.product_id.name!='Shipping costs':
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
                                        if (active_inactive==True):
                                            active_inactive='Active'
                                        else:
                                            active_inactive='Inactive'
                                        datas.append(active_inactive)
                                        datas.append(inv_id.date_invoice if inv_id else '')
                                        datas.append(purchase_date)
                                        datas.append(location)
#                                            print "datass of suspensionnnnnnnnnnnnnnnnn",datas
                                        pls_write = writer.writerow(datas)
                                        datas = []

#            pls_write = writer.writerow(datas)
#            datas = []
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
export_cancel_service_csv()
