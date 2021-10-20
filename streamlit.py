import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from matplotlib.lines import Line2D

# @st.cache()
# def get_overlap_date_list(Lebron_first_season_date, Kobe_last_season_date):
#     overlap_days = (Kobe_last_season_date - Lebron_first_season_date).days
#     overlap_date_list = [datetime.strftime(Lebron_first_season_date + timedelta(days=i), '%Y-%m-%d') for i in range(overlap_days+1)]
#     return overlap_date_list

# get season start date of every year
def get_year_of_season(time):
    if time.month <= 8:
        year = time.year - 1
    else:
        year = time.year
    return year

type_to_column_name = {
    'Points':  "PTS",
    'Rebounds': "TRB",
    'Assists': "AST",
    'Steals': "STL",
    "Blocks": "BLK",
    "Turnovers": "TOV",
    "Personal Fouls": "PF",
    "Game Score": "GmSc",
    "Field Goal Percentage": "FG%",
    "3-Point Field Goal Percentage": "3P%",
    "Free Throws": "FT",
    "Free Throws Percentage": "FT%"
}
type_to_tick_spacing= {
    'Points':  3,
    'Rebounds': 1,
    'Assists': 1,
    'Steals': 1,
    "Blocks": 1,
    "Turnovers": 1,
    "Personal Fouls": 1,
    "Game Score": 2,
    "Field Goal Percentage": 0.1,
    "3-Point Field Goal Percentage": 0.1,
    "Free Throws": 1,
    "Free Throws Percentage": 0.1
}

@st.cache
def get_all_granularity_data(data):
    granularity_data = {}

    granularity_data["Day"] = data
    
    data_add_week = data.copy()
    data_add_week["Date"] = data_add_week["Date"].apply(lambda x: x - timedelta(days=x.isoweekday() % 7))
    data_groupby_week = data_add_week.groupby(by=["Player", "Date"]).mean().reset_index()
    data_groupby_week['Color'] = data_groupby_week["Player"].apply(lambda x: "y" if x == "Kobe Bryant" else "b")

    granularity_data["Week"] = data_groupby_week

    data_add_month = data.copy()
    data_add_month["Date"] = data_add_month["Date"].apply(lambda x: x.replace(day=1))
    data_groupby_month = data_add_month.groupby(by=["Player", "Date"]).mean().reset_index()
    data_groupby_month['Color'] = data_groupby_month["Player"].apply(lambda x: "y" if x == "Kobe Bryant" else "b")
    granularity_data["Month"] = data_groupby_month

    data_add_year = data.copy()
    data_add_year["Date"] = data_add_year["Date"].apply(lambda x: datetime.strptime(str(get_year_of_season(x)), "%Y"))
    data_groupby_year = data_add_year.groupby(by=["Player", "Date"]).mean().reset_index()
    data_groupby_year['Color'] = data_groupby_year["Player"].apply(lambda x: "y" if x == "Kobe Bryant" else "b")
    granularity_data["Year"] = data_groupby_year

    granularity_data["Regular/Playoff"] = data.groupby(by=["Player", "RSorPO"]).mean().reset_index()

    return granularity_data

@st.cache
def get_plot_data(granularity_data, data_type, start_date, end_date, granularity, align_career_time, career_time_diff):
    selected_granularity_data = granularity_data[granularity].copy()
    if align_career_time:
        selected_granularity_data.loc[selected_granularity_data["Player"] == "Kobe Bryant", "Date"] += career_time_diff
    return selected_granularity_data[selected_granularity_data["Date"].between(start_date, end_date)][["Date", type_to_column_name[data_type], "Color"]]

if __name__ == '__main__':
    # clean data
    all_games_stats = pd.read_csv('Player_Data/allgames_stats.csv')
    all_games_stats = all_games_stats[all_games_stats["Player"].isin(['Kobe Bryant', 'Lebron James'])]
    all_games_stats['Date'] = all_games_stats["Date"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))
    all_games_stats['Color'] = all_games_stats["Player"].apply(lambda x: "y" if x == "Kobe Bryant" else "b")

    salary = pd.read_csv('Player_Data/salaries.csv')
    salary = salary[salary["Player"].isin(['Kobe Bryant', 'Lebron James'])]
    salary["Date"] = salary["Season"].apply(lambda x: datetime.strptime(x.split("-")[0], "%Y"))
    salary["Salary"] = salary["Salary"].apply(lambda x: float(x[1:]) / 1e6)
    Kobe_salary = salary[salary["Player"] == "Kobe Bryant"]
    Lebron_salary = salary[salary["Player"] == "Lebron James"]

    # get data of both players
    Kobe_all_games_stats = all_games_stats[all_games_stats['Player'] == 'Kobe Bryant']
    Lebron_all_games_stats = all_games_stats[all_games_stats['Player'] == 'Lebron James']

    season_start_time = {}
    for game_time in all_games_stats["Date"].tolist():
        game_year = get_year_of_season(game_time)
        if game_year not in season_start_time.keys():
            season_start_time[game_year] = game_time
        elif season_start_time[game_year] > game_time:
            season_start_time[game_year] = game_time

    # get first and last game date of two players (not currently used)
    Kobe_first_season_date = min(Kobe_all_games_stats['Date'])
    Lebron_first_season_date = min(Lebron_all_games_stats['Date'])

    Kobe_last_season_date = max(Kobe_all_games_stats['Date'])
    Lebron_last_season_date = max(Lebron_all_games_stats['Date'])

    career_time_diff = Lebron_first_season_date - Kobe_first_season_date

    granularity_data = get_all_granularity_data(all_games_stats)

    # get overlap days
    overlap_days = (Lebron_last_season_date - Kobe_first_season_date + career_time_diff).days
    overlap_date_list = [datetime.strftime(Kobe_first_season_date + timedelta(days=i), '%Y-%m-%d') for i in range(overlap_days+1)]

    # get selected display days
    start_date, end_date = st.select_slider(
            'Select display time range',
            options=overlap_date_list,
            value=(datetime.strftime(Kobe_first_season_date, '%Y-%m-%d'), datetime.strftime(Lebron_last_season_date, '%Y-%m-%d')))
    data_type = st.selectbox("Which type of data?", ('Points', 'Rebounds', 'Assists', 'Steals', "Blocks", "Turnovers", "Personal Fouls", "Game Score", "Field Goal Percentage", "3-Point Field Goal Percentage", "Free Throws", "Free Throws Percentage"))
    granularity = st.selectbox("What's the granularity?", ('Day', 'Week', 'Month', 'Year'))
    show_salary = st.checkbox('Show salary')
    align_career_time = st.checkbox('Align Career Time')

    # get plot data
    plot_data = get_plot_data(granularity_data, data_type, start_date, end_date, granularity, align_career_time, career_time_diff)
    if align_career_time:
        Kobe_salary["Date"] += career_time_diff

    fig, ax1 = plt.subplots()

    # plot scatter
    ax1.scatter(plot_data["Date"], plot_data[type_to_column_name[data_type]], c=plot_data["Color"].values, alpha=0.4, edgecolors='none')
    locator = plticker.MultipleLocator(type_to_tick_spacing[data_type])
    ax1.yaxis.set_major_locator(locator)

    # set legend
    lines1 = [
        Line2D([0], [0], marker='o', color='w', alpha=0.5, label='Kobe Bryant', markerfacecolor='y'),
        Line2D([0], [0], marker='o', color='w', alpha=0.5, label='LeBron James', markerfacecolor='b'),
    ]
    labels1 = [
        "Kobe Bryant",
        "LeBron James",
    ]

    if show_salary:

        ax2 = ax1.twinx()
        ax2.fill_between(Kobe_salary[Kobe_salary["Date"].between(start_date, end_date)]["Date"], 0, Kobe_salary[Kobe_salary["Date"].between(start_date, end_date)]["Salary"], alpha=0.15, edgecolors='none', label="Kobe Bryant")
        ax2.fill_between(Lebron_salary[Lebron_salary["Date"].between(start_date, end_date)]["Date"], 0, Lebron_salary[Lebron_salary["Date"].between(start_date, end_date)]["Salary"], alpha=0.15, edgecolors='none', label="LeBron James")
        ax2.yaxis.set_major_formatter(plticker.FormatStrFormatter('$%.1fm'))
    
    # set legend
    if show_salary:
        legend_elements = [Line2D([0], [0], marker='o', color='w', alpha=0.5, label='LeBron James', markerfacecolor='b'),
                        Line2D([0], [0], marker='o', color='w', alpha=0.5, label='Kobe Bryant', markerfacecolor='y')]
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2)
    else:
        ax1.legend(lines1, labels1)



    # plot
    st.pyplot(fig)
