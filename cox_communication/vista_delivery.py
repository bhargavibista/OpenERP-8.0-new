# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import csv
import cStringIO
import base64
from datetime import date, datetime, timedelta

class vista_report(osv.osv):
    _name = "vista.report"
    _columns = {
    'name': fields.char('Attachment Name', size=256),
    'datas': fields.binary('Attachment'),
    'create_date': fields.datetime('Creation Date', readonly=True, select=True, help="Date on which sales order is created."),
    }
    def create_delivery_report(self,cr,uid,context={}):
        pick_obj=self.pool.get('stock.picking')
        if context is None:
            context={}
        if context.get('date_create',False):
            today=context['date_create']
            today = datetime.strptime(today, "%Y-%m-%d")
        else:
            today=date.today()
        state_date = today - timedelta(days=5)
        state_date = state_date.strftime("%Y-%m-%d")
        start_date = str(state_date)+' 00:00:00'
        end_date = today + timedelta(days=5)
        end_date = end_date.strftime("%Y-%m-%d")
        end_date = str(end_date)+' 24:00:00'
        today = today.strftime("%Y-%m-%d")
        cr.execute("select pi.id "\
                   "from stock_picking pi,sale_order s,sale_shop sp "\
                   "where pi.sale_id=s.id and pi.state not in('done','cancel') and s.shop_id=sp.id and sp.name ilike '%s' and (pi.date >='%s' and pi.date <='%s')"%('%play%',start_date,end_date))
        pick_ids= filter(None, map(lambda x:x[0], cr.fetchall()))
        if pick_ids:
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            datas1=[]
            datas1.append("Date")
            datas1.append("Sale Order")
            datas1.append("Delivery Order")
            datas1.append("Email")
            datas1.append("Address")
            datas1.append("Product/Qty")
            datas1.append("Tracking Number")
            pls_write = writer.writerow(datas1)
            warehouse_id = False
            for picking in pick_obj.browse(cr,uid,pick_ids):
                if not warehouse_id:
                    warehouse_id = picking.sale_id.shop_id.warehouse_id
                datas = []
                datas.append(picking.date)
                datas.append(picking.origin)
                datas.append(picking.name)
                datas.append(picking.partner_id.emailid)
                delivery_address=picking.partner_id
                address=delivery_address.partner_id.name+'\n'\
                        +delivery_address.street+'\n'\
                        +delivery_address.zip+','+delivery_address.city+'\n'\
                        +delivery_address.state_id.name+','+delivery_address.country_id.name
                datas.append(address)
                products=''
                for move in picking.move_lines:
                    products+=str(move.product_id.name_template)+'/'+str(move.product_qty)+'\n'
                datas.append(products)
                datas.append('')
                pls_write = writer.writerow(datas)
            out=base64.encodestring(buf.getvalue())
            buf.close()
            if (warehouse_id) and (warehouse_id.partner_id) and (warehouse_id.partner_id.emailid or warehouse_id.partner_id.email):
                smtp_obj = self.pool.get('email.smtpclient')
                smtpserver_id = smtp_obj.search(cr,uid,[('pstate','=','running'),('active','=',True)])
                if smtpserver_id:
                        content = "Please Find Attachmend for the Delivery Report"
                        context['my_attachments']=[{'name':'Delivery_Order_'+str(today)+'.csv','data':out}]
			emailid = (warehouse_id.partner_id.emailid or warehouse_id.partner_id.email)
			if emailid:
	                        queue_id = smtp_obj.send_email(cr, uid, smtpserver_id[0],emailid, 'Delivery Report', content,[],context=context)
        	                if queue_id:
                	            result=smtp_obj._my_check_queue(cr,uid,queue_id)
            return self.create(cr, uid, {'datas':out,'name': 'Delivery_Order_'+str(today)+'.csv'})
vista_report()
