import time
from openerp.report import report_sxw
from openerp.osv import osv



class report_webkit_sale_return(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_webkit_sale_return, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
        })
report_sxw.report_sxw('report.webkitaccount.return',
                       'return.order',
                       'addons/bista_order_returns/report/report_webkit_sale_return.mako',
                       parser=report_webkit_sale_return)

