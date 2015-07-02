# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import csv
import cStringIO
from openerp.tools.translate import _
import base64

class flarewatch_customer(osv.osv_memory):
    _name='flarewatch.customer'
    _columns = {
        'name' : fields.char('Name',size=32),
        'csv_file' : fields.binary('CSV file'),
    }
    def flarewatch_customer(self,cr,uid,ids,context={}):
        cr.execute("select id from res_partner where create_date <= '2013-10-31'")
        partner_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        partner_obj = self.pool.get('res.partner')
        if partner_ids:
            datas = []
            datas.append("Customer Name")
            datas.append("Email")
            datas.append("Zip")
            datas.append("City")
            datas.append("Phone Number")
            buf=cStringIO.StringIO()
            writer=csv.writer(buf, 'UNIX')
            pls_write = writer.writerow(datas)
            datas = []
            for each_part in partner_obj.browse(cr,uid,partner_ids):
                datas.append(each_part.name)
                datas.append(each_part.emailid if each_part.emailid else '')
                datas.append(each_part.zip if each_part.zip else '')
                datas.append(each_part.city if each_part.city else '')
                datas.append(each_part.phone if each_part.phone else '')
                pls_write = writer.writerow(datas)
                datas = []
            out=base64.encodestring(buf.getvalue())
            buf.close()
            return self.write(cr, uid, ids, {'csv_file':out,'name': 'FlareWatch_Customers.csv'})
    
flarewatch_customer()