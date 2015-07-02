
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class stock_partial_picking_line(osv.TransientModel):
   _inherit = "stock.partial.picking.line"
   _columns = {
       'product_id' : fields.many2one('product.product', string="Part ID", required=True, ondelete='CASCADE'),
       'quantity_received' : fields.float('Quantity Received',digits=(16,2 )),
   }

class stock_partial_picking(osv.osv_memory):
    _inherit = 'stock.partial.picking'

    def _partial_move_for(self, cr, uid, move):
#        print "partialllllll velodyne"
        partial_move = {
            'product_id' : move.product_id.id,
            'quantity' : move.state in ('assigned','new') and move.received_qty or 0,
            'product_uom' : move.product_uom.id,
            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
            'location_id' : move.location_id.id,
            'location_dest_id' : move.location_dest_id.id,
        }
        if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
            partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
        return partial_move
    #Added by Bista to automatically get the real stock values
    #TODO:Taking stock location as the main location, need to change this to the location available in move line
    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """

#        print "default getting called in barcode scanning"
        if context is None:
            context = {}

        pick_obj = self.pool.get('stock.picking')
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        if not picking_ids:
            return res

        result = []
        for pick in pick_obj.browse(cr, uid, picking_ids, context=context):
            pick_type = self.get_picking_type(cr, uid, pick, context=context)
            for m in pick.move_lines:
                if m.state in ('done', 'cancel'):
                    continue
                result.append(self.__create_partial_picking_memory(m, pick_type, cr, uid, context))

#        if 'product_moves_in' in fields:
#            res.update({'product_moves_in': result})
#        if 'product_moves_out' in fields:
#            res.update({'product_moves_out': result})
#        print "result append",result
#        print "res previous",res
        if 'move_ids' in fields:
            res.update({'move_ids':result})
#        print "res append",res
        if 'date' in fields:
            res.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return res
    def __create_partial_picking_memory(self, picking, pick_type, cr =False, uid=False, context={}):

        validate_qty = picking.product_qty
        if (picking.picking_id.type == 'out') and (picking.picking_id.skip_barcode == False):
#            received_qty = picking.received_qty
            validate_qty = picking.received_qty
            validate_received_qty = validate_qty
        else:
            validate_received_qty = validate_qty
#        print "validate qty",validate_qty
        #quantity availble in selected source location
        product_id = picking.product_id
        location_id = picking.location_id.id
        if not location_id:
            raise osv.except_osv(_('Error!'),  _('Please Specify Source Location for %s')%(product_id.name))
#        qty_available = picking.product_id.qty_available#self.pool.get('stock.location')._product_get(self.cr, self.uid, location_id, [product_id], context={})[product_id]
#        if cr:
#            qty_available = self.pool.get('stock.location')._product_get(cr, uid, location_id, [product_id.id], context={})[product_id.id]
#        ##TODO
        if cr:
            cr.execute(
            'select sum(product_qty) '\
            'from stock_move '\
            'where location_id NOT IN  %s '\
            'and location_dest_id = %s '\
            'and product_id  = %s '\
            'and state = %s ',tuple([(location_id,), location_id, product_id.id, 'done']))
            wh_qty_recieved = cr.fetchone()[0] or 0.0
                            #this gets the value which is sold and confirmed
            argumentsnw = [location_id,(location_id,),product_id.id,( 'done',)]#this will take reservations into account
            cr.execute(
            'select sum(product_qty) '\
            'from stock_move '\
            'where location_id = %s '\
            'and location_dest_id NOT IN %s '\
            'and product_id  = %s '\
            'and state in %s ',tuple(argumentsnw))
            qty_with_reserve = cr.fetchone()[0] or 0.0

            qty_available = wh_qty_recieved - qty_with_reserve
#        ##TODO
#        print "picking type ",picking.picking_id.skip_barcode
#        if picking.picking_id.type == 'out' and picking.picking_id.skip_barcode == True:
#            if validate_qty <= qty_available:
#                validate_qty = picking.product_qty
#
#            elif validate_qty >= qty_available:
#                validate_qty = qty_available
#                if not validate_qty >= 0.0:
#                    validate_qty = 0.0
#        # If Shipping Type is 'internal'
#        if picking.picking_id.type == 'internal':
#            if validate_qty <= qty_available:
#                validate_qty = picking.product_qty
        #end
#        print "validate quantity barcode true move menory",validate_qty,validate_received_qty
        move_memory = {
            'product_id' : picking.product_id.id,
            'quantity' : validate_qty,
            'quantity_received' : validate_received_qty,# code for velodyne to create a backorder based on the scanned quantity
            'product_uom' : picking.product_uom.id,
            'prodlot_id' : picking.prodlot_id.id,
            'move_id' : picking.id,
            'location_id' : picking.location_id.id,
            'location_dest_id' : picking.location_dest_id.id,
        }

        if pick_type == 'in':
            move_memory.update({
                'cost' : picking.product_id.standard_price,
                'currency' : picking.product_id.company_id.currency_id.id,
            })
        return move_memory
    def get_picking_type(self, cr, uid, picking, context=None):
        picking_type = picking.type
        for move in picking.move_lines:
            if picking.type == 'in' and move.product_id.cost_method == 'average':
                picking_type = 'in'
                break
            else:
                picking_type = 'out'
        return picking_type

    def do_partial(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time'
        stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : partial.date
        }
        picking_type = partial.picking_id.type
        for wizard_line in partial.move_ids:
            line_uom = wizard_line.product_uom
            move_id = wizard_line.move_id.id

            #Quantiny must be Positive
            if wizard_line.quantity < 0:
                raise osv.except_osv(_('Warning!'), _('Please provide Proper Quantity !'))

            #Compute the quantity for respective wizard_line in the line uom (this jsut do the rounding if necessary)
            qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, line_uom.id)

            if line_uom.factor and line_uom.factor <> 0:
                if qty_in_line_uom <> wizard_line.quantity:
                    raise osv.except_osv(_('Warning'), _('The uom rounding does not allow you to ship "%s %s", only roundings of "%s %s" is accepted by the uom.') % (wizard_line.quantity, line_uom.name, line_uom.rounding, line_uom.name))
            if move_id:
                #Check rounding Quantity.ex.
                #picking: 1kg, uom kg rounding = 0.01 (rounding to 10g), 
                #partial delivery: 253g
                #=> result= refused, as the qty left on picking would be 0.747kg and only 0.75 is accepted by the uom.
                initial_uom = wizard_line.move_id.product_uom
                #Compute the quantity for respective wizard_line in the initial uom
                qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, initial_uom.id)
                without_rounding_qty = (wizard_line.quantity / line_uom.factor) * initial_uom.factor
                if qty_in_initial_uom <> without_rounding_qty:
                    raise osv.except_osv(_('Warning'), _('The rounding of the initial uom does not allow you to ship "%s %s", as it would let a quantity of "%s %s" to ship and only roundings of "%s %s" is accepted by the uom.') % (wizard_line.quantity, line_uom.name, wizard_line.move_id.product_qty - without_rounding_qty, initial_uom.name, initial_uom.rounding, initial_uom.name))
            else:
                seq_obj_name =  'stock.picking.' + picking_type
                move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                                                    'product_id': wizard_line.product_id.id,
                                                    'product_qty': wizard_line.quantity,
                                                    'product_uom': wizard_line.product_uom.id,
                                                    'prodlot_id': wizard_line.prodlot_id.id,
                                                    'location_id' : wizard_line.location_id.id,
                                                    'location_dest_id' : wizard_line.location_dest_id.id,
                                                    'picking_id': partial.picking_id.id
                                                    },context=context)
                stock_move.action_confirm(cr, uid, [move_id], context)
            partial_data['move%s' % (move_id)] = {
                'product_id': wizard_line.product_id.id,
                'product_qty': wizard_line.quantity,
                'product_uom': wizard_line.product_uom.id,
                'prodlot_id': wizard_line.prodlot_id.id,
            }
#            print "partial_data",partial_data
#            fdffd
            if (picking_type == 'in') and (wizard_line.product_id.cost_method == 'average'):
                partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
                                                                 product_currency=wizard_line.currency.id)
        stock_picking.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
        return {'type': 'ir.actions.act_window_close'}

stock_partial_picking()
