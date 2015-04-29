from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp


class report_avg_customer_lifetime(osv.osv):
    _name = "report.avg.customer.lifetime"
    _description = "Report Avg Customer Lifetime"
    _auto = False
    _columns = {
        'cancel_date': fields.date('Cancel Date'),
        'return_count' : fields.integer('Return Count'),
        'return_cancel_reason': fields.text('Return/Cancellation Reason'),
        'year': fields.char('Year', size=4, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_avg_customer_lifetime')
        cr.execute("""
            CREATE OR REPLACE view report_avg_customer_lifetime AS (
		select row_number() OVER () AS id,
                count(rsp.id) as return_count,
                to_char(rsp.cancel_date, 'YYYY-MM-DD') as cancel_date,
                to_char(rsp.cancel_date, 'MM') as month,
                to_char(rsp.cancel_date, 'YYYY') as year,
                rsp.return_cancel_reason as return_cancel_reason
                from
                res_partner_policy rsp
		where rsp.cancel_date is not null
                group by
		return_cancel_reason, month,year,cancel_date                
               )
        """)


