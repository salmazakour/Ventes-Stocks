import pandas as pd

def filter_data(sales, stock, selected_stations, date_range):
    # Filtrer ventes
    filtered_sales = sales[
        (sales['Branch_Name'].isin(selected_stations)) &
        (sales['Date_Time'].dt.date.between(date_range[0], date_range[1])) 
    ]

    # Filtrer stock
    filtered_stock = stock[
     (stock['Branch_Name'].isin(selected_stations)) &
     (stock['Date_Stamp'].dt.date.between(date_range[0], date_range[1]))
]

    # Dernier stock par station
    last_stock_per_station = (
        filtered_stock
        .sort_values('Date_Stamp')
        .groupby(['Branch_Name', 'Product_Code'])
        .tail(1)
    )

    # Stock global (somme sur toutes les stations sélectionnées)
    stock_summary_global = (
        last_stock_per_station
        .groupby('Product_Code')['Stock_on_Hand']
        .sum()
        .reset_index()
    )

    # Top 100 global
    top_products_global = (
        filtered_sales
        .groupby(['Product_Code', 'Product_Description'])
        .agg({'Qty_Sold': 'sum'})
        .reset_index()
        .sort_values(by='Qty_Sold', ascending=False)
        .head(100)
    )

    top_products_global = top_products_global.merge(
        stock_summary_global, on='Product_Code', how='left'
    )

    return top_products_global, last_stock_per_station



def availability_display(qty):
    if pd.isna(qty) or qty <= 0:
        return "❌ Out of Stock"
    else:
        return f"{int(qty)} pcs available"
