def get_target_proportion_dollars_eth(price):
    """
    Get the target proportion of dollars allocated to ETH based on the current price.
    The more expensive ETH is, the lower the target proportion.
    """
    K_SCALER = 9000.0
    N_EXPONENT = 1.15

    PRICE_FLOOR = 3000.0
    PRICE_CEILING = 5000.0

    PROP_C_MAX = 0.90
    PROP_C_MIN = 0.20

    if price < PRICE_FLOOR:
        return PROP_C_MAX
    elif price > PRICE_CEILING:
        return PROP_C_MIN
    else:
        return round(K_SCALER / (price ** N_EXPONENT), 3)


def analyze_and_trade(eth_units, eth_price, dollars_liquid):
    dollars_eth = eth_units * eth_price
    dollars_total = dollars_eth + dollars_liquid
    dollars_eth_proportion = dollars_eth / dollars_total

    LABEL_WIDTH = 15
    print(f"{'$$$ ETH': <{LABEL_WIDTH}}{dollars_eth:.0f}")
    print(f"{'$$$ Liquid': <{LABEL_WIDTH}}{dollars_liquid:.0f}")
    print(f"{'$$$ ETH %': <{LABEL_WIDTH}}{dollars_eth_proportion:.1%}")

    target_dollars_eth_proportion = get_target_proportion_dollars_eth(eth_price)
    print()
    print(f"Target ETH %: {target_dollars_eth_proportion:.1%}")

    target_dollars_eth = dollars_total * target_dollars_eth_proportion
    trade_amount_dollars = dollars_eth - target_dollars_eth

    action = "SELL" if trade_amount_dollars > 0 else "BUY"
    amount = round(abs(trade_amount_dollars), -1)

    return action, amount

