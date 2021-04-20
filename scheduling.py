import runtime
import model
import csv
from typing import List, Dict
from datetime import datetime, timedelta, date
import time
import math
import dataset_importer


def orders_processor(orders: Dict[str, model.Order]) -> List[runtime.RuntimeProduct]:
    orders_list = list(orders.values())
    sorted_orders_list = sorted(orders_list, key=lambda order: order.latest_end_time)
    products_lines = runtime.RuntimeProductLines()

    for sorted_order in sorted_orders_list:
        for item in sorted_order.products:
            runtime_product = runtime.RuntimeProduct(item["product"], item["amount"])
            runtime_product.set_ddl_start(sorted_order.latest_end_time, sorted_order.earliest_start_time)
            products_lines.add_runtime_product(runtime_product)

    runtime_product = products_lines.pop_runtime_product()

    produce_tree = []

    produce_list = []

    while runtime_product is not None:
        search_semi_products(0, produce_tree, produce_list, runtime_product)
        runtime_product = products_lines.pop_runtime_product()

    return produce_list


def search_semi_products(floor, produce_tree, produce_list, runtime_product):

    runtime_semi_products = []
    produce_tree.append({"runtime_product": runtime_product, "runtime_semi_products": runtime_semi_products})
    # print("F", runtime_product.product.product_id, runtime_product.ddl)
    if len(runtime_product.product.semi_products) > 0:
        for i in range(runtime_product.amount):
            for item in runtime_product.product.semi_products:

                runtime_semi_product = runtime.RuntimeProduct(item["semi_product"], item["amount"])
                runtime_semi_product.set_ddl_start(runtime_product.ddl, runtime_product.start)

                # print("C", runtime_semi_product.product.product_id, runtime_semi_product.ddl)

                for k in range(runtime_semi_product.amount):
                    search_semi_products(floor+1, runtime_semi_products, produce_list, runtime_semi_product)

    print("L", floor, runtime_product.product.product_id, runtime_product.ddl)
    produce_list.append(runtime_product)


def products_processor(runtime_products: List[runtime.RuntimeProduct]):

    runtime_products_processes_list: List[Dict[str, any]] = []

    for runtime_product in runtime_products:
        processes_list: List[runtime.RuntimeProcess] = []
        production_times: int = 0
        for process in runtime_product.product.processes:
            # 执行工序的次数
            process_number = math.ceil(float(runtime_product.amount) / float(process.max_quantity))
            for i in range(process_number):
                runtime_process: runtime.RuntimeProcess = \
                    runtime.RuntimeProcess(runtime_product, process)
                production_times += runtime_process.process.pdt_time
                processes_list.append(runtime_process)

        runtime_product.set_delay(production_times)
        runtime_products_processes_list.append({"runtimeProduct": runtime_product, "runtimeProcess": processes_list})

    runtime_products_processes_list = \
        sorted(runtime_products_processes_list,
               key=lambda dict_item:
               (dict_item["runtimeProduct"].ddl, dict_item["runtimeProduct"].delay))

    # 输出检查
    for item in runtime_products_processes_list:
        for runtime_process in item["runtimeProcess"]:
            runtime_product: runtime.RuntimeProduct = item["runtimeProduct"]
            # print(runtime_product.product.product_id, runtime_product.delay, runtime_process.process.pcs_id)

    return runtime_products_processes_list


def resource_processor(runtime_products_processes_list: List[Dict[str, any]],
                       resource_pool: runtime.RuntimeResourcePool,
                       start_time: datetime):
    could_alloc = True

    for item in runtime_products_processes_list:
        runtime_resource_needs: List[runtime.RuntimeResourceNeed] = []
        for runtime_process in item["runtimeProcess"]:
            runtime_process: runtime.RuntimeProcess = runtime_process
            for resource_item in runtime_process.process.res_needs:
                resource_attr = resource_item["rcs_attr"]
                amount = resource_item["amount"]
                for i in range(amount):
                    runtime_resource_need: runtime.RuntimeResourceNeed = runtime.RuntimeResourceNeed(
                        runtime_process,
                        resource_attr,
                        runtime_process.process.workspace,
                        start_time,
                        start_time + timedelta(minutes=runtime_process.process.pdt_time))
                    runtime_resource_needs.append(runtime_resource_need)

        if resource_pool.try_alloc_resource(runtime_resource_needs):
            resource_pool.alloc_resource(runtime_resource_needs)
        else:
            while resource_pool.reset_earliest_free_start_time(runtime_resource_needs):
                resource_pool.try_alloc_resource(runtime_resource_needs)
                resource_pool.alloc_resource(runtime_resource_needs)

            for runtime_resource_need in runtime_resource_needs:
                if runtime_resource_need.could_alloc is False:
                    could_alloc = False
                    break

    return could_alloc


if __name__ == "__main__":

    start_time: datetime = datetime.combine(date(2020, 8, 12), datetime.min.time())

    m_orders, m_products, m_processes, m_resources = dataset_importer.import_dataset()
    resource_pool: runtime.RuntimeResourcePool = runtime.RuntimeResourcePool(m_resources.values(), start_time)
    produce_list = orders_processor(m_orders)
    rt_rcs_list = products_processor(produce_list)
    print(resource_processor(rt_rcs_list, resource_pool, start_time))
