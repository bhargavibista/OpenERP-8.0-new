from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools import float_compare 


class stock_production_lot(osv.osv):
    '''
    Inherit this class to create reference fields many2one to manufacturing order
    '''
    _inherit = "stock.production.lot"
    _columns={
       'serial_used_received':fields.boolean('Serail Used For Receiving'), ###scanning while receving product
       'qty_avail': fields.integer('Quantity Available', help="Help !!"),
       'production_id': fields.many2one('mrp.production', 'Manufacturing Order',
            ondelete='cascade'),
       'location_id':fields.many2one('stock.location', 'Source Location',select=True, help="Sets a location for this serial number"), ###changes for assigning serial number according to location
       'move_prod_lot_ids': fields.many2many('stock.move','stock_move_lot', 'production_lot','stock_move_id','Serial numbers',readonly=True),
       'used':fields.boolean('Used'),
       'order_created':fields.boolean('Order Created'),
       'created_during_activation':fields.boolean('Activation Create'),
       'scanning_id':fields.many2one('manual.scanning','Scanning'),
    }

    _sql_constraints = [
        ('nameunique', 'unique(name)', 'Serial Already Exists!'),
        
    ]
    '''def onchange_serial_num (self, cr, uid, ids,name, product_id):
        mrp_obj = self.pool.get('mrp.production')
        print"name",name,product_id
        
        warning = {'title': _('Warning!')}
        return_value,return_value['value']={},{}
        if product_id:
            serial_no = self.pool.get('stock.production.lot').search(cr,uid,[('product_id','=',product_id),('name','=',name)])
            if serial_no:
                warning.update({'message' : _('Serial Number Already Exists')})
                return_value['warning'] = warning
                return_value['value']['name'] = False
#                raise osv.except_osv(_('Warning!'), _('Serial number already assigned'))
            else:
                return_value = ({'value':{'product_id':product_id}})
        return return_value'''
        
stock_production_lot()

class mrp_production(osv.osv):
    """
    Production Orders / Manufacturing Orders
    """
    _inherit = 'mrp.production'
#    _columns = {
#        'created_serials_random':fields.one2many('stock.production.lot','production_id'),
#
#    }

    '''def action_produce(self, cr, uid, production_id, production_qty, production_mode, context=None):
        """ To produce final product based on production mode (consume/consume&produce).
        If Production mode is consume, all stock move lines of raw materials will be done/consumed.
        If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
        and stock move lines of final product will be also done/produced.
        @param production_id: the ID of mrp.production object
        @param production_qty: specify qty to produce
        @param production_mode: specify production mode (consume/consume&produce).
        @return: True
        """
        stock_mov_obj = self.pool.get('stock.move')
        prodlot_obj = self.pool.get('stock.production.lot')
        production = self.browse(cr, uid, production_id, context=context)
        print"production",production
        wf_service = netsvc.LocalService("workflow")
        if not production.move_lines and production.state == 'ready':
            # trigger workflow if not products to consume (eg: services)
            wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce', cr)

        produced_qty = 0
        for produced_product in production.move_created_ids2:
            if (produced_product.scrapped) or (produced_product.product_id.id != production.product_id.id):
                continue
            produced_qty += produced_product.product_qty
        if production_mode in ['consume','consume_produce']:
            consumed_data = {}

            # Calculate already consumed qtys
            serial_no_list=[]
            for consumed in production.move_lines2:
                if consumed.scrapped:
                    continue
                if not consumed_data.get(consumed.product_id.id, False):
                    consumed_data[consumed.product_id.id] = 0
                    
                consumed_data[consumed.product_id.id] += consumed.product_qty

            # Find product qty to be consumed and consume it
            for scheduled in production.product_lines:

                # total qty of consumed product we need after this consumption
                total_consume = ((production_qty + produced_qty) * scheduled.product_qty / production.product_qty)

                # qty available for consume and produce
                qty_avail = scheduled.product_qty - consumed_data.get(scheduled.product_id.id, 0.0)
                
                if float_compare(qty_avail, 0, precision_rounding=scheduled.product_id.uom_id.rounding) <= 0:
                    # there will be nothing to consume for this raw material
                    continue

                raw_product = [move for move in production.move_lines if move.product_id.id==scheduled.product_id.id]
                if raw_product:
                    # qtys we have to consume
                    qty = total_consume - consumed_data.get(scheduled.product_id.id, 0.0)
		    #print"qty",qty,float_compare(qty, qty_avail, precision_rounding=scheduled.product_id.uom_id.rounding)
                    if float_compare(qty, qty_avail, precision_rounding=scheduled.product_id.uom_id.rounding) == 1:
			print"float_compare(qty, qty_avail, precision_rounding=scheduled.product_id.uom_id.rounding)",float_compare(qty, qty_avail, precision_rounding=scheduled.product_id.uom_id.rounding)
                        # if qtys we have to consume is more than qtys available to consume
                        prod_name = scheduled.product_id.name_get()[0][1]
                        raise osv.except_osv(_('Warning!'), _('You are going to consume total %s quantities of "%s".\nBut you can only consume up to total %s quantities.') % (qty, prod_name, qty_avail))
                    if float_compare(qty, 0, precision_rounding=scheduled.product_id.uom_id.rounding) <= 0:
                        # we already have more qtys consumed than we need
                        continue

                    raw_product[0].action_consume(qty, raw_product[0].location_id.id, context=context)
                    print"scheduled.product_id.id",scheduled.product_id.id
                    serial_no = self.pool.get('stock.production.lot').search(cr,uid,[('product_id','=',scheduled.product_id.id),('location_id','=',production.location_src_id.id),('serial_used','=',False)]) 
                    serial_no_list += serial_no
                    print"serial_no_list",serial_no_list
                    
#                    print"serial_no_list",serial_no_list
#                    serial_no_list
        if not serial_no_list:
            raise osv.except_osv(_('Warning!'), _('Please assign serial Number.'))
        else:
            serial_no_list.sort()
        if production_mode == 'consume_produce':
            # To produce remaining qty of final product
            #vals = {'state':'confirmed'}
            #final_product_todo = [x.id for x in production.move_created_ids]
            #stock_mov_obj.write(cr, uid, final_product_todo, vals)
            #stock_mov_obj.action_confirm(cr, uid, final_product_todo, context)
            produced_products = {}
            for produced_product in production.move_created_ids2:
                if produced_product.scrapped:
                    continue
                if not produced_products.get(produced_product.product_id.id, False):
                    produced_products[produced_product.product_id.id] = 0
                produced_products[produced_product.product_id.id] += produced_product.product_qty
            prod_qty = production_qty
            for produce_product in production.move_created_ids:
                produced_qty = produced_products.get(produce_product.product_id.id, 0)
                subproduct_factor = self._get_subproduct_factor(cr, uid, production.id, produce_product.id, context=context)
                rest_qty = (subproduct_factor * production.product_qty) - produced_qty
                print"rest_qty",rest_qty,subproduct_factor * production_qty
                if rest_qty < (subproduct_factor * production_qty):
                    prod_name = produce_product.product_id.name_get()[0][1]
                    raise osv.except_osv(_('Warning!'), _('You are going to produce total %s quantities of "%s".\nBut you can only produce up to total %s quantities.') % ((subproduct_factor * production_qty), prod_name, rest_qty))
                if rest_qty > 0 and len(serial_no_list) >= rest_qty:
                    if produce_product.product_id.track_production == True:
                        prodlot_obj = self.pool.get('stock.production.lot')
                        move_obj = self.pool.get('stock.move')
                        prod_lots = []
                        random_counter = 0
                        while prod_qty > 0:
                            print"prod_qty",prod_qty
                            context.update({'type':'consumed'})
#                            self.pool.get('mrp.production').write(cr,uid,)
                            ## suitable tech code to differentiate between Lot type split
                            ## single and whether its a random serial number product or no
#                                if not produce_product.product_id.random_serial:
#                            stock_prodlot_id = move_obj.set_prodlot(cr, uid, produce_product,context)
#                            prodlot_obj.write(cr,uid,stock_prodlot_id[0],{'qty_avail':1.0})
#                            if not production.created_serials_random:
#                                        raise osv.except_osv(_('Warning!'), _('No Random serial numbers exists for production.'))
#                            elif production.created_serials_random and len(production.created_serials_random) >= prod_qty:
#                                stock_prodlot_id = [production.created_serials_random[random_counter].id]
#                                print"stock_prodlot_id",stock_prodlot_id,production
                            print"serial_no_list",serial_no_list
                            stock_prodlot_id  = serial_no_list[:1]
                            if stock_prodlot_id:
                                del serial_no_list[:1]
                                prodlot_obj.write(cr,uid,stock_prodlot_id,{'qty_avail':1.0,'location_id':production.location_dest_id.id,'product_id':produce_product.product_id.id})
    #                            production.created_serials_random[random_counter].write({'production_id' : False})
                                
                                move_obj.write(cr,uid,[produce_product.id],{'serial_no_quantity':1.0,'prodlot_id':stock_prodlot_id[0]})
                                cr.execute("insert into stock_move_lot(stock_move_id,production_lot) values(%s,%s)"%(produce_product.id,stock_prodlot_id[0]))
                                cr.commit()
#                                prodlot_obj.write(cr,uid, stock_prodlot_id,{'move_ids':[(6,0, [produce_product.id])]})
#                            else:
#                                raise osv.except_osv(_('Warning!'), _('In Sufficient Random serial numbers created for production.'))
#                            
                            
#                            prod_lots.append(stock_prodlot_id[0])
                            prod_qty -= 1
                            random_counter += 1
                    stock_mov_obj.action_consume(cr, uid, [produce_product.id], (subproduct_factor * production_qty), context=context)
                else:
                    raise osv.except_osv(_('Warning!'), _('Insufficient Serial Number'))
        for raw_product in production.move_lines2:
            new_parent_ids = []
            parent_move_ids = [x.id for x in raw_product.move_history_ids]
            for final_product in production.move_created_ids2:
                if final_product.id not in parent_move_ids:
                    new_parent_ids.append(final_product.id)
            for new_parent_id in new_parent_ids:
                stock_mov_obj.write(cr, uid, [raw_product.id], {'move_history_ids': [(4,new_parent_id)]})

        wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce_done', cr)
        return True'''
        
        
        
    def action_produce(self, cr, uid, production_id, production_qty, production_mode, wiz=False, context=None):
        print"production",production_id
        """ To produce final product based on production mode (consume/consume&produce).
        If Production mode is consume, all stock move lines of raw materials will be done/consumed.
        If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
        and stock move lines of final product will be also done/produced.
        @param production_id: the ID of mrp.production object
        @param production_qty: specify qty to produce in the uom of the production order
        @param production_mode: specify production mode (consume/consume&produce).
        @param wiz: the mrp produce product wizard, which will tell the amount of consumed products needed
        @return: True
        """
        stock_mov_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get("product.uom")
        product_obj = self.pool.get('product.product')
        production = self.browse(cr, uid, production_id, context=context)
        production_qty_uom = uom_obj._compute_qty(cr, uid, production.product_uom.id, production_qty, production.product_id.uom_id.id)

        main_production_move,serial_no_list,rem_qty = False,[],0.0
        
        if production_mode == 'consume_produce':
            # To produce remaining qty of final product
            produced_products = {}
            for produced_product in production.move_created_ids2:
                if produced_product.scrapped:
                    continue
                if not produced_products.get(produced_product.product_id.id, False):
                    produced_products[produced_product.product_id.id] = 0
                produced_products[produced_product.product_id.id] += produced_product.product_qty
            
            
            

            for produce_product in production.move_created_ids:
                print"produce_product",produce_product
                subproduct_factor = self._get_subproduct_factor(cr, uid, production.id, produce_product.id, context=context)
                lot_id = False
                if wiz:
                    lot_id = wiz.lot_id.id
                
                qty = min(subproduct_factor * production_qty_uom, produce_product.product_qty) #Needed when producing more than maximum quantity
                new_moves = stock_mov_obj.action_consume(cr, uid, [produce_product.id], qty,
                                                         location_id=produce_product.location_id.id, restrict_lot_id=lot_id, context=context)
                stock_mov_obj.write(cr, uid, new_moves, {'production_id': production_id}, context=context)
                remaining_qty = subproduct_factor * production_qty_uom - qty
                if remaining_qty: # In case you need to make more than planned
                    #consumed more in wizard than previously planned
                    extra_move_id = stock_mov_obj.copy(cr, uid, produce_product.id, default={'state': 'confirmed',
                                                                                             'product_uom_qty': remaining_qty,
                                                                                             'production_id': production_id}, context=context)
                    if extra_move_id:
                        stock_mov_obj.action_done(cr, uid, [extra_move_id], context=context)

                if produce_product.product_id.id == production.product_id.id:
                    main_production_move = produce_product.id
            
            for produce_product in production.move_lines:
                    if context.get('csv',False)==True or context.get('scan',False)==True:
                        serial_no_list=context.get('serial_number_list',False)
                #else:
                #    print"elseeeeeeeeeee",production.product_id.id
                #    serial_no = self.pool.get('stock.production.lot').search(cr,uid,[('product_id','=',produce_product.product_id.id),('location_id','=',production.location_src_id.id),('serial_used','=',False)]) 
                #    print"serial_nooooooooooooooooooo",serial_no
#                #    serial_no = self.pool.get('stock.production.lot').search(cr,uid,[('product_id','=',scheduled.product_id.id),('location_id','=',production.location_src_id.id),('serial_used','=',False)]) 
                 #   serial_no_list += serial_no
                #print"serial_no_list",serial_no_list
                    
        if not serial_no_list:
            raise osv.except_osv(_('Warning!'), _('Please assign serial Number.'))

        if production_mode in ['consume', 'consume_produce']:
            if wiz:
                consume_lines = []
                for cons in wiz.consume_lines:
                    consume_lines.append({'product_id': cons.product_id.id, 'lot_id': cons.lot_id.id, 'product_qty': cons.product_qty})
            else:
                consume_lines = self._calculate_qty(cr, uid, production, production_qty_uom, context=context)
            for consume in consume_lines:
                product_brw = product_obj.browse(cr,uid,consume['product_id'])
                remaining_qty = consume['product_qty']
                for raw_material_line in production.move_lines:
                    print"raw_material_line",raw_material_line
                    if remaining_qty <= 0:
                        break
                    if consume['product_id'] != raw_material_line.product_id.id:
                        continue
                    
                    consumed_qty = min(remaining_qty, raw_material_line.product_qty)
                    rem_qty = remaining_qty
                    if production.product_id.track_production == True:
                        if raw_material_line.product_id.track_incoming==True:
                            if rem_qty > 0 and len(serial_no_list) >= rem_qty:
                        
                                prodlot_obj = self.pool.get('stock.production.lot')
                                move_obj = self.pool.get('stock.move')
                                prod_lots = []
                                random_counter = 0
                                while rem_qty > 0 and len(serial_no_list) >= rem_qty:
        #                            context.update({'type':'consumed'})
                                    stock_prodlot_id  = serial_no_list[:1]
                                    if stock_prodlot_id:
                                        del serial_no_list[:1]
                                        prodlot_obj.write(cr,uid,stock_prodlot_id,{'qty_avail':1.0,'location_id':production.location_dest_id.id,'product_id':production.product_id.id,'ref':production.name})
            #                            production.created_serials_random[random_counter].write({'production_id' : False})

                                        move_obj.write(cr,uid,[main_production_move],{'serial_no_quantity':1.0})
                                        cr.execute("insert into stock_move_lot(stock_move_id,production_lot) values(%s,%s)"%(main_production_move,stock_prodlot_id[0]))
        #                                cr.commit()
                                    rem_qty -= 1
                                    random_counter += 1
                            else:
                                raise osv.except_osv(_('Warning!'), _('Insufficient Serial Number.'))
                        stock_mov_obj.action_consume(cr, uid, [raw_material_line.id], consumed_qty, raw_material_line.location_id.id,
                                                     restrict_lot_id=consume['lot_id'], consumed_for=main_production_move, context=context)
                        remaining_qty -= consumed_qty
                             
                if remaining_qty:
                    #consumed more in wizard than previously planned
                    product = self.pool.get('product.product').browse(cr, uid, consume['product_id'], context=context)
                    extra_move_id = self._make_consume_line_from_data(cr, uid, production, product, product.uom_id.id, remaining_qty, False, 0, context=context)
                    if extra_move_id:
                        if consume['lot_id']:
                            stock_mov_obj.write(cr, uid, [extra_move_id], {'restrict_lot_id': consume['lot_id']}, context=context)
                        stock_mov_obj.action_done(cr, uid, [extra_move_id], context=context)

        self.message_post(cr, uid, production_id, body=_("%s produced") % self._description, context=context)
        self.signal_workflow(cr, uid, production_id, 'button_produce_done')
        return True

mrp_production()


