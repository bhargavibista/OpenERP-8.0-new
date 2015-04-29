from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp


class report_churn_analysis(osv.osv):
    _name = "report.churn.analysis"
    _description = "Churn Reasons Analysis"
    _auto = False
    _columns = {
#        'cancel_date': fields.date('Cancel Date'),
        'return_count' : fields.integer('Return Count'),
        'return_cancel_reason': fields.text('Return/Cancellation Reason'),
#        'year': fields.char('Year', size=4, readonly=True),
#        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
#            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
#            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_churn_analysis')
        cr.execute("""
            CREATE OR REPLACE view report_churn_analysis AS (
		select row_number() OVER () AS id,
                        concat(to_char(row_number() OVER (),'09'),'-',return_cancel_reason) as return_cancel_reason,
                        return_count
                from
                (
                select          return_cancel_reason
                                ,count(id) as return_count
                                from res_partner_policy
                                where return_cancel_reason is not null
                                group by return_cancel_reason
                                order by return_count
                                limit 15
                ) as dataset
                order by 2

               )
        """)
report_churn_analysis()
