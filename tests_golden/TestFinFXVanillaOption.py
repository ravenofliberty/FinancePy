###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

from FinTestCases import FinTestCases, globalTestCaseMode
from financepy.utils.date import Date
from financepy.products.rates.ibor_deposit import IborDeposit
from financepy.products.rates.ibor_single_curve import IborSingleCurve
from financepy.utils.calendar import CalendarTypes
from financepy.utils.day_count import DayCountTypes
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.models.sabr import SABR
from financepy.products.fx.fx_vanilla_option import FXVanillaOption
from financepy.utils.global_types import OptionTypes
import time
import numpy as np
import sys
sys.path.append("..")


testCases = FinTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinFXVanillaOptionWystupExample1():

    # Example from Book extract by Uwe Wystup with results in Table 1.2
    # https://mathfinance.com/wp-content/uploads/2017/06/FXOptionsStructuredProducts2e-Extract.pdf

    # Not exactly T=1.0 but close so don't exact exact agreement
    # (in fact I do not get exact agreement even if I do set T=1.0)
    value_date = Date(13, 2, 2018)
    expiry_date = Date(13, 2, 2019)

    # In BS the FX rate is the price in domestic of one unit of foreign
    # In case of EURUSD = 1.3 the domestic currency is USD and foreign is EUR
    # DOM = USD , FOR = EUR
    ccy1 = "EUR"
    ccy2 = "USD"
    ccy1CCRate = 0.030  # EUR
    ccy2CCRate = 0.025  # USD

    currency_pair = ccy1 + ccy2  # Always ccy1ccy2
    spot_fx_rate = 1.20
    strike_fx_rate = 1.250
    volatility = 0.10

    notional = 1000000.0

    dom_discount_curve = DiscountCurveFlat(value_date, ccy2CCRate)
    for_discount_curve = DiscountCurveFlat(value_date, ccy1CCRate)

    model = BlackScholes(volatility)

    # Two examples to show that changing the notional currency and notional
    # keeps the value unchanged
    notional = 1000000.0
    call_option = FXVanillaOption(expiry_date,
                                  strike_fx_rate,
                                  currency_pair,
                                  OptionTypes.EUROPEAN_CALL,
                                  notional,
                                  "EUR", 2)

    value = call_option.value(value_date, spot_fx_rate,
                              dom_discount_curve,
                              for_discount_curve, model)

    notional = 1250000.0
    call_option = FXVanillaOption(expiry_date,
                                  strike_fx_rate,
                                  currency_pair,
                                  OptionTypes.EUROPEAN_CALL,
                                  notional,
                                  "USD", 2)

    value = call_option.value(
        value_date,
        spot_fx_rate,
        dom_discount_curve,
        for_discount_curve,
        model)

    delta = call_option.delta(
        value_date,
        spot_fx_rate,
        dom_discount_curve,
        for_discount_curve,
        model)

    testCases.header("value", "delta")
    testCases.print(value, delta)

###############################################################################


def test_FinFXVanillaOptionWystupExample2():

    # Example Bloomberg Pricing at
    # https://stackoverflow.com/questions/48778712/fx-vanilla-call-price-in-quantlib-doesnt-match-bloomberg

    value_date = Date(13, 2, 2018)
    expiry_date = Date(13, 2, 2019)

    # In BS the FX rate is the price in domestic of one unit of foreign
    # In case of EURUSD = 1.3 the domestic currency is USD and foreign is EUR
    # DOM = USD , FOR = EUR
    ccy1 = "EUR"
    ccy2 = "USD"
    ccy1CCRate = 0.0396  # EUR
    ccy2CCRate = 0.0357  # USD

    currency_pair = ccy1 + ccy2  # Always ccy1ccy2
    spot_fx_rate = 0.9090
    strike_fx_rate = 0.9090
    volatility = 0.12

    notional = 1000000.0

    dom_discount_curve = DiscountCurveFlat(value_date, ccy2CCRate)
    for_discount_curve = DiscountCurveFlat(value_date, ccy1CCRate)

    model = BlackScholes(volatility)

    # Two examples to show that changing the notional currency and notional
    # keeps the value unchanged
    notional = 1000000.0
    call_option = FXVanillaOption(expiry_date,
                                  strike_fx_rate,
                                  currency_pair,
                                  OptionTypes.EUROPEAN_PUT,
                                  notional,
                                  "EUR", 2)

    value = call_option.value(
        value_date,
        spot_fx_rate,
        dom_discount_curve,
        for_discount_curve,
        model)

    delta = call_option.delta(
        value_date,
        spot_fx_rate,
        dom_discount_curve,
        for_discount_curve,
        model)

    testCases.header("value", "delta")
    testCases.print(value, delta)

###############################################################################


def test_FinFXVanillaOptionBloombergExample():

    # Example Bloomberg Pricing at
    # https://stackoverflow.com/questions/48778712/fx-vanilla-call-price-in-quantlib-doesnt-match-bloomberg

    value_date = Date(13, 2, 2018)
    expiry_date = Date(15, 2, 2019)

    # In BS the FX rate is the price in domestic of one unit of foreign
    # In case of EURUSD = 1.3 the domestic currency is USD and foreign is EUR
    # DOM = USD , FOR = EUR
    forName = "EUR"
    domName = "USD"
    forDepoRate = 0.05  # EUR
    domDepoRate = 0.02  # USD

    currency_pair = forName + domName  # Always FORDOM
    spot_fx_rate = 1.30
    strike_fx_rate = 1.3650
    volatility = 0.20

    spot_days = 0
    settle_date = value_date.add_weekdays(spot_days)
    maturity_date = settle_date.add_months(12)
    notional = 1000000.0
    notional_currency = "EUR"
    cal_type = CalendarTypes.TARGET

    depos = []
    fras = []
    swaps = []
    depo = IborDeposit(settle_date, maturity_date, domDepoRate,
                       DayCountTypes.ACT_360, notional, cal_type)
    depos.append(depo)
    dom_discount_curve = IborSingleCurve(value_date, depos, fras, swaps)

    depos = []
    fras = []
    swaps = []
    depo = IborDeposit(settle_date, maturity_date, forDepoRate,
                       DayCountTypes.ACT_360, notional, cal_type)
    depos.append(depo)
    for_discount_curve = IborSingleCurve(value_date, depos, fras, swaps)

    model = BlackScholes(volatility)

    call_option = FXVanillaOption(expiry_date,
                                  strike_fx_rate,
                                  currency_pair,
                                  OptionTypes.EUROPEAN_CALL,
                                  notional,
                                  notional_currency, 2)

    value = call_option.value(
        value_date,
        spot_fx_rate,
        dom_discount_curve,
        for_discount_curve,
        model)

    delta = call_option.delta(
        value_date,
        spot_fx_rate,
        dom_discount_curve,
        for_discount_curve,
        model)

    testCases.header("value", "delta")
    testCases.print(value, delta)

###############################################################################


def test_FinFXVanillaOptionHullExample():

    #   Example from Hull 4th edition page 284
    value_date = Date(1, 1, 2015)
    expiry_date = value_date.add_months(4)
    spot_fx_rate = 1.60
    volatility = 0.1411
    dom_interest_rate = 0.08
    forInterestRate = 0.11
    model = BlackScholes(volatility)
    dom_discount_curve = DiscountCurveFlat(value_date, dom_interest_rate)
    for_discount_curve = DiscountCurveFlat(value_date, forInterestRate)

    num_paths_list = [10000, 20000, 40000, 80000, 160000, 320000]

    testCases.header("NUMPATHS", "VALUE_BS", "VALUE_MC")
    strike_fx_rate = 1.60

    for num_paths in num_paths_list:

        call_option = FXVanillaOption(expiry_date,
                                      strike_fx_rate,
                                      "EURUSD",
                                      OptionTypes.EUROPEAN_CALL,
                                      1000000,
                                      "USD")

        value = call_option.value(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)

        start = time.time()

        value_mc = call_option.value_mc(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model,
            num_paths)

        end = time.time()
        duration = end - start
        testCases.print(num_paths, value, value_mc)

##########################################################################

    spot_fx_rates = np.arange(100, 200, 10)
    spot_fx_rates = spot_fx_rates/100.0
    num_paths = 100000

    testCases.header("NUMPATHS", "CALL_VALUE_BS", "CALL_VALUE_MC")

    for spot_fx_rate in spot_fx_rates:

        call_option = FXVanillaOption(expiry_date,
                                      strike_fx_rate,
                                      "EURUSD",
                                      OptionTypes.EUROPEAN_CALL,
                                      1000000,
                                      "USD")

        value = call_option.value(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        start = time.time()
        value_mc = call_option.value_mc(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model,
            num_paths)
        end = time.time()
        duration = end - start
        testCases.print(num_paths, value, value_mc)

##########################################################################

    spot_fx_rates = np.arange(100, 200, 10) / 100.0
    num_paths = 100000

    testCases.header("SPOT FX RATE", "PUT_VALUE_BS", "PUT_VALUE_MC")

    for spot_fx_rate in spot_fx_rates:

        put_option = FXVanillaOption(expiry_date,
                                     strike_fx_rate,
                                     "EURUSD",
                                     OptionTypes.EUROPEAN_PUT,
                                     1000000,
                                     "USD")

        value = put_option.value(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        start = time.time()
        value_mc = put_option.value_mc(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model,
            num_paths)
        end = time.time()
        duration = end - start
        testCases.print(spot_fx_rate, value, value_mc)

##########################################################################

    spot_fx_rates = np.arange(100, 200, 10)/100.0

    testCases.header(
        "SPOT FX RATE",
        "CALL_VALUE_BS",
        "DELTA_BS",
        "VEGA_BS",
        "THETA_BS",
        "RHO_BS")

    for spot_fx_rate in spot_fx_rates:
        call_option = FXVanillaOption(expiry_date,
                                      strike_fx_rate,
                                      "EURUSD",
                                      OptionTypes.EUROPEAN_CALL,
                                      1000000,
                                      "USD")
        value = call_option.value(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        delta = call_option.delta(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        vega = call_option.vega(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        theta = call_option.theta(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        #  call_option.rho(value_date,stock_price, interest_rate,
        #  dividend_yield, modelType, model_params)
        rho = 999
        testCases.print(spot_fx_rate, value, delta, vega, theta, rho)

    testCases.header(
        "SPOT FX RATE",
        "PUT_VALUE_BS",
        "DELTA_BS",
        "VEGA_BS",
        "THETA_BS",
        "RHO_BS")

    for spot_fx_rate in spot_fx_rates:
        put_option = FXVanillaOption(expiry_date,
                                     strike_fx_rate,
                                     "EURUSD",
                                     OptionTypes.EUROPEAN_PUT,
                                     1000000,
                                     "USD")

        value = put_option.value(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        delta = put_option.delta(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        vega = put_option.vega(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        theta = put_option.theta(
            value_date,
            spot_fx_rate,
            dom_discount_curve,
            for_discount_curve,
            model)
        # put_option.rho(value_date,stock_price, interest_rate, dividend_yield,
        # modelType, model_params)
        rho = 999
        testCases.print(spot_fx_rate, value, delta, vega, theta, rho)

##########################################################################

    testCases.header("SPOT FX RATE", "VALUE_BS", "VOL_IN", "IMPLD_VOL")

    spot_fx_rates = np.arange(100, 200, 10)/100.0

    for spot_fx_rate in spot_fx_rates:
        call_option = FXVanillaOption(expiry_date,
                                      strike_fx_rate,
                                      "EURUSD",
                                      OptionTypes.EUROPEAN_CALL,
                                      1000000,
                                      "USD")

        value = call_option.value(value_date,
                                  spot_fx_rate,
                                  dom_discount_curve,
                                  for_discount_curve,
                                  model)['v']

        impliedVol = call_option.implied_volatility(value_date,
                                                    spot_fx_rate,
                                                    dom_discount_curve,
                                                    for_discount_curve,
                                                    value)

        testCases.print(spot_fx_rate, value, volatility, impliedVol)

###############################################################################

def test_FinFXVanillaOptionSABRExample():
    """
    Test case for FXVanilla option pricing with SABR model
    """
    # define option
    value_date = Date(5, 4, 2023)
    forName = "USD"
    domName = "JPY"
    forCCRate = 0.0381  # USD
    domCCRate = 0.000396  # JPY
    dom_discount_curve = DiscountCurveFlat(value_date, domCCRate)
    for_discount_curve = DiscountCurveFlat(value_date, forCCRate)
    currency_pair = forName + domName
    spot_fx_rate = 131.32
    strike_price = 130
    expiry_date = value_date.add_tenor("10M")
    notional = 70000000

    call_option = FXVanillaOption(expiry_date,
                                  strike_price,
                                  currency_pair,
                                  OptionTypes.EUROPEAN_CALL,
                                  notional, "USD")

    volatility = 0.1043
    # set the params of SABR

    alpha = 0.174
    beta = 0.5
    rho = -0.50
    nu = 0.5

    model = SABR(alpha, beta, rho, nu)
    blackVol = volatility
    t_exp = 0.8444  # 10M
    model.set_alpha_from_black_vol(blackVol,
                                   spot_fx_rate,
                                   strike_price,
                                   t_exp)

    spot_fx_rate = np.linspace(80, 300, 1000)

    call_values = []

    for f in spot_fx_rate:

        call_value = call_option.value(value_date, f, dom_discount_curve,
                                       for_discount_curve, model)['cash_dom']

        call_values.append(call_value)

    testCases.header("spot fx rate", "value")
    testCases.print(spot_fx_rate, call_value)

###############################################################################


test_FinFXVanillaOptionWystupExample1()
test_FinFXVanillaOptionWystupExample2()
test_FinFXVanillaOptionBloombergExample()
test_FinFXVanillaOptionHullExample()
test_FinFXVanillaOptionSABRExample()
testCases.compareTestCases()
