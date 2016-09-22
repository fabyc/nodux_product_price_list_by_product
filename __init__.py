#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from .product import *
from .price_list import *

def register():
    Pool.register(
        Template,
        ListByProduct,
        PriceList,
        UpdateListByProduct,
        UpdatePriceListByProduct,
        module='nodux_product_price_list_by_product', type_='model')
    Pool.register(
        WizardListByProduct,
        WizardPriceListByProduct,
        module='nodux_product_price_list_by_product', type_='wizard')
