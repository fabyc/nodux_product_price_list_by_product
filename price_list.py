#! -*- coding: utf8 -*-

#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

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
try:
    import bcrypt
except ImportError:
    bcrypt = None
import random
import hashlib
import string

__all__ = ['PriceList', 'UpdateListByProduct', 'WizardListByProduct', 'PriceListLine']
__metaclass__ = PoolMeta

class PriceList():
    'Price List'
    __name__ = 'product.price_list'

    incluir_lista = fields.Boolean('Incluir lista de precio en producto', states={
        'readonly': (Eval('definir_precio_venta', True)) | (Eval('definir_precio_tarjeta', True))
    })

    definir_precio_venta = fields.Boolean('Definir como precio de venta', help="Definir como precio de venta principal")

    definir_precio_tarjeta = fields.Boolean('Precio tarjeta de credito', help="Definir como precio de tarjeta de credito")

    @classmethod
    def __setup__(cls):
        super(PriceList, cls).__setup__()

    @fields.depends('incluir_lista', 'definir_precio_venta')
    def on_change_definir_precio_venta(self):
        res = {}
        if self.definir_precio_venta == True:
            res['incluir_lista'] = True
        else:
            if self.incluir_lista:
                res['incluir_lista'] = self.incluir_lista
            else:
                res['incluir_lista'] = False
        return res

    @fields.depends('incluir_lista', 'definir_precio_tarjeta')
    def on_change_definir_precio_tarjeta(self):
        res = {}
        if self.definir_precio_tarjeta == True:
            res['incluir_lista'] = True
        else:
            if self.incluir_lista:
                res['incluir_lista'] = self.incluir_lista
            else:
                res['incluir_lista'] = False
        return res

    @classmethod
    def validate(cls, price_lists):
        for price_list in price_lists:
            for price_list in price_lists:
                super(PriceList, cls).validate(price_lists)

    def pre_validate(self):
        pool = Pool()
        User = pool.get('res.user')
        Product = pool.get('product.template')
        Variante = pool.get('product.product')

        def in_group():
            pool = Pool()
            ModelData = pool.get('ir.model.data')
            User = pool.get('res.user')
            Group = pool.get('res.group')
            origin = str(self)
            user = User(Transaction().user)

            group = Group(ModelData.get_id('nodux_product_price_list_by_product',
                    'group_update_price_force'))
            transaction = Transaction()
            user_id = transaction.user
            if user_id == 0:
                user_id = transaction.context.get('user', user_id)
            if user_id == 0:
                return True
            user = User(user_id)
            return origin and group in user.groups

        if not in_group():
            self.raise_user_error("No esta autorizado a cambiar/crear una lista de precio")

class PriceListLine():
    'Price List Line'
    __name__ = 'product.price_list.line'

    new_formula = fields.Char('Formula', readonly = True)
    use_new_formula = fields.Boolean('Utilizar formula')

    @classmethod
    def __setup__(cls):
        super(PriceListLine, cls).__setup__()

    @staticmethod
    def default_new_formula():
        return 'costo/(1-%)'

    @fields.depends('percentage', 'formula', '_parent_price_list.definir_precio_tarjeta')
    def on_change_percentage(self):
        pool = Pool()
        res= {}
        if self.percentage:
            if self.percentage > 0:
                percentage = self.percentage/100
                p = str(percentage)
                if self.price_list.definir_precio_tarjeta == True:
                    formula = 'product.list_price * (1 + ' +p+')'
                else:
                    formula = 'product.cost_price * (1 + ' +p+')'
                res['formula'] = formula
            else:
                res['formula'] = ""
        else:
            res['formula'] = ""
        return res

    @fields.depends('percentage', 'formula', 'new_formula', 'use_new_formula',
        '_parent_price_list.definir_precio_tarjeta')
    def on_change_use_new_formula(self):
        pool = Pool()
        res= {}
        p = '0'
        if self.percentage > 0:
            percentage = self.percentage/100
            p = str(percentage)
        if self.use_new_formula:
            if self.use_new_formula == True:
                if self.price_list.definir_precio_tarjeta == True:
                    formula = 'product.list_price / (1 - ' +p+')'
                else:
                    formula = 'product.cost_price / (1 - ' +p+')'
                res['formula'] = formula
            else:
                if self.price_list.definir_precio_tarjeta == True:
                    formula = 'product.list_price * (1 + ' +p+')'
                else:
                    formula = 'product.cost_price * (1 +' +p+')'
                res['formula'] = formula
        else:
            if self.price_list.definir_precio_tarjeta == True:
                formula = 'product.list_price * (1 + '+p+')'
            else:
                formula = 'product.cost_price * (1 +' +p+')'
            res['formula'] = formula
        return res

class UpdateListByProduct(ModelView):
    'Update List By Product'
    __name__ = 'nodux_product_price_list_by_product.update.start'

    password = fields.Char('Password', required=True, size=20)
    user = fields.Char('Usuario', required=True, readonly=True)

    def hash_password(self, password):
        if not password:
            return ''
        return getattr(self, 'hash_' + self.hash_method())(password)

    @staticmethod
    def hash_method():
        return 'bcrypt' if bcrypt else 'sha1'

    @classmethod
    def hash_sha1(cls, password):
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        salt = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        hash_ = hashlib.sha1(password + salt).hexdigest()
        return '$'.join(['sha1', hash_, salt])

    def check_password(self, password, hash_):
        if not hash_:
            return False
        hash_method = hash_.split('$', 1)[0]
        return getattr(self, 'check_' + hash_method)(password, hash_)

    @classmethod
    def check_sha1(cls, password, hash_):
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        if isinstance(hash_, unicode):
            hash_ = hash_.encode('utf-8')
        hash_method, hash_, salt = hash_.split('$', 2)
        salt = salt or ''
        assert hash_method == 'sha1'
        return hash_ == hashlib.sha1(password + salt).hexdigest()

    @classmethod
    def hash_bcrypt(cls, password):
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        hash_ = bcrypt.hashpw(password, bcrypt.gensalt())
        return '$'.join(['bcrypt', hash_])

    @classmethod
    def check_bcrypt(cls, password, hash_):
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        if isinstance(hash_, unicode):
            hash_ = hash_.encode('utf-8')
        hash_method, hash_ = hash_.split('$', 1)
        assert hash_method == 'bcrypt'
        return hash_ == bcrypt.hashpw(password, hash_)

    @fields.depends('password')
    def on_change_password(self):
        res = {}
        User = Pool().get('res.user')
        user = None
        value = False
        if self.password:
            users = User.search([('password_hash', '!=', None)])
            if users:
                for u in users:
                    value = self.check_password(self.password, u.password_hash)
                    if value == True:
                        res['user'] = u.name
                        break
                if value == False:
                    self.raise_user_error(u'Contraseña no valida')
        return res

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
        Taxes1 = pool.get('product.category-customer-account.tax')
        Taxes2 = pool.get('product.template-customer-account.tax')
        ListByProduct = pool.get('product.list_by_product')
        PriceList = pool.get('product.price_list')
        priceslists = PriceList.browse(Transaction().context['active_ids'])
        pls = PriceList(Transaction().context['active_id'])
        user =  User(Transaction().user)
        incluido = False
        lineas = None

        def in_group():
            pool = Pool()
            ModelData = pool.get('ir.model.data')
            User = pool.get('res.user')
            Group = pool.get('res.group')
            origin = str(pls)
            user = User(Transaction().user)

            group = Group(ModelData.get_id('nodux_product_price_list_by_product',
                    'group_update_price_force'))
            transaction = Transaction()
            user_id = transaction.user
            if user_id == 0:
                user_id = transaction.context.get('user', user_id)
            if user_id == 0:
                return True
            user = User(user_id)
            return origin and group in user.groups

        if not in_group():
            self.raise_user_error("No esta autorizado a agregar las listas de precio en todos los productos")

        lineas = []

        for pricelist in priceslists:
            if pricelist.incluir_lista == False:
                pass
            elif pricelist.incluir_lista == True:
                products = Product.search([('id', '>', 0)])

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
                                if line.percentage:
                                    if line.percentage > 0:
                                        percentage = line.percentage/100
                                    if line.use_new_formula == True:
                                        if line.price_list.definir_precio_tarjeta == True:
                                            precio_final = p.list_price / (1 - percentage)
                                        else:
                                            precio_final = p.cost_price / (1 - percentage)
                                    else:
                                        if line.price_list.definir_precio_tarjeta == True:
                                            precio_final = p.list_price * (1 + percentage)
                                        else:
                                            precio_final = p.cost_price * (1 + percentage)
                                else:
                                    self.raise_user_error('No ha definido el porcentaje, modifique la lista de precio')
                                if user.company.currency:
                                    precio_final = user.company.currency.round(precio_final)

                            if p.taxes_category == True:
                                if p.category.taxes_parent == True:
                                    taxes1= Taxes1.search([('category','=', p.category.parent)])
                                    taxes2 = Taxes2.search([('product','=', p)])
                                else:
                                    taxes1= Taxes1.search([('category','=', p.category)])
                            else:
                                taxes1= Taxes1.search([('category','=', p.category)])
                                taxes2 = Taxes2.search([('product','=', p)])

                            if taxes1:
                                for t in taxes1:
                                    iva = precio_final * t.tax.rate
                            elif taxes2:
                                for t in taxes2:
                                    iva = precio_final * t.tax.rate

                            precio_total = precio_final + iva

                            if pricelist.definir_precio_venta == True:
                                p.list_price = precio_final
                                p.list_price_with_tax = precio_total
                                p.save()

                            lineas.append({
                                'template': p.id,
                                'lista_precio': pricelist.id,
                                'fijo' : precio_final,
                                'fijo_con_iva': precio_total,
                                'precio_venta': pricelist.definir_precio_venta,
                                'product': variante.id
                            })

                    else:
                        for line in pricelist.lines:
                            if line.percentage:
                                if line.percentage > 0:
                                    percentage = line.percentage/100
                                if line.use_new_formula == True:
                                    if line.price_list.definir_precio_tarjeta == True:
                                        precio_final = p.list_price / (1 - percentage)
                                    else:
                                        precio_final = p.cost_price / (1 - percentage)
                                else:
                                    if line.price_list.definir_precio_tarjeta == True:
                                        precio_final = p.list_price * (1 + percentage)
                                    else:
                                        precio_final = p.cost_price * (1 + percentage)
                            else:
                                self.raise_user_error('Debe asignar el porcentaje de ganancia en la lista de precio')
                            if user.company.currency:
                                precio_final = user.company.currency.round(precio_final)

                        if p.taxes_category == True:
                            if p.category.taxes_parent == True:
                                taxes1= Taxes1.search([('category','=', p.category.parent)])
                                taxes2 = Taxes2.search([('product','=', p)])
                            else:
                                taxes1= Taxes1.search([('category','=', p.category)])
                        else:
                            taxes1= Taxes1.search([('category','=', p.category)])
                            taxes2 = Taxes2.search([('product','=', p)])

                        if taxes1:
                            for t in taxes1:
                                iva = precio_final * t.tax.rate
                        elif taxes2:
                            for t in taxes2:
                                iva = precio_final * t.tax.rate

                        precio_total = precio_final + iva

                        if pricelist.definir_precio_venta == True:
                            p.list_price = precio_final
                            p.list_price_with_tax = precio_total
                            p.save()

                        lineas.append({
                            'template': p.id,
                            'lista_precio': pricelist.id,
                            'fijo' : precio_final,
                            'fijo_con_iva': precio_total,
                            'precio_venta': pricelist.definir_precio_venta,
                            'product' : variante.id
                        })
        listas_precios = ListByProduct.create(lineas)
        return 'end'
