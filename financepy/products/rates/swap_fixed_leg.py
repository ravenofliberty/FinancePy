##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

from ...utils.error import FinError
from ...utils.date import Date
from ...utils.math import ONE_MILLION
from ...utils.day_count import DayCount, DayCountTypes
from ...utils.frequency import FrequencyTypes
from ...utils.calendar import CalendarTypes,  DateGenRuleTypes
from ...utils.calendar import Calendar, BusDayAdjustTypes
from ...utils.schedule import Schedule
from ...utils.helpers import format_table, label_to_string, check_argument_types
from ...utils.global_types import SwapTypes
from ...market.curves.discount_curve import DiscountCurve

##########################################################################


class SwapFixedLeg:
    """ Class for managing the fixed leg of a swap. A fixed leg is a leg with
    a sequence of flows calculated according to an ISDA schedule and with a
    coupon that is fixed over the life of the swap. """

    def __init__(self,
                 effective_date: Date,  # Date interest starts to accrue
                 end_date: (Date, str),  # Date contract ends
                 leg_type: SwapTypes,
                 coupon: (float),
                 freq_type: FrequencyTypes,
                 dc_type: DayCountTypes,
                 notional: float = ONE_MILLION,
                 principal: float = 0.0,
                 payment_lag: int = 0,
                 cal_type: CalendarTypes = CalendarTypes.WEEKEND,
                 bd_type: BusDayAdjustTypes = BusDayAdjustTypes.FOLLOWING,
                 dg_type: DateGenRuleTypes = DateGenRuleTypes.BACKWARD,
                 end_of_month: bool = False):
        """ Create the fixed leg of a swap contract giving the contract start
        date, its maturity, fixed coupon, fixed leg frequency, fixed leg day
        count convention and notional.  """

        check_argument_types(self.__init__, locals())

        if type(end_date) == Date:
            self._termination_date = end_date
        else:
            self._termination_date = effective_date.add_tenor(end_date)

        calendar = Calendar(cal_type)

        self._maturity_date = calendar.adjust(self._termination_date,
                                              bd_type)

        if effective_date > self._maturity_date:
            raise FinError("Effective date after maturity date")

        self._effective_date = effective_date
        self._end_date = end_date
        self._leg_type = leg_type
        self._freq_type = freq_type
        self._payment_lag = payment_lag
        self._notional = notional
        self._principal = principal
        self._cpn = coupon

        self._dc_type = dc_type
        self._cal_type = cal_type
        self._bd_type = bd_type
        self._dg_type = dg_type
        self._end_of_month = end_of_month

        self._startAccruedDates = []
        self._endAccruedDates = []
        self._payment_dates = []
        self._payments = []
        self._year_fracs = []
        self._accrued_days = []
        self._rates = []

        self.generate_payments()

###############################################################################

    def generate_payments(self):
        ''' These are generated immediately as they are for the entire
        life of the swap. Given a valuation date we can determine
        which cash flows are in the future and value the swap
        The schedule allows for a specified lag in the payment date
        Nothing is paid on the swap effective date and so the first payment
        date is the first actual payment date. '''

        schedule = Schedule(self._effective_date,
                            self._termination_date,
                            self._freq_type,
                            self._cal_type,
                            self._bd_type,
                            self._dg_type,
                            end_of_month=self._end_of_month)

        scheduleDates = schedule._adjusted_dates

        if len(scheduleDates) < 2:
            raise FinError("Schedule has none or only one date")

        self._startAccruedDates = []
        self._endAccruedDates = []
        self._payment_dates = []
        self._payments = []
        self._year_fracs = []
        self._accrued_days = []
        self._rates = []

        prev_dt = scheduleDates[0]

        day_counter = DayCount(self._dc_type)
        calendar = Calendar(self._cal_type)

        for next_dt in scheduleDates[1:]:

            self._startAccruedDates.append(prev_dt)
            self._endAccruedDates.append(next_dt)

            if self._payment_lag == 0:
                payment_date = next_dt
            else:
                payment_date = calendar.add_business_days(next_dt,
                                                          self._payment_lag)

            self._payment_dates.append(payment_date)

            (year_frac, num, den) = day_counter.year_frac(prev_dt,
                                                          next_dt)

            self._rates.append(self._cpn)

            payment = year_frac * self._notional * self._cpn

            self._payments.append(payment)
            self._year_fracs.append(year_frac)
            self._accrued_days.append(num)

            prev_dt = next_dt

###############################################################################

    def value(self,
              value_date: Date,
              discount_curve: DiscountCurve):

        self._paymentDfs = []
        self._paymentPVs = []
        self._cumulativePVs = []

        notional = self._notional
        dfValue = discount_curve.df(value_date)
        legPV = 0.0
        numPayments = len(self._payment_dates)

        dfPmnt = 0.0

        for iPmnt in range(0, numPayments):

            pmntDate = self._payment_dates[iPmnt]
            pmntAmount = self._payments[iPmnt]

            if pmntDate > value_date:

                dfPmnt = discount_curve.df(pmntDate) / dfValue
                pmntPV = pmntAmount * dfPmnt
                legPV += pmntPV

                self._paymentDfs.append(dfPmnt)
                self._paymentPVs.append(pmntAmount*dfPmnt)
                self._cumulativePVs.append(legPV)

            else:

                self._paymentDfs.append(0.0)
                self._paymentPVs.append(0.0)
                self._cumulativePVs.append(0.0)

        if pmntDate > value_date:
            paymentPV = self._principal * dfPmnt * notional
            self._paymentPVs[-1] += paymentPV
            legPV += paymentPV
            self._cumulativePVs[-1] = legPV

        if self._leg_type == SwapTypes.PAY:
            legPV = legPV * (-1.0)

        return legPV

##########################################################################

    def print_payments(self):
        """ Prints the fixed leg dates, accrual factors, discount factors,
        cash amounts, their present value and their cumulative PV using the
        last valuation performed. """

        print("START DATE:", self._effective_date)
        print("MATURITY DATE:", self._maturity_date)
        print("COUPON (%):", self._cpn * 100)
        print("FREQUENCY:", str(self._freq_type))
        print("DAY COUNT:", str(self._dc_type))

        if len(self._payments) == 0:
            print("Payments not calculated.")
            return

        header = [ "PAY_NUM", "PAY_DATE", "ACCR_START", "ACCR_END",
                    "DAYS", "YEARFRAC", "RATE", "PMNT"]

        rows = []
        num_flows = len(self._payment_dates)
        for iFlow in range(0, num_flows):
            rows.append([
                iFlow + 1,
                self._payment_dates[iFlow],
                self._startAccruedDates[iFlow],
                self._endAccruedDates[iFlow],
                self._accrued_days[iFlow],
                round(self._year_fracs[iFlow], 4),
                round(self._rates[iFlow] * 100.0, 4),
                round(self._payments[iFlow], 2),
            ])

        table = format_table(header, rows)
        print("\nPAYMENTS SCHEDULE:")
        print(table)

###############################################################################

    def print_valuation(self):
        """ Prints the fixed leg dates, accrual factors, discount factors,
        cash amounts, their present value and their cumulative PV using the
        last valuation performed. """

        print("START DATE:", self._effective_date)
        print("MATURITY DATE:", self._maturity_date)
        print("COUPON (%):", self._cpn * 100)
        print("FREQUENCY:", str(self._freq_type))
        print("DAY COUNT:", str(self._dc_type))

        if len(self._payments) == 0:
            print("Payments not calculated.")
            return

        header = ["PAY_NUM", "PAY_DATE", "NOTIONAL",
                  "RATE", "PMNT", "DF", "PV", "CUM_PV"]

        rows = []
        num_flows = len(self._payment_dates)
        for iFlow in range(0, num_flows):
            rows.append([
                iFlow + 1,
                self._payment_dates[iFlow],
                round(self._notional, 0),
                round(self._rates[iFlow] * 100.0, 4),
                round(self._payments[iFlow], 2),
                round(self._paymentDfs[iFlow], 4),
                round(self._paymentPVs[iFlow], 2),
                round(self._cumulativePVs[iFlow], 2),
            ])

        table = format_table(header, rows)
        print("\nPAYMENTS VALUATION:")
        print(table)

##########################################################################

    def __repr__(self):
        s = label_to_string("OBJECT TYPE", type(self).__name__)
        s += label_to_string("START DATE", self._effective_date)
        s += label_to_string("TERMINATION DATE", self._termination_date)
        s += label_to_string("MATURITY DATE", self._maturity_date)
        s += label_to_string("NOTIONAL", self._notional)
        s += label_to_string("PRINCIPAL", self._principal)
        s += label_to_string("LEG TYPE", self._leg_type)
        s += label_to_string("COUPON", self._cpn)
        s += label_to_string("FREQUENCY", self._freq_type)
        s += label_to_string("DAY COUNT", self._dc_type)
        s += label_to_string("CALENDAR", self._cal_type)
        s += label_to_string("BUS DAY ADJUST", self._bd_type)
        s += label_to_string("DATE GEN TYPE", self._dg_type)
        return s

###############################################################################

    def _print(self):
        """ Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. """
        print(self)

###############################################################################
