from trytond.pool import Pool
from .product import *
from .price_list import *

def register():
    Pool.register(
        Template,
        ListByProduct,
        PriceList,
        PriceListLine,
        UpdateListByProduct,
        UpdatePriceListByProduct,
        module='nodux_product_price_list_by_product', type_='model')
    Pool.register(
        WizardListByProduct,
        WizardPriceListByProduct,
        module='nodux_product_price_list_by_product', type_='wizard')
