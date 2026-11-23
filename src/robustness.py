""" Does each hypothesis keep its sign when changing the choice we made """

#variations: change one per run and keep everything else the same
#1. use 1-week forward carry instead of 4-week
#2. use quantile level 10% instead of 5%
#3. start sample from 2010 instead of 2000
#4. exclude 2024 unwind from sample
#5. exclude weeks before MoF intervention

import pandas as pd
from src import config
from src import quantile_regressions as qr

TAU = 0.05


""" QUANTILE REGRESSION """

#T/F MoF intervention feature that we decided to remove from `modellin_table` to use in `robustness` instead
def intervention_ahead(amount, weeks):
    """ True when an intervention happens in any of the next `weeks` weeks """
    return sum([amount.shift(-i) > 0 for i in range(1, weeks + 1)]) > 0

#uses Thomas' qr code but changes one variation at a time and return results
def run_one(name, df, target, tau):
    """ Fit one variation and return coefficients with bootstrap intervals """
    formula = f"{target} ~ " + " + ".join(qr.FEATURES)
    coef = qr.fit(df, tau, formula=formula)
    ci = qr.block_bootstrap(df, tau, formula=formula)
    out = pd.DataFrame({"coef": coef, "ci_low": ci.loc[0.025], "ci_high": ci.loc[0.975]})
    out = out.drop(index="Intercept").rename_axis("feature").reset_index()
    out.insert(0, "variation", name)
    return out

#sets out in code the variations that we are interested in, runs the regressions, checks sign alignment, saves results
def run():
    raw = pd.read_parquet(config.DIRECTORY / "modelling_table.parquet") #Thomas' loader throws away intervention columns, so we need to bring them back from `modelling_table`
    d4 = qr.load_data() # 4-week target
    d1 = qr.load_data("fwd_carry_1w") # 1-week target

    amount = raw["yen_buy_amt"] + raw["yen_sell_amt"]
    flag4 = intervention_ahead(amount, 4).reindex(d4.index)

    runs = [
        ("baseline", d4, "fwd_carry_4w", TAU),
        ("1-week target", d1, "fwd_carry_1w", TAU),
        ("10% tail", d4, "fwd_carry_4w", 0.10),
        ("from 2010", d4.loc["2010-01-01":], "fwd_carry_4w", TAU),
        ("without 2024 unwind", d4.drop(d4.loc["2024-06-01":"2024-08-31"].index), "fwd_carry_4w", TAU),
        ("without interventions", d4[~flag4], "fwd_carry_4w", TAU),
    ]

    #runs regression for for each variation and stacks results in a table
    table = pd.concat([run_one(*r) for r in runs], ignore_index=True) 

    #sign check
    base = table[table["variation"] == "baseline"].set_index("feature")["coef"]
    table["same_sign_as_baseline"] = (table["coef"] > 0) == (table["feature"].map(base) > 0)

    qr.RESULTS.mkdir(exist_ok=True)
    table.to_csv(qr.RESULTS / "robustness.csv", index=False)
    return table

#need this to prevet launching the whole analysis (including lengthy bootstrap) when importing the file
if __name__ == "__main__":
    print(run().round(4).to_string(index=False))
