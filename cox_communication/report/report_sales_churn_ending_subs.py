# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp.osv import fields, osv


#Class for Sales Churn Ending Subscription
class sale_churn_ending_subs(osv.osv):
    _name = "sale.churn.ending.subs"
    _description = "Sales-Churn-Ending Subs"
    _auto = False
    _rec_name = 'month'
    _columns = {
        'year': fields.char('Year', size=4, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'count': fields.integer('Count', readonly=True),
        'category':fields.selection([('1','Sales'),('2','Churn'),('3','Ending')],'Category',readonly=True)
    }
    _order = 'month desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_churn_ending_subs')
        cr.execute("""
            create or replace view sale_churn_ending_subs as (
                select row_number() OVER () AS id
                ,month
                ,year
                ,category
                ,count
        from
        (
                SELECT  to_char(date_confirm, 'MM') as month
                        ,to_char(date_confirm, 'YYYY') as year
                        ,'1' as category
                        ,count(id) as count
                FROM sale_order
                WHERE sale_order.state in ('done','progress')
                group by to_char(date_confirm, 'MM')
                        ,to_char(date_confirm, 'YYYY')

                union all


                select to_char(cancel_date, 'MM') as month
                        ,to_char(cancel_date, 'YYYY') as year
                        ,'2' as category
                        ,count(return_cancel_reason) as count
                from res_partner_policy
                where return_cancel_reason is not null
                group by to_char(cancel_date, 'MM')
                        ,to_char(cancel_date, 'YYYY')


                union all

                (
                        select 	coalesce(sale_count.month,return_count.month)
                                ,coalesce(sale_count.year,return_count.year)
                                ,'3' as category
                                ,coalesce(sale_count.count,0)-coalesce(return_count.count,0) as count
                        from
                        (
                                SELECT  to_char(date_confirm, 'MM') as month
                                        ,to_char(date_confirm, 'YYYY') as year
                                        ,count(id) as count
                                FROM sale_order
                                WHERE sale_order.state in ('done','progress')
                                group by to_char(date_confirm, 'MM')
                                        ,to_char(date_confirm, 'YYYY')
                        ) as sale_count
                        full outer join
                        (
                                select to_char(cancel_date, 'MM') as month
                                        ,to_char(cancel_date, 'YYYY') as year
                                        ,count(return_cancel_reason) as count
                                from res_partner_policy
                                where return_cancel_reason is not null
                                group by to_char(cancel_date, 'MM')
                                        ,to_char(cancel_date, 'YYYY')
                        ) as return_count on (sale_count.year=return_count.year and sale_count.month=return_count.month)
                        order by 2,1

                )
        ) as data
        where year=(select to_char(current_date, 'YYYY'))
        order by 4,3,2



            )
        """)
sale_churn_ending_subs()
