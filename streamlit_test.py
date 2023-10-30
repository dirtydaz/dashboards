import streamlit as st
import pandas as pd
import numpy as np
from owid import catalog

generation_capacity = catalog.find('renewable_electricity_capacity', version = '2023-06-26').load()
aus_generation_capacity = generation_capacity.query('iso_code == "AUS"')

st.area_chart(aus_generation_capacity.set_index('year').drop(columns=['iso_code']))


