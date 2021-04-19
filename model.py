from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Set, Optional
from utils import *


@auto_str
@auto_repr
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


@auto_str
@auto_repr
class Product:

    def __init__(self, product_id: str, product_name: str):
        self.product_id: str = product_id
        self.product_name: str = product_name
        self.semi_products: List[Dict[str, any]] = []
        self.processes: List[Process] = []

    def add_semi_product(self, semi_product: Product, amount):
        if semi_product.product_id != self.product_id:
            self.semi_products.append({
                "semi_product": semi_product,
                "amount": amount
            })

    def add_process(self, process):
        self.processes.append(process)


@auto_str
@auto_repr
class Workspace:

    def __init__(self, name: str):
        self.name: str = name


@auto_str
@auto_repr
class Process:

    def __init__(self,
                 pcs_id: str,
                 pcs_name: str,
                 product: Product,
                 workspace: Workspace):

        self.pcs_id: str = pcs_id
        self.pcs_name: str = pcs_name
        self.product: Product = product

        self.production_mode: int = 0
        self.min_quantity: int = 0
        self.max_quantity: int = 0

        self.pdt_time: int = 0

        self.prev_pcs: Optional[Process] = None
        self.last_pcs: Optional[Process] = None

        self.res_needs: List[Dict[str, any]] = []
        self.workspace: Workspace = workspace

    def set_pre_last_pcs(self, prev_pcs: Optional[Process], last_pcs: Optional[Process]):
        self.prev_pcs: Process = prev_pcs
        self.last_pcs: Process = last_pcs

    def set_mode_quantity(self, production_mode: int, min_quantity: int, max_quantity: int):
        self.production_mode: int = production_mode
        self.min_quantity: int = max_quantity
        self.max_quantity: int = min_quantity

    def set_product_time(self, pdt_time: int):
        self.pdt_time: int = pdt_time

    def add_res_need(self, rcs_attr: str, amount: int):
        self.res_needs.append({
            "rcs_attr": rcs_attr,
            "amount": amount
        })


@auto_str
@auto_repr
class Resource:

    def __init__(self, rsc_id: str, rsc_name: str, rsc_type: str, workspace: str):
        self.rsc_id: str = rsc_id
        self.rsc_name: str = rsc_name
        self.rsc_type: str = rsc_type
        self.amount: int = 0

        self.basic_attr: Optional[str] = None
        self.attrs: Set = set()
        self.workspace: str = workspace

    def set_amount(self, amount: int):
        self.amount: int = amount

    def set_basic_attr(self, basic_attr: Optional[str]):
        self.basic_attr = basic_attr
        self.attrs.add(basic_attr)

    def add_attr(self, attr: str):
        self.attrs.add(attr)
