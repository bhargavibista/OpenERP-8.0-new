#! /usr/bin/python
from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp


class report_inventory_analysis_custom(osv.osv):
    _name = "report.inventory.analysis.custom"
    _description = "Stock Statistics"
    _auto = False
    _columns = {
        'date': fields.datetime('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month', readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'product_categ_id':fields.many2one('product.category', 'Product Category', readonly=True),
        'location_id': fields.many2one('stock.location', 'Location', readonly=True),
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'product_qty':fields.float('Quantity',  digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'value' : fields.float('Total Value',  digits_compute=dp.get_precision('Account'), required=True),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True,
              help='When the stock move is created it is in the \'Draft\' state.\n After that it is set to \'Confirmed\' state.\n If stock is available state is set to \'Avaiable\'.\n When the picking it done the state is \'Done\'.\
              \nThe state is \'Waiting\' if the move is waiting for another one.'),
        'location_type': fields.selection([('supplier', 'Supplier Location'), ('view', 'View'), ('internal', 'Internal Location'), ('customer', 'Customer Location'), ('inventory', 'Inventory'), ('procurement', 'Procurement'), ('production', 'Production'), ('transit', 'Transit Location for Inter-Companies Transfers')], 'Location Type', required=True),
        'scrap_location': fields.boolean('scrap'),
        'total_product_qty':fields.float('Quantity',  digits_compute=dp.get_precision('Product Unit of Measure')),
        'current_product_qty':fields.float('Total Today',  digits_compute=dp.get_precision('Product Unit of Measure')),
        'previous_product_qty':fields.float('Total Yesterday',  digits_compute=dp.get_precision('Product Unit of Measure')),
        'active':fields.boolean('Active'),
        'yesterday_so_qty':fields.float('Yesterday Sale Quantity',  digits_compute=dp.get_precision('Product Unit of Measure')),
        'yesterday_exchng_qty':fields.float('Yesterday Exchange Quantity',  digits_compute=dp.get_precision('Product Unit of Measure')),

    }
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_inventory_analysis_custom')
        cr.execute("""
CREATE OR REPLACE view report_inventory_analysis_custom AS (
    (
    select 	all_data.location_id as id
	,all_data.location_id as location_id
	,all_data.product_id as product_id
	,all_data.qty as total_product_qty
	,coalesce(current_data.qty,0.00) as current_product_qty
	,coalesce(previous_data.qty,0.00) as previous_product_qty
	,all_data.active as active
    ,coalesce(previous_data2.so_qty,0.00) as yesterday_so_qty
    ,coalesce(previous_data1.ext_qty,0.00) as yesterday_exchng_qty
from
(
	SELECT temp2.location_id AS location_id,temp2.location_name,temp2.product_id,sum(temp2.product_qty) as qty,temp2.active as active,temp2.p_name as p_name
	FROM
	((SELECT
				min(m.id ) as id, m.date as date,
				to_char(m.date, 'YYYY') as year,
				to_char(m.date, 'MM') as month,
				m.partner_id as partner_id, m.location_id as location_id,l.name as location_name,l.active as active,
				m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, l.scrap_location as scrap_location,
				m.company_id,
				pt.name as p_name,
				m.state as state, m.prodlot_id as prodlot_id,
				p.type as type1,

				coalesce(sum(-pt.standard_price * m.product_qty * pu.factor / pu2.factor)::decimal, 0.0) as value,
				coalesce(sum(-m.product_qty * pu.factor / pu2.factor)::decimal, 0.0) as product_qty
			    FROM
				stock_move m
				    LEFT JOIN stock_picking p ON (m.picking_id=p.id )
				    LEFT JOIN product_product pp ON (m.product_id=pp.id )
					LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id )
					LEFT JOIN product_uom pu ON (pt.uom_id=pu.id )
					LEFT JOIN product_uom pu2 ON (m.product_uom=pu2.id )
				    LEFT JOIN product_uom u ON (m.product_uom=u.id )
				    LEFT JOIN stock_location l ON (m.location_id=l.id )
				    WHERE m.state != 'cancel'
			    GROUP BY
				m.id , m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, l.name, m.location_dest_id,pt.name,
				m.prodlot_id, m.date, m.state, l.usage,l.active, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'), to_char(m.date, 'MM'),p.type
			) UNION ALL (
			    SELECT
				-m.id  as id, m.date as date,
				to_char(m.date, 'YYYY') as year,
				to_char(m.date, 'MM') as month,
				m.partner_id as partner_id, m.location_dest_id as location_id,l.name as location_name,l.active as active,
				m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, l.scrap_location as scrap_location,
				m.company_id,
				pt.name as p_name,
				m.state as state, m.prodlot_id as prodlot_id,
				p.type as type1,
				coalesce(sum(pt.standard_price * m.product_qty * pu.factor / pu2.factor)::decimal, 0.0) as value,
				coalesce(sum(m.product_qty * pu.factor / pu2.factor)::decimal, 0.0) as product_qty
			    FROM
				stock_move m
				    LEFT JOIN stock_picking p ON (m.picking_id=p.id )
				    LEFT JOIN product_product pp ON (m.product_id=pp.id )
					LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id )
					LEFT JOIN product_uom pu ON (pt.uom_id=pu.id )
					LEFT JOIN product_uom pu2 ON (m.product_uom=pu2.id )
				    LEFT JOIN product_uom u ON (m.product_uom=u.id )
				    LEFT JOIN stock_location l ON (m.location_dest_id=l.id )
				    WHERE m.state != 'cancel'
			    GROUP BY
				m.id , m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id,l.name, m.location_dest_id,pt.name,
				m.prodlot_id, m.date, m.state, l.usage,l.active, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'), to_char(m.date, 'MM'),p.type
			    ))
			    AS temp2
			    GROUP BY temp2.location_id, temp2.location_name,temp2.product_id,temp2.active,temp2.p_name
) as all_data left join
(
	 select temp1.location_id as location_id, temp1.product_id, sum(temp1.product_qty) as qty
	 from
	 (SELECT
		-m.id as id,m.date as date,
		m.location_id as location_id,l.name as location_name ,l.usage as location_type,
		m.product_id as product_id,
		m.state as state,
		m.product_qty as product_qty
	    FROM
		stock_move m
		    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
		    LEFT JOIN product_product pp ON (m.product_id=pp.id)
			LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
		    LEFT JOIN stock_location l ON (m.location_id=l.id)
		    WHERE m.state = 'done' and l.usage='internal' and p.type='out' and cast(m.date as date)= (SELECT CURRENT_DATE) and (m.origin like 'SO%' or m.origin like 'RO%')
	    GROUP BY
		m.id, m.product_id,m.location_id,l.name,l.usage
		order by m.date asc
		)
		as temp1
		group by temp1.location_id ,temp1.product_id
) as current_data on (all_data.location_id=current_data.location_id and all_data.product_id=current_data.product_id)
left join
(
	 select temp1.location_id as location_id, temp1.product_id, sum(temp1.product_qty) as qty
	 from
	 (SELECT
		-m.id as id,m.date as date,
		m.location_id as location_id,l.name as location_name ,l.usage as location_type,
		m.product_id as product_id,
		m.state as state,
		m.product_qty as product_qty
	    FROM
		stock_move m
		    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
		    LEFT JOIN product_product pp ON (m.product_id=pp.id)
			LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
		    LEFT JOIN stock_location l ON (m.location_id=l.id)
		    WHERE m.state = 'done' and l.usage='internal' and p.type='out' and cast(m.date as date)= (SELECT CURRENT_DATE-1) and (m.origin like 'SO%' or m.origin like 'RO%')
	    GROUP BY
		m.id, m.product_id,  m.location_id,l.name, l.usage
		order by m.date asc
		)
		as temp1
		group by temp1.location_id ,temp1.product_id
) as previous_data on (all_data.location_id=previous_data.location_id and all_data.product_id=previous_data.product_id)
left join
(
	 select temp3.location_id as location_id, temp3.product_id, sum(temp3.product_qty) as qty,sum(temp3.ex_qty) as ext_qty
	 from
	 (SELECT
		-m.id as id,m.date as date,
		m.location_dest_id as location_id,l.name as location_name ,l.usage as location_type,
		m.product_id as product_id,
		m.state as state,
		m.product_qty as product_qty,
		m.product_qty as ex_qty
	    FROM
		stock_move m
		    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
		    LEFT JOIN product_product pp ON (m.product_id=pp.id)
			LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
		    LEFT JOIN stock_location l ON (m.location_id=l.id)


		    WHERE m.state = 'done' and l.usage='internal' and p.type='out'and cast(m.date as date)= (SELECT CURRENT_DATE-1) and (m.origin like 'RO%')
	    GROUP BY
		m.id, m.product_id, m.location_id,l.name, l.usage,p.type,m.origin
		order by m.date asc
		)
		as temp3
		group by temp3.location_id ,temp3.product_id,temp3.ex_qty
) as previous_data1 on (all_data.location_id=previous_data1.location_id and all_data.product_id=previous_data1.product_id)
left join
(
	 select temp1.location_id as location_id, temp1.product_id, sum(temp1.product_qty) as qty,sum(temp1.so_qty) as so_qty
	 from
	 (SELECT
		-m.id as id,m.date as date,
		m.location_id as location_id,l.name as location_name ,l.usage as location_type,
		m.product_id as product_id,
		m.state as state,
		m.product_qty as product_qty,
		m.product_qty as so_qty

	    FROM
		stock_move m
		    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
		    LEFT JOIN product_product pp ON (m.product_id=pp.id)
			LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
		    LEFT JOIN stock_location l ON (m.location_id=l.id)

		    WHERE m.state = 'done' and l.usage='internal' and p.type='out' and cast(m.date as date)= (SELECT CURRENT_DATE-1) and (m.origin like 'SO%')
	    GROUP BY
		m.id, m.product_id,m.location_id,l.name, l.usage
		order by m.date asc
		)
		as temp1
		group by temp1.location_id ,temp1.product_id,temp1.so_qty
) as previous_data2 on (all_data.location_id=previous_data2.location_id and all_data.product_id=previous_data2.product_id)
order by 1,3
    )
);
        """)
report_inventory_analysis_custom()
