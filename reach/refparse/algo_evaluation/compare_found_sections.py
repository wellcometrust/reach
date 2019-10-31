# coding: utf-8
"""
Utility for comparing predicted and actual reference sections.

Takes the scarpe_data.csv produced by evaluate_algo.py, and produces an
interactive dashboard through which actual and predicted references sections
can be compared.

Requires streamlit>=0.47.3

pip3 install streamlit
streamlit run compare_found_sections.py
"""

import numpy as np
import pandas as pd
import streamlit as st

# Load scrape_date produced by evaluate_algo.py

data = pd.read_csv("./scrape_data.csv")

# Drop examples for which no comparison can be made

data.dropna(subset=["Predicted text", "Actual text"], inplace=True)

# Add sidebar

st.sidebar.title("Reference section explorer")

# Create selector for file hash in sidebar.

pdf_file = st.sidebar.selectbox("pdf file", data["File"].to_list())

lev = data.loc[data["File"] == pdf_file, ["lev_distance"]].iloc[0]["lev_distance"]
comment = st.sidebar.text_area("Comment about the prediction")
actual = data.loc[data["File"] == pdf_file, ["Actual text"]].iloc[0]["Actual text"]
predicted = data.loc[data["File"] == pdf_file, ["Predicted text"]].iloc[0]["Predicted text"]

# Produce a line which can easily be copied and pasted into a markdown table

st.write("Copy the line below into a markdown table:")
st.write(f"|{pdf_file}|{len(actual)}|{len(predicted)}|{np.round(lev, 2)}|{comment}|")

st.table(data.loc[data["File"] == pdf_file, ["Actual text" ,"Predicted text"]])
