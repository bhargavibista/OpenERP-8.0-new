# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from openerp import netsvc
import time
from operator import attrgetter
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    def action_done(self, cr, uid, ids, context=None):
        super(stock_picking,self).action_done(cr,uid,ids,context)
        replenish_obj = self.pool.get('stock.replenish')
        search_replenish_record = replenish_obj.search(cr,uid,[('linked_picking_id','in',ids),('state','!=','done')])
        if search_replenish_record:
            replenish_obj.write(cr,uid,search_replenish_record,{'state':'done'})
        return True
stock_picking()

class stock_replenish(osv.osv):
    _name = "stock.replenish"
    _inherit = ['mail.thread']
    _description = "Replenish List"
    _order = "id desc"

    def _set_maximum_date(self, cr, uid, ids, name, value, arg, context=None):
        """ Calculates planned date if it is greater than 'value'.
        @param name: Name of field
        @param value: Value of field
        @param arg: User defined argument
        @return: True or False
        """
        if not value:
            return False
        if isinstance(ids, (int, long)):
            ids = [ids]
        for pick in self.browse(cr, uid, ids, context=context):
            sql_str = """update stock_move set
                    date_expected='%s'
                where
                    picking_id=%d """ % (value, pick.id)
            if pick.max_date:
                sql_str += " and (date_expected='" + pick.max_date + "')"
            cr.execute(sql_str)
        return True

    def _set_minimum_date(self, cr, uid, ids, name, value, arg, context=None):
        """ Calculates planned date if it is less than 'value'.
        @param name: Name of field
        @param value: Value of field
        @param arg: User defined argument
        @return: True or False
        """
        if not value:
            return False
        if isinstance(ids, (int, long)):
            ids = [ids]
        for pick in self.browse(cr, uid, ids, context=context):
            sql_str = """update stock_move set
                    date_expected='%s'
                where
                    picking_id=%s """ % (value, pick.id)
            if pick.min_date:
                sql_str += " and (date_expected='" + pick.min_date + "')"
            cr.execute(sql_str)
        return True

    def get_min_max_date(self, cr, uid, ids, field_name, arg, context=None):
        """ Finds minimum and maximum dates for picking.
        @return: Dictionary of values
        """
        res = {}
        for id in ids:
            res[id] = {'min_date': False, 'max_date': False}
        if not ids:
            return res
        cr.execute("""select
                picking_id,
                min(date_expected),
                max(date_expected)
            from
                stock_move
            where
                picking_id IN %s
            group by
                picking_id""",(tuple(ids),))
        for pick, dt1, dt2 in cr.fetchall():
            res[pick]['min_date'] = dt1
            res[pick]['max_date'] = dt2
        return res

    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/') or (vals.get('name') == False):
            vals['name'] = self.pool.get('ir.sequence').get(cr, user, 'stock.replenish')
        new_id = super(stock_replenish, self).create(cr, user, vals, context)
        location_id,location_dest_id = False,False
        move_lines =vals.get('move_lines',[])
        for line in move_lines:
            new_location_id = line[2].get('location_id')
            new_location_dest_id = line[2].get('location_dest_id')
            if not location_id:
                location_id = line[2].get('location_id')
            if not location_dest_id:
                location_dest_id = line[2].get('location_dest_id')
            if new_location_id != location_id:
                raise osv.except_osv(_('Warning!'),_('Source Location should be same for all the lines'))
            if new_location_dest_id != location_dest_id:
                raise osv.except_osv(_('Warning!'),_('Destination Location should be same for all the lines'))
        return new_id

    def write(self, cr, uid, ids,vals, context=None):
        location_id = False
        location_dest_id = False
        move_lines = vals.get('move_lines',[])
        if move_lines:
            for line in move_lines:
                if line[0] != 2:
                    new_location_id = line[2].get('location_id',False) if line[2] else False
                    new_location_dest_id = line[2].get('location_dest_id',False) if line[2] else False
                    if line[1]:
                        line_obj=self.pool.get('stock.move.replenish')
                        if line[0] == 4:
                            location_id = line_obj.browse(cr,uid,line[1]).location_id.id
                            location_dest_id = line_obj.browse(cr,uid,line[1]).location_dest_id.id
                        if not location_id:
                            location_id = line[2].get('location_id')
                        if not location_dest_id:
                            location_dest_id = line[2].get('location_dest_id')
                        if line[0] == 1:
                            if line[2].get('location_id'):
                                new_location_id = line[2].get('location_id')
                            if line[2].get('location_dest_id'):
                                new_location_dest_id = line[2].get('location_dest_id')
                        if line[0] == 0:
                            if line[2].get('location_id'):
                                new_location_id = line[2].get('location_id')
                            if line[2].get('location_dest_id'):
                                new_location_dest_id = line[2].get('location_dest_id')
                        if new_location_id and location_id and new_location_id != location_id:
                            raise osv.except_osv(_('Warning!'),_('Source Location should be same for all the lines'))
                        if new_location_dest_id != location_dest_id:
                            raise osv.except_osv(_('Warning!'),_('Destination Location should be same for all the lines'))
        return super(stock_replenish, self).write(cr, uid, ids,vals, context)	
    
    _columns = {
        'name': fields.char('Reference', size=64, select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'origin': fields.char('Source Document', size=64, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, help="Reference of the document", select=True),
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'note': fields.text('Notes', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
#        'stock_journal_id': fields.many2one('stock.journal','Stock Journal', select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}), ## cox gen2
        'location_id': fields.many2one('stock.location', 'Location', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, help="Keep empty if you produce at the location where the finished products are needed." \
                "Set a location if you produce at a fixed location. This can be a partner location " \
                "if you subcontract the manufacturing operations.", select=True),
        'location_dest_id': fields.many2one('stock.location', 'Dest. Location', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, help="Location where the system will stock the finished products.", select=True),
        'move_type': fields.selection([('direct', 'Partial'), ('one', 'All at once')], 'Delivery Method', required=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, help="It specifies goods to be deliver partially or all at once"),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('cancel', 'Cancelled'),
            ('done', 'Transferred'),
	    ('approved', 'Approved'),	
            ], 'Status', readonly=True, select=True, track_visibility='onchange', help="""
            * Draft: not confirmed yet and will not be scheduled until confirmed\n
            * Transferred: has been processed, can't be modified or cancelled anymore\n
            * Cancelled: has been cancelled, can't be confirmed anymore"""
        ),
        'min_date': fields.function(get_min_max_date, fnct_inv=_set_minimum_date, multi="min_max_date",
                 store=True, type='datetime', string='Scheduled Time', select=1, help="Scheduled time for the shipment to be processed"),
        'date': fields.datetime('Creation Date', help="Creation date, usually the time of the order.", select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'date_done': fields.datetime('Date of Transfer', help="Date of Completion", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'max_date': fields.function(get_min_max_date, fnct_inv=_set_maximum_date, multi="min_max_date",
                 store=True, type='datetime', string='Max. Expected Date', select=2),
        'move_lines': fields.one2many('stock.move.replenish', 'picking_id', 'Internal Moves', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        'product_id': fields.related('move_lines', 'product_id', type='many2one', relation='product.product', string='Product'),
        'auto_picking': fields.boolean('Auto-Picking', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'partner_id': fields.many2one('res.partner', 'Partner', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Control",
            select=True, required=True, readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True, select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'linked_picking_id':fields.many2one('stock.picking', 'Linked Move'),
    }
    _defaults = {
        'name': lambda self, cr, uid, context: '/',
        'state': 'draft',
        'move_type': 'direct',
        'type': 'internal',
        'invoice_state': 'none',
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.picking', context=c)
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Reference must be unique per Company!'),
    ]

    def draft_confirm(self,cr,uid,ids,context=None):
        picking = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
	todo_moves,picking_out_id = [],False
        picking_type_id = self.pool.get('stock.picking.type').search(cr,uid,[('code','=','internal')]) ##cox gen2
        for obj in self.browse(cr,uid,ids,context):
            picking_internal_id = picking.create(cr,uid, {
                'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking'),
                'partner_id':obj.partner_id and obj.partner_id.id or False,
#                'type':'internal',  ##cox gen2
                'picking_type_id':picking_type_id[0],   ##cox gen2
                'date': obj.date,
                'origin': obj.name},{})
            for line in obj.move_lines:
                move_id = move_obj.create(cr, uid, {
                'name': line.product_id.name,
                'location_id': line.location_id.id,
                'location_dest_id': line.location_dest_id.id,
                'product_id': line.product_id.id,
#                'product_qty': line.product_qty,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_uom.id,
                'type': 'internal',
                'date_expected': line.date_expected,
                'date': line.date,
                'company_id': line.company_id.id,
                'origin':line.name,
                'picking_id':picking_internal_id
                },{})
		todo_moves.append(move_id)
	    if todo_moves and picking_internal_id:
		move_obj.action_confirm(cr, uid, todo_moves)
             	wf_service = netsvc.LocalService("workflow")
	        wf_service.trg_validate(uid, 'stock.picking', picking_internal_id, 'button_confirm', cr)		
            self.write(cr,uid,[obj.id],{'state':'approved','linked_picking_id':picking_internal_id})
        return True
stock_replenish()

class stock_move_replenish(osv.osv):
    _name = "stock.move.replenish"
    _description = "Stock Move Replenish"
    _order = 'date_expected desc, id'
    _log_create = False

    def copy(self,cr,uid,id,default,context={}):
        default.update({'return_move_id':0})
        return super(stock_move_replenish, self).copy(cr, uid, id, default, context=context)
    def get_parent_stock_mv_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
#        so_line_obj = self.pool.get('sale.order.line')
#        stock_move_obj = self.pool.get('stock.move')
        for each_move in self.browse(cr, uid, ids, context=context):
#            if each_move.sale_line_id:
#                search_child_so_line_id = so_line_obj.search(cr,uid,[('parent_so_line_id','=',each_move.sale_line_id.id)])
#                if search_child_so_line_id:
#                    for each_line in search_child_so_line_id:
#                        search_stock_move = stock_move_obj.search(cr,uid,[('sale_line_id','=',each_line),('state','in',('confirmed','assigned'))])
#                        if search_stock_move and len(search_stock_move) == 1:
#                            result[search_stock_move[0]] = each_move.id
#                            result[each_move.id] = False
            if each_move.return_move_id:
                    result[each_move.id] = each_move.return_move_id
        return result
    _columns = {
        'name': fields.char('Description', required=True, select=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'date': fields.datetime('Date', required=True, select=True, help="Move date: scheduled date until move is done, then date of actual move processing"),
        'date_expected': fields.datetime('Scheduled Date',required=True, select=True, help="Scheduled date for the processing of this move"),
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True, domain=[('type','<>','service')]),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
            required=True,
            help="This is the quantity of products from an inventory "
                "point of view. For moves in the state 'done', this is the "
                "quantity of products that were actually moved. For other "
                "moves, this is the quantity of product that is planned to "
                "be moved. Lowering this quantity does not generate a "
                "backorder. Changing this quantity on assigned moves affects "
                "the product reservation, and should be done with care."
        ),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'location_id': fields.many2one('stock.location', 'Source Location', required=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True, select=True, help="Location where the system will stock the finished products."),
        'partner_id': fields.many2one('res.partner', 'Destination Address ', help="Optional address where goods are to be delivered, specifically used for allotment"),
        'move_dest_id': fields.many2one('stock.move', 'Destination Move', help="Optional: next stock move when chaining them", select=True),
        'picking_id': fields.many2one('stock.replenish', 'Reference', select=True),
        'note': fields.text('Notes'),
        'state': fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True,
                 help= "* New: When the stock move is created and not yet confirmed.\n"\
                       "* cancel: When move are cancelled, it is set to \'Cancel\'.\n"\
                       "* Done: When the shipment is processed, the state is \'Done\'."),
        'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price'), help="Technical field used to record the product cost set by the user during a picking confirmation (when average price costing method is used)"),
        'price_currency_id': fields.many2one('res.currency', 'Currency for average price', help="Technical field used to record the currency chosen by the user during a picking confirmation (when average price costing method is used)"),
        'company_id': fields.many2one('res.company', 'Company', required=True, select=True),
        'origin': fields.related('picking_id','origin',type='char', size=64, relation="stock.picking", string="Source", store=True),
        'type': fields.related('picking_id', 'type', type='selection', selection=[('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], string='Shipping Type'),
        'return_move_id': fields.integer('Return Move Id'),
        'parent_stock_mv_id': fields.function(get_parent_stock_mv_id, type='many2one', relation='stock.move', string='Parent Stock Move Id',store=True),
    }
    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.move.replenish', context=c),
    }  
    def create(self, cr, uid, vals, context=None):
        if vals.get('product_qty',0.0) <= 0:
            if vals.get('product_qty',0.0) in (0.0,0):
                raise osv.except_osv(_('Warning!'),_('Quantity Cannot be Zero'))
        return super(stock_move_replenish, self).create(cr, uid, vals, context)
    def write(self, cr, uid, ids,vals, context=None):
        if vals.get('product_qty',0.0) <= 0:
            if vals.get('product_qty',0.0) in (0.0,0):
	        raise osv.except_osv(_('Warning!'),_('Quantity Cannot be Zero'))
        return super(stock_move_replenish, self).write(cr, uid, ids,vals, context)	
      
    #def create(self, cr, uid, vals, context=None):
     #   id=super(stock_move_replenish, self).create(cr, uid, vals, context)
      #  if vals.get('product_id',False) and vals.get('picking_id',False):
       #     picking_brw=self.pool.get('stock.picking').browse(cr,uid,vals.get('picking_id'))
        #    if picking_brw.type == 'out':
         #       cr.execute("select comp_product_id from extra_prod_config where product_id=%s"%(vals.get('product_id')))
          #      sub_products=filter(None, map(lambda x:x[0], cr.fetchall()))
           #     if sub_products:
            #        vals.update({'parent_stock_mv_id':id})
             #       self.create_subproduct_move(cr, uid, vals, sub_products, context)
#            if picking_brw.type == 'out':
#                if not (picking_brw.pack_length):
#                    prod_brw = self.pool.get('product.product').browse(cr,uid,vals.get('product_id',False))
#                    length = prod_brw.prod_length
#                    width = prod_brw.prod_width
#                    height = prod_brw.prod_height
#                    cr.execute("update stock_picking set pack_length=%s,pack_width=%s,pack_height=%s where id=%s"%(length,width,height,picking_brw.id))
#        return id
    def create_subproduct_move(self, cr, uid, vals, sub_products, context=None):
        for product in sub_products:
            vals.update({'product_id':product})
            self.create(cr, uid, vals, context)
        return True
    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """ Finds UoM for changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            d = {'product_uom': [('category_id', '=', prod.uom_id.category_id.id)]}
            v = {'product_uom': prod.uom_id.id,'name':prod.name}
            return {'value': v, 'domain': d}
        return {'domain': {'product_uom': []}}

    def onchange_quantity(self, cr, uid, ids, product_id, product_qty,
                          product_uom):
        """ On change of product quantity finds UoM and UoS quantities
        @param product_id: Product id
        @param product_qty: Changed Quantity of product
        @param product_uom: Unit of measure of product
        @param product_uos: Unit of sale of product
        @return: Dictionary of values
        """
        result = {}
        warning = {}

        if (not product_id) or (product_qty <=0.0):
            result['product_qty'] = 0.0
            return {'value': result}

        product_obj = self.pool.get('product.product')
        uos_coeff = product_obj.read(cr, uid, product_id, ['uos_coeff'])

        # Warn if the quantity was decreased
        if ids:
            for move in self.read(cr, uid, ids, ['product_qty']):
                if product_qty < move['product_qty']:
                    warning.update({
                       'title': _('Information'),
                       'message': _("By changing this quantity here, you accept the "
                                "new quantity as complete: OpenERP will not "
                                "automatically generate a back order.") })
                break

        return {'value': result, 'warning': warning}

    def onchange_date(self, cr, uid, ids, date, date_expected, context=None):
        """ On change of Scheduled Date gives a Move date.
        @param date_expected: Scheduled Date
        @param date: Move Date
        @return: Move Date
        """
        if not date_expected:
            date_expected = time.strftime('%Y-%m-%d %H:%M:%S')
        return {'value':{'date': date_expected}} 

stock_move_replenish()

class stock_warehouse_replenish(osv.osv):
    """
    Defines Replenish stock rules.
    """
    _name = "stock.warehouse.replenish"
    _description = "Minimum Replenish Inventory Rule"

    def _get_draft_replenish(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        stock_obj = self.pool.get('stock.replenish')
        for orderpoint in self.browse(cr, uid, ids, context=context):
            stock_ids = stock_obj.search(cr, uid , [('state', '=', 'draft'), ('origin', '=', orderpoint.name)])
            result[orderpoint.id] = stock_ids
        return result

    def _check_product_uom(self, cr, uid, ids, context=None):
        '''
        Check if the UoM has the same category as the product standard UoM
        '''
        if not context:
            context = {}

        for rule in self.browse(cr, uid, ids, context=context):
            if rule.product_id.uom_id.category_id.id != rule.product_uom.category_id.id:
                return False

        return True
    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the replenish rule without removing it."),
#        'logic': fields.selection([('max','Order to Max'),('price','Best price (not yet active!)')], 'Reordering Mode', required=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True, ondelete="cascade"),
        'location_id': fields.many2one('stock.location', 'Location', required=True, ondelete="cascade"),
        'product_id': fields.many2one('product.product', 'Product', required=True, ondelete='cascade', domain=[('type','!=','service')]),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
        'product_min_qty': fields.float('Minimum Quantity', required=True,
            help="When the virtual stock goes below the Min Quantity specified for this field, OpenERP generates "\
            "a incoming to bring the forecasted quantity to the Max Quantity."),
        'product_max_qty': fields.float('Maximum Quantity', required=True,
            help="When the virtual stock goes below the Min Quantity, OpenERP generates "\
            "a incoming to bring the forecasted quantity to the Quantity specified as Max Quantity."),
        'qty_multiple': fields.integer('Qty Multiple', required=True,
            help="The incoming quantity will be rounded up to this multiple."),
        'replenish_internal_id': fields.many2one('stock.replenish', 'Latest Internal', ondelete="set null"),
        'company_id': fields.many2one('res.company','Company',required=True),
        'replenish_internal_draft_ids': fields.function(_get_draft_replenish, type='many2many', relation="stock.replenish", \
                                string="Related Replenish-Orders",help="Draft Internal Shipments of the product and location of that replenish rule"),
    }
    _defaults = {
        'active': lambda *a: 1,
        'qty_multiple': lambda *a: 1,
        'name': lambda x,y,z,c: x.pool.get('ir.sequence').get(y,z,'stock.warehouse.replenish') or '',
        'product_uom': lambda sel, cr, uid, context: context.get('product_uom', False),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.warehouse.orderpoint', context=c)
    }
    _sql_constraints = [
        ('qty_multiple_check', 'CHECK( qty_multiple > 0 )', 'Qty Multiple must be greater than zero.'),
    ]
    _constraints = [
        (_check_product_uom, 'You have to select a product unit of measure in the same category than the default unit of measure of the product', ['product_id', 'product_uom']),
    ]

#    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context=None):
#        """ Finds location id for changed warehouse.
#        @param warehouse_id: Changed id of warehouse.
#        @return: Dictionary of values.
#        """
#        if warehouse_id:
#            w = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context=context)
#            v = {'location_id': w.lot_stock_id.id}
#            return {'value': v}
#        return {}

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """ Finds UoM for changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            d = {'product_uom': [('category_id', '=', prod.uom_id.category_id.id)]}
            v = {'product_uom': prod.uom_id.id}
            return {'value': v, 'domain': d}
        return {'domain': {'product_uom': []}}

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.warehouse.replenish') or '',
        })
        return super(stock_warehouse_replenish, self).copy(cr, uid, id, default, context=context)

    def run_replinsh_scheduler(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        ''' Runs through scheduler.
        @param use_new_cursor: False or the dbname
        '''
        if use_new_cursor:
            use_new_cursor = cr.dbname
#        self._procure_confirm(cr, uid, use_new_cursor=use_new_cursor, context=context)
        self._create_replenish_order(cr, uid, automatic=automatic,\
                use_new_cursor=use_new_cursor, context=context)

    def _get_orderpoint_date_planned(self, cr, uid, orderpoint, start_date, context=None):
        date_planned = start_date + \
                       relativedelta(days=orderpoint.product_id.seller_delay or 0.0)
        return date_planned.strftime(DEFAULT_SERVER_DATE_FORMAT)

    def _prepare_orderpoint_procurement(self, cr, uid, orderpoint, context=None):

        return {'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.replenish'),
                'partner_id':orderpoint.location_id.partner_id and orderpoint.location_id.partner_id.id or False,
#                'stock_journal_id':self.pool.get('stock.journal').search(cr, uid, [], context=context)[0],
                'type':'internal',
                'date': self._get_orderpoint_date_planned(cr, uid, orderpoint, datetime.today(), context=context),
                'origin': orderpoint.name}
#                'product_id': orderpoint.product_id.id,
#                'product_qty': product_qty,
#                'company_id': orderpoint.company_id.id,
#                'product_uom': orderpoint.product_uom.id,
#                'location_id': orderpoint.location_id.id,
#                'procure_method': 'make_to_order',
#                'origin': orderpoint.name}

    def _prepare_stock_move(self,cr,uid,ids,orderpoint,qty,picking_id,source,context={}):
        move_obj = self.pool.get('stock.move.replenish')
        id = move_obj.create(cr, uid, {
                'name': orderpoint.product_id.name,
                'location_id': source,
                'location_dest_id': orderpoint.location_id.id,
                'product_id': orderpoint.product_id.id,
                'product_qty': qty,
                'product_uom': orderpoint.product_uom.id,
                'type': 'out',
                'date_expected': self._get_orderpoint_date_planned(cr, uid, orderpoint, datetime.today(), context=context),
                'date': self._get_orderpoint_date_planned(cr, uid, orderpoint, datetime.today(), context=context),
#                'state': 'draft',
                'company_id': orderpoint.company_id.id,
                'origin':orderpoint.name,
                'picking_id':picking_id
            })
#        move_obj.action_confirm(cr, uid, [id], context=context)
        return id

    def _product_virtual_get(self, cr, uid, order_point):
        location_obj = self.pool.get('stock.location')
        return location_obj._product_virtual_get(cr, uid,
                order_point.location_id.id, [order_point.product_id.id],
                {'uom': order_point.product_uom.id})[order_point.product_id.id]
    
#    def create_replenish_order(self, cr, uid, ids,context=None):
    def _create_replenish_order(self, cr, uid, automatic=False,\
            use_new_cursor=False, context=None, user_id=False):
        '''
        Create procurement based on Orderpoint
        use_new_cursor: False or the dbname

        @param self: The object pointer
        @param cr: The current row, from the database cursor,
        @param user_id: The current user ID for security checks
        @param context: A standard dictionary for contextual values
        @param param: False or the dbname
        @return:  Dictionary of values
        """
        '''
        if context is None:
            context = {}
        if use_new_cursor:
            cr = openerp.registry(use_new_cursor).db.cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.replenish')

        stock_obj = self.pool.get('stock.replenish')
        move_obj = self.pool.get('stock.move.replenish')
        offset = 0
        ids = [1]
#        if automatic:
#            self.create_automatic_op(cr, uid, context=context)
#        while ids:
        ids = orderpoint_obj.search(cr, uid, [], offset=offset, limit=100)
        for op in orderpoint_obj.browse(cr, uid, ids, context=context):
            prods = self._product_virtual_get(cr, uid, op)
            if prods is None:
                continue
            if prods < op.product_min_qty:
                qty = max(op.product_min_qty, op.product_max_qty)-prods

                reste = qty % op.qty_multiple
                if reste > 0:
                    qty += op.qty_multiple - reste

                if qty <= 0:
                    continue
                if op.product_id.type not in ('consu'):
                    if op.replenish_internal_draft_ids:
                    # Check draft procurement related to this order point
                        pro_ids = [x.id for x in op.replenish_internal_draft_ids]
                        move_ids = move_obj.search(cr,uid,[('picking_id','in',pro_ids),('product_id','=',op.product_id.id)], context=context)
                        procure_datas = move_obj.read(
                            cr, uid, move_ids, ['id', 'product_qty'], context=context)
                        to_generate = qty
                        for proc_data in procure_datas:
                            if to_generate >= proc_data['product_qty']:
#                                    self.signal_button_confirm(cr, uid, [proc_data['id']])
                                move_obj.write(cr, uid, [proc_data['id']],  {'origin': op.name}, context=context)
                                to_generate -= proc_data['product_qty']
                            if not to_generate:
                                break
                        qty = to_generate

                if qty:
                    replenish_id = stock_obj.create(cr, uid,
                                                     self._prepare_orderpoint_procurement(cr, uid, op, context=context),
                                                     context=context)
                    #Prepare stock move
                    source = op.warehouse_id.lot_stock_id.id
                    self._prepare_stock_move(cr,uid,ids,op,qty,replenish_id,source,context=context)
#                        self.signal_button_confirm(cr, uid, [proc_id])
#                        self.signal_button_check(cr, uid, [proc_id])
                    orderpoint_obj.write(cr, uid, [op.id],
                            {'replenish_internal_id': replenish_id}, context=context)
            offset += len(ids)
            if use_new_cursor:
                cr.commit()
        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}

stock_warehouse_replenish()


