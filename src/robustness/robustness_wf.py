""" Does each hypothesis keep its sign when changing the choice we made """

#variations: change one per run and keep everything else the same
#1. use 1-week forward carry instead of 4-week
#2. use quantile level 10% instead of 5%
#4. exclude 2024 unwind from sample
#5. exclude post-2025 rate break
#6. exclude weeks before MoF intervention
#7. use 6 months as BIS release date lag instead of 4 months
#(2010 variation is left out because walk-forward is already 2012 onwards)

import pandas as pd
from src import config
from src.quantile_regressions import RESULTS
from src.robustness_qr import intervention_ahead
from src.walk_forward import load_data, score, walk_forward

def summarise(name, fc, tau):
    """ One row: pinball losses, skill, coverage and Kupiec p-value of the model """
    s = score(fc, tau)
    model, hist, normal = (s.loc[m, "pinball"] for m in ["model", "hist", "normal"])
    return {
        "variation": name,
        "n_test_weeks": len(fc),
        "model_pinball": model,
        "hist_pinball": hist,
        "normal_pinball": normal,
        "skill_vs_hist": s.loc["model", "skill_vs_hist"], #quantifies the gain in explanatory power (positive is good)
        "model_coverage": s.loc["model", "coverage"], #calibration - should be close to tail level 
        "kupiec_p": s.loc["model", "kupiec_p"], #calibration - should be above 0.05
        "model_beats_both": model < min(hist, normal), #if T, model beats both benchmarks
    }

#runs walk forward validation for each variation and stacks results in a table
def run():

    #creating same variations as in robustness_qr.py
    raw = pd.read_parquet(config.DIRECTORY / "modelling_table.parquet") #Thomas' loader throws away intervention columns, so we need to bring them back from `modelling_table`

    df = load_data()
    before_break = df.drop(df.loc[config.JP_3M_BREAK:].index)

    df_lag = df.copy()
    df_lag["credit_yoy"] = df_lag["credit_yoy"].shift(8) # 6-month BIS lag
    df_lag = df_lag.dropna(subset=["credit_yoy"])

    amount = raw["yen_buy_amt"] + raw["yen_sell_amt"]
    flag4 = intervention_ahead(amount, 4)

    fc_lag = walk_forward(df_lag) # 6-month BIS lag, 5%
    fc4 = walk_forward(df) # 4 weeks, 5%
    fc1 = walk_forward(df, target="fwd_carry_1w", horizon=pd.Timedelta(weeks=1)) # 1 week, 5%
    fc10 = walk_forward(df, tau=0.10) # 4 weeks, 10%
    fc_break = walk_forward(before_break) # pre-2025, 5%

    rows = [
        summarise("baseline", fc4, 0.05),
        #2024 is left out of the scoring only; the model is still trained on it
        summarise("without 2024 (scoring)", fc4[fc4.index.year != 2024], 0.05),
        summarise("1-week target", fc1, 0.05),
        summarise("10% tail", fc10, 0.10),
        summarise("before 2025 rate break", fc_break, 0.05),
        summarise("6-month BIS lag", fc_lag, 0.05),
        #weeks followed by an intervention are left out of the scoring only
        summarise("without interventions (scoring)", fc4[~flag4.reindex(fc4.index)], 0.05),
    ]
    table = pd.DataFrame(rows)

    RESULTS.mkdir(exist_ok=True)
    table.to_csv(RESULTS / "robustness_wf.csv", index=False)
    return table


if __name__ == "__main__":
    print(run().round(4).to_string(index=False))