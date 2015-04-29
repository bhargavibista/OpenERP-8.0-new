# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
import base64
import csv
from openerp.tools.translate import _

class vista_report_wizard(osv.osv_memory):
    _name = "vista.report.wizard"
    _description = "Export CSV"
    _columns = {
        'date_create' : fields.date('Date'),
        'option':fields.selection([('create_report','Create Warehouse Report' ),('import_report','Import Warehouse Report')],'Report Options'),
        'csv_file': fields.binary('Attachment'),
    }
    def create_report(self,cr,uid,ids,context={}):
        if context is None:
            context={}
        report_obj=self.browse(cr,uid,ids[0])
        vista_report_obj=self.pool.get('vista.report')
        create_date=report_obj.date_create
        if create_date:
            context.update({'date_create':create_date})
            new_record = vista_report_obj.create_delivery_report(cr,uid,context)
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': new_record,
                'res_model': 'vista.report',
                'type': 'ir.actions.act_window'
                    }
        return {'type': 'ir.actions.act_window_close'}

    def import_report(self,cr,uid,ids,context={}):
        if context is None:
            context={}
        report_obj=self.browse(cr,uid,ids[0])
        pick_obj=self.pool.get('stock.picking')
        #sale_obj=self.pool.get('sale.order')
        csv_file=report_obj.csv_file
        if not csv_file:
            raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))
        val = base64.decodestring(csv_file)
        stock_data = val.split("\n")
        if stock_data:
            stock_data.pop(0)
            file_Reader = csv.reader(stock_data)
        for i in file_Reader:
            if i and len(i) > 6:
                reference=i[2]
                tracking_number=i[6]
                pick_ids=pick_obj.search(cr,uid,[('name','=',reference)])
                if pick_ids and tracking_number:
                    for picking in pick_obj.browse(cr,uid,pick_ids):
                        if picking.state!='done':
                            pick_obj.draft_force_assign(cr,uid,[picking.id],context)
                            pick_obj.force_assign(cr,uid,[picking.id],context)
                            pick_obj.test_assigned(cr,uid,[picking.id])
                            picking.action_assign_wkf()
                            context['action_process_original'] = True ##Extra Line of Code
                            process = pick_obj.action_process(cr, uid, [picking.id], context=context)
                            context = process.get('context')
                            context['active_id']=ids[0]
                            res_id = process.get('res_id')
                            if res_id:
                                self.pool.get('stock.partial.picking').do_partial( cr, uid, [process['res_id']], context)
                                picking.action_done()
                        cr.execute("update stock_picking set carrier_tracking_ref='%s' where id=%s"%(tracking_number,picking.id))
                        if picking.sale_id:
                            cr.execute("update sale_order set tracking_no='%s' where id=%s"%(tracking_number,picking.sale_id.id))
        return {'type': 'ir.actions.act_window_close'}
vista_report_wizard()