<!-- saved_by=api pipeline='design:dg_wireframe_spec' utc=2026-04-22T12:44:38Z -->

# ERP Dashboard Wireframe Specification

## Screen Inventory
1. **Home/Summary Screen**
2. **Sales Comparison Screen**
3. **Purchase Comparison Screen**
4. **Detailed Sales Data Screen**
5. **Detailed Purchase Data Screen**
6. **Settings/Customization Screen**

## Per-Screen Layout Descriptions

### 1. Home/Summary Screen
- **Header:** 
  - Title: “ERP Dashboard”
  - Date Range Selector: Dropdown for selecting the date range (e.g., last week, last month, custom).
  
- **Main Content Area:**
  - **KPI Overview Section:** 
    - Total Sales (large, bold number)
    - Total Purchases (large, bold number)
    - Profit Margin (large, bold number)
    
  - **Graphs Section:**
    - **Sales Trend Graph:** Line graph showing sales trends over the selected date range.
    - **Purchases Trend Graph:** Line graph showing purchase trends over the selected date range.

- **Footer:** 
  - Navigation Links: Home, Sales Comparison, Purchase Comparison, Settings.

### 2. Sales Comparison Screen
- **Header:** 
  - Title: “Sales Comparison”
  - Date Selector: Dropdown for selecting time frame (week/month/year).

- **Main Content Area:**
  - **KPI Comparison Section:**
    - Comparison metrics (e.g., sales amount, average sales).
    
  - **Bar Graph:** 
    - Displaying sales comparison between the selected time frames.

### 3. Purchase Comparison Screen
- **Header:** 
  - Title: “Purchase Comparison”
  - Date Selector: Similar to Sales Comparison.

- **Main Content Area:**
  - **KPI Comparison Section:**
    - Comparison metrics (e.g., total purchases, average purchase amount).
    
  - **Bar Graph:** 
    - Displaying purchase comparison between the selected time frames.

### 4. Detailed Sales Data Screen
- **Header:** 
  - Title: “Sales Data”
  - Date Range Selector: Similar to Home Screen.

- **Main Content Area:**
  - **Table of Sales Data:** 
    - Columns: Date, Product, Quantity Sold, Sales Amount.

### 5. Detailed Purchase Data Screen
- **Header:** 
  - Title: “Purchase Data”
  - Date Range Selector: Similar to Home Screen.

- **Main Content Area:**
  - **Table of Purchase Data:** 
    - Columns: Date, Supplier, Quantity Purchased, Purchase Amount.

### 6. Settings/Customization Screen
- **Header:** 
  - Title: “Settings”

- **Main Content Area:**
  - Options for dashboard customization (e.g., theme, default date range).
  - Save and Cancel buttons for user actions.

## User Flows

| User Actions          | Resulting Screen              | Notes                                            |
|----------------------|-------------------------------|--------------------------------------------------|
| Select Date Range    | Home/Summary Screen           | KPIs and graphs update to reflect selection.    |
| View Sales Data      | Detailed Sales Data Screen    | Access to granular sales information in table form. |
| View Purchases Data  | Detailed Purchase Data Screen  | Access to granular purchase information in table form. |
| Compare Sales        | Sales Comparison Screen        | Visual comparison of sales metrics over time.   |
| Compare Purchases    | Purchase Comparison Screen     | Visual comparison of purchase metrics over time. |

## Empty/Loading/Error States
- **Loading State:** Display a spinner or message indicating data is being loaded.
- **Empty State:** Message stating "No data available for this selection" if no sales or purchase data exists for the selected period.
- **Error State:** General error message with options to retry or check internet connection.

### Open Questions for Validation
- Are there specific organizational branding guidelines to consider in this dashboard design?
- Which KPIs are most crucial to the user and should be prioritized on the home screen?
- Are there any additional user flows or screens needed to enhance the dashboard's functionality?