import os
import pickle
import sys
import csv
import time
import zipfile
from StringIO import StringIO
import cStringIO
import base64
from openerp.tools.translate import _
from openerp.osv import fields, osv
import logging
logger = logging.getLogger('arena_log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

class import_serials(osv.osv_memory):

    _name = 'import.serials'
    _description = "Importing serial numbers"

    def create_serial_numbers(self,cr,uid,ids,context=None):
        print"context",context
        product_obj = self.pool.get('product.product')
        picking_in_obj = self.pool.get('stock.picking.in')
        picking_obj = self.pool.get('stock.picking')
        prodlot_obj = self.pool.get('stock.production.lot')
        csv_data = self.browse(cr,uid,ids[0])
        if not context.get('active_ids') or len(context.get('active_ids')) > 1:
            raise osv.except_osv(_('Active Ids Issue !'), _('Improper Manufacturing ID or you \'re trying to select multiple Manufacturing ids '))
        picking_id = context.get('active_ids')[0]
        picking_brw = picking_in_obj.browse(cr,uid,picking_id)
        module_data = csv_data.csv_file_supplier
        val = base64.decodestring(module_data)
        partner_data = val.split("\r")
        if len(partner_data) == 1 and partner_data[0].find('\n') != 1:
            partner_data = partner_data[0].split('\n')        
        ## dictionary to prepare for the products in the csv in order to map in the specific 
        ## stock moves
        ##  count total numbers of quantities in CSV and Incoming Shipment
        total_qty_in_csv=total_qty_in_shipment=csv_list_qty=0
        for lines in picking_brw.move_lines:
            print "linesss",lines.product_qty
            total_qty_in_shipment += lines.product_qty
            for each in partner_data[1:-1]:
                partno = each.split(';')[0]
                prod_id = product_obj.search(cr, uid, [('default_code','=', partno)])
                if prod_id and prod_id[0] ==  lines.product_id.id:
                    qty =  int(each.split(';')[1])
                    total_qty_in_csv += qty
        print "total_qty_in_csv",total_qty_in_csv,total_qty_in_shipment
        if total_qty_in_csv < total_qty_in_shipment:
            raise osv.except_osv(_('Error!'), _('Insufficient Serial Number!.'))

        if len(partner_data) > 1:
            for lines in picking_brw.move_lines:
                print "linesssssssssssssssssssssssss",lines.id
                for i in range(1,len(partner_data)):
                    partner_data_line = partner_data[i]
                    partner_single_row = partner_data_line.split(';')
                    logger.info('CSV single row %s'%(partner_single_row))
                    if len(partner_single_row)==3:
                        if partner_single_row[0] == ''  or partner_single_row[0] == '\n' :
                            raise osv.except_osv(_('Error!'), _('Part number can not be blank.Please correct the csv file!.'))

                        if partner_single_row[1] == ''  or partner_single_row[1] == '\n' or partner_single_row[1] == '0' :
                            raise osv.except_osv(_('Error!'), _('Quantity can not be blank or 0.Please correct the csv file!.'))

                        if partner_single_row[2] == ''  or partner_single_row[2] == '\n' :
                            raise osv.except_osv(_('Error!'), _('Serial number can not be blank.Please correct the csv file!.'))

                    if partner_single_row[0] == ''  or partner_single_row[0] == '\n':
                        continue
                    part_number = partner_single_row[0].replace(" ","")
                    part_number = partner_single_row[0].replace("\"","")
                    print "part_numberrrrrrrrrrrrr",part_number.split(';')[0],part_number
                    ### search for the part number mentioned in the csv
                    part_ids = product_obj.search(cr, uid, [('default_code','=',part_number.split(';')[0])])

                    if not part_ids:
                        raise osv.except_osv(_('Error!'), _('Product %s does not exist in database.Please correct the csv file!.'%(part_number)))
                    if len(part_ids)>1:
                        raise osv.except_osv(_('Error!'), _('You have same %s product more than one time!.'%(part_number)))
                    if part_ids[0] == lines.product_id.id:                        
                    ### check the quantity in the csv
                        quantity = partner_single_row[1].replace(" ","")
                        quantity = partner_single_row[1].replace("\"", "")
                        print"quantity",quantity
                        ### check the serial Lots in the csv
                        serial_lot = partner_single_row[2].replace(" ","")
                        serial_lot = partner_single_row[2].replace("\"","")
                        if quantity > '1':
                            raise osv.except_osv(_('Error!'), _('Quantity can not be more than 1 for %s serial number!.'%(serial_lot)))
                        if serial_lot:
                            lot_ids = prodlot_obj.search(cr, uid, [('name','=',serial_lot)])
                            if not lot_ids and context.get('active_model',False)=='stock.picking.in':
                                if csv_list_qty < total_qty_in_shipment:
                                    csv_list_qty+= 1
                                    lot_id = [prodlot_obj.create(cr, uid, {
                                            'name' : serial_lot,
                                            'product_id' : part_ids[0],
                                            'ref' : lines.product_id.name,
                                            'qty_avail' : float(quantity),
                                            'location_id': lines.location_dest_id.id
                                        })]
                                    cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (lines.id, lot_id[0]))
                            elif lot_ids and context.get('active_model',False)=='stock.picking':
                                internal_lot_ids = prodlot_obj.search(cr, uid, [('name','=',serial_lot),('location_id','=', lines.location_id.id)])
                                print"internal_lot_ids",internal_lot_ids
                                if csv_list_qty < total_qty_in_shipment:
                                    csv_list_qty+= 1
                                    prodlot_obj.write(cr,uid,internal_lot_ids,{'location_id':lines.location_dest_id.id,'ref':picking_brw.name})
                                    for each_lot in internal_lot_ids:
                                        cr.execute("insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)"%(lines.id,each_lot))
                            elif not lot_ids and context.get('active_model',False)=='stock.picking':
                                continue
#                                self.pool.get('stock_move_lot').create(cr,uid)
#                                dhfgjgf
                                
                            else:
                              raise osv.except_osv(_('Error!'), _('Serial number %s already present!.'%(serial_lot)))                
            if context.get('active_model',False)== 'stock.picking':
                picking_state=picking_obj.write(cr,uid,[picking_id],{'state':'shipping'})
            else:
                incoming_picking_id= context.get('active_ids')
                partial_id = self.pool.get("stock.partial.picking").create(cr, uid, {}, context=context)
                context.update({'partial_id':partial_id})
                self.pool.get('stock.picking').make_picking_done(cr, uid, incoming_picking_id, context)
#            else:
                
        return True

    def import_serial_numbers(self, cr, uid, ids, context=None):
        print"context",context
        csv_data = self.browse(cr,uid,ids[0])
        obj_partner = self.pool.get('res.partner')
        obj_category = self.pool.get('product.category')
        obj_uom = self.pool.get('product.uom')
        picking_obj = self.pool.get('stock.picking')
        partial_picking_obj = self.pool.get('stock.partial.picking')
        product_obj = self.pool.get('product.product')
        prodlot_obj = self.pool.get('stock.production.lot')
        move_obj = self.pool.get('stock.move')

        ### suitable code to check the active ids and throw an exception if the user selects
        ### more than one pickings
        
        if not context.get('active_ids') or len(context.get('active_ids')) > 1:
            raise osv.except_osv(_('Active Ids Issue !'), _('Improper picking Id or you \'re trying to select multiple picking ids '))


        picking_id = context.get('active_ids')[0]
        income_picking = picking_obj.browse(cr, uid, picking_id)
        type = income_picking.type
        print"type",type
        if not csv_data.csv_file_supplier:
            raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))

        module_data = csv_data.csv_file_supplier
        val = base64.decodestring(module_data)
        partner_data = val.split("\r")

        
        if len(partner_data) == 1 and partner_data[0].find('\n') != 1:
            partner_data = partner_data[0].split('\n')
        count = 1
        ## dictionary to prepare for the products in the csv in order to map in the specific 
        ## stock moves
        part_dict = {}
        dupli_lot=''
        if len(partner_data)>1:
            for i in range(1,len(partner_data)):
                dict = {}
                partner_data_line = partner_data[i]

                partner_single_row = partner_data_line.split(',')
                logger.info('CSV single row %s'%(partner_single_row))
                if len(partner_single_row)==3:
                    if partner_single_row[0] == ''  or partner_single_row[0] == '\n' :
                        raise osv.except_osv(_('Error!'), _('Part number can not be blank.Please correct the csv file!.'))

                    if partner_single_row[1] == ''  or partner_single_row[1] == '\n' or partner_single_row[1] == '0' :
                        raise osv.except_osv(_('Error!'), _('Quantity can not be blank or 0.Please correct the csv file!.'))

                    if partner_single_row[2] == ''  or partner_single_row[2] == '\n' :
                        raise osv.except_osv(_('Error!'), _('Serial number can not be blank.Please correct the csv file!.'))
                    
                if partner_single_row[0] == ''  or partner_single_row[0] == '\n':
                    
                    continue

                
                part_number = partner_single_row[0].replace(" ","")
                part_number = partner_single_row[0].replace("\"","")
                print "part_numberrrrrrr",part_number
                ### search for the part number mentioned in the csv
                part_ids = product_obj.search(cr, uid, [('default_code','=',part_number.strip())])
                
                if not part_ids:
                    raise osv.except_osv(_('Error!'), _('Part number %s does not exist in database.Please correct the csv file!.'%(part_number)))
                if len(part_ids)>1:
                    raise osv.except_osv(_('Error!'), _('You have same part number %s more than one product!.'%(part_number)))
                cur_prod = product_obj.browse(cr, uid, part_ids[0])
                ### check the quantity in the csv



                quantity = partner_single_row[1].replace(" ","")
                quantity = partner_single_row[1].replace("\"", "")
                
                ### check the serial Lots in the csv
                serial_lot = partner_single_row[2].replace(" ","")
                serial_lot = partner_single_row[2].replace("\"","")
                
                if quantity > '1':
                    raise osv.except_osv(_('Error!'), _('Quantity can not be more than 1 for %s serial number!.'%(serial_lot)))

                dict['quantity'] = float(quantity)

                lot_ids = []
                if type == 'out':
                    context.update({'active_model':'stock.picking.out'})
                    ## code to check if the serial lots exists in the system or no
                    ## if the serial lots exist then get the serials directly or else
                    ## create new ones
                    if serial_lot:
                        current_move=''
                        lot_ids = prodlot_obj.search(cr, uid, [('name','=',serial_lot)])
                        if lot_ids:
                            prod_bw = prodlot_obj.browse(cr,uid,lot_ids[0])
                            if prod_bw.serial_used:
                                raise osv.except_osv(_('Error!'), _('%s serial number already scanned!.'%(serial_lot)))
                        ## code to check if no move line exist for importing serials
                        flag=False
                        for each_move_line in income_picking.move_lines:
                            if each_move_line.product_id.id==cur_prod.id:
                                current_move =  each_move_line
                                flag=True
                                break
                        if not flag:
                            raise osv.except_osv(_('Error!'), _('There is no move line for %s serial number !.'%(serial_lot)))
                        if not lot_ids:
                            

                          ## code create serials if not exist in database and move line exist in picking
                            lot_ids = [prodlot_obj.create(cr, uid, {
                                'name' : serial_lot,
                                'product_id' : part_ids[0],
                                'ref' : income_picking.name,
                                'qty_avail' : float(quantity),
                                'location_id':current_move.location_dest_id.id,
                                'serial_used':True
                            })]
                        else:
                            prodlot_obj.write(cr,uid,lot_ids,{'ref':income_picking.name,
                                'location_id':current_move.location_dest_id.id,'serial_used':True})
#                            raise osv.except_osv(_('Error!'), _('Serial number %s  already exists in OpenERP !.'%(serial_lot)))

                        lot_ids = list(set(lot_ids))
                        ##code to update qty_avail of already created serials if splite type is none
                        for lot in lot_ids:
                            old_qty=prodlot_obj.browse(cr,uid,lot).qty_avail
                            prodlot_obj.write(cr,uid,[lot],{'qty_avail':(float(quantity))})

                else:
                    context.update({'active_model':'stock.picking'})
                    current_move=''
                    if serial_lot:
                        flag=False
                        for each_move_line in income_picking.move_lines:
                            if each_move_line.product_id.id==cur_prod.id:
                                current_move=each_move_line
                                flag=True
                                break
                        lot_ids = prodlot_obj.search(cr, uid, [('name','=',serial_lot),('location_id','=',current_move.location_id.id)])
                        if lot_ids:
                            ## code to check if no move line exist for importing serials
                            
                            if not flag:
                                raise osv.except_osv(_('Error!'), _('There is no move line for %s serial number !.'%(serial_lot)))

                            prodlot_obj.write(cr,uid,lot_ids,{'ref':income_picking.name, 'location_id':current_move.location_dest_id.id})
                        else:
                            raise osv.except_osv(_('Error!'), _('Serial number %s  not found !.'%(serial_lot)))
                            ## code to check duplicate serial if splite type single
    #                        lot_name=[val.name+'/' for val in prodlot_obj.browse(cr,uid,lot_ids) if val.product_id.lot_split_type=='single' ]
    #                        if len(lot_name)>0:
    #                            dupli_lot=dupli_lot+lot_name[0]
                        lot_ids = list(set(lot_ids))
                        ##code to update qty_avail of already created serials if splite type is none
                        for lot in lot_ids:
#                            old_qty=prodlot_obj.browse(cr,uid,lot).qty_avail
                            prodlot_obj.write(cr,uid,[lot],{'qty_avail':(float(quantity))})

                dict['serial_lots'] = lot_ids
                ### code to check if the part dict already exists or no.
                ### if it exists update the quantity or else create a new part dict
                ### below code commented since for split type as none too the lines will be split
                ### for batch lot as well.

    #            if part_dict.has_key(part_ids[0]) and not cur_prod.split_type=='single':
                if part_dict.has_key(part_ids[0]):
                    part_dict[part_ids[0]]['quantity'] += float(quantity)
                    part_dict[part_ids[0]]['serial_lots'].extend(lot_ids)
                else:
                    part_dict[part_ids[0]] = dict

        else:
             raise osv.except_osv(_('Error!'), _('No record found in csv file!.'))
        print"part_dict",part_dict
        received_qty=0
        move_lines = []
        for each_move_line in income_picking.move_lines:
            prod_id = each_move_line.product_id.id
            for key,value in part_dict.iteritems():
                if key == each_move_line.product_id.id:
                    if each_move_line.product_qty == each_move_line.received_qty:
                        raise osv.except_osv(_('Error!'), _('Serial Numbers are already scanned for move %s'%(income_picking.name)))
                    if part_dict[prod_id]['quantity'] <= each_move_line.product_qty - each_move_line.received_qty:
                        
                        received_qty = each_move_line.received_qty + part_dict[part_ids[0]]['quantity']
#                        move_lines.append([0, False,{
#                                                           'product_id': each_move_line.product_id.id,
#                                                           'quantity': part_dict[prod_id]['quantity'],
#                                                           'product_uom' : each_move_line.product_uom.id,
#                                                           'location_id' : each_move_line.location_id.id,
#                                                           'location_dest_id':each_move_line.location_dest_id.id,
#                                                           'move_id' : each_move_line.id,
#                                                           'cost' : each_move_line.product_id.standard_price,
#                                                           'currency' : each_move_line.picking_id and each_move_line.picking_id.company_id and \
#                                                                        each_move_line.picking_id.company_id.currency_id and \
#                                                                        each_move_line.picking_id.company_id.currency_id.id or False,
#                                                           }])
                        part_dict[prod_id]['serial_lots'] = list(set(part_dict[prod_id]['serial_lots']))
                        print"part_dictttttttttt",part_dict
                        for each_serial in part_dict[prod_id]['serial_lots']:
                            print"each_serial",each_serial
                            move_obj.write(cr, uid, [each_move_line.id],{'prodlot_id':each_serial})
                            cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (each_move_line.id, each_serial))
                            cr.commit()
#                        move_obj.write(cr, uid, [each_move_line.id],{'stock_prod_lots' : [(6,0, part_dict[prod_id]['serial_lots'])],'received_qty':received_qty})
                        move_obj.write(cr, uid, [each_move_line.id],{'received_qty':received_qty})
                    else:
                        raise osv.except_osv(_('Error!'), _('Import quantity is greater than move quantity of part number %s.Please correct the csv file!.'%(each_move_line.product_id.default_code)))
             
#        write_id=income_picking.write({'duplicate_serials':dupli_lot},context=context)

#        if move_lines:
#            partial_picking_id = partial_picking_obj.create(cr,uid,{
#                'picking_id' : picking_id,
#                'move_ids' : move_lines,
#                'date' : date.today(),
#            })
#            partial_picking_obj.do_partial(cr, uid, [partial_picking_id],context)
#        else:
#            raise osv.except_osv(_('Error!'), _('Can not process receiving either more serials than receiving quantity in csv file or problem in move line !.'))
#
#        picking_obj.draft_force_assign(cr,uid,[income_picking.id])
#        return {'type':'ir.actions.act_window_close'}
#        context['active_model']='ir.ui.menu'
        status = picking_obj.browse(cr,uid,picking_id).state
        if status == 'draft':
           draft_validate = picking_obj.draft_validate(cr, uid, [picking_id], context=context)
        context['action_process_original'] = True ##Extra Line of Code
        function = picking_obj.action_process(cr, uid, [picking_id], context=context)
        #self.pool.get('stock.picking').write(cr,uid,[pick.id],{'scan_uid':uid,'scan_date':time.strftime('%Y-%m-%d %H:%M:%S')})
        res_id = function.get('res_id')
        
        if res_id:
            do_partial = self.pool.get("stock.partial.picking").do_partial(cr,uid,[res_id],context=context)
        print"contexxxxxxxxxxxxxxxxxxxxxxttttt",context
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': context.get('active_ids')[0],
                'res_model': context.get('active_model'),
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'domain': '[]',
                'context': context,
        }
        
    def assign_serial_numbers(self,cr,uid,ids,context=None):
        print "contextttttt",context
        mrp_obj = self.pool.get('mrp.production')
        prodlot_obj = self.pool.get('stock.production.lot')
        product_obj = self.pool.get('product.product')
        serial_no_list,lot_ids_list,total_qty=[],[],0.0
        csv_data = self.browse(cr,uid,ids[0])
        manufacturing_id = context.get('active_ids')
        manufacturing_brw = mrp_obj.browse(cr,uid,manufacturing_id[0])
        if manufacturing_brw.move_lines:
            print"iff"
            move_lines = manufacturing_brw.move_lines
        else:
            print"elseeeeeeeeee"
            move_lines = manufacturing_brw.move_lines2
        print "move_lines",move_lines
        module_data = csv_data.csv_file_supplier
        val = base64.decodestring(module_data)
        partner_data = val.split("\r")
        print"partner_data",partner_data
        if len(partner_data) == 1 and partner_data[0].find('\n') != 1:
            partner_data = partner_data[0].split('\n')
        total,serial_num = 0.0,[]
        for each_move in move_lines:
            total += each_move.product_qty
        for each_move in move_lines:
            for each in partner_data[1:-1]:
                print"each",each
                partno = each.split(';')[0]
                print"partno",partno
#                serial_no = each.split(',')[2]
                prod_id = product_obj.search(cr, uid, [('default_code','=',partno)])
                if not prod_id:
                    continue
                if prod_id[0] !=  each_move.product_id.id:
                    continue
                else:
                    qty =  int(each.split(';')[1])
                    serial_num = prodlot_obj.search(cr,uid,[('name','=',each.split(';')[2])])
                    if serial_num and not  serial_num in serial_no_list:
                        serial_no_list.append(serial_num[0])
                    total_qty += qty
                print "total_qtyyyyy",total_qty
                print "manufacturing_brw.product_qtyyy",manufacturing_brw.product_qty
                print"serial_no_list",serial_no_list
                print"manufacturing_brw.location_src_id.id",manufacturing_brw.location_src_id.id
                serial_numbers = prodlot_obj.search(cr,uid,[('product_id','=',prod_id[0]),('location_id','=',manufacturing_brw.location_src_id.id),('serial_used','=',False)]) 
#                serial_numbers=[63]
                print"serial_num",serial_num
                print"serial_numbers",serial_numbers
                cancel_final_list=set(serial_num) & set(serial_numbers)
                print"cancel_final_list",cancel_final_list
                if not cancel_final_list:
                    raise osv.except_osv(_('Error!'),_('Serial Number not Found'))
                if len(partner_data) > 1:
                    for i in range(1,len(partner_data)):
                        dict = {}
                        partner_data_line = partner_data[i]
                        partner_single_row = partner_data_line.split(';')
                        logger.info('CSV single row %s'%(partner_single_row))
                        if len(partner_single_row)==3:
                            if partner_single_row[0] == ''  or partner_single_row[0] == '\n' :
                                raise osv.except_osv(_('Error!'), _('Part number can not be blank.Please correct the csv file!.'))

                            if partner_single_row[1] == ''  or partner_single_row[1] == '\n' or partner_single_row[1] == '0' :
                                raise osv.except_osv(_('Error!'), _('Quantity can not be blank or 0.Please correct the csv file!.'))

                            if partner_single_row[2] == ''  or partner_single_row[2] == '\n' :
                                raise osv.except_osv(_('Error!'), _('Serial number can not be blank.Please correct the csv file!.'))

                        if partner_single_row[0] == ''  or partner_single_row[0] == '\n':
                            continue
                        part_number = partner_single_row[0].replace(" ","")
                        part_number = partner_single_row[0].replace("\"","")
                        ### search for the part number mentioned in the csv
                        part_ids = product_obj.search(cr, uid, [('default_code','=',part_number.strip())])

                        if not part_ids:
                            raise osv.except_osv(_('Error!'), _('Part number %s does not exist in database.Please correct the csv file!.'%(part_number)))
                        if len(part_ids)>1:
                            raise osv.except_osv(_('Error!'), _('You have same part number %s more than one product!.'%(part_number)))
                        cur_prod = product_obj.browse(cr, uid, part_ids[0])
    #                    print"part_ids",part_ids,manufacturing_brw.product_id.id
                        if part_ids[0] == each_move.product_id.id:
                        ### check the quantity in the csv
                            quantity = partner_single_row[1].replace(" ","")
                            quantity = partner_single_row[1].replace("\"", "")
                            print"quantity",quantity
                            ### check the serial Lots in the csv
                            serial_lot = partner_single_row[2].replace(" ","")
                            serial_lot = partner_single_row[2].replace("\"","")
                            print"serial_lot",serial_lot
                            if quantity > '1':
                                raise osv.except_osv(_('Error!'), _('Quantity can not be more than 1 for %s serial number!.'%(serial_lot)))
                            dict['quantity'] = float(quantity)
                            if serial_lot:
                                lot_ids = prodlot_obj.search(cr, uid, [('name','=',serial_lot),('location_id','=',manufacturing_brw.location_src_id.id),('serial_used','=',False)])
                                print"lot_ids",lot_ids
                                
                                if lot_ids and not lot_ids[0] in lot_ids_list:
                                    lot_ids_list.append(lot_ids[0])
            print"lot_ids_list",lot_ids_list
            if serial_no_list:
                context.update({'csv':True,'serial_number_list':lot_ids_list})
            print"context serial number",context
        self.pool.get('mrp.production').action_produce(cr, uid, manufacturing_id, context.get('production_qty'), context.get('mode'), context=context)
#        serial_no = self.pool.get('stock.production.lot').search(cr,uid,[('product_id','=',scheduled.product_id.id),('location_id','=',production.location_src_id.id),('serial_used','=',False)]) 
        return True
        
    def default_get(self, cr, uid, fields, context=None):
        res={}
        """
             To get default values for the object.
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param fields: List of fields for which we want default values
             @param context: A standard dictionary
             @return: A dictionary which of fields with values.

        """
        
        if context is None:
            context = {}
        
        if context.get('active_model', False)=='mrp.production':
            res.update({'mrp_object':True})
        return res

    _columns = {

          'csv_file_supplier': fields.binary('CSV file'),

          'mrp_object': fields.boolean('MRP Object'),
          'move_internal':fields.boolean('Internal Moves'),
          
#          'sel_type': fields.selection([('sale','Sale'),('purchase','Purchase')],'Type'),

    }
    _default = {
        'mrp_object':False,
        'picking_object':False,
        'move_internal':False,
    }

import_serials()
