import model
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class RuntimeProduct:

    def __init__(self, product, amount):
        self.ddl: datetime = datetime.today()
        self.start: datetime = datetime.today()
        self.delay = datetime.today()
        self.product: model.Product = product
        self.amount: int = amount

    def set_ddl_start(self, ddl: datetime, start: datetime):
        self.ddl = ddl
        self.start = start

    def set_delay(self, processes_pdt_times):
        self.delay = self.ddl - timedelta(minutes=processes_pdt_times)


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


class RuntimeResourceNeed:

    def __int__(self,
                process: model.Process,
                resource_attr: str,
                workspace: str,
                start: datetime, end: datetime):
        if start < end:
            raise RuntimeError("the start time must before the end time")

        self.process: model.Process = process
        self.resource_attr: str = resource_attr
        self.workspace: str = workspace
        self.start: datetime = start
        self.end: datetime = end


class RuntimeResource:

    def __init__(self, resource: model.Resource):
        self.resource: model.Resource = resource
        self.workspace: str = self.resource.workspace
        self.basic_attr = self.resource.basic_attr
        self.resource_attrs = self.resource.attrs
        self.schedules: List[RuntimeResourceNeed] = []

    def add_schedule(self, schedule: RuntimeResourceNeed) -> bool:

        pre_need: Optional[RuntimeResourceNeed] = None
        back_need: Optional[RuntimeResourceNeed] = None

        for resource_need in self.schedules:
            if resource_need.end > schedule.start:
                pre_need = resource_need
            if back_need is not None \
                    and resource_need.start < resource_need.end:
                back_need = resource_need

        if pre_need is not None or back_need is not None:
            return False
        else:
            self.schedules.append(schedule)
            self.schedules = sorted(self.schedules, key=lambda need: need.start)
            return True


class RuntimeResourcePool:

    def __init__(self, resources: List[model.Resource]):
        self.pool: List[RuntimeResource] = []

        for resource in resources:
            runtime_resource = RuntimeResource(resource)
            self.pool.append(runtime_resource)

    def alloc_resource(self, resource_need: RuntimeResourceNeed) -> bool:
        # 精确搜索
        for runtime_resource in self.pool:
            if runtime_resource.basic_attr == resource_need.resource_attr:
                if runtime_resource.add_schedule(resource_need) is True:
                    return True
        # 放宽条件搜索
        for runtime_resource in self.pool:
            if resource_need.resource_attr in runtime_resource.resource_attrs:
                if runtime_resource.add_schedule(resource_need) is True:
                    return True

        return False
