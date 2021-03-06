# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import fields, osv

class picking_scanning(osv.osv_memory):
    _name = "picking.scanning"
    _description = 'Make Scanning'
    _rec_name='bcquantity'
    _columns = {
        'start_range' : fields.integer('Range', required=True),
        'range_scan' : fields.boolean('Is Range',help="Should do a Range scan or no"),
        'bcquantity': fields.integer('Quantity'),
        'default_code': fields.char('Bar Code', size=32, help="Keep focus on this field and use bar code scanner to scan products"),
        'picking_ids':fields.many2many('stock.picking',  'picking_scan_rel', 'scan_id', 'picking_id', 'Stock Picking'),
        'line_ids':fields.many2many('stock.move','picking_move_rel','scan_id','line_id','Packing Lines'),
        'skip_barcode': fields.boolean('Skip Barcode Scanning'),
        'is_new_pick': fields.boolean('New Picking ID'),
        'continue_scan': fields.boolean('Continue Scan',help="Check this field to continue scan with new barcode"),
        'new_barcode': fields.char('New Bar Code', size=13),
        'new_product_id':fields.many2one('product.product','Product'),
        'new_qty': fields.integer('New Quantity'),
        'packaging' : fields.many2one('product.packaging','New Packaging', help="Gives the different ways to package the same product. This has no impact on the picking order and is mainly used if you use the EDI module."),
#        'pack_nobar_image': fields.binary(string='Scan Product'),
        'br_product_id': fields.many2one('product.product', 'Scan image for this product', readonly=True),
        'reference_no': fields.integer('Reference NO'),
        'carrier_track_done': fields.boolean('Picking Done'),
        'note': fields.char('Note', size=100),
        'check_note': fields.boolean('Check_note'),
        'stock_picking_id' : fields.many2one('stock.picking','Picking'), ##cox gen2 changed the relation to stock.picking from stock.picking.out
    }

    def default_get(self, cr, uid, fields, context=None):
        """
             To get default values for the object.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param fields: List of fields for which we want default values
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        picking_ids = []
        if context is None:
            context = {}
        picking_obj = self.pool.get('stock.picking') ##cox gen2 odoo8 changed class from stock.picking.out to stock.picking
        if context.get('active_model', False):
            if context['active_model'] == 'stock.picking':  ##cox gen2  odoo8 changed class from stock.picking.out to stock.picking
                picking_ids = context.get('active_ids', [])
            elif context['active_model'] == 'sale.order':
                name = self.pool.get('sale.order').browse(cr,uid,context['active_ids']).name
                pick_id=picking_obj.search(cr,uid,[('origin','=',name)])
                if pick_id:
                    picking_ids = pick_id
        pick,scanning_line = [],[]
        res = super(picking_scanning, self).default_get(cr, uid, fields, context=context)
        if picking_ids:
            res.update({'stock_picking_id':picking_ids[0]})
        for picking in picking_obj.browse(cr, uid, picking_ids, context=context):
           
            if picking.state == 'done' or picking.shipping_process == 'wait':
                continue
            stockids = picking.move_lines
            for stock in stockids:
                
                if stock.state == 'done':
                    continue
                scanning_line.append(stock.id)
            pick.append(picking.id)
        if 'bcquantity' in fields:
            res.update({'bcquantity': 1})
        res.update({'picking_ids':pick})
        if len(scanning_line):
            res.update({'line_ids':scanning_line})
        res.update({'start_range':1})
        return res


    # To add domain filter for product
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                       context=None, toolbar=False, submenu=False):
       """
        Changes the view dynamically
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return: New arch of view.
       """
       product_ids,picking_ids = [],[]
       if context is None:
           context={}
       picking_obj = self.pool.get('stock.picking')
       if context.get('active_model', False):
           if context['active_model']=='stock.picking': ##cox gen2 odoo8  changed class from stock.picking.out to stock.picking
               picking_ids = context['active_ids']
           elif context['active_model']=='sale.order':
               pick_id=picking_obj.search(cr,uid,[('sale_id','=',context['active_ids'])])
               if pick_id:
                    picking_ids = pick_id
           for picking_id in picking_ids:
               picking_id_obj = picking_obj.browse(cr, uid, picking_id)
               #if picking_id_obj.state == 'done':
                #   raise osv.except_osv(_('Warning!'),_('You cannot Scan this Order %s because Its in Done State')%(picking_id_obj.name))
               for moveline in picking_id_obj.move_lines:
                   product_ids.append(moveline.product_id.id)
       res = super(picking_scanning, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
       
       if res.get('fields').get('new_product_id'):
            res['fields']['new_product_id']['domain'] = [('id', 'in', product_ids)]
            
       return res
  
    ###testing new code
    def carrier_track_ref(self, cr, uid, reference_no, default_code, context=None):
        picking_obj = self.pool.get('stock.picking')
        if reference_no:
            picking_ids = picking_obj.search(cr, uid, [('name', '=', reference_no)])
        if len(picking_ids):
            for picking in picking_obj.browse(cr, uid, picking_ids, context=context):
                pick_id = picking.id
                if picking.carrier_id and picking.carrier_id.is_scan_tracking == True:
                    car = picking_obj.write(cr,uid,[pick_id],{'carrier_tracking_ref':default_code,})
                    return {'value': {'carrier_track_done': True, 'carrier':True}}
#        carrier_track_done = self.write(cr,uid,ids,{'carrier_track_done':True})
                else:
                    return {'value': {'carrier_track_done': True,'carrier':False}}

#    def onchange_defaultcode(self, cr, uid, ids, default_code=False, bcquantity=False,picking_ids=False ,line_ids=False, new_product_id=False,start_range=False, range_scan=False,reference_no=False,carrier_track_done=False,note=False,check_note=False,context=None):
    def onchange_defaultcode(self, cr, uid, ids, default_code=False,picking_ids=False ,line_ids=False, new_product_id=False,range_scan=False,reference_no=False,carrier_track_done=False,note=False,check_note=False,context=None):
        #bar code scanning
        #search the product in stock move
        #search packaging and find out product and its quantity. Update stock move as per packaging details
        #search delivery orders and populate the products from them
        prodlot_obj = self.pool.get('stock.production.lot')
        tr_barcode_obj = self.pool.get('tr.barcode')
        start_range = 1
        if context is None:
            context={}
        picking_obj = self.pool.get('stock.picking')
        stock_move_obj = self.pool.get('stock.move')
        search_picking_ids = picking_obj.search(cr, uid, [('name', '=', default_code)])
        type = 'in'
        if search_picking_ids:
            type = picking_obj.browse(cr, uid, search_picking_ids[0]).type
        calltracking = False
# Updatation for wizard SCANNED_QTY
        picking_obj1 = picking_obj.browse(cr, uid, picking_ids[0][2][0])
        line_scanned_ids = []
        if picking_obj1:
            for each_move_line in picking_obj1.move_lines:
                if each_move_line.procurement_id.sale_line_id.order_id:
                    line_scanned_ids.append(each_move_line.id) 
        if reference_no:
            picking = picking_obj.search(cr, uid, [('name', '=', reference_no)])
            if len(picking):
                for pick in picking_obj.browse(cr, uid, picking, context=context):
                    if pick.carrier_id and pick.carrier_id.is_scan_tracking == True and pick.carrier_tracking_ref == False:
                        calltracking = True
        search_prod_barcode = self.pool.get('stock.production.lot').search(cr, uid, [('name','=',default_code)])
        search_tr_barcode_ids = tr_barcode_obj.search(cr, uid, [('code','=',default_code)])
        if len(search_picking_ids) != 0 and len(search_prod_barcode) == 0:
            reference_no = default_code
            scanning_line = []
            stockids = []
            return_move_lines = {'default_code': False,'reference_no': reference_no}
            for picking_out in picking_obj.browse(cr, uid, search_picking_ids, context=context):
                if picking_out.shipping_process == 'wait':
                    return_move_lines['note']='Order is in hold state'
                    continue
                if picking_out.state == 'done':
                    return_move_lines['note']='Order Dispatched'
                    continue
                stockids.append(picking_out.move_lines)
                carrier_ids = picking_out.carrier_id.id
                pick_id = picking_out.id
                #check if the carrier_track_ref is checked or not
                if carrier_ids:
                    carrier = self.pool.get('delivery.carrier').browse(cr, uid,carrier_ids).is_scan_tracking
                    return_move_lines['check_note']=carrier
                    if carrier == True:
                        note = "Please Enter the Carrier Tracking Reference no"
                    else:
                        note=""
                        return_move_lines['carrier_track_done']= True
                    return_move_lines['note']=note
                else:
                    return_move_lines['carrier_track_done']= True
                    return_move_lines['note']=""
            for stockid in stockids:
                for stock in stockid:
                    scanning_line.append(stock.id)
                    #check if the product has image attached
                    # need to change this function in future ########('') Velodyne
                    package_ids = self.pool.get('product.packaging').search(cr, uid, [('product_tmpl_id', '=', stock.product_id.id)])
                    if len(package_ids):
#                        tr_barcode_image = self.pool.get('product.packaging').browse(cr, uid, package_ids[0]).tr_barcode_id
#                        if tr_barcode_image:
#                        barcode_image = tr_barcode_image.image
                        return_move_lines.update({'br_product_id': stock.product_id.id})
            if len(line_ids[0][2]):
                for line in line_ids[0][2]:
                    scanning_line.append(line)
            if len(scanning_line):
                return_move_lines.update({'line_ids': sorted(set(scanning_line))})
            if len(picking_ids[0][2]):
                for picking_add in picking_ids[0][2]:
                    search_picking_ids.append(picking_add)
            return_move_lines.update({'picking_ids': sorted(set(search_picking_ids))})
            return {'value': return_move_lines}
		 #This scanning is for carrier tracking reference
        elif search_tr_barcode_ids:
            product_id = tr_barcode_obj.browse(cr, uid, search_tr_barcode_ids[0]).product_id.id
            return { 'value' : {'new_product_id': product_id}}
        elif len(search_prod_barcode) == 0 and reference_no != 0 and calltracking == True:
            track_ids = self.carrier_track_ref(cr, uid,reference_no, default_code)
            carrier = False
            carrier_track_done = track_ids['value']['carrier_track_done']
            done = track_ids['value']['carrier']
            if done == True:
                tracking_note='Tracking Reference saved! Please Scan products now'
            else:
                tracking_note='Wrong barcode ! Please Scan products now'
    #            return_values = {'default_code': False,'carrier_track_ref': False}
            return {'value': {'carrier_track_done': True,'default_code': False,'check_note': carrier, 'note':tracking_note}}
        elif len(search_prod_barcode) == 0 and reference_no == 0 and type =='out':
            #raise osv.except_osv(_('Error !'), _('Please enter the order reference no'))
            return {'value': {'default_code': False,'note':'Please enter the order reference no'}}
         ##this scanning is for product
        else:
            product_ids = []
            scanning_line = []
            product_array = []
            exceeds = True
            quantity = 0
            receiv_qty = 0
            purchase_status = False
            faulty_barcode = False
            for line in line_ids:
                for line in line[2]:
                    if line != 0:
                        product = self.pool.get('stock.move').browse(cr,uid,line).product_id.id
                        if product not in product_array:
                            product_array.append(product)
            picking = picking_ids[0][2]
            packaging = self.pool.get('stock.production.lot').search(cr,uid,[('name','=',default_code),('serial_used','=',False)])
            test_serial = self.pool.get('stock.production.lot').search(cr,uid,[('name','=',default_code)])
            if not test_serial:
                faulty_barcode =  True
            product_ids = self.pool.get('product.product').search(cr, uid, [('ean13', '=', default_code)])
            for line in line_ids:
                line = line[2]
                for line in line:
                    scanning_line.append(line)
            type = False
            if picking:
                for pick in picking:
                    shipping_type = self.pool.get('stock.picking').browse(cr,uid,pick).picking_type_id.code ##cox gen2 odoo8 changed type to picking_type_id.code
                    if shipping_type == 'incoming': ##cox gen2 odoo8 changed 'in' to 'incoming'
                        type = 'in'
                    else:
                        type = 'out'
            if type == 'in':
                #packaging = self.pool.get('product.packaging').search(cr,uid,[('barcode','=',default_code)])
                #productids = self.pool.get('product.product').search(cr, uid, [('ean13', '=', default_code)])
                # Doing scanning without purchase order
                if default_code != False:
                    if picking:
                        for pick in picking:
                            ##cox gen2 
                            pick_browse = picking_obj.browse(cr,uid,pick)
                            
                            if pick_browse.move_lines :
                                for each_move in pick_browse.move_lines:
                                    if each_move.purchase_line_id:
                                        
                                        purchase = each_move.purchase_line_id.order_id.id
                            ####commented the below line coz there no field purchase_id in stock.picking
#                            purchase = self.pool.get('stock.picking').browse(cr,uid,pick).procurement_id.purchase_id  ##cox gen2 changed purchase_id to .procurement_id.purchase_id
                            if purchase:
                                purchase_status = True
                            else:
                                purchase_status = False
                                dest_id = self.pool.get('stock.picking').browse(cr,uid,picking[0]).dest_id.id
                                move_lines = self.pool.get('stock.picking').browse(cr,uid,picking[0]).move_lines
                        if purchase_status != False:
                            if default_code != False:
                                #### velodyne modified code for Incoming shipment
                                #### for allocating new serial numbers to the stock moves each time
                                stock_move_ids = line_ids[0][2]
                                stock_move_ids.sort()
                                obj_stock_moves = stock_move_obj.browse(cr, uid, stock_move_ids)
                                if range_scan:
                                    if new_product_id and start_range:
                                        validate_scan_vals = {
                                            'default_code' : default_code,
                                            'new_product_id' : new_product_id,
                                            'start_range' : start_range,
                                            'range_scan' : range_scan,
                                            'line_ids' : obj_stock_moves,
                                        }
                                        return_vals = self.validate_scan(cr, uid, ids, validate_scan_vals)
                                        return_vals['line_ids'] = line_scanned_ids
                                        return {'value': return_vals}
                                    else:
                                        return True
                                if test_serial:
                                    return {'value': {'default_code': False, 'note':'Product Already Scanned', 'new_product_id':False, 'start_range': 0, 'range_scan': False}}
                                total_scanned_moves = 0
                                for each_move in obj_stock_moves:
                                    if each_move.status == 'done':
                                        total_scanned_moves += 1
                                for each_move in obj_stock_moves:
                                    current_stock_move_id = each_move.id
                                    received_qty = 0
                                    if each_move.received_qty:
                                        received_qty = each_move.received_qty
                                    if not new_product_id:
                                        raise osv.except_osv(_('Product ERROR !'), _('Please select a product'))
                                    scan_product_id = new_product_id
                                    if each_move.product_id.id != scan_product_id:
                                        continue
                                    if each_move.product_qty == each_move.received_qty:
                                        return {'value': {'default_code': False, 'bcquantity': 1,'is_new_pick':False,'note':'Product Already scanned'}}
                                    received_qty = received_qty + 1
                                    status = stock_move_obj.write(cr, uid, each_move.id,{'received_qty': received_qty})
                                    search_child_mv_ids = stock_move_obj.search(cr,uid,[('parent_stock_mv_id','=',each_move.id)])
                                    if search_child_mv_ids:
                                        stock_move_obj.write(cr, uid, search_child_mv_ids,{'received_qty': received_qty})
                                    prodlot_id = prodlot_obj.create(cr, uid, {'product_id': scan_product_id,'name': default_code})
                                    cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (current_stock_move_id, prodlot_id))
                                    cr.commit()
                                    line_scanned_ids = []
                                    if picking_obj1:
                                        if picking_obj1.move_lines:
                                            for each_move_line in picking_obj1.move_lines:
                                                if each_move_line.sale_line_id and each_move_line.sale_line_id.order_id:
                                                    line_scanned_ids.append(each_move_line.id)
                                    if each_move.product_qty == received_qty:
                                        stock_move_obj.write(cr, uid, each_move.id,{'status': 'done'})
                                        if search_child_mv_ids:
                                            status = stock_move_obj.write(cr, uid, search_child_mv_ids,{'status': 'done'})
                                        total_scanned_moves += 1
                                        if total_scanned_moves == len(obj_stock_moves):
                                            return {'value': {'bcquantity': 1,'line_ids':[],'is_new_pick':False,'default_code': False,'note':'Scan Next Shipment!'},'type': 'ir.actions.act_window_close'}
                                        else:
                                            return {'value': {'default_code': False, 'line_ids':line_scanned_ids,'bcquantity': 1,'is_new_pick':False,'note':''}}
                                    else:
                                            return {'value': {'default_code': False, 'line_ids':line_scanned_ids,'bcquantity': 1,'is_new_pick':False,'note':''}}
                                #### Velodyne code ends here
            else:
                #change the image if the prevous one is scanned
                barcode_product = barcode_image =False
                stock_move_obj=self.pool.get('stock.move')
                if type == 'out':
                    if default_code != False:
                        if picking:
                            stock_move_ids = line_ids[0][2]
                            stock_move_ids.sort()
                            obj_stock_moves = stock_move_obj.browse(cr, uid, stock_move_ids)
                            stock_lot_id= prodlot_obj.search(cr,uid,[('name', '=', default_code)])
#                            if not stock_lot_id:
#                                return {'value': {'default_code': False, 'note':'Invalid barcode'}}
                            if range_scan:
                                if new_product_id and start_range:
                                    validate_scan_vals = {
                                        'default_code' : default_code,
                                        'new_product_id' : new_product_id,
                                        'start_range' : start_range,
                                        'range_scan' : range_scan,
                                        'line_ids' : obj_stock_moves,
                                    }
                                    return_vals = self.validate_scan(cr, uid, ids, validate_scan_vals)
                                    return_vals['line_ids'] = line_scanned_ids
                                    return {'value': return_vals}
                                else:
                                    return True
                            total_scanned_moves = 0
                            for each_move in obj_stock_moves:
                                if each_move.status == 'done':
                                    total_scanned_moves += 1
                            for each_move in obj_stock_moves:
                                current_stock_move_id = each_move.id
                                received_qty = 0
                                if each_move.received_qty:
                                    received_qty = each_move.received_qty
                                if not new_product_id:
                                    raise osv.except_osv(_('Product ERROR !'), _('Please select a product'))
                                scan_product_id = new_product_id
                                if each_move.product_id.id != scan_product_id:
                                    continue
                                if each_move.product_qty == each_move.received_qty:
                                    return {'value': {'default_code': False, 'bcquantity': 1,'is_new_pick':False,'note':'Product Already scanned'}}
                                if stock_lot_id:
                                    current_stock_lot_obj = prodlot_obj.browse(cr, uid, stock_lot_id[0])
                                    if current_stock_lot_obj.serial_used:
                                        return {'value': {'default_code': False, 'bcquantity': 1,'line_ids':scanning_line,'is_new_pick':False,'note':'This Serial Number is Already used'}}
                                    else:
                                        if picking_obj1:
                                            for each_move_line in picking_obj1.move_lines:
                                                if each_move_line.sale_line_id and each_move_line.sale_line_id.order_id:
                                                    line_scanned_ids.append(each_move_line.id)
                                        cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (current_stock_move_id, stock_lot_id[0]))
                                        cr.commit()
                                        received_qty = received_qty + 1
                                        status = stock_move_obj.write(cr, uid, each_move.id,{'received_qty': received_qty})
                                        search_child_mv_ids = stock_move_obj.search(cr,uid,[('parent_stock_mv_id','=',each_move.id)])
                                        if search_child_mv_ids:
                                            status = stock_move_obj.write(cr, uid, search_child_mv_ids,{'received_qty': received_qty})
                                        prodlot_status = prodlot_obj.write(cr, uid, stock_lot_id[0], {'serial_used':True})
                                        if each_move.product_qty == received_qty:
                                            stock_move_obj.write(cr, uid, each_move.id,{'status': 'done'})
                                            if search_child_mv_ids:
                                                status = stock_move_obj.write(cr, uid, search_child_mv_ids,{'status': 'done'})
                                            total_scanned_moves += 1
                                            if total_scanned_moves == len(obj_stock_moves):
                                                return {'value': {'bcquantity': 1,'is_new_pick':False,'default_code': False,'note':'Scan Next Shipment!'},'type': 'ir.actions.act_window_close'}
                                            else:
                                                return {'value': {'default_code': False, 'bcquantity': 1,'is_new_pick':False,'note':''}}
                                        else:
                                            return {'value': {'default_code': False, 'bcquantity': 1,'is_new_pick':False,'note':''}}
                                else:
                                    received_qty = received_qty + 1
                                    status = stock_move_obj.write(cr, uid, each_move.id,{'received_qty': received_qty})
                                    prodlot_id = prodlot_obj.create(cr, uid, {'product_id': scan_product_id,'name': default_code})
                                    cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (current_stock_move_id, prodlot_id))
                                    cr.commit()
                                line_scanned_ids = []
                                if picking_obj1:
                                    for each_move_line in picking_obj1.move_lines:
                                        if each_move_line.sale_line_id and each_move_line.sale_line_id.order_id:
                                            line_scanned_ids.append(each_move_line.id)
                                if each_move.product_qty == received_qty:
                                    stock_move_obj.write(cr, uid, each_move.id,{'status': 'done'})
                                    total_scanned_moves += 1
                                    if total_scanned_moves == len(obj_stock_moves):
                                        return {'value': {'bcquantity': 1,'line_ids':[],'is_new_pick':False,'default_code': False,'note':'Scan Next Shipment!'},'type': 'ir.actions.act_window_close'}
                                    else:
                                        return {'value': {'default_code': False, 'line_ids':line_scanned_ids,'bcquantity': 1,'is_new_pick':False,'note':''}}
                                else:
                                        return {'value': {'default_code': False, 'line_ids':line_scanned_ids,'bcquantity': 1,'is_new_pick':False,'note':''}}

        return {'value':{}}                              
    def validate_autocomp_scan(self, cr, uid, picking_id, context):
        #this is run so that the availability of stock is checked
        shippingres_obj = self.pool.get('shipping.response')
        picking_obj = self.pool.get('stock.picking')
        error_required = False
        if picking_id:
            try:
                picking_obj.action_assign(cr, uid, [picking_id])
            except:
                pass
                #try except to avoid any kind of message
        context['active_model']='ir.ui.menu'
        context['active_ids']= [picking_id]
        context['active_id']=picking_id
        status = picking_obj.browse(cr,uid,picking_id).state
        if status == 'draft':
#             draft_validate = picking_obj.draft_validate(cr, uid, [picking_id], context=context) odoo8 changes

            draft_validate = picking_obj.action_confirm(cr, uid, [pick.id], context=context)
        function = picking_obj.do_enter_transfer_details(cr, uid, [pick.id], context=context)
                
        res_id = function.get('res_id')
        if res_id:
            do_partial = self.pool.get("stock.transfer_details").do_detailed_transfer(cr,uid,[res_id],context=context)
        return {
                'name':_('Make Scanning'),
                'view_mode': 'form',
                'view_id': False,
                #'views': [(resource_id,'form')],
                'view_type': 'form',
                'res_id' : [], # id of the object to which to redirected
                'res_model': 'picking.scanning', # object name
                'type': 'ir.actions.act_window',
                'target': 'new', # if you want to open the form in new tab
                }

    def validate_scan_backorder(self, cr, uid, ids, context=None):
        picking_list = []
        partial = self.browse(cr, uid, ids[0], context=context)
        picking = partial.picking_ids
        status = partial.skip_barcode
        line_ids =  partial.line_ids
        picking_ids = []
        if status == False:
            for line in line_ids:
                picking_ids.append(line.picking_id.id)
                received = line.received_qty
                if received > 0:
                    pick = line.picking_id
                    if pick not in picking_list:
                        picking_list.append(pick)
        else:
            for line in line_ids:
                pick = line.picking_id
                picking_ids.append(line.picking_id.id)
                if pick not in picking_list:
                    picking_list.append(pick)
        unc_picking_ids = list(set(picking_ids))
        #this is run so that the availability of stock is checked
        picking_obj = self.pool.get('stock.picking')
        if len(unc_picking_ids):
                try:
                    picking_obj.action_assign(cr, uid, unc_picking_ids)
                except:
                    pass
                #try except to avoid any kind of message
        for pick in picking_list:
           ans =  self.pool.get('stock.picking').write(cr,uid,[pick.id],{'skip_barcode':status})
           context['active_model']='ir.ui.menu'
           context['active_ids']= [pick.id]
           context['active_id']=pick.id
           status = self.pool.get('stock.picking').browse(cr,uid,pick.id).state
           if status == 'draft':
#               draft_validate = self.pool.get('stock.picking').draft_validate(cr, uid, [pick.id], context=context)
               draft_validate = picking_obj.action_confirm(cr, uid, [pick.id], context=context)##cox gen2 changed function to action_confirm from draft_validate
           function = picking_obj.do_enter_transfer_details(cr, uid, [pick.id], context=context)
           #self.pool.get('stock.picking').write(cr,uid,[pick.id],{'scan_uid':uid,'scan_date':time.strftime('%Y-%m-%d %H:%M:%S')})
           res_id = function['res_id']

            ##cox gen2 odoo8 class stock_partial_picking has been changed
#           res_id=self.pool.get("stock.partial.picking").create(cr, uid, {}, context=context)
#           do_partial = self.pool.get("stock.partial.picking").do_partial(cr,uid,[res_id],context=context)
#           res_id=self.pool.get("stock.transfer_details").create(cr, uid, {}, context=context)
           do_partial = self.pool.get("stock.transfer_details").do_detailed_transfer(cr,uid,[res_id],context=context)
        return {'type': 'ir.actions.act_window_close'}


    def validate_scan(self, cr, uid, ids, context=None):
        # Velodyne code for Incoming shipment scan in Lots
        prodlot_obj = self.pool.get('stock.production.lot')
        stock_move_obj = self.pool.get('stock.move')
        scan_product_id = context.get('new_product_id')
        start_range = context.get('start_range')
        initial_barcode = context.get('default_code')
        obj_stock_moves = context.get('line_ids')
        if initial_barcode and start_range:
            converted_barcode = int(initial_barcode)
            total_scanned_moves = 0
            barcode_list = []
            for each_move in obj_stock_moves:
                if each_move.status == 'done':
                    total_scanned_moves += 1
            for each_move in obj_stock_moves:
                picking_type = each_move.picking_id.picking_type_id.code ## cox gen2 changed type field to .picking_type_id.code
                stock_move_id = each_move.id
                if each_move.product_id.id != scan_product_id:
                    continue
                testing_initial_barcode = converted_barcode
                for i in range(0, start_range):
                    barcode_list.append(str(testing_initial_barcode))
                    testing_initial_barcode +=1
                if picking_type == 'incoming': ##cox gen2 changed 'in' to 'incoming'
                    cr.execute('SELECT id,name from stock_production_lot where name IN %s and product_id =%s',(tuple(barcode_list),scan_product_id))
                else:
                    cr.execute('SELECT id,name from stock_production_lot where name IN %s and product_id =%s and serial_used=True',(tuple(barcode_list),scan_product_id))
                serial_number_records = cr.fetchall()
                # Velodyne code for serial numbers been already used
                if serial_number_records:
                    raise osv.except_osv(_('Duplicate Serial Number !'),_('Serial numbers belonging to this range has been already assigned'))
                scanned_qty = each_move.received_qty
                product_qty = each_move.product_qty
                remaining_scanned_qty = product_qty - scanned_qty
                if start_range > remaining_scanned_qty:
                    raise osv.except_osv(_('Range ERROR !'),_('The quantity to be scanned is less than the range selected'))
                stock_lot_ids_out = []
                for i in range(0, start_range):
                    scanned_qty += 1
                    if picking_type == 'incoming': ##cox gen2 changed 'in' to 'incoming'
                        prodlot_id = prodlot_obj.create(cr, uid, {'product_id': scan_product_id,'name': converted_barcode})
                        stock_lot_ids_out.append(prodlot_id)
                    else:
                        stock_lot_id = prodlot_obj.search(cr, uid, [('name','=',converted_barcode)])
                        if not stock_lot_id:
                            prodlot_id = prodlot_obj.create(cr, uid, {'product_id': scan_product_id,'name': converted_barcode})
                            stock_lot_ids_out.append(prodlot_id)
                        else:
                            stock_lot_ids_out.append(stock_lot_id[0])
                    converted_barcode += 1
                value_str = ''
                if picking_type == 'incoming': ##cox gen2 changed 'in' to 'incoming'
                    for each_stock_lot_id in stock_lot_ids_out:
                        value_str += "(%s,%s),"%(stock_move_id,each_stock_lot_id)
                    value_str = value_str[:-1]
                    cr.execute("insert into stock_move_lot(stock_move_id,production_lot) values %s"%(value_str))
                else:
                    for each_stock_lot_id in stock_lot_ids_out:
                        value_str += "(%s,%s),"%(stock_move_id,each_stock_lot_id)
                    value_str = value_str[:-1]
                    cr.execute("insert into stock_move_lot (stock_move_id,production_lot) values %s"%(value_str))
                    prodlot_id = prodlot_obj.write(cr, uid, stock_lot_ids_out,{'serial_used': True})
                cr.commit()
                stock_lot_ids_out = []
                if scanned_qty == product_qty:
                    status = stock_move_obj.write(cr, uid, stock_move_id,{'received_qty': scanned_qty, 'status' : 'done'})
                    total_scanned_moves +=1

                    if total_scanned_moves == len(obj_stock_moves):
                        return_vals = {'line_ids':[],'is_new_pick':False,'default_code': False,'start_range': 0,'new_product_id': False, 'note':'Scan Next Shipment!','new_product_id': False}
                        return return_vals
                    else:
                        return_vals = {'is_new_pick':False,'default_code': False,'start_range': 0,'note':'','new_product_id': False}
                        return return_vals
                else:
                    status = stock_move_obj.write(cr, uid, stock_move_id, {'received_qty' : scanned_qty})
                    return_vals = {'default_code': False,'start_range': 0,'note':'','new_product_id': scan_product_id}
                    return return_vals
        else:
            raise osv.except_osv(_('Serial Number, Range ERROR !'),_('Please enter a Proper serial number and Range'))
    #onchange product give default package qty scanning

    def onchange_new_product(self, cr, uid, ids, new_product_id=False,line_ids= False,context=None):
        if line_ids:
            list_ids = line_ids[0][2]
            packaging = self.pool.get('product.packaging')
            qty = 0
            if new_product_id:
                product_tmpl_id = self.pool.get('product.product').browse(cr,uid,new_product_id).product_tmpl_id
                packages = packaging.search(cr,uid,[('product_tmpl_id','=',product_tmpl_id)])## cox gen2 odoo8 changed product_id field to product_tmpl_id in search condition
                if len(packages):
                    for pack in packages:
                        qty = packaging.browse(cr,uid,pack).qty
            return{'value': {'default_code': False, 'bcquantity': 1,'line_ids':list_ids,'new_qty':qty}}

    #if packaging is new this function will get call.
    def onchange_continue_scan(self, cr, uid, ids,new_barcode=False,bcquantity=False,picking_ids=False,line_ids=False,new_product_id=False,new_qty=False, context=None):
        
        #partial = self.browse(cr, uid, ids[0], context=context)
        default_code = new_barcode
        bcquantity = bcquantity
        picking_ids =picking_ids
        line_ids = line_ids
        product = new_product_id
        product_tmpl_id = False
        if product:
            product_tmpl_id = self.pool.get('product.product').browse(cr,uid,product).product_tmpl_id.id
            new_qty = new_qty
            ul = self.pool.get('product.ul').search(cr,uid,[('name','=','Box')])
            if not len(ul):
                ul = []
                pul = self.pool.get('product.ul').create(cr,uid,{'name':'Box','type':'box'})
                ul.append(pul)
            vals = {
                'barcode':default_code,
                'product_tmpl_id':product_tmpl_id,
                'qty':new_qty,
    #            'is_default':True,
                'ul':ul[0]
            }
            pack = self.pool.get('product.packaging').create(cr,uid,vals)
        res = self.onchange_defaultcode(cr, uid, ids, default_code, picking_ids,line_ids,reference_no=False,context=None)
        
        res_val = res['value']
        res_val['continue_scan'] = False
        res_val['new_product_id']= False
        res_val['new_qty']= 0
        res['value'] = res_val
        return res
picking_scanning()

class product_packaging(osv.osv):
    _inherit = "product.packaging"
    _rec_name = 'ean'
    _columns = {
        'ean' : fields.char('Bar Code', size=64,
            help="The EAN code of the package unit."),
        'barcode' : fields.char('Bar Code', size=18,
            help="The Barcode of the package unit."),
    }
product_packaging()


class serial_no_ref(osv.osv_memory):
    _name='serial.no.ref'
    _columns={
        'so_ref':fields.char('SO Reference',size=256),
        'purchase_date':fields.date('Purchase Date'),
        'move_ref':fields.char('Move Reference',size=256),
        'ro_ref':fields.char('RO Reference',size=256),
        'cust_name':fields.char('Customer Name',size=256),
        'cust_ref':fields.char('Customer Reference',size=256),
        }
	#####function for serial no reference
    def default_get(self,cr,uid,fields,context=None):
        stock_move_obj=self.pool.get('stock.move')
        res={}
        ro_ref,so_ref,move_ref,purchase_date=[],'','',''
        if context is None:
            context = {}
        active_id=context.get('active_id')
        if active_id:
            cr.execute("select stock_move_id from stock_move_lot where production_lot=%s"%(active_id))
            stock_moves_ids =filter(None, map(lambda x:x[0], cr.fetchall()))
            for each_move in stock_move_obj.browse(cr, uid, stock_moves_ids):
		if each_move.picking_id:
                    move_ref=each_move.picking_id.name
                    cust_name=each_move.picking_id.partner_id.name
                    cust_ref=each_move.picking_id.partner_id.ref
                if each_move.picking_id and each_move.picking_id.return_id:
                    ro_ref.append(each_move.picking_id.return_id.name)
                elif each_move.picking_id and each_move.picking_id.sale_id:
                    so_ref = each_move.picking_id.sale_id.name
                    purchase_date = each_move.picking_id.sale_id.date_order
            res.update({'so_ref':so_ref,'ro_ref':ro_ref,'purchase_date' : purchase_date,'move_ref':move_ref,'cust_name':cust_name,'cust_ref':cust_ref})
            return res

serial_no_ref()
