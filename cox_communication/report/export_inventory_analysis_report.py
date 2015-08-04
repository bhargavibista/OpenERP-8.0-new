#! /usr/bin/python
from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools.translate import _
from openerp.osv import osv, fields
import csv
import cStringIO
import base64
from dateutil import parser


class inventory_analysis_report(osv.osv_memory):
    _name = "inventory.analysis.report"
    _description = "Export CSV Inventory Analysis Report"
    _columns = {
        'name' : fields.char('Name',size=32),
        'csv_file' : fields.binary('CSV file'),
    }

    def export_csv_analysis_report(self,cr,uid,ids,context={}):
        cr.execute("""
        select 	all_data.location_id as id
	,all_data.location_id as location_id
          ,all_data.location_name
	,all_data.product_id as product_id
	,all_data.p_name
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
				m.state as state, m.restrict_lot_id as prodlot_id,
				spt.code as type1,

				coalesce(sum(-ip.value_float * m.product_qty * pu.factor / pu2.factor)::decimal, 0.0) as value,
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
                                    LEFT JOIN stock_picking_type spt ON (p.picking_type_id = spt.id)
                                    LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.template,',pt.id) AND ip.company_id=p.company_id)
				    WHERE m.state != 'cancel'
			    GROUP BY
				m.id , m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, l.name, m.location_dest_id,pt.name,
				m.restrict_lot_id, m.date, m.state, l.usage,l.active, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'), to_char(m.date, 'MM'),spt.code
			) UNION ALL (
			    SELECT
				-m.id  as id, m.date as date,
				to_char(m.date, 'YYYY') as year,
				to_char(m.date, 'MM') as month,
				m.partner_id as partner_id, m.location_dest_id as location_id,l.name as location_name,l.active as active,
				m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, l.scrap_location as scrap_location,
				m.company_id,

				pt.name as p_name,
				m.state as state, m.restrict_lot_id as prodlot_id,
				spt.code as type1,
				coalesce(sum(ip.value_float * m.product_qty * pu.factor / pu2.factor)::decimal, 0.0) as value,
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
                                    LEFT JOIN stock_picking_type spt ON (p.picking_type_id = spt.id)
                                    LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.template,',pt.id) AND ip.company_id=p.company_id)
				    WHERE m.state != 'cancel'
			    GROUP BY
				m.id , m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id,l.name, m.location_dest_id,pt.name,
				m.restrict_lot_id, m.date, m.state, l.usage,l.active, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'), to_char(m.date, 'MM'),spt.code
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
		    LEFT JOIN stock_picking_type spt ON (p.picking_type_id = spt.id)
                    WHERE m.state = 'done' and l.usage='internal' and spt.code='outgoing' and cast(m.date as date)= (SELECT CURRENT_DATE) and (m.origin like 'SO%' or m.origin like 'RO%')
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
                    LEFT JOIN stock_picking_type spt ON (p.picking_type_id = spt.id)
		    WHERE m.state = 'done' and l.usage='internal' and spt.code='outgoing' and cast(m.date as date)= (SELECT CURRENT_DATE-1) and (m.origin like 'SO%' or m.origin like 'RO%')
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
                    LEFT JOIN stock_picking_type spt ON (p.picking_type_id = spt.id)

		    WHERE m.state = 'done' and l.usage='internal' and spt.code='outgoing'and cast(m.date as date)= (SELECT CURRENT_DATE-1) and (m.origin like 'RO%')
	    GROUP BY
		m.id, m.product_id, m.location_id,l.name, l.usage,spt.code,m.origin
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
                    LEFT JOIN stock_picking_type spt ON (p.picking_type_id = spt.id)
		    WHERE m.state = 'done' and l.usage='internal' and spt.code='outgoing' and cast(m.date as date)= (SELECT CURRENT_DATE-1) and (m.origin like 'SO%')
	    GROUP BY
		m.id, m.product_id,m.location_id,l.name, l.usage
		order by m.date asc
		)
		as temp1
		group by temp1.location_id ,temp1.product_id,temp1.so_qty
) as previous_data2 on (all_data.location_id=previous_data2.location_id and all_data.product_id=previous_data2.product_id)
order by 1,3
""")


        search_result= cr.fetchall()
        buf=cStringIO.StringIO()
        len_result=len(search_result)
        writer=csv.writer(buf, 'UNIX')
        if search_result:
            datas = ["Location ID","Location Name","Product ID","Product Name","Total Product Quantity","Current Product Quantity","Previous Product Quantity","Active","Yesterday Sale Quantity","Yesterday Exchange Quantity"]
            writer.writerow(datas)
            for each in search_result:
                datas=[]
                datas.append(each[1])
                datas.append(each[2])
                datas.append(each[3])
                datas.append(each[4])
                datas.append(each[5])
                datas.append(each[6])
                datas.append(each[7])
                datas.append(each[8])
                datas.append(each[9])
                datas.append(each[10])
                writer.writerow(datas)
        else:
            datas.append('')
#        pls_write = writer.writerow(datas)
        out=base64.encodestring(buf.getvalue())
        buf.close()
        self.write(cr, uid, ids, {'csv_file':out,'name': 'Inventory Analysis Report.csv'})
        return {
              'name':_("Inventory Analysis Report"),
              'view_mode': 'form',
              'view_id': False,
              'view_type': 'form',
              'res_model': 'inventory.analysis.report',
              'res_id': ids[0],
              'type': 'ir.actions.act_window',
              'nodestroy': True,
              'target': 'new',
              'context': context,
            }
inventory_analysis_report()