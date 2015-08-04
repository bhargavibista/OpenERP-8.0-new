# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import osv, fields
import csv
import cStringIO
import base64
#from dbexts import sort
from dateutil import parser

class export_customer_history(osv.osv_memory):
    """ Export Module """
    _name = "export.customer.history"
    _description = "Export CSV"
    _columns = {
        'name' : fields.char('Name',size=32),
        'csv_file' : fields.binary('CSV file'),
        'date_from':fields.date('From'),
        'date_to':fields.date('To'),
    }

    def export_customer_details(self,cr,uid,ids,context={}):
        so_obj = self.pool.get('sale.order')
        return_obj = self.pool.get('return.order')
	partner_obj = self.pool.get('res.partner')
        so_line_obj = self.pool.get('sale.order.line')
        return_line_obj = self.pool.get('return.order.line')
        policy_obj = self.pool.get('res.partner.policy')
        self_obj=self.browse(cr,uid,ids[0])
        search_so = so_obj.search(cr,uid,[('state','in',('progress','done')),('create_date','>=',self_obj.date_from),('create_date','<=',self_obj.date_to)])
        return_so = return_obj.search(cr,uid,[('date_order','>=',self_obj.date_from),('date_order','<=',self_obj.date_to)])
        cr.execute("select partner_id from sale_order where create_date >= '%s' and create_date <= '%s'"%(self_obj.date_from,self_obj.date_to))
        so_partner_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        cr.execute("select partner_id from return_order where date_order >= '%s' and date_order <= '%s'"%(self_obj.date_from,self_obj.date_to))
        return_partner_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#        cr.execute("select id from sale_order where state in ('progress','done') and create_date >= '2013-10-29' and invoiced = True")
#        search_so = filter(None, map(lambda x:x[0], cr.fetchall()))
#        search_so = [1503]
        datas = ["Customer Details","","","","","","","","",
        "Sale Order","","","","","","","","","","","","","","","","",
        "Return","","","","","","","","","","","",
        "Rental","","","","",""]
        buf=cStringIO.StringIO()
        writer=csv.writer(buf, 'UNIX')
        pls_write = writer.writerow(datas)
        datas = []
        all_partners=[]
        all_partners =list(set(so_partner_ids+return_partner_ids))
        partners=all_partners
        if search_so and all_partners:
            datas = ["Customer No","Customer Name","Street", "City","State","Zip","Email ID","Phone Number","Date",
            "Sale No.","Sales Channel","Order Date","Creation Date","Confirm Date", "Product Name","Quantity","Promo Code",
            "Untaxed Amount","Taxes","Shipping Cost","Total", "Order Status","Card Number","Paid",
            "Shipping","Invoice No",
            "Return Status","Return No.","Sale Reference","Return Type","Return Order Date","Return Product Name",
            "Return Quantity","Return Amount","Return Tax","Return Reason","Return Invoice Ref","Expense Account",
            "Rental Transaction Data","Origin","Invoice No.","Invoice Total","Invoice Date","Account Receivable"]
#            buf=cStringIO.StringIO()
#            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            datas = []
            orders=[]
            for partner in all_partners:
                so_orders = so_obj.search(cr,uid,[('partner_id','=',partner)])
                ro_orders = return_obj.search(cr,uid,[('partner_id','=',partner)])
                for so_id_obj in so_obj.browse(cr,uid,so_orders):
                    street,city,zip,phone,country_state,sales_channel,sales_tax,return_tax ='','','','','','',0.0,0.0
                    if so_id_obj.cox_sales_channels:
                        if so_id_obj.cox_sales_channels =='call_center':
                            sales_channel = 'Call Center'
                        elif so_id_obj.cox_sales_channels =='ecommerce':
                            sales_channel = 'Ecommerce'
                        elif so_id_obj.cox_sales_channels =='retail':
                            sales_channel = 'Retail Store'
                    if so_id_obj.partner_invoice_id:
                        street = str(so_id_obj.partner_invoice_id.street) + (str(so_id_obj.partner_invoice_id.street2) if (so_id_obj.partner_invoice_id.street2) else '')
                        city = so_id_obj.partner_invoice_id.city
                        zip = so_id_obj.partner_invoice_id.zip
                        phone = so_id_obj.partner_invoice_id.phone
                        if so_id_obj.partner_invoice_id.state_id:
                            country_state = so_id_obj.partner_invoice_id.state_id.name
                    for line in so_id_obj.order_line:
                        return_line_id_obj,line_ids,prod_ids,cancel_return_reason = False,[],[],''
                        datas.append(so_id_obj.partner_id.ref if so_id_obj.partner_id.ref else '')
                        datas.append(so_id_obj.partner_id.name)
                        datas.append(street)
                        datas.append(city)
                        datas.append(country_state)
                        datas.append(zip)
                        datas.append(so_id_obj.partner_id.emailid)
                        datas.append(phone)
                        datas.append(so_id_obj.partner_id.date)
                        datas.append(so_id_obj.name)
                        datas.append(sales_channel)
                        datas.append(so_id_obj.date_order)
                        datas.append(so_id_obj.create_date)
                        datas.append(so_id_obj.date_confirm)
                        datas.append((line.product_id.name if line.product_id else line.name))
                        datas.append(float(line.product_uom_qty))
                        datas.append(so_id_obj.promo_code if so_id_obj.promo_code else '')
    #                    datas.append((so_id_obj.location_id.name if so_id_obj.location_id else ''))

                        datas.append(float(line.price_subtotal))
                        if sales_tax == 0.0 :
                            if so_id_obj.amount_tax >= 0.0:
                                sales_tax = so_id_obj.amount_tax
                                datas.append(sales_tax)
                        else:
                            datas.append(0.0)
                        inv_number=''
                        a=[]
                        [a.append(str(invoice.number)) if invoice.number else '' for invoice in so_id_obj.invoice_ids]
                        b=(str(a).replace('[', '').replace(']','')).replace('False','')
                        datas.append(0.0)
                        datas.append(so_id_obj.amount_total)
                        datas.append(so_id_obj.state)
                        datas.append(so_id_obj.cc_number)
                        datas.append(so_id_obj.invoiced)
                        datas.append(so_id_obj.shipped)
                        datas.append(b)
#                        datas.append(so_id_obj)
                        
    #                    datas.append((so_id_obj.user_id.name if so_id_obj.user_id else ''))
                        
                        pls_write = writer.writerow(datas)
                        datas = []

                        
                for ro_id_obj in return_obj.browse(cr,uid,ro_orders):
                    status,return_no,sale_ref,return_type,return_date,product,qty,amount,tax,return_reason,invoice_ref,account ='','','','','','',0.0,0.0,0.0,'','',''

                    if ro_id_obj.partner_id:
                        street = str(ro_id_obj.partner_id.street) + (str(ro_id_obj.partner_id.street2) if (ro_id_obj.partner_id.street2) else '')
                        city = ro_id_obj.partner_id.city
                        zip = ro_id_obj.partner_id.zip
                        phone = ro_id_obj.partner_id.phone
                        if ro_id_obj.partner_id.state_id:
                            country_state = ro_id_obj.partner_id.state_id.name

                    for line in ro_id_obj.order_line:
                        return_line_id_obj,line_ids,prod_ids,cancel_return_reason = False,[],[],''
                        datas.append(ro_id_obj.partner_id.ref if ro_id_obj.partner_id.ref else '')
                        datas.append(ro_id_obj.partner_id.name)
                        datas.append(street)
                        datas.append(city)
                        datas.append(country_state)
                        datas.append(zip)
                        datas.append(ro_id_obj.partner_id.emailid)
                        datas.append(phone)
                        datas.append(ro_id_obj.partner_id.date)
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')
                        datas.append('')

                        
                        datas.append(ro_id_obj.state)
                        datas.append(ro_id_obj.partner_id.ref if ro_id_obj.partner_id.ref else '')
                        
                        datas.append(ro_id_obj.linked_sale_order.name)
                        datas.append(ro_id_obj.refund_type)
                        datas.append(ro_id_obj.date_order)
                        datas.append((line.product_id.name if line.product_id else line.name))
                        datas.append(float(line.product_uom_qty))

                        datas.append(float(line.price_subtotal))
                        if sales_tax == 0.0 :
                            if ro_id_obj.amount_tax >= 0.0:
                                sales_tax = ro_id_obj.amount_tax
                                datas.append(sales_tax)
                        else:
                            datas.append(0.0)
    #                    datas.append((ro_id_obj.user_id.name if ro_id_obj.user_id else ''))
                        line_ids.append(line.id)
                        prod_ids.append(line.product_id.id if line.product_id else '')
                        search_child_so_line_id = so_line_obj.search(cr,uid,[('parent_so_line_id','in',line_ids)])
                        if search_child_so_line_id:
                            for each_child in  so_line_obj.browse(cr,uid,search_child_so_line_id):
                                line_ids.append(each_child.id)
                                if each_child.product_id:
                                    prod_ids.append(each_child.product_id.id)
                        
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
                        pls_write = writer.writerow(datas)
                        datas = []
                        
            out=base64.encodestring(buf.getvalue())
            buf.close()
            self.write(cr, uid, ids, {'csv_file':out,'name': 'Sales Report.csv'})
            return {
              'name':_("Export Customer History"),
              'view_mode': 'form',
              'view_id': False,
              'view_type': 'form',
              'res_model': 'export.customer.history',
              'res_id': ids[0],
              'type': 'ir.actions.act_window',
              'nodestroy': True,
              'target': 'new',
              'domain': '[]',
              'context': context,
            }
export_customer_history()