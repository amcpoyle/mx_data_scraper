from sx_scraper import get_ind_lap_time, get_lap_chart, get_results
import pandas

# df = get_ind_lap_time("https://www.supercrosslive.com/event/individual-lap-times/S2405/1864030/", 2024)

""" info_df, df = get_lap_chart("https://www.supercrosslive.com/event/lap-chart/S2405/1864030/", 2024)
df.to_csv("C:/mx_data_scraper/test_lc.csv")
"""

df = get_results("https://www.supercrosslive.com/event/official-results/S2405/1864030/", 2024)
