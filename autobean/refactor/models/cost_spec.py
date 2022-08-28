import copy
import datetime
import decimal
from typing import MutableSequence, Optional, Type, TypeVar
from .generated import cost_spec
from .cost_component import CostComponent
from . import internal
from .date import Date
from .punctuation import Asterisk
from .escaped_string import EscapedString
from .currency import Currency
from .number_expr import NumberExpr
from .amount import Amount
from .compound_amount import CompoundAmount
from .cost import UnitCost, TotalCost

_Self = TypeVar('_Self', bound='CostSpec')


@internal.tree_model
class CostSpec(cost_spec.CostSpec):
    
    @internal.custom_property
    def raw_cost_components(self) -> MutableSequence[CostComponent]:
        return self.raw_cost.raw_components

    raw_compound_amount_comp = internal.unordered_node_property(raw_cost_components, CompoundAmount, prepend=True)
    raw_amount_comp = internal.unordered_node_property(raw_cost_components, Amount, prepend=True)
    raw_number_comp = internal.unordered_node_property(raw_cost_components, NumberExpr, prepend=True)
    raw_currency_comp = internal.unordered_node_property(raw_cost_components, Currency, prepend=True)
    raw_date_comp = internal.unordered_node_property(raw_cost_components, Date)
    raw_label_comp = internal.unordered_node_property(raw_cost_components, EscapedString)
    raw_asterisk_comp = internal.unordered_node_property(raw_cost_components, Asterisk)

    @internal.custom_property
    def raw_number_per(self) -> Optional[NumberExpr]:
        if compound_amount := self.raw_compound_amount_comp:
            return compound_amount.raw_number_per
        if not isinstance(self.raw_cost, UnitCost):
            return None
        if amount := self.raw_amount_comp:
            return amount.raw_number
        return self.raw_number_comp

    @raw_number_per.setter
    def __raw_number_per(self, value: Optional[NumberExpr]) -> None:
        if compound_amount := self.raw_compound_amount_comp:  # CompoundAmount
            compound_amount.raw_number_per = value
        elif isinstance(self.raw_cost, UnitCost):
            if amount := self.raw_amount_comp:
                if value:  # Amount(per)
                    amount.raw_number = value
                else:  # Amount(per) - Number(per) -> Currency
                    self.raw_currency_comp = copy.deepcopy(amount.raw_currency)
                    self.raw_amount_comp = None
            elif (currency := self.raw_currency_comp) and value:  # Currency + Number(per) -> Amount(per)
                self.raw_amount_comp = Amount.from_children(value, copy.deepcopy(currency))
                self.raw_currency_comp = None
            else:  # Number(per)
                self.raw_number_comp = value
        elif isinstance(self.raw_cost, TotalCost) and value:
            if amount := self.raw_amount_comp:  # Amount(total) + Number(per) -> CompoundAmount
                self._into_unit_cost(self.raw_cost)
                compound_amount = CompoundAmount.from_children(
                    value,
                    copy.deepcopy(amount.raw_number),
                    copy.deepcopy(amount.raw_currency))
                self.raw_compound_amount_comp = compound_amount
                self.raw_amount_comp = None
            elif currency := self.raw_currency_comp:  # Currency(total) + Number(per) -> Amount(per)
                self._into_unit_cost(self.raw_cost)
                amount = Amount.from_children(value, copy.deepcopy(currency))
                self.raw_amount_comp = amount
                self.raw_currency_comp = None
            elif self.raw_number_comp:  # Number(total) + Number(per) -> error
                raise ValueError('Cannot set both number_per and number_total without a currency.')
            else:  # /(total) + Number(per) -> Number(per)
                self._into_unit_cost(self.raw_cost)
                self.raw_number_comp = value

    @internal.custom_property
    def raw_number_total(self) -> Optional[NumberExpr]:
        if compound_amount := self.raw_compound_amount_comp:
            return compound_amount.raw_number_total
        if not isinstance(self.raw_cost, TotalCost):
            return None
        if amount := self.raw_amount_comp:
            return amount.raw_number
        return self.raw_number_comp

    @raw_number_total.setter
    def __raw_number_total(self, value: Optional[NumberExpr]) -> None:
        if compound_amount := self.raw_compound_amount_comp:  # CompoundAmount
            compound_amount.raw_number_total = value
        elif isinstance(self.raw_cost, TotalCost):
            if amount := self.raw_amount_comp:
                if value:  # Amount(total):
                    amount.raw_number = value
                else:  # Amount(total) - Number(total) -> Currency
                    self.raw_currency_comp = copy.deepcopy(amount.raw_currency)
                    self.raw_amount_comp = None
            elif (currency := self.raw_currency_comp) and value:  # Currency + Number(total) -> Amount(total)
                self.raw_amount_comp = Amount.from_children(value, copy.deepcopy(currency))
                self.raw_currency_comp = None
            else:  # Number(total)
                self.raw_number_comp = value
        elif isinstance(self.raw_cost, UnitCost) and value:
            if amount := self.raw_amount_comp:  # Amount(per) + Number(total) -> CompoundAmount
                compound_amount = CompoundAmount.from_children(
                    copy.deepcopy(amount.raw_number),
                    value,
                    copy.deepcopy(amount.raw_currency))
                self.raw_compound_amount_comp = compound_amount
                self.raw_amount_comp = None
            elif currency := self.raw_currency_comp:  # Currency(per) + Number(total) -> Amount(total)
                self._into_total_cost(self.raw_cost)
                amount = Amount.from_children(value, copy.deepcopy(currency))
                self.raw_amount_comp = amount
                self.raw_currency_comp = None
            elif self.raw_number_comp:  # Number(per) + Number(total) -> error
                raise ValueError('Cannot set both number_per and number_total without a currency.')
            else:  # /(per) + Number(total) -> Number(total)
                self._into_total_cost(self.raw_cost)
                self.raw_number_comp = value

    @internal.custom_property
    def raw_currency(self) -> Optional[Currency]:
        if compound_amount := self.raw_compound_amount_comp:
            return compound_amount.raw_currency
        if amount := self.raw_amount_comp:
            return amount.raw_currency
        return self.raw_currency_comp

    @raw_currency.setter
    def __raw_currency(self, value: Optional[Currency]) -> None:
        if compound_amount := self.raw_compound_amount_comp:
            if value:  # CompoundAmount
                compound_amount.raw_currency = value
            else:  # CompoundAmount - Currency
                match compound_amount.raw_number_per, compound_amount.raw_number_total, self.raw_cost:
                    case NumberExpr(), None, UnitCost():
                        self.raw_number_comp = copy.deepcopy(compound_amount.raw_number_per)
                    case NumberExpr(), None, TotalCost() as c:
                        self._into_unit_cost(c)
                        self.raw_number_comp = copy.deepcopy(compound_amount.raw_number_per)
                    case None, NumberExpr(), TotalCost():
                        self.raw_number_comp = copy.deepcopy(compound_amount.raw_number_total)
                    case None, NumberExpr(), UnitCost() as c:
                        self._into_total_cost(c)
                        self.raw_number_comp = copy.deepcopy(compound_amount.raw_number_total)
                    case NumberExpr(), NumberExpr(), _:
                        raise ValueError('Cannot remove currency from compound amount with both numbers.')
                self.raw_compound_amount_comp = None
        elif amount := self.raw_amount_comp:
            if value:  # Amount
                amount.raw_currency = value
            else:  # Amount - Currency -> Number
                self.raw_number_comp = copy.deepcopy(amount.raw_number)
                self.raw_amount_comp = None
        else:  # Currency
            self.raw_currency_comp = value

    raw_date = raw_date_comp
    raw_label = raw_label_comp
    raw_asterisk = raw_asterisk_comp

    number_per = internal.optional_decimal_property(raw_number_per, NumberExpr)
    number_total = internal.optional_decimal_property(raw_number_total, NumberExpr)
    currency = internal.optional_string_property(raw_currency, Currency)
    date = internal.optional_date_property(raw_date, Date)
    label = internal.optional_string_property(raw_label, EscapedString)

    @property
    def merge(self) -> bool:
        return self.raw_asterisk is not None

    @merge.setter
    def merge(self, value: bool) -> None:
        current = self.merge
        if current and not value:
            self.raw_asterisk = None
        elif not current and value:
            self.raw_asterisk = Asterisk.from_default()

    @classmethod
    def from_value(
            cls: Type[_Self],
            number_per: Optional[decimal.Decimal],
            number_total: Optional[decimal.Decimal],
            currency: Optional[str],
            date: Optional[datetime.date] = None,
            label: Optional[str] = None,
            merge: bool = False,
    ) -> _Self:
        type_: Type[UnitCost | TotalCost]
        comps: list[CostComponent] = []
        if number_per is not None and number_total is not None:  # CompoundAmount
            if currency is None:
                raise ValueError('Cannot set both number_per and number_total without a currency.')
            type_ = UnitCost
            comps.append(CompoundAmount.from_children(
                NumberExpr.from_value(number_per),
                NumberExpr.from_value(number_total),
                Currency.from_value(currency)))
        elif number_per is not None:
            type_ = UnitCost
            if currency is None:
                comps.append(NumberExpr.from_value(number_per))
            else:
                comps.append(Amount.from_children(
                    NumberExpr.from_value(number_per),
                    Currency.from_value(currency)))
        elif number_total is not None:
            type_ = TotalCost
            if currency is None:
                comps.append(NumberExpr.from_value(number_total))
            else:
                comps.append(Amount.from_children(
                    NumberExpr.from_value(number_total),
                    Currency.from_value(currency)))
        elif currency is not None:
            type_ = UnitCost
            comps.append(Currency.from_value(currency))
        else:
            type_ = UnitCost
        if date is not None:
            comps.append(Date.from_value(date))
        if label is not None:
            comps.append(EscapedString.from_value(label))
        if merge:
            comps.append(Asterisk.from_default())
        return cls.from_children(type_.from_children(comps))

    def _into_unit_cost(self, total_cost: TotalCost) -> None:
        self._cost = total_cost.into_unit_cost()

    def _into_total_cost(self, unit_cost: UnitCost) -> None:
        self._cost = unit_cost.into_total_cost()
