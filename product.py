#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
#! -*- coding: utf8 -*-
from trytond.pool import *
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval
from trytond.pyson import Id
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from decimal import Decimal

__all__ = ['Template', 'ListByProduct']
__metaclass__ = PoolMeta

STATES = {
    'readonly': ~Eval('active', True),
    }
DEPENDS = ['active']

class Template:
    __name__ = 'product.template'

    listas_precios = fields.One2Many('product.list_by_product', 'template', 'Listas de precio',
        states=STATES,depends=DEPENDS)

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__

class ListByProduct(ModelSQL, ModelView):
    "Product Variant"
    __name__ = "product.list_by_product"
    _order_name = 'rec_name'
    template = fields.Many2One('product.template', 'Product Template',
        required=True, ondelete='CASCADE', select=True, states=STATES,
        depends=DEPENDS)
    lista_precio = fields.Many2One('product.price_list', 'Product Template',
        required=True, ondelete='CASCADE', select=True, states=STATES,
        depends=DEPENDS)
    fijo = fields.Numeric('Valor fijo', digits=(16, 2))
    con_iva = fields.Boolean('Calcular precio inc. IVA')
    incluir_barra = fields.Boolean('Utilizar en Impresion de Codigo de Barra')

    @fields.depends('_parent_template.cost_price', 'lista_precio', 'fijo', 'con_iva')
    def on_change_lista_precio(self):
        pool = Pool()
        res= {}
        percentage = 0
        if self.lista_precio:
            if self.lista_precio.lines:
                for line in self.lista_precio.lines:
                    if line.percentage > 0:
                        percentage = line.percentage/100
            precio_final = self.template.cost_price * (1 + percentage)
            res['fijo'] = precio_final
        return res

    @fields.depends('_parent_template.cost_price', 'lista_precio', 'fijo', 'con_iva', '_parent_template.taxes_category'
        '_parent_template.category')
    def on_change_con_iva(self):
        pool = Pool()
        Taxes1 = pool.get('product.category-customer-account.tax')
        Taxes2 = pool.get('product.template-customer-account.tax')
        iva = Decimal(0.0)
        res= {}
        if self.lista_precio:
            if self.fijo:
                if self.con_iva == True:
                    if self.template.taxes_category == True:
                        if self.template.category.taxes_parent == True:
                            taxes1= Taxes1.search([('category','=', self.template.category.parent)])
                            taxes2 = Taxes2.search([('product','=', self.template)])
                        else:
                            taxes1= Taxes1.search([('category','=', self.template.category)])
                            taxes2 = Taxes2.search([('product','=', self.template)])
                    else:
                        taxes1= Taxes1.search([('category','=',self.template.category)])
                        taxes2 = Taxes2.search([('product','=', self.template)])

                    if taxes1:
                        for t in taxes1:
                            iva = self.fijo * t.tax.rate
                    elif taxes2:
                        for t in taxes2:
                            iva = self.fijo * t.tax.rate
                    elif taxes3:
                        for t in taxes3:
                            iva = self.fijo * t.tax.rate
                    precio_total = self.fijo + iva
                    res['fijo'] = precio_total

                if self.con_iva == False:
                    if self.template.taxes_category == True:
                        if self.template.category.taxes_parent == True:
                            taxes1= Taxes1.search([('category','=', self.template.category.parent)])
                            taxes2 = Taxes2.search([('product','=', self.template)])
                        else:
                            taxes1= Taxes1.search([('category','=', self.template.category)])
                            taxes2 = Taxes2.search([('product','=', self.template)])
                    else:
                        taxes1= Taxes1.search([('category','=',self.template.category)])
                        taxes2 = Taxes2.search([('product','=', self.template)])

                    if taxes1:
                        for t in taxes1:
                            iva = self.fijo * t.tax.rate
                    elif taxes2:
                        for t in taxes2:
                            iva = self.fijo * t.tax.rate
                    elif taxes3:
                        for t in taxes3:
                            iva = self.fijo * t.tax.rate
                    precio_total = self.fijo - iva
                    res['fijo'] = precio_total
        return res
