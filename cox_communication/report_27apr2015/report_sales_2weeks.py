# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields, osv
from datetime import datetime, timedelta
class sale_report_analysis(osv.osv):
    _name = "sale.report.analysis"
    _description = "Sales Orders Statistics"
    _auto = False
#    _rec_name = 'day'
    _columns = {
#        'day': fields.char('Day', size=128, readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'sale_count': fields.float('Number of Sales'),
    }
#    _order = 'day desc'
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_report_analysis')
        current_date = datetime.now()
        before_2weeky= (current_date-timedelta(days=15)).strftime('%Y-%m-%d')
        current_date = current_date.strftime("%Y-%m-%d")
        cr.execute("""
            create or replace view sale_report_analysis as (
                SELECT min(s.id) as id
                        ,s.user_id as user_id
                        ,count(*) as sale_count
                FROM
                        sale_order s
                WHERE s.state in ('done','progress') and (s.date_confirm > '%s' and s.date_confirm <= '%s')
                group BY
                        s.user_id
                order BY sale_count desc
            )
        """%(before_2weeky,current_date))	
#    def init(self, cr):
 #       tools.drop_view_if_exists(cr, 'sale_report_analysis')
  #      cr.execute("""
   #         create or replace view sale_report_analysis as (
    #            SELECT min(s.id) as id
     #                   ,s.user_id as user_id
      #                  ,count(s.id) as sale_count
#
 #                       ,to_char(s.date_confirm, 'YYYY-MM-DD') as day
  #              FROM
   #                     sale_order s
    #            WHERE s.state in ('done','progress')
     #           GROUP BY
      #                  s.user_id,
       #                 to_char(s.date_confirm, 'YYYY-MM-DD')
        #    )
#        """)
	
sale_report_analysis()

#experimental
class month_type(osv.osv):
    _name = "month.type"
    _columns = {
        'name': fields.char('Sales Month', size=32),
    }

month_type()

class sale_report_monthly_analysis(osv.osv):
    _name = "sale.report.monthly.analysis"
    _description = "Month to Month Sale"
    _auto = False
    _rec_name = 'date'
    _columns = {
        'date': fields.integer('Date', readonly=True),
        'current_count': fields.integer('Current Month Count', readonly=True),
        'category': fields.many2one('month.type','Sales Month',readonly=True),
        'previous_count': fields.integer('Previous Month Count', readonly=True),
    }

#    _order = 'date desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_report_monthly_analysis')
        cr.execute("""
            create or replace view sale_report_monthly_analysis as (
           select  row_number() OVER () AS id
	,al.date as date
	,al.category as category
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
                        and extract(month from sale_order.date_confirm)=extract(month from (select current_date))-1
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
                        and extract(month from sale_order.date_confirm)=extract(month from (select current_date))-2
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
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
