# -*- coding: utf-8 -*-
from openerp.tools.translate import _
from openerp.osv import osv, fields

class picking_scanning(osv.osv_memory):
    _inherit = "picking.scanning"
    _description = 'Make Scanning'
    
    def get_product_ids(self,cr,uid,context={}):
        product_ids,move_prod_id,picking_ids= [],[],[]
        if context is None:
            context={}
        picking_obj = self.pool.get('stock.picking')
        if context.get('active_model',''):
           if context['active_model'] in ('stock.picking'):
               picking_ids = context.get('active_ids', [])
           elif context['active_model']=='sale.order':
               pick_id=picking_obj.search(cr,uid,[('sale_id','=',context['active_ids']),('state','not in',('done','cancel'))])
               if pick_id:
                    picking_ids = pick_id
           for picking_id_obj in picking_obj.browse(cr, uid, picking_ids):
#               picking_id_obj = self.pool.get('stock.picking').browse(cr, uid, picking_id)
	       if picking_id_obj.state == 'done' or picking_id_obj.shipping_process == 'wait':
                    continue	
               if context.get('trigger') == 'retail_store':
		   procurement_ids=[]
                   if context.get('procurement_id'):
                        #procurement_ids = context.get('procurement_id'
			procurement_id = context.get('procurement_id').replace('[','').replace(']','')
			if ',' in procurement_id:
        			procurement = procurement_id.split(',')
        			print"procuementprocuement",procurement
        			procurement_ids = procurement
			else:
        			procurement_ids = [procurement_id]
			print"idddddddd procuement",procurement_ids
                        for each in procurement_ids:
#                            print"procurement_id",type(procurement_id),procurement_id[0]
                            cr.execute("select product_id from stock_move where state not in ('done','cancel') and procurement_id =%s"%(each))        ##cox gen2
                            product_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if product_id and not product_id in product_ids:
                                product_ids.append(product_id[0])
#                   if context.get('so_line_ids'):
#                        so_line_id = [context.get('so_line_ids')]
#                        if so_line_id:
#                            for each_so in so_line_id:
##                            cr.execute("select product_id from stock_move where sale_line_id in %s and state not in ('done','cancel')", (tuple(so_line_id),))
#                                cr.execute("select product_id from stock_move where  state not in ('done','cancel') and procurement_id in (select id from procurement_order where sale_line_id in %s)", (tuple(so_line_id),)) ##cox gen2
#                                product_ids.append(filter(None, map(lambda x:x[0], cr.fetchall())))
               else:
                   for moveline in picking_id_obj.move_lines:
#                       if moveline.sale_line_id:
 #                          if moveline.sale_line_id and moveline.state != 'cancel' and (not moveline.parent_stock_mv_id):
			   if moveline.state != 'cancel' and (not moveline.parent_stock_mv_id):	
                                product_ids.append(moveline.product_id.id)
           if product_ids:
               print"product_idssssss",product_ids
               product_obj = self.pool.get('product.product')
               [move_prod_id.append((each_prod.id,each_prod.name))for each_prod in product_obj.browse(cr,uid,product_ids)]
        return list(set(move_prod_id))
    
    #Function is inherited to show only main product in the Packing Lines
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
        picking_ids,pick,scanning_line = [],[],[]
        if context is None:
            context = {}
        print"context",context
        picking_obj = self.pool.get('stock.picking')
        if context.get('active_model', False):
            if context['active_model'] in ('stock.picking'):
                picking_ids = context.get('active_ids', [])
            elif context['active_model'] == 'sale.order':
                name = self.pool.get('sale.order').browse(cr,uid,context['active_ids']).name
                pick_id=picking_obj.search(cr,uid,[('origin','=',name),('state','not in',('done','cancel'))])
                if pick_id:
                    picking_ids = pick_id
        res = super(picking_scanning, self).default_get(cr, uid, fields, context=context)
        if picking_ids:
            print"picking_idspicking_ids",picking_ids
            res.update({'stock_picking_id':picking_ids[0]})
        for picking in picking_obj.browse(cr, uid, picking_ids, context=context):
            if picking.state == 'done' or picking.shipping_process == 'wait':
                continue
            stockids = picking.move_lines
            for stock in stockids:
                if stock.state == 'done':
                    continue
                if not context.get('trigger'):
    #                if (stock.sale_line_id) and (not stock.parent_stock_mv_id) and (stock.state != 'cancel'):
		    if (not stock.parent_stock_mv_id) and (stock.state != 'cancel'):	
                        scanning_line.append(stock.id)
            pick.append(picking.id)
            print"pick",pick
        if 'bcquantity' in fields:
            res.update({'bcquantity': 1})
        res.update({'picking_ids':pick})
        res.update({'line_ids':scanning_line})
        res.update({'start_range':1})
        ##Code to view selected Picking lines for Retail Store
        move_ids=[]
        if context.get('trigger'):
            ######cox gen2
#             if context.get('so_line_ids'):
#                 so_line_id = [context.get('so_line_ids')]
#                 
#                 for each_so in so_line_id:
# #                   cr.execute("select id from stock_move where sale_line_id in %s and state not in ('done','cancel')", (tuple(so_line_id),))
#                     cr.execute("select id from stock_move where state not in ('done','cancel') and procurement_id in (select id from procurement_order where sale_line_id = '%s')"%(int(each_so)))        ##cox gen2
#                     move_ids.append(filter(None, map(lambda x:x[0], cr.fetchall())))
#                print"move_ids",move_ids
            ########end
	    procurement_ids=[]
            if context.get('procurement_id'):
                print"context.get('procurement_id')",context.get('procurement_id')
#                if not isinstance(context.get('procurement_id'), list):
#                    print"listttttttttttt"
#                    procurement_id = [context.get('procurement_id')]
#                else:
#                    procurement_id = procurement_id
                procurements = context.get('procurement_id')
		print"context.get('procurement_id').replace('[','').replace(']','')",context.get('procurement_id').replace('[','').replace(']','')
		procurement_id = context.get('procurement_id').replace('[','').replace(']','')
		if ',' in procurement_id:
			procurement = procurement_id.split(',')
			print"procuementprocuement",procurement
			procurement_ids = procurement
		else:
			procurement_ids = [procurement_id]
		print"idddddddd procuement",procurement_ids
                for each in procurement_ids:
                    print"each",each
                    cr.execute("select id from stock_move where state not in ('done','cancel') and procurement_id =%s"%(each))        ##cox gen2
                    move_id = filter(None, map(lambda x:x[0], cr.fetchall()))
                    print"move_id",move_id
                    if move_id and not move_id in move_ids:
                        move_ids.append(move_id[0])
                print"move_ids",move_ids
                if move_ids:
                    res.update({'line_ids':move_ids})
                res.update({'active_model':'sale.order'})
        if context.get('pick_up_location',''):
            res.update({'pick_up_location':context.get('pick_up_location')})
        if context.get('src_location',''):
            res.update({'src_location':context.get('src_location')})
        return res
    
#    ##Funcition is inherited to show only main product while scanning product
#    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
#                       context=None, toolbar=False, submenu=False):
#       """
#        Changes the view dynamically
#        @param self: The object pointer.
#        @param cr: A database cursor
#        @param uid: ID of the user currently logged in
#        @param context: A standard dictionary
#        @return: New arch of view.
#       """
#       product_ids, picking_ids= [],[]
#       if context is None:
#           context={}
#       picking_obj = self.pool.get('stock.picking')
#       if context.get('active_model',''):
#           if context['active_model'] in ('stock.picking.out','stock.picking'):
#               picking_ids = context.get('active_ids', [])
#           elif context['active_model']=='sale.order':
#               pick_id=picking_obj.search(cr,uid,[('sale_id','=',context['active_ids'])])
#               if pick_id:
#                    picking_ids = pick_id
#           for picking_id in picking_ids:
#               picking_id_obj = self.pool.get('stock.picking').browse(cr, uid, picking_id)
#               if context.get('trigger') == 'retail_store':
#                   if context.get('so_line_ids'):
#                        so_line_id = context.get('so_line_ids')
#                        if so_line_id:
#                            cr.execute("select product_id from stock_move where sale_line_id in %s", (tuple(so_line_id),))
#                            product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#               else:
#                   for moveline in picking_id_obj.move_lines:
#                       if moveline.sale_line_id:
#                           if moveline.sale_line_id and moveline.state != 'cancel' and (not moveline.parent_stock_mv_id):
#                                product_ids.append(moveline.product_id.id)
#       res = super(picking_scanning, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
#       if res.get('fields').get('new_product_id'):
#            res['fields']['new_product_id']['domain'] = [('id', 'in', product_ids)]
#            res['fields']['new_product_id']['widget'] = "selection"
#       return res
    
    def validate_scan_backorder(self, cr, uid, ids, context=None):
        if (context.get('trigger') == 'retail_store' and context.get('sale_id')) or context.get('return_id',False):
            picking_list,picking_ids = [],[]
            move_obj = self.pool.get('stock.move')
            partial = self.browse(cr, uid, ids[0], context=context)
            print"partial",partial
            picking = partial.picking_ids
            print"picking",picking
            status = partial.skip_barcode
            line_ids =  partial.line_ids
            print"picking_ids",picking_ids
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
               ##Extra Line of code for Instore Pickup Starts here
                if partial.pick_up_location and partial.pick_up_location != partial.src_location:
                   search_move_ids = move_obj.search(cr, uid, [('picking_id', '=', pick.id)])
                   if search_move_ids:
                       move_obj.write(cr,uid,search_move_ids,{'location_id':partial.pick_up_location.id})
                #################
                ans =  picking_obj.write(cr,uid,[pick.id],{'skip_barcode':status})
                context['active_model']='ir.ui.menu'
                context['active_ids']= [pick.id]
                context['active_id']=pick.id
                status = picking_obj.browse(cr,uid,pick.id).state
                if status == 'draft':
#                   draft_validate = picking_obj.draft_validate(cr, uid, [pick.id], context=context)
                   draft_validate = picking_obj.action_confirm(cr, uid, [pick.id], context=context)
                context['action_process_original'] = True ##Extra Line of Code
#                function = picking_obj.action_process(cr, uid, [pick.id], context=context)
                function = picking_obj.do_enter_transfer_details(cr, uid, [pick.id], context=context)
                print"functionnnnnnnnnnnnnnn"
                #self.pool.get('stock.picking').write(cr,uid,[pick.id],{'scan_uid':uid,'scan_date':time.strftime('%Y-%m-%d %H:%M:%S')})
                res_id = function.get('res_id')
                if res_id:
#                    cox gen2
                    do_partial = self.pool.get("stock.transfer_details").do_detailed_transfer(cr,uid,[res_id],context=context)
#                   
            if context.get('trigger') == 'retail_store' and context.get('sale_id'):
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': context.get('sale_id'),
                    'res_model': 'sale.order',
                    'type': 'ir.actions.act_window'
            }
            elif context.get('return_id',False):
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': context.get('return_id'),
                    'res_model': 'return.order',
                    'type': 'ir.actions.act_window'
            }
        else:
            print"elssssssseeeeeeeee",ids
            active_ids =context.get('active_ids',False)
            context.update({'active_id':active_ids[0], 'active_ids':active_ids,'active_model':'stock.picking'})
            print"contextshipping processssssssssssssss",context
            pre_shipping_process_id = self.pool.get("pre.shipping.process").create(cr, uid, {}, context=context)
            return {
                'name':_("Shipping Process"),
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': pre_shipping_process_id,
                'res_model': 'pre.shipping.process',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,
        }
#        return {'type': 'ir.actions.act_window_close'}
    
    def onchange_defaultcode(self, cr, uid, ids, default_code=False,picking_ids=False ,line_ids=False, new_product_id=False,start_range=False, range_scan=False,reference_no=False,carrier_track_done=False,note=False,check_note=False,context=None):
        #bar code scanning
        #search the product in stock move
        #search packaging and find out product and its quantity. Update stock move as per packaging details
        ##line_ids
        #search delivery orders and populate the products from them
        prodlot_obj = self.pool.get('stock.production.lot')
        tr_barcode_obj = self.pool.get('tr.barcode')
        if context is None:
            context={}
        picking_obj = self.pool.get('stock.picking')
        stock_move_obj = self.pool.get('stock.move')
        search_picking_ids = picking_obj.search(cr, uid, [('name', '=', default_code)])
        type = 'in'
        if search_picking_ids:
            type = picking_obj.browse(cr, uid, search_picking_ids[0]).type
        calltracking,picking_obj1,line_scanned_ids = False,False,[]
# Updatation for wizard SCANNED_QTY
        print"picking_ids",picking_ids
        if picking_ids and picking_ids[0][2]:
            picking_obj1 = picking_obj.browse(cr, uid, picking_ids[0][2][0])
        if not line_ids:
            if picking_obj1:
                for each_move_line in picking_obj1.move_lines:
                    if each_move_line.sale_line_id.order_id:
                        line_scanned_ids.append(each_move_line.id)
        else:
            line_scanned_ids = line_ids[0][2]
        if reference_no:
            picking = picking_obj.search(cr, uid, [('name', '=', reference_no)])
            if len(picking):
                for pick in picking_obj.browse(cr, uid, picking, context=context):
                    if pick.carrier_id and pick.carrier_id.is_scan_tracking == True and pick.carrier_tracking_ref == False:
                        calltracking = True
        search_prod_barcode = prodlot_obj.search(cr, uid, [('name','=',default_code)])
        search_tr_barcode_ids = tr_barcode_obj.search(cr, uid, [('code','=',default_code)])
        
        if len(search_picking_ids) != 0 and len(search_prod_barcode) == 0:
            reference_no = default_code
            scanning_line,stockids = [],[]
            product_pacakging = self.pool.get('product.packaging')
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
#                pick_id = picking_out.id
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
                    package_ids = product_pacakging.search(cr, uid, [('product_id', '=', stock.product_id.id)])
                    if len(package_ids):
                        return_move_lines.update({'br_product_id': stock.product_id.id})
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
            return {'value': {'carrier_track_done': True,'default_code': False,'check_note': carrier, 'note':tracking_note}}
        elif len(search_prod_barcode) == 0 and reference_no == 0 and type =='out':
            return {'value': {'default_code': False,'note':'Please enter the order reference no'}}
        else:
            product_ids,scanning_line,product_array,purchase_status = [],[],[],False
            stock_mv_obj = self.pool.get('stock.move')
            for line in line_ids:
                for line in line[2]:
                    if line != 0:
                        product = stock_mv_obj.browse(cr,uid,line).product_id.id
                        if product not in product_array:
                            product_array.append(product)
            picking = picking_ids[0][2]
            test_serial = prodlot_obj.search(cr,uid,[('name','=',default_code)])
            for line in line_ids:
                line = line[2]
                for line in line:
                    scanning_line.append(line)
            type = False
            if picking:
                for pick in picking:
                    shipping_type = self.pool.get('stock.picking').browse(cr,uid,pick).picking_type_id.code
                    print"shipping_type",shipping_type
                    if shipping_type == 'incoming':
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
                            purchase = self.pool.get('stock.picking').browse(cr,uid,pick).purchase_id
                            if purchase:
                                purchase_status = True
                            else:
                                purchase_status = False
#                                dest_id = self.pool.get('stock.picking').browse(cr,uid,picking[0]).dest_id.id
#                                move_lines = self.pool.get('stock.picking').browse(cr,uid,picking[0]).move_lines
                        if purchase_status != False:
                            if default_code != False:
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
                                        total_scanned_moves += 1
                                        if total_scanned_moves == len(obj_stock_moves):
                                            return {'value': {'bcquantity': 1,'line_ids':line_scanned_ids,'is_new_pick':False,'note':'Scanning is Done!'},'type': 'ir.actions.act_window_close'}
                                        else:
                                            return {'value': {'line_ids':line_scanned_ids,'bcquantity': 1,'is_new_pick':False,'note':''}}
                                    else:
                                            return {'value': {'line_ids':line_scanned_ids,'bcquantity': 1,'is_new_pick':False,'note':''}}
            else:
                #change the image if the prevous one is scanned
#                barcode_product = barcode_image =False
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
#                                if each_move.status != 'done':
                                if each_move.product_qty == each_move.received_qty:
                                    return {'value': {'bcquantity': 1,'is_new_pick':False,'note':'Product Already scanned'}}
                                if stock_lot_id:
                                    current_stock_lot_obj = prodlot_obj.browse(cr, uid, stock_lot_id[0])
                                    if current_stock_lot_obj.serial_used:
                                        return {'value': {'bcquantity': 1,'line_ids':scanning_line,'is_new_pick':False,'note':'This Serial Number is Already used'}}
                                    else:
                                        if picking_obj1:
                                            for each_move_line in picking_obj1.move_lines:
                                                if each_move_line.procurement_id.sale_line_id and each_move_line.procurement_id.sale_line_id.order_id:
                                                    line_scanned_ids.append(each_move_line.id)
                                        cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (current_stock_move_id, stock_lot_id[0]))
                                        cr.commit()
                                        received_qty = received_qty + 1
                                        status = stock_move_obj.write(cr, uid, each_move.id,{'received_qty': received_qty,'restrict_lot_id':current_stock_lot_obj.id})
                                        search_child_mv_ids = stock_move_obj.search(cr,uid,[('parent_stock_mv_id','=',each_move.id)])
                                        if search_child_mv_ids:
                                            status = stock_move_obj.write(cr, uid, search_child_mv_ids,{'received_qty': received_qty})
                                        prodlot_status = prodlot_obj.write(cr, uid, stock_lot_id[0], {'serial_used':True})
                                        if each_move.product_qty == received_qty:
                                            stock_move_obj.write(cr, uid, each_move.id,{'status': 'done'})
                                            stock_move_obj.write(cr, uid, search_child_mv_ids,{'status': 'done'})
                                            total_scanned_moves += 1
                                            if total_scanned_moves == len(obj_stock_moves):
                                                return {'value': {'bcquantity': 1,'line_ids':scanning_line,'is_new_pick':False,'note':'Scan Next Shipment!'},'type': 'ir.actions.act_window_close'}
                                            else:
                                                return {'value': {'bcquantity': 1,'is_new_pick':False,'note':''}}
                                        else:
                                            return {'value': {'bcquantity': 1,'is_new_pick':False,'note':''}}
                                else:
                                    received_qty = received_qty + 1
#                                    stock_move_obj.write(cr, uid, each_move.id,{'received_qty': received_qty})
                                    
                                    search_child_mv_ids = stock_move_obj.search(cr,uid,[('parent_stock_mv_id','=',each_move.id)])
                                    if search_child_mv_ids:
                                        status = stock_move_obj.write(cr, uid, search_child_mv_ids,{'received_qty': received_qty})
                                    stock_lot_id = prodlot_obj.create(cr, uid, {'product_id': scan_product_id,'name': default_code,'serial_used':True})
                                    cr.execute("update stock_move set received_qty ='%s',restrict_lot_id = '%s'  where id='%s' "%(received_qty,stock_lot_id,current_stock_move_id))
                                    cr.commit()
                                    cr.execute('insert into stock_move_lot (stock_move_id,production_lot) values (%s,%s)', (current_stock_move_id, stock_lot_id))
                                    cr.commit()
                                line_scanned_ids = []
                                if not line_ids:
                                    if picking_obj1:
                                        for each_move_line in picking_obj1.move_lines:
                                            if each_move_line.sale_line_id and each_move_line.sale_line_id.order_id:
                                                line_scanned_ids.append(each_move_line.id)
                                else:
                                    line_scanned_ids = line_ids[0][2]

                                if each_move.product_qty == received_qty:
                                    stock_move_obj.write(cr, uid, each_move.id,{'status': 'done','restrict_lot_id':stock_lot_id})
                                    search_child_mv_ids = stock_move_obj.search(cr,uid,[('parent_stock_mv_id','=',each_move.id)])
                                    if search_child_mv_ids:
                                        stock_move_obj.write(cr, uid, search_child_mv_ids,{'status': 'done'})
                                    total_scanned_moves += 1
                                    if total_scanned_moves == len(obj_stock_moves):
                                        return {'value': {'bcquantity': 1,'line_ids':line_scanned_ids,'is_new_pick':False,'note':'Scanning is Done'}}
                                    else:
                                        return {'value': {'line_ids':line_scanned_ids,'bcquantity': 1,'is_new_pick':False,'note':'', 'stock_picking_id':picking_obj1.id,'default_code':False,'picking_ids':picking_ids}}
                                else:
                                        return {'value': {'line_ids':line_scanned_ids, 'bcquantity': 1, 'note':'','stock_picking_id':picking_obj1.id,'default_code':False,'picking_ids':picking_ids}}
    _columns = {
        'active_model' : fields.char('Active Model',size=64),
        'src_location':fields.many2one('stock.location','Source Location'),
        'pick_up_location':fields.many2one('stock.location','Pick Up Location'),
        'new_product_id': fields.selection(get_product_ids,'Product')
        }
picking_scanning()
