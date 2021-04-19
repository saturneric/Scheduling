from __future__ import annotations
import model
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from copy import deepcopy


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


# 运行时工序
class RuntimeProcess:

    def __init__(self, runtime_product: RuntimeProduct, process: model.Process):
        self.runtime_product = runtime_product
        self.process = process
        self.ddl = runtime_product.ddl
        self.delay = self.runtime_product.ddl - timedelta(minutes=process.pdt_time)


# 运行时资源需求
class RuntimeResourceNeed:

    def __init__(self, runtime_process: RuntimeProcess, resource_attr: str, workspace: str,
                start: datetime, end: datetime):
        if start > end:
            raise RuntimeError("the start time must before the end time")

        self.process: model.Process = runtime_process.process
        self.resource_attr: str = resource_attr
        self.workspace: str = workspace
        self.start: datetime = start
        self.end: datetime = end
        self.plan_alloc_resources_id: List[str] = []
        self.could_alloc = False
        self.ddl = runtime_process.ddl

    def add_plan_alloc_resource(self, runtime_resource_id: str):
        self.plan_alloc_resources_id.append(runtime_resource_id)


# 运行时资源
class RuntimeResource:

    def __init__(self, resource: model.Resource, start_time: datetime):
        self.resource: model.Resource = resource
        self.workspace: str = self.resource.workspace
        self.basic_attr = self.resource.basic_attr
        self.resource_attrs = self.resource.attrs
        self.schedules: List[RuntimeResourceNeed] = []
        self.start_time: datetime = start_time

    def add_schedule(self, schedule: RuntimeResourceNeed, do: bool) -> bool:

        pre_need: Optional[RuntimeResourceNeed] = None
        back_need: Optional[RuntimeResourceNeed] = None

        if schedule.ddl < self.start_time:
            return False

        for resource_need in self.schedules:
            if resource_need.end > schedule.start:
                pre_need = resource_need
            if back_need is not None \
                    and resource_need.start < resource_need.end:
                back_need = resource_need

        if pre_need is not None or back_need is not None:
            return False
        else:
            if do is True:
                self.schedules.append(schedule)
                self.schedules = sorted(self.schedules, key=lambda need: need.start)
            return True

    def get_earliest_available_free_times(self, duration: timedelta) -> datetime:

        # 没有已分配任务
        if len(self.schedules) == 0:
            return self.start_time

        # 只有一个已分配任务
        if len(self.schedules) == 1:
            target_schedule = self.schedules[0]
            if self.start_time < target_schedule.start:
                if target_schedule.start - self.start_time > duration + timedelta(minutes=1):
                    return target_schedule.start - duration

            else:
                return target_schedule.end
        # 正常执行
        for i in range(len(self.schedules) - 2):
            pre_schedule = self.schedules[i]
            back_schedule = self.schedules[i + 1]

            if self.start_time < pre_schedule.start:
                if pre_schedule.start - self.start_time > duration + timedelta(minutes=1):
                    return pre_schedule.start - duration - timedelta(minutes=1)

            elif back_schedule.start - pre_schedule.end > duration + timedelta(minutes=1):
                return pre_schedule.end

        return self.schedules[-1].end


class RuntimeResourcePool:

    def __init__(self, resources: List[model.Resource], start_time: datetime):
        self.pool: Dict[str, RuntimeResource] = {}
        self.start_time: datetime = start_time

        for resource in resources:
            runtime_resource = RuntimeResource(resource, self.start_time)
            self.pool[runtime_resource.resource.rsc_id] = runtime_resource

    # 资源分配操作
    def alloc_resource(self, resource_needs: List[RuntimeResourceNeed]):
        for resource_need in resource_needs:
            if resource_need.could_alloc is False:
                continue
            for plan_alloc_resource_id in resource_need.plan_alloc_resources_id:
                self.pool[plan_alloc_resource_id].add_schedule(resource_need, True)

    def try_alloc_resource(self, resource_needs: List[RuntimeResourceNeed]) -> bool:

        temp_pool = deepcopy(list(self.pool.values()))

        # 已经满足的需求
        fulfilled_needs = []

        if_all_alloc = True

        for resource_need in resource_needs:

            if resource_need.could_alloc is True:
                continue

            # 精确搜索
            for runtime_resource in temp_pool:
                # 排除不同车间
                if runtime_resource.workspace != resource_need.workspace:
                    continue
                if runtime_resource.basic_attr == resource_need.resource_attr:
                    if runtime_resource.add_schedule(resource_need, False) is True:
                        resource_need.add_plan_alloc_resource(runtime_resource.resource.rsc_id)
                        fulfilled_needs.append(resource_need)
                        runtime_resource.add_schedule(resource_need, True)
                        resource_need.could_alloc = True
                        break

            # 是否已经分配完成
            if resource_need.could_alloc is False:
                # 放宽条件搜索
                for runtime_resource in temp_pool:
                    # 排除不同车间
                    if runtime_resource.workspace != resource_need.workspace:
                        continue
                    if resource_need.resource_attr in runtime_resource.resource_attrs:
                        if runtime_resource.add_schedule(resource_need, False) is True:
                            resource_need.add_plan_alloc_resource(runtime_resource.resource.rsc_id)
                            fulfilled_needs.append(resource_need)
                            runtime_resource.add_schedule(resource_need, True)
                            resource_need.could_alloc = True
                            break

            if resource_need not in fulfilled_needs:
                if_all_alloc = False

        return if_all_alloc

    def reset_earliest_free_start_time(self, resource_needs: List[RuntimeResourceNeed]) -> bool:

        if_found = False

        for resource_need in resource_needs:

            if resource_need.could_alloc is True:
                continue

            earliest_time: Optional[datetime] = None

            duration = resource_need.end - resource_need.start

            # 精确搜索
            for runtime_resource in self.pool.values():
                # 排除不同车间
                if runtime_resource.workspace != resource_need.workspace:
                    continue
                if runtime_resource.basic_attr == resource_need.resource_attr:
                    temp_earliest_time = runtime_resource.get_earliest_available_free_times(duration)
                    # 时间不能超过DDL
                    if temp_earliest_time > resource_need.ddl - duration:
                        continue
                    if earliest_time is None or earliest_time > temp_earliest_time:
                        earliest_time = temp_earliest_time

            # 优先利用对口资源
            if earliest_time is not None:
                resource_need.start = earliest_time
            # 放宽条件搜索
            else:
                for runtime_resource in self.pool.values():
                    # 排除不同车间
                    if runtime_resource.workspace != resource_need.workspace:
                        continue
                    if resource_need.resource_attr in runtime_resource.resource_attrs:
                        temp_earliest_time = runtime_resource.get_earliest_available_free_times(duration)
                        # 时间不能超过DDL
                        if temp_earliest_time > resource_need.ddl - duration:
                            continue
                        if earliest_time is None or earliest_time > temp_earliest_time:
                            earliest_time = temp_earliest_time

            if earliest_time is None:
                if_found = False
            else:
                resource_need.start = earliest_time
                resource_need.end = earliest_time + duration
                if_found = True

        return if_found

