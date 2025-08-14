import streamlit as st
import os
from data_loader import load_data
from processor import filter_data, availability_display
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd



st.set_page_config(page_title="Analyse ventes & stock", layout="wide")

# Menu latéral
st.sidebar.title("📌 Menu")
page = st.sidebar.radio("Navigation", ["Top Produits", "Ruptures", "Evolution"])

sales_file = st.sidebar.file_uploader("Télécharger le fichier VENTES", type=['csv', 'xlsx', 'xls'])
stock_file = st.sidebar.file_uploader("Télécharger le fichier STOCK", type=['csv', 'xlsx', 'xls'])

# Vérifier que les deux fichiers sont chargés
if sales_file is None or stock_file is None:
    st.warning("Veuillez importer les fichiers de ventes et de stock pour continuer.")
    st.stop()

# Charger les données
sales, stock = load_data(sales_file, stock_file)

if sales.empty or stock.empty:
    st.warning("⚠️ Les fichiers sont vides ou mal formatés.")
    st.stop()


# Harmoniser les colonnes pour le filtre
stock['Department'] = stock['Major_Department']
sales['Department'] = sales['Department']

# Récupérer la liste des départements uniques
departments = sorted(set(stock['Department'].dropna().unique()) | set(sales['Department'].dropna().unique()))

# Widget multiselect dans la barre latérale (sidebar)
selected_departments = st.sidebar.multiselect("🏢 Sélectionner département(s)", departments, default=departments)

# Filtrer les DataFrames selon le(s) département(s) sélectionné(s)
stock = stock[stock['Department'].isin(selected_departments)]
sales = sales[sales['Department'].isin(selected_departments)]





# Harmoniser les colonnes pour le filtre
stock['sub_Department'] = stock['Department_Name']
sales['sub_Department'] = sales['SubDepartment']

# Récupérer la liste des sub_départements uniques
subdepartments = sorted(set(stock['sub_Department'].dropna().unique()) | set(sales['sub_Department'].dropna().unique()))

# Widget multiselect dans la barre latérale (sidebar)
selected_subdepartments = st.sidebar.multiselect(" Sélectionner Sous-département(s)", subdepartments, default=subdepartments)

# Filtrer les DataFrames selon le(s)  sub département(s) sélectionné(s)
stock = stock[stock['sub_Department'].isin(selected_subdepartments)]
sales = sales[sales['sub_Department'].isin(selected_subdepartments)]





# Filtres communs
stations = sorted(sales['Branch_Name'].dropna().unique().tolist())
selected_stations = st.sidebar.multiselect("📍 Stations", stations, default=stations)

min_date = sales['Date_Time'].min().date()
max_date = sales['Date_Time'].max().date()

if sales['Date_Time'].notna().any():
    min_date = sales['Date_Time'].min().date()
    max_date = sales['Date_Time'].max().date()
else:
    st.warning("Aucune date disponible après application des filtres.")
    st.stop()

date_range = st.sidebar.date_input("📅 Plage de dates", [min_date, max_date])






# Traitement
top_products_global, last_stock_per_station = filter_data(sales, stock, selected_stations, date_range)

top_products_global['Availability'] = top_products_global['Stock_on_Hand'].apply(availability_display)

if page == "Top Produits":
    st.title("🧾 Top 100 Produits ")

    # Barre de recherche
    search_query = st.text_input("🔍 Rechercher un produit", "")

    # Bouton pour filtrer uniquement les ruptures
    show_only_ruptures = st.checkbox("🚨 Afficher uniquement les produits en rupture")

    df_display = top_products_global.copy()

    if show_only_ruptures:
        df_display = df_display[df_display['Stock_on_Hand'].fillna(0) <= 0]

    # Filtrer par recherche
    if search_query:
        df_display = df_display[df_display['Product_Code'].str.contains(search_query, case=False, na=False)]

    st.dataframe(
        df_display[['Product_Code', 'Product_Description', 'Qty_Sold', 'Availability']],
        use_container_width=True
    )

elif page == "Ruptures":
    st.title("🚨 Produits en rupture ")

    # Barre de recherche
    search_query = st.text_input("🔍 Rechercher un produit en rupture", "")

    ruptures = last_stock_per_station[last_stock_per_station['Stock_on_Hand'].fillna(0) <= 0]

    if search_query:
        ruptures = ruptures[ruptures['Product_Code'].str.contains(search_query, case=False, na=False)]

    st.dataframe(
        ruptures[['Branch_Name', 'Product_Code', 'Product_Description', 'Stock_on_Hand']],
        use_container_width=True
    )



elif page == "Evolution":
    st.subheader("📈 Évolution des ventes d’un produit")

    # --- Conversion en string pour éviter le ".0"
    sales['Product_Code'] = sales['Product_Code'].astype(str)
    stock['Product_Code'] = stock['Product_Code'].astype(str)

    # Filtrer selon stations et dates
    filtered_sales = sales[
        (sales['Branch_Name'].isin(selected_stations)) &
        (sales['Date_Time'].dt.date.between(date_range[0], date_range[1]))
    ]

    # Liste des produits disponibles
    product_codes = sorted(filtered_sales['Product_Code'].unique())
    selected_product = st.selectbox(" Sélectionnez un produit", product_codes)

    # Sélection du pas d’évolution
    freq_map = {"Jour": "D", "Semaine": "W", "Mois": "M"}
    selected_freq_label = st.radio("📊 Pas d’évolution", list(freq_map.keys()), horizontal=True)
    selected_freq = freq_map[selected_freq_label]

    if selected_product:
        # Filtrer les ventes du produit choisi
        product_data = filtered_sales[filtered_sales['Product_Code'] == selected_product]

        if not product_data.empty:
            # Récupérer le nom du produit
            product_name = product_data['Product_Description'].iloc[0]

            # Grouper par pas choisi
            product_data = (
                product_data
                .set_index('Date_Time')
                .groupby(pd.Grouper(freq=selected_freq))['Qty_Sold']
                .sum()
                .reset_index()
            )

            # Création des couleurs
            colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(product_data)))

            # --- STYLE ---
            plt.style.use("seaborn-v0_8-darkgrid")
            fig, ax = plt.subplots(figsize=(8, 4))

            bars = ax.bar(
                product_data['Date_Time'].dt.strftime("%Y-%m-%d"),
                product_data['Qty_Sold'],
                color=colors,
                edgecolor="black",
                linewidth=0.6
            )

            # Ajouter les valeurs au-dessus des barres
            for bar in bars:
                yval = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2, yval + 0.1,
                    f"{yval:.0f}",
                    ha='center', va='bottom',
                    fontsize=8, color="#333333"
                )

            # Titres et axes
            ax.set_xlabel("Date", fontsize=11, fontweight="bold")
            ax.set_ylabel("Quantité vendue", fontsize=11, fontweight="bold")
            ax.set_title(
                f"{product_name} ({selected_product}) - Évolution par {selected_freq_label.lower()}",
                fontsize=13, fontweight="bold"
            )

            plt.xticks(rotation=45, ha="right")
            ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))

            st.pyplot(fig)
        else:
            st.warning("⚠️ Aucune donnée trouvée pour ce produit dans la période sélectionnée.")

