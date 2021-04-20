from typing import List, Dict
import mysql.connector
import model


def import_order(res) -> Dict[str, model.Order]:
    """
    导入订单
    :param res: 数据库返回的行对象
    :return: 订单对象集合
    """

    orders: Dict[str, model.Order] = {}

    for record in res:
        order: model.Order = model.Order(record[0], record[1])
        order.set_time(record[2], record[3])
        orders[order.order_id] = order

    return orders


def import_product(res) -> Dict[str, model.Product]:
    """
    导入产品
    :param res: 数据库返回的行对象
    :return: 产品对象集合
    """

    products: Dict[str, model.Product] = {}

    for record in res:
        product: model.Product = model.Product(record[0], record[1])
        products[product.product_id] = product

    return products


def import_order_product(res, orders: Dict[str, model.Order], products: Dict[str, model.Product]) -> None:
    for record in res:
        orders[record[0]].add_product(products[record[1]], record[2])


def import_product_component(res, products: Dict[str, model.Product]):
    for record in res:
        products[record[0]].add_semi_product(products[record[1]], record[2])


def import_process(res, products: Dict[str, model.Product]) -> Dict[str, model.Process]:
    processes: Dict[str, model.Process] = {}

    for record in res:
        process: model.Process = model.Process(record[0], record[1], products[record[2]], record[9])
        process.set_mode_quantity(record[5], record[7], record[6])
        process.set_product_time(record[8])
        products[record[2]].add_process(process)
        processes[process.pcs_id] = process

    for record in res:

        pre_process = None
        if record[3] is not None:
            pre_process = processes[record[3]]

        last_process = None
        if record[4] is not None:
            last_process = processes[record[4]]

        processes[record[0]].set_pre_last_pcs(pre_process, last_process)

    return processes


def import_resource(res) -> Dict[str, model.Resource]:
    resources: Dict[str, model.Resource] = {}

    for record in res:
        resource = model.Resource(record[0], record[1], record[2], record[4])
        resource.set_amount(record[3])
        resources[resource.rsc_id] = resource

    return resources


def import_resource_attributes(res, resources: Dict[str, model.Resource]):
    for record in res:
        resources[record[0]].set_basic_attr(record[1])
        resources[record[0]].add_attr(record[2])


def import_dataset():
    conn = mysql.connector.connect(
        host="gz-cynosdbmysql-grp-4ynd0gkb.sql.tencentcdb.com",
        port="23027",
        user="outsoursing",
        password="Npu1234!",
        database="outsoursing_dataset")

    cur = conn.cursor()

    cur.execute("SELECT * FROM aps_order;")
    res = cur.fetchall()

    orders = import_order(res)

    cur.execute("SELECT * FROM aps_product;")
    res = cur.fetchall()

    products = import_product(res)

    cur.execute("SELECT * FROM aps_order_product;")
    res = cur.fetchall()

    import_order_product(res, orders, products)

    cur.execute("SELECT * FROM aps_product_component;")
    res = cur.fetchall()

    import_product_component(res, products)

    cur.execute("SELECT * FROM aps_process;")
    res = cur.fetchall()

    processes = import_process(res, products)

    cur.execute("SELECT * FROM aps_resource;")
    res = cur.fetchall()

    resources = import_resource(res)

    cur.execute("SELECT * FROM aps_resource_arrtibutes;")
    res = cur.fetchall()

    import_resource_attributes(res, resources)

    conn.close()

    return orders, products, processes, resources
