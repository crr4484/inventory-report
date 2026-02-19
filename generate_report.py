"""
Generate Inventory Reorder Report

Main script that generates the HTML dashboard and optionally sends it via email.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List

import config
from inventory_engine import load_inventory, generate_supplier_summary, generate_alerts, Product


def format_number(value: float) -> str:
    """Format number with no decimal places if it's a whole number."""
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def get_status_badge_class(status: str) -> str:
    """Get CSS class for status badge."""
    status_map = {
        'OUT OF STOCK': 'out-of-stock',
        'CRITICAL': 'critical',
        'LOW': 'low',
        'OK': 'ok',
        'OVERSTOCK': 'overstock',
        'NO DEMAND': 'no-demand'
    }
    return status_map.get(status, 'ok')


def generate_supplier_cards(supplier_summary: dict) -> str:
    """Generate HTML for supplier order summary cards."""
    if not supplier_summary:
        return '<p style="color: #8b949e;">No orders required at this time.</p>'
    
    cards_html = []
    for supplier, data in supplier_summary.items():
        items_html = []
        for item in data['items'][:10]:  # Show top 10 items
            items_html.append(
                f'<li><span class="sku">{item["sku"]}</span> <span class="qty">{format_number(item["qty"])}</span></li>'
            )
        
        if data['item_count'] > 10:
            items_html.append(f'<li style="color: #8b949e;">... and {data["item_count"] - 10} more items</li>')
        
        card = f"""
        <div class="supplier-card">
            <h3>{supplier}</h3>
            <div class="supplier-stats">
                <div class="stat">
                    <div class="stat-value">{format_number(data['total_qty'])}</div>
                    <div class="stat-label">Total Units</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{data['item_count']}</div>
                    <div class="stat-label">Items</div>
                </div>
            </div>
            <ul class="supplier-items">
                {''.join(items_html)}
            </ul>
        </div>
        """
        cards_html.append(card)
    
    return '\n'.join(cards_html)


def generate_reorder_rows(products: List[Product]) -> str:
    """Generate HTML table rows for products that need reordering."""
    rows = []
    
    # Filter and sort products with order volume > 0
    reorder_products = [p for p in products if p.order_volume > 0]
    reorder_products.sort(key=lambda p: p.days_to_out_of_stock)
    
    for product in reorder_products:
        # Check if order qty should be shown in red
        qty_class = 'qty-warning' if product.stock_on_hand < product.low_stock_threshold else ''
        
        row = f"""
        <tr>
            <td class="monospace">{product.sku}</td>
            <td>{product.name}</td>
            <td>{product.supplier}</td>
            <td>{format_number(product.annual_volume)}</td>
            <td>{format_number(product.stock_on_hand)}</td>
            <td>{format_number(product.days_to_out_of_stock)}</td>
            <td>{format_number(product.low_stock_threshold)}</td>
            <td>{format_number(product.target_stock_level)}</td>
            <td>{format_number(product.buffer_qty)}</td>
            <td>{format_number(product.on_order)}</td>
            <td class="{qty_class}">{format_number(product.order_volume)}</td>
            <td><span class="badge {get_status_badge_class(product.status)}">{product.status}</span></td>
        </tr>
        """
        rows.append(row)
    
    if not rows:
        return '<tr><td colspan="12" style="text-align: center; color: #8b949e;">No items to reorder</td></tr>'
    
    return '\n'.join(rows)


def generate_inventory_rows(products: List[Product]) -> str:
    """Generate HTML table rows for all inventory products."""
    rows = []
    
    # Sort by SKU
    sorted_products = sorted(products, key=lambda p: p.sku)
    
    for product in sorted_products:
        row = f"""
        <tr>
            <td class="monospace">{product.sku}</td>
            <td>{product.name}</td>
            <td>{product.supplier}</td>
            <td>{format_number(product.annual_volume)}</td>
            <td>{format_number(product.stock_on_hand)}</td>
            <td>{format_number(product.days_to_out_of_stock)}</td>
            <td>{format_number(product.low_stock_threshold)}</td>
            <td>{format_number(product.target_stock_level)}</td>
            <td>{format_number(product.buffer_qty)}</td>
            <td>{format_number(product.on_order)}</td>
            <td>{format_number(product.manual_adjustment)}</td>
            <td>{format_number(product.order_volume)}</td>
            <td>{format_number(product.overstock_amount)}</td>
            <td><span class="badge {get_status_badge_class(product.status)}">{product.status}</span></td>
        </tr>
        """
        rows.append(row)
    
    return '\n'.join(rows)


def generate_supplier_options(products: List[Product]) -> str:
    """Generate HTML options for supplier filter dropdown."""
    suppliers = sorted(set(p.supplier for p in products))
    options = [f'<option value="{s}">{s}</option>' for s in suppliers]
    return '\n'.join(options)


def generate_html_dashboard(products: List[Product]) -> str:
    """Generate the complete HTML dashboard."""
    # Load template
    template_path = os.path.join('templates', 'dashboard.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Generate summary data
    alerts = generate_alerts(products)
    supplier_summary = generate_supplier_summary(products)
    
    # Count statuses
    out_of_stock_count = len(alerts['out_of_stock'])
    critical_count = len(alerts['critical'])
    low_count = len(alerts['low'])
    healthy_count = sum(1 for p in products if p.status == 'OK')
    
    # Total order quantities
    total_items_to_order = sum(1 for p in products if p.order_volume > 0)
    total_order_qty = sum(p.order_volume for p in products)
    
    # Replace placeholders
    html = template.replace('{{REPORT_DATE}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    html = html.replace('{{OUT_OF_STOCK_COUNT}}', str(out_of_stock_count))
    html = html.replace('{{CRITICAL_COUNT}}', str(critical_count))
    html = html.replace('{{LOW_COUNT}}', str(low_count))
    html = html.replace('{{HEALTHY_COUNT}}', str(healthy_count))
    html = html.replace('{{TOTAL_ITEMS_TO_ORDER}}', str(total_items_to_order))
    html = html.replace('{{TOTAL_ORDER_QTY}}', format_number(total_order_qty))
    html = html.replace('{{SUPPLIER_CARDS}}', generate_supplier_cards(supplier_summary))
    html = html.replace('{{SUPPLIER_OPTIONS}}', generate_supplier_options(products))
    html = html.replace('{{REORDER_ROWS}}', generate_reorder_rows(products))
    html = html.replace('{{INVENTORY_ROWS}}', generate_inventory_rows(products))
    
    return html


def send_email(html_content: str):
    """Send the HTML dashboard via email."""
    if not config.EMAIL_SENDER or not config.EMAIL_PASSWORD or not config.EMAIL_RECIPIENTS:
        print("⚠️  Email credentials not configured. Skipping email send.")
        print("   Set EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECIPIENTS environment variables to enable email.")
        return
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📦 Inventory Reorder Report — {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = config.EMAIL_SENDER
        msg['To'] = ', '.join(config.EMAIL_RECIPIENTS)
        
        # Plain text fallback
        text_content = "This is an HTML email. Please view it in an HTML-compatible email client."
        
        # Attach parts
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {len(config.EMAIL_RECIPIENTS)} recipient(s)")
    
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("📦 INVENTORY REORDER REPORT GENERATOR")
    print("=" * 80)
    print()
    
    # Load inventory
    csv_path = config.CSV_INPUT_PATH
    print(f"📂 Loading inventory from: {csv_path}")
    products = load_inventory(csv_path)
    print(f"✅ Loaded {len(products)} products")
    print()
    
    # Generate alerts summary
    alerts = generate_alerts(products)
    print("📊 INVENTORY STATUS SUMMARY:")
    print(f"   🔴 Out of Stock:     {len(alerts['out_of_stock'])}")
    print(f"   🟠 Critical (<30d):  {len(alerts['critical'])}")
    print(f"   🟡 Low Stock:        {len(alerts['low'])}")
    print(f"   🟣 Overstock:        {len(alerts['overstock'])}")
    print(f"   🟢 Healthy:          {sum(1 for p in products if p.status == 'OK')}")
    print(f"   ⚪ No Demand:        {sum(1 for p in products if p.status == 'NO DEMAND')}")
    print()
    
    # Order summary
    total_items_to_order = sum(1 for p in products if p.order_volume > 0)
    total_order_qty = sum(p.order_volume for p in products)
    print("📦 ORDER SUMMARY:")
    print(f"   Items to Order:  {total_items_to_order}")
    print(f"   Total Quantity:  {format_number(total_order_qty)}")
    print()
    
    # Generate HTML dashboard
    print("🎨 Generating HTML dashboard...")
    html_content = generate_html_dashboard(products)
    
    # Save to file
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'dashboard.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard saved to: {output_path}")
    print()
    
    # Send email
    print("📧 Attempting to send email...")
    send_email(html_content)
    print()
    
    print("=" * 80)
    print("✅ Report generation complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
