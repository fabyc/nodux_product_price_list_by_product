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
from trytond.wizard import (Wizard, StateView, StateAction, StateTransition,
    Button)
try:
    import bcrypt
except ImportError:
    bcrypt = None
import random
import hashlib
import string


__all__ = ['Template', 'ListByProduct', 'UpdatePriceListByProduct', 'WizardPriceListByProduct']
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

    @fields.depends('cost_price', 'listas_precios', 'id')
    def on_change_cost_price(self):
        pool = Pool()
        Product = pool.get('product.product')
        products = Product.search([('template', '=', self.id)])
        for p in products:
            product = p
        PriceList = pool.get('product.price_list')
        User = pool.get('res.user')
        priceslist = PriceList.search([('incluir_lista', '=', True)])
        res= {}
        percentage = 0
        precio_final = Decimal(0.0)
        user =  User(Transaction().user)
        if self.listas_precios:
            pass
        else:
            if self.cost_price:
                lineas = []
                for pricelist in priceslist:
                    for line in pricelist.lines:
                        if line.percentage > 0:
                            percentage = line.percentage/100
                        precio_final = self.cost_price * (1 + percentage)
                        if user.company.currency:
                            precio_final = user.company.currency.round(precio_final)
                    lineas.append({
                        'lista_precio': pricelist.id,
                        'fijo' : precio_final,
                        'precio_venta' : pricelist.definir_precio_venta,
                    })
                    if pricelist.definir_precio_venta == True:
                        precio_para_venta = precio_final
                res['listas_precios'] = lineas
                res['list_price'] = precio_para_venta
        return res

class ListByProduct(ModelSQL, ModelView):
    "List By Product"
    __name__ = "product.list_by_product"

    template = fields.Many2One('product.template', 'Product Template',
        required=True, ondelete='CASCADE', select=True, states=STATES,
        depends=DEPENDS)
    lista_precio = fields.Many2One('product.price_list', 'Lista de Precio',
        required=True, ondelete='CASCADE', select=True, states=STATES,
        depends=DEPENDS)
    fijo = fields.Numeric('Valor fijo', digits=(16, 2))
    con_iva = fields.Boolean('Calcular precio inc. IVA')
    precio_venta = fields.Boolean('Definir como precio de VENTA')
    product = fields.Many2One('product.product', 'Product Template')

    @classmethod
    def __setup__(cls):
        super(ListByProduct, cls).__setup__()

    def get_rec_name(self, lista_precio):
        return self.lista_precio.name

    @fields.depends('_parent_template.cost_price', 'lista_precio', 'fijo', 'con_iva')
    def on_change_lista_precio(self):
        pool = Pool()
        res= {}
        percentage = 0
        precio_final = Decimal(0.0)
        if self.lista_precio:
            if self.lista_precio.lines:
                for line in self.lista_precio.lines:
                    if line.percentage > 0:
                        percentage = line.percentage/100
            if self.template.cost_price:
                precio_final = self.template.cost_price * (1 + percentage)
            res['fijo'] = precio_final
        return res

    @fields.depends('_parent_template.list_price', '_parent_template.id', 'fijo', 'precio_venta')
    def on_change_precio_venta(self):
        res= {}
        if self.precio_venta == True:
            res['list_price'] = self.fijo
        return res

    @fields.depends('_parent_template.cost_price', 'lista_precio', 'fijo', 'con_iva',
        '_parent_template.category', '_parent_template.account_category', '_parent_template.taxes_category', '_parent_template.id')
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
                    else:
                        taxes1= Taxes1.search([('category','=', self.template.category)])
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
                    else:
                        taxes1= Taxes1.search([('category','=',self.template.category)])
                        taxes2 = Taxes2.search([('product','=', self.template)])

                    if taxes1:
                        for t in taxes1:
                            iva = t.tax.rate
                    elif taxes2:
                        for t in taxes2:
                            iva = t.tax.rate
                    elif taxes3:
                        for t in taxes3:
                            iva = t.tax.rate
                    precio_total = self.fijo /(1+iva)
                    res['fijo'] = precio_total
        return res

class UpdatePriceListByProduct(ModelView):
    'Update Price List By Product'
    __name__ = 'nodux_product_price_list_by_product.update_price.start'

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
                    self.raise_user_error(u'Invalid password')
        return res

class WizardPriceListByProduct(Wizard):
    'Wizard Price List By Product'
    __name__ = 'nodux_product_price_list_by_product.update_price'

    start = StateView('nodux_product_price_list_by_product.update_price.start',
        'nodux_product_price_list_by_product.update_price_list_start_view_form', [
        Button('Cancel', 'end', 'tryton-cancel'),
        Button('Ok', 'accept', 'tryton-ok', default=True),
        ])
    accept = StateTransition()

    def transition_accept(self):
        pool = Pool()
        User = pool.get('res.user')
        Product = pool.get('product.template')
        Variante = pool.get('product.product')

        products = Product.browse(Transaction().context['active_ids'])
        p = Product(Transaction().context['active_id'])
        percentage = 0
        precio_final = Decimal(0.0)
        new_list_price = Decimal(0.0)

        def in_group():
            pool = Pool()
            ModelData = pool.get('ir.model.data')
            User = pool.get('res.user')
            Group = pool.get('res.group')
            origin = str(p)
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
            self.raise_user_error("No esta autorizado a actualizar el precio de la lista de precio")

        for product in products:
            if product.listas_precios:
                for listas in product.listas_precios:
                    if listas.lista_precio.lines:
                        for line in listas.lista_precio.lines:
                            if line.percentage:
                                if line.percentage > 0:
                                    percentage = line.percentage/100
                            else:
                                self.raise_user_error('No ha definido el porcentaje de ganancia en las listas de precio')
                    if product.cost_price:
                        precio_final = product.cost_price * (1+percentage)

                    if listas.precio_venta == True:
                        new_list_price = precio_final

                    listas.fijo = precio_final
                    listas.save()
                product.list_price = new_list_price
                product.save()

        return 'end'
