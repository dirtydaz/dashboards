# prism_farm_calculator
# Luna staking yield calculator taken from lejimmy's prism dashboard 
# https://github.com/lejimmy/prism/blob/master/streamlit_app.py

import requests
import streamlit as st
import pandas as pd

# st.set_page_config(layout="wide")
st.title("PRISM Farm APR Calculator")


# lejimmy code

risk_free_rate = 0.195
luna_ust_address = "terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552"


@st.cache
def get_price(pair_address):

    # requests headers
    headers = {
        "authority": "api.coinhall.org",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
        "accept": "*/*",
        "sec-gpc": "1",
        "origin": "https://coinhall.org",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://coinhall.org/",
        "accept-language": "en-US,en;q=0.9",
    }

    # coinhall api
    response = requests.get(
        "https://api.coinhall.org/api/v1/charts/terra/pairs", headers=headers
    ).json()

    # convert to dataframe
    df = (
        pd.DataFrame.from_dict(response, orient="index")
        .reset_index(drop=False)
        .rename(columns={"index": "address"})
        .drop(labels=["timestamp", "unofficial", "startAt", "endAt"], axis=1)
    )

    # filter for astroport pair
    df = df[df["address"] == pair_address].reset_index()

    # parse json data
    df = pd.concat(
        [
            df,
            df["asset0"].apply(pd.Series).add_prefix("asset0_"),
            df["asset1"].apply(pd.Series).add_prefix("asset1_"),
        ],
        axis=1,
    )

    # price
    if df["asset0_symbol"][0] == "UST":
        price = float(df["asset0_poolAmount"] / df["asset1_poolAmount"])
    else:
        price = float(df["asset1_poolAmount"] / df["asset0_poolAmount"])

    return price


@st.cache
def get_oracle_rewards(luna_price):

    # oracle address
    response = requests.get(
        " https://lcd.terra.dev/bank/balances/terra1jgp27m8fykex4e4jtt0l7ze8q528ux2lh4zh0f",
    ).json()

    # convert to dataframe
    df = pd.DataFrame.from_dict(response["result"]).set_index("denom")

    # parse for ust and luna rewards
    ust_rewards = int(df.loc["uusd", "amount"]) / 1e6
    luna_rewards = int(df.loc["uluna", "amount"]) / 1e6

    # add ust and value of luna
    oracle_rewards = ust_rewards + luna_rewards * luna_price

    return oracle_rewards


@st.cache
def get_staked_luna():

    # staking pool
    response = requests.get(
        " https://lcd.terra.dev/cosmos/staking/v1beta1/pool",
    ).json()

    # convert to dataframe
    df = pd.DataFrame.from_dict(response)

    # parse number of staked luna
    staked_luna = round(int(df.loc["bonded_tokens", "pool"]) / 1e6, -6)

    return staked_luna


@st.cache
def get_staking_yield(luna_price, staked_luna):

    # amount of oracle rewards in UST
    oracle_rewards = get_oracle_rewards(luna_price)

    avg_validator_commission = 0.05

    # oracle rewards paid over two years, distributed to staked luna, divided my current luna price, minus validator commissions
    staking_yield = (
        oracle_rewards / 2 / staked_luna / luna_price * (1 - avg_validator_commission)
    )

    return staking_yield


# initial parameters
luna_price = get_price(luna_ust_address)
staked_luna = get_staked_luna()
staking_yield = get_staking_yield(luna_price, staked_luna) * 100

#lejimmy end

prism_rewards = 130000000

st.markdown(
    """
    Calculate the Prism yLuna Farm APR based on total yLuna staked and the prices of yLuna, Luna and Prism. There are 130,000,000 Prism tokens to be farmed over 12 months.
    
    This calculator builds on lejimmy's [Prism Valuation Calculator](https://share.streamlit.io/lejimmy/prism) to predict the upcoming Prism yLuna Farm APR.

    Note: Changing the price of Luna will automatically adjust the raw Luna Staking APR.
    """
)

st.info(
    "To support more community tools like this, consider delegating to the [GT Capital Validator](https://station.terra.money/validator/terravaloper1rn9grwtg4p3f30tpzk8w0727ahcazj0f0n3xnk)."
)

with st.expander("Assumptions", expanded=True):
    
    yluna_staked = st.number_input(
        "yLuna Staked in Prism", min_value = 0, value = 1000000, step = 250000
        )
    
    yluna_price = st.number_input(
        "yLuna Price", min_value = 0.0, value = 40.0, step = 0.25,
        format = "%0.1f"
    )

    luna_price_input = st.number_input(
        "Luna Price", min_value = 0.0, value = get_price(luna_ust_address), 
        step = 0.5, format = "%0.1f"
    )
    
    prism_price = st.number_input(
        "Prism Price", min_value = 0.0, value = 0.45, step = 0.01,
        format = "%0.2f"
    )









# yLuna APR calculations
luna_apr = get_staking_yield(luna_price_input, staked_luna) * 100
prism_per_yluna = prism_rewards / yluna_staked  
yluna_apr = prism_per_yluna * prism_price / yluna_price
luna_farm_apr = prism_per_yluna * prism_price / luna_price_input

col1, col2, col3 = st.columns(3)
# col1.text("   ")
col1.metric("PRISM Farm yLuna APR","{:.1%}".format(yluna_apr))
col2.metric("PRISM Farm Luna APR", "{:.1%}".format(luna_farm_apr))
col3.metric("Luna Staking APR", "{:.1%}".format(luna_apr/100))

# disclaimer
st.warning("This tool was created for educational purposes only, not financial advice.")