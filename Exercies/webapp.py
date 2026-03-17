import streamlit as st
import plotly.express as px
import pandas as pd

st.title("The temperature in the form of Graph")

df = pd.read_csv("../data2.txt")

fig = px.line(x=df["date"], y=df["temperature"],
                            labels={"x": "Date", "y": "Temperature (C)"})

st.plotly_chart(fig)

