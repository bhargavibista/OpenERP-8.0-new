# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import osv, fields
import csv
import cStringIO
import base64
from dateutil import parser
import datetime
#from datetime import date, datetime, timedelta


class export_account_report_csv(osv.osv_memory):
    """ Export Module """
    _name = "export.account.report.csv"
    _description = "Export CSV"
    _columns = {
        'name' : fields.char('Name',size=32),
        'csv_file' : fields.binary('CSV file'),
        'date_from':fields.date('From',required=True),
        'date_to':fields.date('To',required=True),
    }

    def export_custom_account_report(self,cr,uid,ids,context={}):
        datas=[]
        count=0
        account_inv_obj=self.pool.get('account.invoice')
        f = open('/tmp/Account Report.csv','w')
        self_obj=self.browse(cr,uid,ids[0])
        strt_date=datetime.datetime.strptime(self_obj.date_from,'%Y-%m-%d')
        end_date=datetime.datetime.strptime(self_obj.date_to,'%Y-%m-%d')
        delta = datetime.timedelta(days=1)
        if strt_date and end_date :
            datas = "Date"+","+"Revenue from Device Sales"+","+"Total Device returned"+","+"Revenue from Service Sales"+","+"Total Services cancelled"+","+"Total Rentals"+","+"Shipping revenue from sales"+","+"Returned shipping revenue"+","+"Sales taxes Revenue"+","+"Returned Sale Taxes revenue"+"\n"
            while strt_date<=end_date:
                device_price,service_price,sales_tax,rental_price,ship_cost=0.0,0.0,0.0,0.0,0.0
                ro_device_price,cs_service_price,ro_tax,ro_ship_cost=0.0,0.0,0.0,0.0
                cr.execute("select id from account_invoice where date_invoice='%s' and state='paid'"%(strt_date))
                invoice_list=filter(None, map(lambda x:x[0], cr.fetchall()))
                if invoice_list:
                    datas += str(datetime.datetime.strftime(strt_date,'%Y-%m-%d'))
                    count=len(invoice_list)
                    for inv_account_obj in account_inv_obj.browse(cr,uid,invoice_list):
                        count=count-1
                        cr.execute("select order_id from sale_order_invoice_rel where invoice_id =%s"%(inv_account_obj.id))
                        so_id=filter(None, map(lambda x:x[0], cr.fetchall()))
                        if so_id:
                            sale_obj_brw=self.pool.get('sale.order').browse(cr,uid,so_id[0])
                        if so_id and sale_obj_brw and sale_obj_brw.cox_sales_channels=='amazon':
                            for each_line in sale_obj_brw.order_line:
                                if each_line.sub_components:
                                    for each_subcom in each_line.sub_components:
                                        if each_subcom.product_id.type=='product':
                                            device_price+=(each_line.price_subtotal)
                                        elif each_subcom.product_id.type=='service':
                                            service_price+=(each_line.price_subtotal)
                                else:
                                    if each_line.product_id.type=='product':
                                        device_price+=each_line.price_subtotal
                                    if each_line.product_id.type=='service':
                                        if each_line.product_id.default_code=='SHIP':
                                            ship_cost+=each_line.price_subtotal
                                        else:
                                            service_price+=each_line.price_subtotal
                            if sale_obj_brw.amount_tax >= 0.0:
                                sales_tax += sale_obj_brw.amount_tax
#                                print"salessssssssssssstexghhhhhhhhhhhhhhhh",sale_obj_brw.amount_tax,sales_tax
                        else:
                                for move_lines in inv_account_obj.move_id.line_id:
                                    if inv_account_obj.move_id.journal_id.type=='sale':
                                        if move_lines.product_id.type=='product':
                                            device_price+=move_lines.credit
                                        if move_lines.product_id.type=='service':
                                            if (('SO' or 'RB') not in inv_account_obj.origin) and ('mag' not in inv_account_obj.origin) :
                                                print"inv_account_obj.origininv_account_obj.origin00",inv_account_obj.origin
                                                rental_price+=move_lines.credit
                                            elif move_lines.product_id.default_code=='SHIP':
                                                ship_cost+=move_lines.credit
                                            else:
                                                service_price+=move_lines.credit
                                        if move_lines.tax_amount:
                                            sales_tax+=move_lines.tax_amount
#                                            print"move_lines.tax_amountmove_lines.tax_amountmove_lines.tax_amount",move_lines.tax_amount,sales_tax
                                    if inv_account_obj.move_id.journal_id.type=='sale_refund':
                                        if move_lines.product_id.type=='product':
                                            ro_device_price+=move_lines.debit
                                        if move_lines.product_id.type=='service':
                                            if move_lines.product_id.default_code=='SHIP':
                                                ro_ship_cost+=move_lines.debit
                                            else:
                                                cs_service_price+=move_lines.debit
                                        if move_lines.tax_amount:
                                            ro_tax+=move_lines.tax_amount
                    if count==0:
                        datas += ","+str(device_price)+","+str(ro_device_price)+"\
                                ,"+str(service_price)+","+str(cs_service_price)+","+str(rental_price)+"\
                                ,"+str(ship_cost)+","+str(ro_ship_cost)+","+str(sales_tax)+","+str(ro_tax)+"\n"
                        f.write(datas)
                        datas=""
                strt_date += delta
            f = open("/tmp/Account Report.csv","rb")
            bytes = f.read()
            out = base64.encodestring(bytes)
        self.write(cr, uid, ids, {'csv_file':out,'name': 'Account Report.csv'})
        return {
            'name':_("Export Account Report"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'export.account.report.csv',
            'res_id': ids[0],
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }
    def export_custom_account_report(self,cr,uid,ids,context={}):
        datas,location_id=[],False
        account_inv_obj=self.pool.get('account.invoice')
#        product_obj=self.pool.get('product.product')
        self_obj=self.browse(cr,uid,ids[0])
        strt_date=datetime.datetime.strptime(self_obj.date_from,'%Y-%m-%d')
        end_date=datetime.datetime.strptime(self_obj.date_to,'%Y-%m-%d')
        delta = datetime.timedelta(days=1)
        if strt_date and end_date:
            datas=["Customer ID","Customer Name","Email","Date of Transaction","Transcation's Type","Document Ref.","Location","Offer/Product Name","Device/Service/Sales tax/Return order","Amount"]
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            while strt_date<=end_date:
#                print"strt_datestrt_datestrt_datestrt_datestrt_datestrt_date",strt_date
                cr.execute("select id from account_invoice where date_invoice='%s' and state='paid'"%(strt_date))
                invoice_list=filter(None, map(lambda x:x[0], cr.fetchall()))
                if invoice_list:
                    for inv_account_obj in account_inv_obj.browse(cr,uid,invoice_list):
                        datas1=list(datas)
                        flag=True
                        product_list=[]
                        for each_line in inv_account_obj.invoice_line:
                            for move_lines in inv_account_obj.move_id.line_id:
                                datas1[0]=inv_account_obj.partner_id.id
                                datas1[1]=inv_account_obj.partner_id.name
                                datas1[2]=inv_account_obj.partner_id.emailid
                                datas1[3]=inv_account_obj.date_invoice
                                if inv_account_obj.origin:
                                    print"inv_account_obj.origin:inv_account_obj.origin:inv_account_obj.origin:inv_account_obj.origin:",inv_account_obj.origin,inv_account_obj
                                    if 'RB' in inv_account_obj.origin:
                                        datas1[4]='Recurring Bill'
                                    elif 'SO' or 'mag' in inv_account_obj.origin:
                                        cr.execute("select order_id from sale_order_invoice_rel where invoice_id='%s'"%(inv_account_obj.id))
                                        so_id=filter(None, map(lambda x:x[0], cr.fetchall()))
                                        print"so_idso_idso_idso_idso_id",so_id
                                        if so_id:
                                            location_id=self.pool.get('sale.order').browse(cr,uid,so_id[0]).location_id
                                            print"location_brwlocation_brwlocation_brwlocation_brw",location_id
                                        if 'mag' in inv_account_obj.origin:
                                             datas1[4]='Magento Order'
                                        else:
                                            datas1[4]='Sale Order'
                                    elif 'RO' in inv_account_obj.origin:
                                        datas1[4]='Return Order'
                                        cr.execute("select order_id from return_order_invoice_rel where invoice_id='%s'"%(inv_account_obj.id))
                                        return_id=filter(None, map(lambda x:x[0], cr.fetchall()))
                                        if return_id:
                                            location_id=self.pool.get('return.order').browse(cr,uid,return_id[0]).source_location
                                            print"lreturn_idreturn_idreturn_idreturn_idlocation_brw",location_id
                                    elif 'CS' in inv_account_obj.origin:
                                        datas1[4]='Credit & Cancellation'
                                    datas1[5]=inv_account_obj.origin
                                    if location_id:
                                        datas1[6]=location_id.name
                                    else:
                                         datas1[6]='N/A'
                                    datas1[7]=each_line.product_id.name
                                if move_lines.product_id and move_lines.invoice_line_id.id==each_line.id:
#                                if move_lines.product_id.id in sub_comp:
                                    product_list.append(move_lines.product_id.id)
#                                    print"move_lines.product_id:move_lines.product_id:move_lines.product_id:",move_lines.product_id
                                    if inv_account_obj.move_id.journal_id.type=='sale':
                                        datas1[8]=move_lines.product_id.name
                                        datas1[9]=(move_lines.credit)
                                    elif inv_account_obj.move_id.journal_id.type=='sale_refund':
                                        datas1[8]=move_lines.product_id.name
                                        datas1[9]=(move_lines.debit)
                                elif move_lines.tax_amount :
                                    if inv_account_obj.move_id.journal_id.type=='sale':
                                        datas1[8]='Sales Tax'
                                    elif inv_account_obj.move_id.journal_id.type=='sale_refund':
                                        datas1[8]='Return Tax'
                                    datas1[9]=(move_lines.tax_amount) if flag==True else 0
                                    flag=False
                                else:
                                    continue
                                pls_write = writer.writerow(datas1)
#                                datas1=[]
                strt_date += delta
            out=base64.encodestring(buf.getvalue())
            buf.close()

        self.write(cr, uid, ids, {'csv_file':out,'name': 'Account Report.csv'})
        return {
            'name':_("Export Account Report"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'export.account.report.csv',
            'res_id': ids[0],
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }
export_account_report_csv()
