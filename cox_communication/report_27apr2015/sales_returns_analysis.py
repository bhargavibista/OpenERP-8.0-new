# -*- coding: utf-8 -*-
import openerp.tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import csv
import cStringIO
import base64
import xlwt
from datetime import date,datetime, timedelta as td


class sales_returns_analysis(osv.osv_memory):
    
    _name = "sales.returns.analysis"
    _columns={
    'start_date': fields.date('Start Date'),
    'end_date': fields.date('End Date'),
#    'product_id':fields.many2one('product.product','Product'),
    'name' : fields.char('Name',size=32),
    'csv_file' : fields.binary('CSV file'),
    }
    _defaults = {
    'end_date':fields.date.context_today
    }

    def generate_reports(self,cr,uid,ids,context={}):
        self_browse=self.browse(cr,uid,ids[0])
        start_date=self_browse.start_date
        end_date=self_browse.end_date
        product_obj=self.pool.get('product.product')
        buf=cStringIO.StringIO()
        writer=csv.writer(buf, 'UNIX')
        cr.execute("select name from stock_location where usage='internal'")
        locations = filter(None, map(lambda x:x[0], cr.fetchall()))
        datas1=[]
        datas1.append("Date")
        datas1.append("Product")
        datas1.append("Type")
        for location in locations:
            datas1.append(location)
        pls_write = writer.writerow(datas1)
        cr.execute("select p.id from product_product p "
                   "join product_template t on (p.product_tmpl_id=t.id) "
                   "where t.type='product' and t.sale_ok=True")
        products = filter(None, map(lambda x:x[0], cr.fetchall()))
        if start_date and end_date:
            d1=datetime.strptime(start_date, "%Y-%m-%d").date()
            d2=datetime.strptime(end_date, "%Y-%m-%d").date()
            diff=d2-d1
            for i in range(diff.days + 1):
                order_date=d1 + td(days=i)
                for product_id in products:
                    product_name=product_obj.browse(cr,uid,product_id).name
                    datas = []
                    datas.append(order_date)
                    datas.append(product_name)
                    datas.append("Sales")
                    return_data=[]
                    return_data.append("")
                    return_data.append("")
                    return_data.append("Returns")
                    for i in range(len(datas1)-3):
                        datas.insert(i+3,"0.00")
                        return_data.insert(i+3,"0.00")
                    cr.execute("select sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty, lo.name as location_name "
                                "from sale_order s "
                                "join sale_order_line l on (s.id=l.order_id) "
                                "left join product_product p on (l.product_id=p.id) "
                                "left join product_template t on (p.product_tmpl_id=t.id) "
                                   "left join product_uom u on (u.id=l.product_uom) "
                                "left join product_uom u2 on (u2.id=t.uom_id) "
                                "left join stock_location lo on (s.location_id=lo.id) "
                                "where l.product_id=%s and s.date_confirm='%s' "
                                "group by location_name"%(product_id,str(order_date)))
                    quantities=cr.dictfetchall()
                    for tuple in quantities:
                        loc_name=tuple['location_name']
                        if loc_name in datas1:
                            datas[datas1.index(loc_name)]=tuple['product_uom_qty']
                    cr.execute("select sum(rl.product_uom_qty / u.factor * u2.factor) as product_uom_qty,sl.name as location_name "
                                "from return_order r "
                                        "join return_order_line rl on (r.id=rl.order_id) "
                                        "left join product_product p on (rl.product_id=p.id) "
                                            "left join product_template t on (p.product_tmpl_id=t.id) "
                                        "left join product_uom u on (u.id=rl.product_uom) "
                                        "left join product_uom u2 on (u2.id=t.uom_id) "
                                        "left join stock_location sl on (r.source_location=sl.id) "
                                "where rl.product_id=%s and r.date_order='%s' "
                                "group by location_name"%(product_id,str(order_date)))
                    quantities=cr.dictfetchall()
                    for tuple in quantities:
                        loc_name=tuple['location_name']
                        if loc_name in datas1:
                            return_data[datas1.index(loc_name)]=tuple['product_uom_qty']
                    pls_write = writer.writerow(datas)
                    pls_write = writer.writerow(return_data)
            out=base64.encodestring(buf.getvalue())
            buf.close()
            return self.write(cr, uid, ids, {'csv_file':out,'name': 'Sales and Returns Analysis.csv'})
        return True

    def close_button(self,cr,uid,ids,context={}):
        return {'type': 'ir.actions.act_window_close'}
sales_returns_analysis()

