# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import osv, fields
import csv
import cStringIO
import base64
from dateutil import parser
from datetime import datetime, timedelta


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
        buf=cStringIO.StringIO()
        writer=csv.writer(buf, 'UNIX')
        datas=[]
        account_obj=self.pool.get('account.move')
        self_obj=self.browse(cr,uid,ids[0])
        strt_date=self_obj.date_from
        end_date=self_obj.date_to
        cr.execute("select distinct date from account_move where date between '%s' and '%s' "%(strt_date,end_date))
        date = filter(None, map(lambda x:x[0], cr.fetchall()))
        if date:
            datas=["Date","Revenue from Device Sales","Total Device returned","Revenue from Service Sales",
                "Total Services cancelled","Total Rentals","Shipping revenue from sales",
                "Returned shipping revenue","Sales taxes Revenue","Returned Sale Taxes revenue"]
            pls_write = writer.writerow(datas)
            datas=[]
            count=0
            for each_date in date:
                device_price,service_price,sales_tax,rental_price,ship_cost=0.0,0.0,0.0,0.0,0.0
                ro_device_price,cs_service_price,ro_tax,ro_ship_cost=0.0,0.0,0.0,0.0
                cr.execute("select id from account_move where date= '%s' and state='posted'"%(each_date))
                acc_list=filter(None, map(lambda x:x[0], cr.fetchall()))
                if acc_list:
#                    print"each_dateeach_dateeach_dateeach_date",each_date
                    datas.append(each_date)
                    count=len(acc_list)
                    for account_id_obj in account_obj.browse(cr,uid,acc_list):
                        count=count-1
                        for move_lines in account_id_obj.line_id:
                            if account_id_obj.journal_id.type=='sale':
                                if move_lines.product_id.type=='product':
                                    device_price+=move_lines.credit
                                if move_lines.product_id.type=='service':
#                                    print"Regfffffffffffffffffffffff----------..........",move_lines.ref
                                    if (('SO' or 'RB') not in account_id_obj.ref) and ('mag' not in account_id_obj.ref) :
                                        rental_price+=move_lines.credit
                                    elif move_lines.product_id.default_code=='SHIP':
                                        ship_cost+=move_lines.credit
                                    else:
                                        service_price+=move_lines.credit
                                if move_lines.tax_amount:
                                    sales_tax+=move_lines.tax_amount
                            if account_id_obj.journal_id.type=='sale_refund':
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
                        datas.append(device_price)
                        datas.append(ro_device_price)
                        datas.append(service_price)
                        datas.append(cs_service_price)
                        datas.append(rental_price)
                        datas.append(ship_cost)
                        datas.append(ro_ship_cost)
                        datas.append(sales_tax)
                        datas.append(ro_tax)
                    pls_write = writer.writerow(datas)
                    datas=[]
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
