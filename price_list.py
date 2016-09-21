#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
#! -*- coding: utf8 -*-
from trytond.pool import *
from trytond.report import Report
from trytond.transaction import Transaction
from trytond.modules.company import CompanyReport
from trytond.pool import Pool
from decimal import Decimal
from trytond.model import ModelSQL, Workflow, fields, ModelView
from trytond.pyson import Bool, Eval, Or, If, Id
from trytond.wizard import (Wizard, StateView, StateAction, StateTransition,
    Button)

__all__ = ['PriceList', 'UpdateListByProduct', 'WizardListByProduct']
__metaclass__ = PoolMeta

class PriceList():
    'Price List'
    __name__ = 'product.price_list'

    incluir_lista = fields.Boolean('Incluir lista de precio en producto')
    definir_precio_venta = fields.Boolean('Definir como precio de venta', help="Definir como precio de venta principal")

    @classmethod
    def __setup__(cls):
        super(PriceList, cls).__setup__()

class UpdateListByProduct(ModelView):
    'Update List By Product'
    __name__ = 'nodux_product_price_list_by_product.update.start'


class WizardListByProduct(Wizard):
    'Wizard List By Product'
    __name__ = 'nodux_product_price_list_by_product.update'

    start = StateView('nodux_product_price_list_by_product.update.start',
        'nodux_product_price_list_by_product.update_list_start_view_form', [
        Button('Cancel', 'end', 'tryton-cancel'),
        Button('Ok', 'accept', 'tryton-ok', default=True),
        ])
    accept = StateTransition()

    def transition_accept(self):
        pool = Pool()
        User = pool.get('res.user')
        Product = pool.get('product.template')
        Variante = pool.get('product.product')

        ListByProduct = pool.get('product.list_by_product')
        PriceList = pool.get('product.price_list')
        priceslists = PriceList.browse(Transaction().context['active_ids'])
        user =  User(Transaction().user)
        incluido = False
        for pricelist in priceslists:
            if pricelist.incluir_lista == False:
                pass
            elif pricelist.incluir_lista == True:
                products = Product.search([('cost_price', '>', Decimal(0.0))])
                lineas = []
                for p in products:
                    variantes = Variante.search([('template', '=', p.id)])
                    for v in variantes:
                        variante = v
                    if p.listas_precios:
                        for listas in p.listas_precios:
                            if pricelist == listas.lista_precio:
                                incluido = True
                                break
                        if incluido == True:
                            pass
                        else:
                            for line in pricelist.lines:
                                if line.percentage > 0:
                                    percentage = line.percentage/100
                                precio_final = p.cost_price * (1 + percentage)
                                if user.company.currency:
                                    precio_final = user.company.currency.round(precio_final)

                            if pricelist.definir_precio_venta == True:
                                p.list_price = precio_final
                                p.save()

                            lineas.append({
                                'template': p.id,
                                'lista_precio': pricelist.id,
                                'fijo' : precio_final,
                                'precio_venta': pricelist.definir_precio_venta,
                                'product': variante.id
                            })

                    else:
                        for line in pricelist.lines:
                            if line.percentage > 0:
                                percentage = line.percentage/100
                            precio_final = p.cost_price * (1 + percentage)
                            if user.company.currency:
                                precio_final = user.company.currency.round(precio_final)
                                
                        if pricelist.definir_precio_venta == True:
                            p.list_price = precio_final
                            p.save()

                        lineas.append({
                            'template': p.id,
                            'lista_precio': pricelist.id,
                            'fijo' : precio_final,
                            'precio_venta': pricelist.definir_precio_venta,
                            'product' : variante.id
                        })
        listas_precios = ListByProduct.create(lineas)
        return 'end'
