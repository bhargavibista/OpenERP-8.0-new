# -*- coding: utf-8 -*-

from openerp import tools
from openerp.osv import fields, osv


class sale_report_monthly_analysis(osv.osv):
    _name = "sale.report.monthly.analysis"
    _description = "Month to Month Sale"
    _auto = False
    _rec_name = 'date'
    _columns = {
        'date': fields.char('Date', readonly=True),
        'current_count': fields.integer('Current Month Count', readonly=True),
	'category': fields.selection([('1','Current Month'),('2','Previous Month')],'Sales Month',readonly=True),
#        'category': fields.many2one('month.type','Sales Month',readonly=True),
        'previous_count': fields.integer('Previous Month Count', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_report_monthly_analysis')
        cr.execute("""
            create or replace view sale_report_monthly_analysis as (
           select  row_number() OVER () AS id
	,to_char(al.date,'09') as date
	,(al.category)::text as category
	,al.current_count as current_count
        from(

        select 	(alldata.generate_series) as id
                ,alldata.generate_series as date
                ,1 as category
                ,coalesce(current_month.orders,0) as current_count
                from
                (
                        select 	extract(day from sale_order.date_confirm) as day
                                ,count(sale_order.id) as orders
                        from sale_order
                        where extract(year from sale_order.date_confirm)=extract(year from (select current_date))
                        and extract(month from sale_order.date_confirm)=extract(month from (select current_date))
                        and sale_order.state in ('done','progress')
                        group by extract(day from sale_order.date_confirm)
                ) as current_month
                right join
                (
                        select * from generate_series(1,31)
                ) as alldata
                on current_month.day=alldata.generate_series


                union all

                select 	min(alldata.generate_series) as id
                ,alldata.generate_series as date
                ,2 as category
                ,coalesce(previous_month.orders,0) as current_count
                from
                (
                        select 	extract(day from sale_order.date_confirm) as day
                                ,count(sale_order.id) as orders
                        from sale_order
                        where extract(year from sale_order.date_confirm)=extract(year from (select current_date))
                        and extract(month from sale_order.date_confirm)=extract(month from (select current_date))-1
                        and sale_order.state in ('done','progress')
                        group by extract(day from sale_order.date_confirm)
                ) as previous_month
                right join
                (
                        select * from generate_series(1,31)
                ) as alldata
                on previous_month.day=alldata.generate_series
                group by alldata.generate_series,coalesce(previous_month.orders,0)
        ) as al

            )
            
        """)
sale_report_monthly_analysis()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
