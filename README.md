# 📦 Inventory Reorder Report System

A complete Python-based inventory management and reorder report system that replaces manual Google Sheets workflows. This system reads inventory data from CSV files, calculates stock metrics and reorder quantities, generates an interactive HTML dashboard, and optionally sends reports via email.

## ✨ Features

- **Automated Stock Analysis**: Calculates daily usage, days to out-of-stock, and reorder quantities
- **Supplier-Specific Buffers**: Different lead time buffers for each supplier
- **Smart Reordering Logic**: Only triggers reorders when stock is below 1 or 2 months
- **Interactive HTML Dashboard**: Dark-themed, filterable tables with real-time search
- **Email Integration**: Automated email delivery with SMTP support
- **GitHub Actions Support**: Scheduled daily reports (Mon-Fri at 7:00 AM UTC)
- **Zero Dependencies**: Uses only Python standard library

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/crr4484/inventory-report.git
cd inventory-report
```

### 2. Update Inventory Data

Edit `data/inventory.csv` with your current inventory data. See [CSV Format](#csv-format) below.

### 3. Run the Report Generator

```bash
python generate_report.py
```

### 4. View the Dashboard

Open `output/dashboard.html` in your web browser to view the interactive dashboard.

## 📋 CSV Format

The inventory CSV file must have the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Product** | Product name | AGCO Roof Adaptor |
| **SKU** | Stock keeping unit | A/001 |
| **Supplier** | Supplier name | SolSteer |
| **Annual Volume** | Expected annual sales volume | 17 |
| **Stock on Hand** | Current inventory quantity | 5 |
| **On Order** | Quantity already ordered | 4 |
| **Manual Adjustment** | Manual adjustment to order quantity | 0 |

**Note**: The system safely handles `N/A`, `#N/A`, and empty values by treating them as 0.

### Sample CSV

```csv
Product,SKU,Supplier,Annual Volume,Stock on Hand,On Order,Manual Adjustment
AGCO Roof Adaptor,A/001,SolSteer,17,5,4,0
AGCO Display Cab Adaptor,A/002,SolSteer,31,7,3,0
Massey GCAN Adaptor,A/003,SolSteer,1,0,0,0
```

## ⚙️ Configuration

All configuration settings are in `config.py`:

### Stock Thresholds

- **Target Stock**: 3 months on hand
- **Low Stock Threshold**: 1 month on hand
- **Reorder Triggers**: < 1 month OR < 2 months stock
- **Max Stock Threshold**: 30 days
- **Analyse All Stock**: Default `False` (set to `True` to analyse all items)
- **Working Days Per Year**: 365

### Supplier Buffer Weeks

Different suppliers have different lead times (in weeks of stock):

| Supplier | Buffer Weeks |
|----------|-------------|
| SolSteer | 3 |
| Harnex | 4 |
| Real Mounts | 1 |
| MMT | 1 |
| Ubiqconn AU | 4 |
| Ubiqconn USA | 1 |
| Rapid direct | 4 |
| OBDWire | 4 |
| **Default** | 2 |

## 📧 Email Setup

The system can send the dashboard report via email using SMTP.

### Environment Variables

Set the following environment variables:

```bash
export EMAIL_SENDER="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export EMAIL_RECIPIENTS="recipient1@example.com,recipient2@example.com"
export SMTP_SERVER="smtp.gmail.com"  # Optional, defaults to Gmail
export SMTP_PORT="587"                # Optional, defaults to 587
```

### Gmail App Password

For Gmail users:

1. Enable 2-factor authentication on your Google account
2. Generate an App Password at https://myaccount.google.com/apppasswords
3. Use the generated password as `EMAIL_PASSWORD`

**Note**: If email credentials are not configured, the system will skip email sending and just save the HTML dashboard locally.

## 🤖 GitHub Actions Setup

The repository includes a GitHub Actions workflow that runs automatically Monday-Friday at 7:00 AM UTC.

### Required Secrets

Configure the following secrets in your GitHub repository:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `EMAIL_SENDER` | Sender email address | your-email@gmail.com |
| `EMAIL_PASSWORD` | Email password or app password | abcd efgh ijkl mnop |
| `EMAIL_RECIPIENTS` | Comma-separated recipient emails | user1@example.com,user2@example.com |
| `SMTP_SERVER` | SMTP server (optional) | smtp.gmail.com |
| `SMTP_PORT` | SMTP port (optional) | 587 |

### Manual Trigger

You can manually trigger the workflow from the **Actions** tab in GitHub.

### Accessing Reports

Dashboard artifacts are saved for 30 days and can be downloaded from the workflow run page.

## 📊 Dashboard Features

The interactive HTML dashboard includes:

### Summary Cards
- Out of Stock count (red)
- Critical <30 days count (orange)
- Low Stock count (orange)
- Healthy count (green)
- Total Items to Order (blue)
- Total Order Quantity (blue)

### Supplier Order Summary
- Grid of cards showing orders per supplier
- Total units and item count
- Top items list with SKUs and quantities

### Reorder Table
- Filterable by supplier, status, and search term
- Shows only items that need reordering
- Order quantities highlighted in red if stock is critically low
- Sorted by days to out-of-stock (ascending)

### Full Inventory Table
- Complete inventory with all metrics
- Searchable with free-text filter
- Sorted by SKU
- Shows overstock amounts

## 🔧 Business Logic

### Reorder Calculation

```
order_volume = max(0, target_stock + buffer_qty - stock_on_hand - on_order + manual_adjustment)
```

**Reorder only triggers when:**
- Stock is below 1 month on hand, OR
- Stock is below 2 months on hand

(Unless `ANALYSE_ALL_STOCK` is set to `True`)

### Stock Status

| Status | Condition |
|--------|-----------|
| **OUT OF STOCK** | Stock on hand = 0 and annual volume > 0 |
| **CRITICAL** | Days to out of stock ≤ 30 |
| **LOW** | Days to out of stock ≤ 60 |
| **OVERSTOCK** | Stock on hand > target stock level |
| **NO DEMAND** | Annual volume = 0 |
| **OK** | All other cases |

### Days to Out of Stock

```
days_to_out_of_stock = stock_on_hand / daily_usage
```

If `daily_usage` is 0, returns 9999 (effectively infinite).

## 📁 Project Structure

```
inventory-report/
├── data/
│   └── inventory.csv          # Inventory data
├── templates/
│   └── dashboard.html         # HTML dashboard template
├── output/
│   └── dashboard.html         # Generated dashboard (created on run)
├── .github/
│   └── workflows/
│       └── daily_report.yml   # GitHub Actions workflow
├── config.py                  # Configuration settings
├── inventory_engine.py        # Core inventory logic
├── generate_report.py         # Main report generator script
├── requirements.txt           # Python dependencies (none)
└── README.md                  # This file
```

## 🛠️ Development

### Running Locally

```bash
# Run the report generator
python generate_report.py

# Open the generated dashboard
open output/dashboard.html  # macOS
xdg-open output/dashboard.html  # Linux
start output/dashboard.html  # Windows
```

### Customizing Configuration

Edit `config.py` to adjust:
- Stock thresholds
- Supplier buffer weeks
- Email settings
- CSV input path

### Testing with Different Data

```bash
# Use a different CSV file
export CSV_INPUT_PATH="path/to/your/inventory.csv"
python generate_report.py
```

## 📝 License

This project is provided as-is for inventory management purposes.

## 🤝 Contributing

Issues and pull requests are welcome!

## 📞 Support

For questions or issues, please open a GitHub issue.
