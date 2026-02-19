"""
Core Inventory Engine

Handles loading inventory data, calculating stock metrics, and generating reports.
"""
import csv
from dataclasses import dataclass, field
from math import ceil
from typing import List, Dict
import config


@dataclass
class Product:
    """Represents an inventory product with all stock calculations."""
    name: str
    sku: str
    supplier: str
    annual_volume: float
    stock_on_hand: float
    on_order: float
    manual_adjustment: float
    
    # Computed fields
    daily_usage: float = field(init=False)
    days_to_out_of_stock: float = field(init=False)
    low_stock_threshold: float = field(init=False)
    target_stock_level: float = field(init=False)
    buffer_weeks: int = field(init=False)
    buffer_qty: float = field(init=False)
    order_volume: float = field(init=False)
    overstock_amount: float = field(init=False)
    status: str = field(init=False)
    
    def __post_init__(self):
        """Calculate all computed fields after initialization."""
        # Daily usage
        self.daily_usage = self.annual_volume / config.WORKING_DAYS_PER_YEAR
        
        # Days to out of stock (handle zero usage → 9999 / infinite)
        if self.daily_usage > 0:
            self.days_to_out_of_stock = self.stock_on_hand / self.daily_usage
        else:
            self.days_to_out_of_stock = 9999
        
        # Monthly usage
        monthly_usage = self.annual_volume / 12
        weekly_usage = self.annual_volume / 52
        
        # Low stock threshold (1 month)
        self.low_stock_threshold = ceil(monthly_usage * config.LOW_STOCK_THRESHOLD_MONTHS)
        
        # Target stock level (3 months)
        self.target_stock_level = ceil(monthly_usage * config.TARGET_STOCK_MONTHS)
        
        # Buffer weeks (supplier-specific)
        self.buffer_weeks = config.SUPPLIER_BUFFER_WEEKS.get(
            self.supplier, 
            config.DEFAULT_BUFFER_WEEKS
        )
        
        # Buffer quantity
        self.buffer_qty = ceil(weekly_usage * self.buffer_weeks)
        
        # Determine if reorder is needed
        # Reorder triggers when stock is below 1 month OR below 2 months
        # Since 1 < 2, this effectively means: reorder when stock < 2 months
        months_of_stock = self.days_to_out_of_stock / 30.0
        needs_reorder = months_of_stock < config.REORDER_TRIGGER_MONTHS_MAX
        
        # Order volume (only if reorder conditions are met)
        if needs_reorder or config.ANALYSE_ALL_STOCK:
            calculated_order = (
                self.target_stock_level + 
                self.buffer_qty - 
                self.stock_on_hand - 
                self.on_order + 
                self.manual_adjustment
            )
            self.order_volume = max(0, calculated_order)
        else:
            self.order_volume = 0
        
        # Overstock amount
        if self.stock_on_hand > self.target_stock_level and self.target_stock_level > 0:
            self.overstock_amount = self.stock_on_hand - self.target_stock_level
        else:
            self.overstock_amount = 0
        
        # Status determination
        if self.stock_on_hand == 0 and self.annual_volume > 0:
            self.status = 'OUT OF STOCK'
        elif self.days_to_out_of_stock <= 30:
            self.status = 'CRITICAL'
        elif self.days_to_out_of_stock <= 60:
            self.status = 'LOW'
        elif self.overstock_amount > 0:
            self.status = 'OVERSTOCK'
        elif self.annual_volume == 0:
            self.status = 'NO DEMAND'
        else:
            self.status = 'OK'


def _parse_value(value_str: str, default: float = 0.0) -> float:
    """Parse a CSV value, handling N/A, #N/A, and empty strings."""
    if not value_str or value_str.strip() in ('N/A', '#N/A', ''):
        return default
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return default


def load_inventory(csv_path: str) -> List[Product]:
    """
    Load inventory from CSV file.
    
    Expected columns: Product, SKU, Supplier, Annual Volume, Stock on Hand, On Order, Manual Adjustment
    """
    products = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                product = Product(
                    name=row.get('Product', '').strip(),
                    sku=row.get('SKU', '').strip(),
                    supplier=row.get('Supplier', '').strip(),
                    annual_volume=_parse_value(row.get('Annual Volume', '0')),
                    stock_on_hand=_parse_value(row.get('Stock on Hand', '0')),
                    on_order=_parse_value(row.get('On Order', '0')),
                    manual_adjustment=_parse_value(row.get('Manual Adjustment', '0'))
                )
                products.append(product)
            except Exception as e:
                print(f"Warning: Skipping row due to error: {e}")
                continue
    
    return products


def generate_supplier_summary(products: List[Product]) -> Dict[str, Dict]:
    """
    Generate supplier order summary.
    
    Groups products by supplier with total quantities and item lists.
    """
    summary = {}
    
    for product in products:
        if product.order_volume > 0:
            if product.supplier not in summary:
                summary[product.supplier] = {
                    'total_qty': 0,
                    'item_count': 0,
                    'items': []
                }
            
            summary[product.supplier]['total_qty'] += product.order_volume
            summary[product.supplier]['item_count'] += 1
            summary[product.supplier]['items'].append({
                'sku': product.sku,
                'name': product.name,
                'qty': product.order_volume
            })
    
    # Sort items within each supplier by quantity descending
    for supplier_data in summary.values():
        supplier_data['items'].sort(key=lambda x: x['qty'], reverse=True)
    
    # Return as sorted list by total quantity
    return dict(sorted(summary.items(), key=lambda x: x[1]['total_qty'], reverse=True))


def generate_alerts(products: List[Product]) -> Dict[str, List[Product]]:
    """
    Categorize products into alert categories.
    
    Returns:
        Dict with keys: out_of_stock, critical, low, overstock
    """
    alerts = {
        'out_of_stock': [],
        'critical': [],
        'low': [],
        'overstock': []
    }
    
    for product in products:
        if product.status == 'OUT OF STOCK':
            alerts['out_of_stock'].append(product)
        elif product.status == 'CRITICAL':
            alerts['critical'].append(product)
        elif product.status == 'LOW':
            alerts['low'].append(product)
        elif product.status == 'OVERSTOCK':
            alerts['overstock'].append(product)
    
    return alerts
