import model
from datetime import datetime, timedelta
from typing import List, Dict


class RuntimeProduct:

    def __init__(self, product, amount):
        self.ddl: datetime = datetime.today()
        self.start: datetime = datetime.today()
        self.product: model.Product = product
        self.amount: int = amount

    def set_ddl_start(self, ddl: datetime, start: datetime):
        self.ddl = ddl
        self.start = start


class ProductLine:

    def __init__(self, product: model.Product):
        self.product: product = product
        self.runtime_products: List[RuntimeProduct] = []

    def add_runtime_product(self, runtime_product: RuntimeProduct):
        self.runtime_products.append(runtime_product)


class RuntimeProductLines:

    def __init__(self):
        self.product_lines: Dict[str, ProductLine] = {}
        self.product_lines_list: List[ProductLine] = []

    def add_runtime_product(self, runtime_product: RuntimeProduct):

        if runtime_product.product.product_id not in self.product_lines.keys():
            self.product_lines[runtime_product.product.product_id] = ProductLine(runtime_product.product)
            self.product_lines_list = list(self.product_lines.values())

        self.product_lines[runtime_product.product.product_id].add_runtime_product(runtime_product)

    def pop_runtime_product(self):
        if self.product_lines_list is None:
            return None

        earliest_end_time_runtime_product_line = self.product_lines_list[0]

        earliest_end_time_runtime_product = None
        if len(earliest_end_time_runtime_product_line.runtime_products) > 0:
            earliest_end_time_runtime_product = earliest_end_time_runtime_product_line.runtime_products[0]

        for product_line in self.product_lines_list:
            if len(product_line.runtime_products) > 0:
                runtime_product = product_line.runtime_products[0]
                if earliest_end_time_runtime_product is None \
                        or runtime_product.ddl < earliest_end_time_runtime_product.ddl:
                    earliest_end_time_runtime_product = runtime_product
                    earliest_end_time_runtime_product_line = product_line

        if len(earliest_end_time_runtime_product_line.runtime_products) > 0:
            earliest_end_time_runtime_product_line.runtime_products.pop(0)

        return earliest_end_time_runtime_product

    def reset(self):
        self.product_lines_list = list(self.product_lines)


class RuntimeProcess:

    def __init__(self, runtime_product: RuntimeProduct, process: model.Process):
        self.runtime_product = runtime_product
        self.process = process
        self.ddl = runtime_product.ddl
        self.delay = self.runtime_product.ddl - timedelta(minutes=process.pdt_time)
