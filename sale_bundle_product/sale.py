from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit = "sale.order"
        
    def add_a_new_line(self, cr, uid, ids, context=None):
        ir_model_data_obj = self.pool.get('ir.model.data')
        ir_model_data_id = ir_model_data_obj.search(cr, uid, [['model', '=', 'ir.ui.view'], ['name', '=', 'view_order_line_form']], context=context)
        if ir_model_data_id:
            res_id = ir_model_data_obj.read(cr, uid, ir_model_data_id, fields=['res_id'])[0]['res_id']        
        sale_order = self.browse(cr, uid, ids[0], context=context)
        ctx = {
            'order_id': ids and ids[0],
            'partner_id': sale_order.partner_id.id,
            'pricelist': sale_order.pricelist_id.id,
            'shop': sale_order.shop_id.id,
            'date_order': sale_order.date_order,
            'fiscal_position': sale_order.fiscal_position.id,
        }
        return {
            'name': 'Sale Order Line',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'sale.order.line',
            'context': ctx,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
sale_order()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"


#    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
#        tax_obj = self.pool.get('account.tax')
#        cur_obj = self.pool.get('res.currency')
#        res = {}
#
#        if context is None:
#            context = {}
#        for line in self.browse(cr, uid, ids, context=context):
#            if line.product_id.product_type in ('bundle') and line.from_magento==False:
#                cr.execute("select so_item_set_id from so_line_so_item_set_rel where sale_order_line_id=%s",(line.id,))
#                itemset_ids = map(lambda x: x[0], cr.fetchall() or [])
#                print "produc_ids",itemset_ids
#                amount=0.0
#                for item in itemset_ids:
#                    cr.execute("select pt.list_price*so.qty_uom \
#                    from product_product p, product_template pt,sale_order_line_item_set so \
#                    where so.product_id=p.id and p.product_tmpl_id=pt.id and so.id=%s",(item,))
#                    sub_total=cr.fetchone()
#                    print sub_total
#                    if sub_total:
#                        amount+=sub_total[0]
#                price = amount * (1 - (line.discount or 0.0) / 100.0)
#            else:
#                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#            if line.order_id:
#                taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
#                cur = line.order_id.pricelist_id.currency_id
#            else:
#                taxes = {}
#                taxes['total'] = 0.0
#                cur = line.so_id.pricelist_id.currency_id
#            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
#        return res


    def _transform_one_resource(self, cr, uid, external_session, convertion_type, resource, mapping, mapping_id,
                     mapping_line_filter_ids=None, parent_data=None, previous_result=None, defaults=None, context=None):
        if not context: context={}
        print resource,"resource"
        line = super(sale_order_line, self)._transform_one_resource(cr, uid, external_session, convertion_type, resource,
                            mapping, mapping_id, mapping_line_filter_ids=mapping_line_filter_ids, parent_data=parent_data,
                            previous_result=previous_result, defaults=defaults, context=context)
        #these code is added to reflect bundle option on order line
        if resource.get('bundle_configuration',False):
            context['bundle_configuration'] = resource.get('bundle_configuration',False)
            budle_items=self.get_bunlde_products_line(cr, uid,external_session,resource,context=context)
            print "budle_items",budle_items
            if budle_items:
                line.update({'so_line_item_set_ids': [(6, 0, budle_items)]})
                
        line.update({'from_magento':True})# this field is added to not compute subtotal for order line by _amount_line function
        if context.get('is_tax_included') and 'price_unit_tax_included' in line:
            line['price_unit'] = line['price_unit_tax_included']
        elif 'price_unit_tax_excluded' in line:
            line['price_unit']  = line['price_unit_tax_excluded']

        line = self.play_sale_order_line_onchange(cr, uid, line, parent_data, previous_result, defaults, context=context)
	print "line",line
        context['bundle_configuration'] = False ##set to False so it will not affect other sale order lines
        if context.get('use_external_tax'):
            if line.get('tax_rate'):
                line_tax_id = self.pool.get('account.tax').get_tax_from_rate(cr, uid, line['tax_rate'], context.get('is_tax_included', False), context=context)
                if not line_tax_id:
                    line_tax_id = self.pool.get('account.tax').create(cr,uid,{
                        'name':'Tax '+ str(line['tax_rate']) ,
                        'amount':line['tax_rate'],
                        'active':True,
                        'type':'percent'
                        })
#                    raise osv.except_osv(_('Error'), _('No tax id found for the rate %s with the tax include = %s')%(line['tax_rate'], context.get('is_tax_included')))
                line['tax_id'] = [(6, 0, [line_tax_id])]

        return line

    def get_bunlde_products_line(self, cr, uid, external_session, resource,context=None):
        sale_item_line_obj = self.pool.get('sale.order.line.item.set')
        product_obj=self.pool.get('product.product')
        res=[]
        print "resource",resource
        print "BUNDLE CONF",resource['bundle_configuration']
        for config in resource['bundle_configuration']:
            print "config",config
            oe_product_id=product_obj.get_oeid(cr, uid, config['product_id'], external_session.referential_id.id, context)
            qty_ordered=config['qty_ordered']
            if oe_product_id:
                uos_id=product_obj.browse(cr,uid,oe_product_id).product_tmpl_id.uom_id.id
                sale_item_ids = sale_item_line_obj.search(cr, uid, [['product_id', '=', oe_product_id], ['qty_uom', '=', qty_ordered], ['uom_id', '=', uos_id]], context=context)
                if sale_item_ids:
                    res.append(sale_item_ids[0])
                else:
                    res.append(sale_item_line_obj.create(cr, uid, {'product_id': oe_product_id, 'qty_uom': qty_ordered, 'uom_id': uos_id}, context=context))
        return res
    
    def product_change(self,cr,uid,ids,product_id,qty,uom,qty_uos,uos,packaging,flag,context):
        product_obj = self.pool.get('product.product')
        product_uom_obj = self.pool.get('product.uom')
        order_item_line_obj=self.pool.get('sale.order.line.item.set')
        update_tax,warning,result,domain = True,{},{},{}
        if product_id:
           product_obj = product_obj.browse(cr,uid,product_id)
           print "product_obj",product_obj
           res = self.product_packaging_change(cr, uid, ids, context.get('pricelist',False), product_id, qty, uom, context.get('partner_id',False), packaging, context=context)
           result = res.get('value', {})
           warning_msgs = res.get('warning') and res['warning']['message'] or ''
           uom2 = False
#           if product_obj.product_type=='bundle':
#               template_id=product_obj.product_tmpl_id.id
#               print "template_id",template_id
#               cr.execute("select product_item_set_id from product_template_item_set_rel where product_template_id=%s",(template_id,))
##               cr.fetchall()
#               item_line=[]
#               itemset_ids = map(lambda x: x[0], cr.fetchall() or [])
#               for item in itemset_ids:
#                   cr.execute("select product_id,uom_id,qty_uom from product_item_set_line where item_set_id=%s and is_default=True",(item,))
#                   item_set_line=cr.fetchone()
#                   print "item_set_line",item_set_line
#                   if item_set_line:
#                       sale_item_ids = order_item_line_obj.search(cr, uid, [['product_id', '=', item_set_line[0]], ['qty_uom', '=', item_set_line[2]], ['uom_id', '=', item_set_line[1]]], context=context)
#                       if sale_item_ids:
#                           item_line.append(sale_item_ids[0])
#                       else:
#                           item_line.append(order_item_line_obj.create(cr, uid, {'product_id': item_set_line[1], 'qty_uom': item_set_line[2], 'uom_id': item_set_line[1]}, context=context))
#               if len(item_line)!=0:
#                    result['so_line_item_set_ids']=[(6,0,item_line)]
           if uom:
                uom2 = product_uom_obj.browse(cr, uid, uom)
                if product_obj.uom_id.category_id.id != uom2.category_id.id:
                    uom = False
           if uos:
                if product_obj.uos_id:
                    uos2 = product_uom_obj.browse(cr, uid, uos)
                    if product_obj.uos_id.category_id.id != uos2.category_id.id:
                        uos = False
                else:
                    uos = False
           if product_obj.description_sale:
                result['notes'] = product_obj.description_sale
           fpos = context.get('fiscal_position',False) and self.pool.get('account.fiscal.position').browse(cr, uid, context.get('fiscal_position',False)) or False
           if update_tax: #The quantity only have changed
            result['delay'] = (product_obj.sale_delay or 0.0)
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)
            result.update({'type': product_obj.procure_method})
           if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context)[0][1]
           if (not uom) and (not uos):
                result['product_uom'] = product_obj.uom_id.id
                if product_obj.uos_id:
                    result['product_uos'] = product_obj.uos_id.id
                    result['product_uos_qty'] = qty * product_obj.uos_coeff
                    uos_category_id = product_obj.uos_id.category_id.id
                else:
                    result['product_uos'] = False
                    result['product_uos_qty'] = qty
                    uos_category_id = False
                result['th_weight'] = qty * product_obj.weight
                domain = {'product_uom':
                            [('category_id', '=', product_obj.uom_id.category_id.id)],
                            'product_uos':
                            [('category_id', '=', uos_category_id)]}

           elif uos and not uom: # only happens if uom is False
                result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
                result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
                result['th_weight'] = result['product_uom_qty'] * product_obj.weight
           elif uom: # whether uos is set or not
                default_uom = product_obj.uom_id and product_obj.uom_id.id
                q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
                if product_obj.uos_id:
                    result['product_uos'] = product_obj.uos_id.id
                    result['product_uos_qty'] = qty * product_obj.uos_coeff
                else:
                    result['product_uos'] = False
                    result['product_uos_qty'] = qty
                result['th_weight'] = q * product_obj.weight        # Round the quantity up
           if not uom2:
                uom2 = product_obj.uom_id
           compare_qty = float_compare(product_obj.virtual_available * uom2.factor, qty * product_obj.uom_id.factor, precision_rounding=product_obj.uom_id.rounding)
           if (product_obj.type=='product') and int(compare_qty) == -1 \
              and (product_obj.procure_method=='make_to_stock'):
                warn_msg = _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') % \
                        (qty, uom2 and uom2.name or product_obj.uom_id.name,
                         max(0,product_obj.virtual_available), product_obj.uom_id.name,
                         max(0,product_obj.qty_available), product_obj.uom_id.name)
                warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"
           if not context.get('pricelist',False):
                warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                        'Please set one before choosing a product.')
                warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
           else:
                price = self.pool.get('product.pricelist').price_get(cr, uid, [context.get('pricelist',False)],
                        product_id, qty or 1.0, context.get('partner_id',False), {
                            'uom': uom or result.get('product_uom'),
                            'date': context.get('date_order',False),
                            })[context.get('pricelist',False)]
                if price is False:
                    warn_msg = _("Couldn't find a pricelist line matching this product and quantity.\n"
                            "You have to change either the product, the quantity or the pricelist.")

                    warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
                else:
                    result.update({'price_unit': price})
           if warning_msgs:
                warning = {
                           'title': _('Configuration Error !'),
                           'message' : warning_msgs
                        }
        return {'value': result, 'domain': domain, 'warning': warning}
    
    def save_and_close(self, cr, uid, ids, context):
        return {}
    
    def save_and_continue(self, cr, uid, ids, context):
        res = self.pool.get('sale.order').add_a_new_line(cr, uid, [context['order_id']], context=None)
        res['nodestroy']=False
        return res
    
    def create(self, cr, uid, vals, context=None):
        if not context:
            context={}
        if context.get('order_id', False):
            vals['order_id']= context['order_id']
        res = super(sale_order_line, self).create(cr, uid, vals, context=context)
        if context.get('order_id', False):
            context['create_sale_order_line_id']=res
        return res
    
    def action_configure_product(self, cr, uid, ids, context=None):
        if not ids:
            return False
        if not context:
            context = {}
        return {
            'name': 'Product Configuration',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.item.set.configurator',
            'context': "{'order_line_id': %s}"%(ids[0]),
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        } 
    _columns = {
#        'so_line_item_set_ids':fields.many2many('sale.order.line.item.set', 'so_line_so_item_set_rel','sale_order_line_id', 'so_item_set_id','Choosen configurtion'), cox gen2
#        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Sale Price')),
        'from_magento':fields.boolean('Order Line from Magento'),
    }
    _defauls={
    'from_magento':False
    }
sale_order_line()

