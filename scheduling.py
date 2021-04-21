import runtime
import model
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, date
import math
import dataset_importer
import os
import utils


def orders_processor(orders: Dict[str, model.Order]) -> Tuple[list, list, list]:
    orders_list = list(orders.values())
    sorted_orders_list = sorted(orders_list, key=lambda order: order.latest_end_time)
    products_lines = runtime.RuntimeProductLines()

    for sorted_order in sorted_orders_list:
        for item in sorted_order.products:
            runtime_product = runtime.RuntimeProduct(item["product"], item["amount"], sorted_order)
            runtime_product.set_ddl_start(sorted_order.latest_end_time, sorted_order.earliest_start_time)
            products_lines.add_runtime_product(runtime_product)

    runtime_product = products_lines.pop_runtime_product()

    products_list = [runtime_product]

    semi_products_list = []

    produce_tree = []

    produce_list = []

    while runtime_product is not None:
        search_semi_products(0, produce_tree, produce_list, runtime_product, semi_products_list)
        runtime_product = products_lines.pop_runtime_product()
        if runtime_product is not None:
            products_list.append(runtime_product)

    return produce_list, products_list, semi_products_list


def search_semi_products(floor, produce_tree, produce_list, runtime_product, semi_products_list):

    runtime_semi_products = []
    produce_tree.append({"runtime_product": runtime_product, "runtime_semi_products": runtime_semi_products})
    # print("F", runtime_product.product.product_id, runtime_product.ddl)
    if len(runtime_product.product.semi_products) > 0:
        for i in range(runtime_product.amount):
            for item in runtime_product.product.semi_products:

                runtime_semi_product = runtime.RuntimeProduct(item["semi_product"],
                                                              item["amount"],
                                                              runtime_product.order)

                runtime_semi_product.set_father_product(runtime_product.product)

                # 记录半成品
                semi_products_list.append(runtime_semi_product)

                runtime_semi_product.set_ddl_start(runtime_product.ddl, runtime_product.start)

                # print("C", runtime_semi_product.product.product_id, runtime_semi_product.ddl)

                for k in range(runtime_semi_product.amount):
                    search_semi_products(floor+1,
                                         runtime_semi_products,
                                         produce_list,
                                         runtime_semi_product,
                                         semi_products_list)

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
                    runtime.RuntimeProcess(runtime_product, process, runtime_product.order)
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
            print(runtime_product.product.product_id, runtime_product.delay, runtime_process.process.pcs_id)

    return runtime_products_processes_list


def resource_processor(runtime_products_processes_list: List[Dict[str, any]],
                       resource_pool: runtime.RuntimeResourcePool,
                       start_time: datetime):

    print("Resource Allocator Start Time", start_time)
    could_alloc = True
    index: int = 0

    runtime_resource_needs_all = []

    for item in runtime_products_processes_list:
        index += 1
        print("Processing", index, "OF", len(runtime_products_processes_list))

        target_runtime_product: runtime.RuntimeProduct = item["runtimeProduct"]

        print("Producing Product", target_runtime_product.product.product_id, "Amount", target_runtime_product.amount)

        runtime_resource_needs: List[runtime.RuntimeResourceNeed] = []
        for runtime_process in item["runtimeProcess"]:
            print("Runtime Process", runtime_process.process.pcs_id,
                  "FOR Runtime Product", runtime_process.runtime_product.product.product_id)

            runtime_process: runtime.RuntimeProcess = runtime_process
            for resource_item in runtime_process.process.res_needs:
                resource_attr = resource_item["rcs_attr"]
                amount = resource_item["amount"]

                print("Process Need Resource", resource_attr, " Amount", amount)

                for i in range(amount):
                    runtime_resource_need: runtime.RuntimeResourceNeed = runtime.RuntimeResourceNeed(
                        runtime_process,
                        resource_attr,
                        runtime_process.process.workspace,
                        start_time,
                        start_time + timedelta(minutes=runtime_process.process.pdt_time))
                    runtime_resource_needs.append(runtime_resource_need)

        if resource_pool.try_alloc_resource(runtime_resource_needs):
            pass
        else:
            while resource_pool.reset_earliest_free_start_time(runtime_resource_needs):
                resource_pool.try_alloc_resource(runtime_resource_needs)
                # resource_pool.alloc_resource(runtime_resource_needs)

            for runtime_resource_need in runtime_resource_needs:
                if runtime_resource_need.could_alloc is False:
                    could_alloc = False
                    break

        runtime_resource_needs_all.append(runtime_resource_needs)

    return could_alloc, runtime_resource_needs_all, resource_pool.pools


def json_writer(filename, obj):

    file = open("./outputs/" + filename, 'w', encoding="utf8")

    file.write(utils.dumps(obj))

    file.close()


def json_generator(orders,
                   runtime_products: List[runtime.RuntimeProduct],
                   runtime_semi_products: List[runtime.RuntimeProduct],
                   runtime_products_processes_list: List[List[runtime.RuntimeResourceNeed]],
                   resource_pools: Dict[int, Dict[str, runtime.RuntimeResource]]):

    folder = os.path.exists("./outputs")

    if not folder:
        os.mkdir("./outputs")

    orders_json = []

    for order in orders.values():
        orders_json.append({
            "name": order.order_id,
            "startTime": order.earliest_start_time.isoformat(),
            "endTime": order.latest_end_time.isoformat()
        })

    json_writer("orders.json", orders_json)

    products_json = []

    for runtime_product in runtime_products:
        products_json.append({
            "name": runtime_product.product.product_id,
            "count": runtime_product.amount,
            "startTime": runtime_product.delay.isoformat(),
            "endTime": runtime_product.ddl.isoformat()
        })

    json_writer("products.json", products_json)

    semi_products_json = []

    for runtime_semi_product in runtime_semi_products:
        semi_products_json.append({
            "name": runtime_semi_product.product.product_id,
            "startTime": runtime_semi_product.delay.isoformat(),
            "endTime": runtime_semi_product.ddl.isoformat()
        })

    json_writer("semi_products.json", semi_products_json)

    processes_json = []

    # 输出检查
    for runtime_resource_needs in runtime_products_processes_list:
        for runtime_resource_need in runtime_resource_needs:
            processes_json.append({
                "name": runtime_resource_need.process.pcs_id,
                "startTime": runtime_resource_need.start.isoformat(),
                "endTime": runtime_resource_need.end.isoformat(),
                "allocResourceName": runtime_resource_need.plan_alloc_resources_id,
                "workspace": runtime_resource_need.workspace
            })

    json_writer("processes.json", processes_json)

    resources_json = []

    # 输出检查
    for pool in resource_pools.values():
        for runtime_resource in pool.values():
            times = []

            for schedule in runtime_resource.schedules:

                in_product = None
                if schedule.father_product is not None:
                    in_product = schedule.father_product.product_id

                times.append({
                    "startTime": schedule.start.isoformat(),
                    "endTime": schedule.end.isoformat(),
                    "inOrder": schedule.order.order_id,
                    "inProduct": in_product,
                    "inSemiProduct": schedule.product.product_id,
                    "inProcess": schedule.product.product_id
                })

            resources_json.append({
                "name": runtime_resource.resource.rsc_name,
                "times": times
            })

    json_writer("resources.json", resources_json)


if __name__ == "__main__":

    start_time: datetime = datetime.combine(date(2020, 8, 12), datetime.min.time())

    m_orders, m_products, m_processes, m_resources = dataset_importer.import_dataset()
    m_resource_pool: runtime.RuntimeResourcePool = runtime.RuntimeResourcePool(m_resources.values(), start_time)
    m_produce_list, m_products_list, m_semi_products_list = orders_processor(m_orders)
    rt_rcs_list = products_processor(m_produce_list)

    m_could_alloc, m_runtime_resource_needs_all, resource_pools = \
        resource_processor(rt_rcs_list, m_resource_pool, start_time)

    json_generator(m_orders, m_products_list, m_semi_products_list, m_runtime_resource_needs_all, resource_pools)


