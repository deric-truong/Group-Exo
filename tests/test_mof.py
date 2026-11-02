"""Checks on the MoF parser and the saved MoF file. Run: python3 -m pytest"""

import pandas as pd
import pytest

from src.data.mof import OUTPUT_FILE, parse_mof

HEADER = "年,月,日,Year,Month,Day,金額(amount),売買通貨,Currency pairs\n"
SOLD = "the US dollar (bought) the Japanese yen (sold)"
BOUGHT = "the US dollar (sold) the Japanese yen (bought)"


def make_csv(rows):
    # Return a bytes object with the given rows, encoded in cp932 (Windows Japanese).
    return (HEADER + "\n".join(rows) + "\n").encode("cp932")


# A small file with the tricky cases: year/month only on the first row,
# a non-yen pair, two operations on one day, a full-width space, amounts with commas

SAMPLE = make_csv([
    f"平成3年,5月,13日,1991,May,13,139,米ドル売り,{BOUGHT}",
    ",,20日,,,20,50,米ドル売り,the US dollar (sold) the German mark (bought)",
    "平成3年4～6月期計,,,April - June 1991,,,189,,",
    f"平成16年,1月,9日,2004,Jan,9,\"16,000\",米ドル買い,{SOLD}",
    ",,9日,,,9,664,ユーロ買い,the Euro (bought) 　the Japanese yen (sold)",
    "平成16年1～3月期計,,,January - March 2004,,,\"16,664\",,",
    "(note2) As the figures in each days are rounded off,,,,,,,,",
])

# 
def test_parse_signs_units_and_sum():
    df = parse_mof(SAMPLE)
    # time line check: confirms each row lands on the day the intervention actually happened
    assert list(df.index) == [pd.Timestamp("1991-05-13"), pd.Timestamp("2004-01-09")]
    # check the value (unit: in yen, sign: yen bought is +, yen sold is -, merging: 16000 + 664 on the same day = 1666.4)
    assert df["amount_bn_jpy"].tolist() == [13.9, -1666.4]


def test_parse_release_after_quarter_end():
    # check that realse_date = end of the intervention's quarter + 45 days (the MoF publishes the daily details about 5-6 weeks after quarter end)
    df = parse_mof(SAMPLE)
    assert df["release_date"].tolist() == [pd.Timestamp("1991-08-14"), pd.Timestamp("2004-05-15")]


def test_parse_rejects_wrong_totals():
    # max tolerance is 5, here we change the quarterly total to be off by 1000, which is more than 5
    bad = SAMPLE.replace("16,664".encode("cp932"), "17,664".encode("cp932"))
    with pytest.raises(ValueError, match="quarterly totals"):
        parse_mof(bad)


def test_parse_rejects_other_files():
    # check that the parser rejects a non-MoF file (e.g. an HTML error page)
    with pytest.raises(ValueError):
        parse_mof(b"<html><body>Not found</body></html>")


@pytest.fixture(scope="module")
def saved():
    # The data/ folder is not in git: skip (not fail) if the file was never fetched
    if not OUTPUT_FILE.exists():
        pytest.skip("run `python3 -m src.data.mof` first")
    return pd.read_parquet(OUTPUT_FILE)


def test_dates_unique_and_sorted(saved):
    assert saved.index.is_unique and saved.index.is_monotonic_increasing


def test_no_missing_or_zero_amounts(saved):
    # no zero or missing amounts: the MoF reports only days with interventions, and the amount must always be always non-zero
    assert saved["amount_bn_jpy"].notna().all()
    assert (saved["amount_bn_jpy"] != 0).all()


def test_amounts_in_billions(saved):
    # The record so far is about 8 tn = 8,000 in JPY (Oct 2011); far above means a unit error
    # forgetting to divide by 10 would push values to around 80,000, so this catches unit mistakes
    assert saved["amount_bn_jpy"].abs().max() < 20_000


def test_release_after_intervention(saved):
    # No look-ahead: data can only be used after it was published
    assert (saved["release_date"] > saved.index).all()
