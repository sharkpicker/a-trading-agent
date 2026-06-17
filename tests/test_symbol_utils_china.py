# Copyright 2026 sharkpicker
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for China A-Share symbol normalization."""

import pytest
from tradingagents.dataflows.symbol_utils import (
    normalize_symbol,
    is_china_stock,
    parse_china_symbol,
)


class TestNormalizeSymbolChina:
    """Test A-Share symbol normalization."""

    def test_shanghai_main_board(self):
        assert normalize_symbol("600000") == "600000.SS"
        assert normalize_symbol("601398") == "601398.SS"
        assert normalize_symbol("603288") == "603288.SS"
        assert normalize_symbol("605117") == "605117.SS"

    def test_shanghai_star_market(self):
        assert normalize_symbol("688001") == "688001.SS"
        assert normalize_symbol("688981") == "688981.SS"

    def test_shenzhen_main_board(self):
        assert normalize_symbol("000001") == "000001.SZ"
        assert normalize_symbol("000858") == "000858.SZ"

    def test_shenzhen_sme(self):
        assert normalize_symbol("002415") == "002415.SZ"
        assert normalize_symbol("002594") == "002594.SZ"

    def test_shenzhen_chinext(self):
        assert normalize_symbol("300750") == "300750.SZ"
        assert normalize_symbol("300059") == "300059.SZ"

    def test_beijing_exchange(self):
        assert normalize_symbol("430047") == "430047.BJ"
        assert normalize_symbol("835305") == "835305.BJ"

    def test_already_has_suffix(self):
        assert normalize_symbol("000001.SZ") == "000001.SZ"
        assert normalize_symbol("600000.SS") == "600000.SS"
        assert normalize_symbol("430047.BJ") == "430047.BJ"

    def test_case_insensitive(self):
        assert normalize_symbol("000001.sz") == "000001.SZ"
        assert normalize_symbol("600000.ss") == "600000.SS"

    def test_non_china_symbols_unchanged(self):
        """Non-A-Share symbols should not be modified."""
        assert normalize_symbol("AAPL") == "AAPL"
        assert normalize_symbol("MSFT") == "MSFT"
        assert normalize_symbol("BTCUSD") == "BTC-USD"
        assert normalize_symbol("EURUSD") == "EURUSD=X"

    def test_invalid_china_code(self):
        """6-digit codes that don't match A-Share patterns stay unchanged."""
        assert normalize_symbol("123456") == "123456"
        assert normalize_symbol("999999") == "999999"


class TestIsChinaStock:
    """Test A-Share identification."""

    def test_true_cases(self):
        assert is_china_stock("000001.SZ") is True
        assert is_china_stock("600000.SS") is True
        assert is_china_stock("000001") is True
        assert is_china_stock("600000") is True
        assert is_china_stock("688001") is True
        assert is_china_stock("300750") is True

    def test_false_cases(self):
        assert is_china_stock("AAPL") is False
        assert is_china_stock("MSFT") is False
        assert is_china_stock("BTC-USD") is False
        assert is_china_stock("") is False
        assert is_china_stock("123456") is False


class TestParseChinaSymbol:
    """Test A-Share symbol parsing."""

    def test_parse_with_suffix(self):
        assert parse_china_symbol("000001.SZ") == ("000001", ".SZ")
        assert parse_china_symbol("600000.SS") == ("600000", ".SS")
        assert parse_china_symbol("430047.BJ") == ("430047", ".BJ")

    def test_parse_without_suffix(self):
        assert parse_china_symbol("000001") == ("000001", ".SZ")
        assert parse_china_symbol("600000") == ("600000", ".SS")
        assert parse_china_symbol("688001") == ("688001", ".SS")

    def test_parse_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_china_symbol("AAPL")
        with pytest.raises(ValueError):
            parse_china_symbol("123456")
