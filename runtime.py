import model
from datetime import datetime, timedelta
from typing import List


class RuntimeProduct:

    def __init__(self, product, amount):
        self.ddl: datetime = datetime.today()
        self.product: model.Product = product
        self.amount: int = amount

    def set_ddl(self, ddl: datetime):
        self.ddl = ddl
        pass


class ProductLine:

    def __init__(self, product: model.Product):
        self.product: product = product
        self.runtime_products: List[RuntimeProduct] = []

    def add_runtime_product(self, runtime_product: RuntimeProduct):
        self.runtime_products.append(runtime_product)


class RuntimeProcess:

    def __init__(self, runtime_product: RuntimeProduct, process: model.Process):
        self.runtime_product = runtime_product
        self.process = process
        self.start_ddl = self.runtime_product.ddl - timedelta(minutes=process.pdt_time)
