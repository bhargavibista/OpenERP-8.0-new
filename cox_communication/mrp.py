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

        
    def action_produce(self, cr, uid, production_id, production_qty, production_mode, wiz=False, context=None):
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


