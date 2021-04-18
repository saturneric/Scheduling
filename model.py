from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Set


class Order:

    def __init__(self, order_id: str, description: str):
        self.order_id: str = order_id
        self.description: str = description
        self.earliest_start_time: datetime = datetime.today()
        self.latest_end_time: datetime = datetime.today()
        self.products: List[Dict[str, any]] = []

    def set_time(self, earliest_start_time: datetime, latest_end_time: datetime):
        self.earliest_start_time = earliest_start_time
        self.latest_end_time = latest_end_time

    def add_product(self, product, amount):
        self.products.append({
            "product": product,
            "amount": amount
        })


class Product:

    def __init__(self, product_id: str, product_name: str):
        self.product_id: str = product_id
        self.product_name: str = product_name


class Workspace:

    def __init__(self, name: str):
        self.name: str = name


class Process:

    def __init__(self,
                 pcs_id: str,
                 pcs_name: str,
                 product: Product,
                 prev_pcs: Process,
                 last_pcs: Process,
                 workspace: Workspace):

        self.pcs_id: str = pcs_id
        self.pcs_name: str = pcs_name
        self.product: Product = product

        self.production_mode: int = 0
        self.min_quantity: int = 0
        self.max_quantity: int = 0

        self.pdt_time: int = 0

        self.prev_pcs: Process = prev_pcs
        self.last_pcs: Process = last_pcs
        self.res_needs: List[Dict[str, any]] = []
        self.workspace: Workspace = workspace

    def set_mode_quantity(self, production_mode: int, min_quantity: int, max_quantity: int):
        self.production_mode: int = production_mode
        self.min_quantity: int = max_quantity
        self.max_quantity: int = min_quantity

    def set_product_time(self, pdt_time: int):
        self.pdt_time: int = pdt_time

    def add_res_need(self, rcs_attrs, amount):
        self.res_needs.append({
            "rcs_attrs": rcs_attrs,
            "amount": amount
        })


class Resource:

    def __init__(self, rsc_id: str, rsc_name: str, rsc_type: str, workspace: Workspace):
        self.rsc_id: str = rsc_id
        self.rsc_name: str = rsc_name
        self.rsc_type: str = rsc_type

        self.attr: str = ""
        self.basic_attrs: Set = set()
        self.workspace: Workspace = workspace

    def set_attr(self, attr: str, basic_attrs: List[str]):
        if attr not in basic_attrs:
            raise Exception("Attr NOT IN Basic_Attrs")

        self.attr: str = attr
        self.basic_attrs: List[str] = basic_attrs
