import time
from datetime import date, datetime

from openerp.report import report_sxw

class returnorder(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(returnorder, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_return_info':self.get_return_info,
        })
    def get_return_info(self):
        return_info=[]
#        self.cr.execute("select r.id, extract(EPOCH from age(r.date_order::timestamp, s.date_confirm::timestamp))/(3600*24) as diffrenece "
#                        "from return_order r,sale_order s "
#                        "where r.linked_sale_order=s.id")
        return_obj=self.pool.get('return.order')
        self.cr.execute("select r.id, extract(EPOCH from age(r.date_order::timestamp, s.date_confirm::timestamp))/(3600*24) as diff "
                        "from return_order r,sale_order s "
                        "where r.linked_sale_order=s.id and r.return_type='%s' and extract(EPOCH from age(r.date_order::timestamp, s.date_confirm::timestamp))/(3600*24) >40 "
                        "order by diff asc"%('car_return'))
        return_ids=self.cr.dictfetchall()
        
        if return_ids:
            for ret in return_ids:
                return_name=''
                return_id=ret.get('id',False)
                if return_id:
                    return_data=return_obj.browse(self.cr,self.uid,return_id)
                    return_name=return_data.name
                    customer_name=return_data.partner_id.name
                    email=return_data.partner_id.emailid
                    location=return_data.source_location.name
                    sale_reference=return_data.linked_sale_order.name
                    sale_resp = return_data.user_id.name
                    days=ret.get('diff')
                    return_info.append({
                        'name':return_name,
                        'days':int(days),
                        'customer':customer_name,
                        'email':email,
                        'location':location,
                        'reference':sale_reference,
                        'sale_resp':sale_resp
                    })
        return return_info
report_sxw.report_sxw('report.return.order', 'return.order', 'addons/cox_communication/report/return_order.rml', parser=returnorder)