# -*- coding: utf-8 -*-
import openerp.tools
from openerp.osv import fields, osv

class sale_report(osv.osv):
    _inherit = "sale.report"
    _columns = {
        'cox_sales_channels': fields.selection([
            ('call_center', 'Call Center'),
            ('ecommerce', 'Ecommerce'),
            ('retail', 'Retail'),
            ], 'Sales Channels'),
        'so_name': fields.char('Order Name',size=64),
        'location_id': fields.many2one('stock.location', 'location'),
            }
    def init(self, cr):
        openerp.tools.drop_view_if_exists(cr, 'sale_report')
        cr.execute("""
            create or replace view sale_report as (
                select
                    min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                    1 as nbr,
                    s.date_order as date,
                    s.cox_sales_channels as cox_sales_channels,
                    s.name as so_name,
                    s.location_id as location_id,
                    s.date_confirm as date_confirm,
                    to_char(s.date_order, 'YYYY') as year,
                    to_char(s.date_order, 'MM') as month,
                    to_char(s.date_order, 'YYYY-MM-DD') as day,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.shop_id as shop_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    s.state,
                    t.categ_id as categ_id,
                    s.shipped,
                    s.shipped::integer as shipped_qty_1,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id
                from
                    sale_order s
                    join sale_order_line l on (s.id=l.order_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                group by
                    l.product_id,
                    l.product_uom_qty,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,
                    s.date_confirm,
                    s.partner_id,
                    s.user_id,
                    s.shop_id,
                    s.company_id,
                    s.state,
                    s.shipped,
                    s.pricelist_id,
                    s.project_id,
                    s.cox_sales_channels,
                    s.name,
                    s.location_id
            )
        """)
sale_report()