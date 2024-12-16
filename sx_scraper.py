import time
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import pandas as pd
import numpy as np
from pathlib import Path

def get_soup(url):
    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'}
    req = Request(url,headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'html.parser')
    return soup

def get_event_info(soup):
    # get event info
    event_info = soup.find("div", class_='event-header')
    event_info_divs = event_info.find_all('div')

    series = event_info_divs[0].text
    race = event_info_divs[1].text
    race_loc = event_info_divs[2].text
    round_date = event_info_divs[3].text
    sx_class = event_info_divs[4].text

    return [series, race, race_loc, round_date, sx_class]

# Individual lap time scraper
def get_ind_lap_time(url, year):
    ind_laps = get_soup(url)
    event_info = get_event_info(ind_laps)

    main_tables = ind_laps.find('div', class_='data-content individual-lap-times')
    rider_divs = main_tables.find_all('div', class_='rider')

    rider_names = []
    lap_numbers = []
    lap_times = []
    race_names = []
    race_locs = []
    series_name = []
    round_dates = []
    sx_classes = []

    for rider in rider_divs:
        rider_table = rider.find('table')
        table_header = rider_table.find('thead')
        header_info = table_header.find_all('th')

        rider_pos = header_info[0].text
        
        rider_name_raw = header_info[1].get_text('\n').strip('RIDER - ')
        rider_name = rider_name_raw.split('\n')[0]
        rider_bike = rider_name_raw.split('\n')[1]

        rider_body = rider_table.find('tbody')
        rider_laps = rider_body.find_all('tr')



        for lap in rider_laps:
            lap_info = lap.find_all('td')
            if len(lap_info) > 1: # normal
                lap_num = lap_info[0].text.strip()
                lap_time = lap_info[1].text.strip()

                rider_names.append(rider_name)
                lap_numbers.append(lap_num)
                lap_times.append(lap_time)
                race_names.append(event_info[1])
                race_locs.append(event_info[2])
                series_name.append(event_info[0])
                round_dates.append(event_info[3])
                sx_classes.append(event_info[4])


            else:
                lap_end = lap_info[0].text
            
                if 'Max' in lap_end:
                    lap_num = 'max'
                    lap_time = lap_end.replace('Max: ', '').strip()  

                    rider_names.append(rider_name)
                    lap_numbers.append(lap_num)
                    lap_times.append(lap_time)
                    race_names.append(event_info[1])
                    race_locs.append(event_info[2])
                    series_name.append(event_info[0])
                    round_dates.append(event_info[3])
                    sx_classes.append(event_info[4])
        

                elif 'Min' in lap_end:
                    lap_num = 'min'
                    lap_time = lap_end.replace('Min: ', '').strip()      

                    rider_names.append(rider_name)
                    lap_numbers.append(lap_num)
                    lap_times.append(lap_time)
                    race_names.append(event_info[1])
                    race_locs.append(event_info[2])
                    series_name.append(event_info[0])
                    round_dates.append(event_info[3])
                    sx_classes.append(event_info[4])

                elif 'Avg' in lap_end:
                    lap_num = 'avg'
                    lap_time = lap_end.replace('Avg: ', '').strip()
                    
                    rider_names.append(rider_name)
                    lap_numbers.append(lap_num)
                    lap_times.append(lap_time)
                    race_names.append(event_info[1])
                    race_locs.append(event_info[2])
                    series_name.append(event_info[0])
                    round_dates.append(event_info[3])
                    sx_classes.append(event_info[4])

                else:
                    print('ERROR in individual lap time')
                    print(lap_info)
                    return


        


    df = pd.DataFrame({'rider_name': rider_names, 'lap_num': lap_numbers, 'lap_time': lap_times, 'race': race_names,
                       'location': race_locs, 'series': series_name, 'race_date': round_dates, 'sx_class': sx_classes,
                       'year': [year]*len(rider_names)})

    return df

def get_lap_chart(url, year):
    lap_chart = get_soup(url)
    event_info = get_event_info(lap_chart)

    series, race, race_loc, round_date, sx_class = event_info

    
    lc = lap_chart.find('tbody')
    lc_rows = lc.find_all('tr')
    
    rider_nums = []
    rider_names = []
    positions = []
    positions_dict = {}    
    for idx in range(len(lc_rows)):
        current_td = lc_rows[idx]
        row_tds = current_td.find_all('td')
        for i in range(len(row_tds)):
            if i == 0:
                # rider num
                rider_num = row_tds[i].text.replace('#', '')
                rider_nums.append(int(rider_num))
            elif i == 1:
                # rider name
                rider_name = row_tds[i].text
                rider_names.append(rider_name)
            elif i == 2:
                # row_tds[2] is just a number that shows position for the lap chart
                position = row_tds[i].text
                position = int(position)
                positions.append(position)
            else:
                # we are charting the numbers who are attributed to this position
                current_num = row_tds[i].text.strip()
                if current_num == '':
                    current_num = None
                else:
                    current_num = int(current_num)
                    
                if position not in positions_dict.keys():
                    positions_dict[position] = []
                    
                positions_dict[position].append(current_num)



    info_df = pd.DataFrame({'rider_num': rider_nums, 'rider_name': rider_names})

    # create a df that contains laps as new rows and positions as columns
    num_laps = range(1, len(positions_dict[1]) + 1)

    rider_numbers = []
    lap_numbers = []
    position_numbers = []
        
    for lap_num in num_laps:
        for pos in positions_dict.keys():
            rider_at_time = positions_dict[pos][lap_num-1]
            rider_numbers.append(rider_at_time)
            lap_numbers.append(lap_num)
            position_numbers.append(pos)

    df = pd.DataFrame({'rider_num': rider_numbers, 'lap_num': lap_numbers, 'position_num': position_numbers, 'series': [series]*len(rider_numbers),
                  'race': [race]*len(rider_numbers), 'round_date': [round_date]*len(rider_numbers), 'sx_class': [sx_class]*len(rider_numbers),
                       'year': [year]*len(rider_numbers)})

    return [info_df, df]


# main results
def get_results(url, year):
    main_results = get_soup(url)

    event_info = get_event_info(main_results)
    series, race, race_loc, round_date, sx_class = event_info

    
    data_table = main_results.find('table', class_='data-table')

    tbody = data_table.find('tbody')
    rows = tbody.find_all('tr')

    pos_nums = []
    rider_nums = []
    rider_names = []
    hometowns = []
    bikes = []
    quali_pos = []
    holeshot_bool = []
    laps_led =  []
    finish_pos = []
    points = []

    for i in range(len(rows)):
        row = rows[i]
        row_tds = row.find_all('td')

        pos = row_tds[0].text.replace('Position', '').strip()
        pos_nums.append(int(pos))
        # print(int(pos))
        rider_num = row_tds[1].text.strip()
        rider_nums.append(int(rider_num))
        # print(rider_num)
        rider_name = row_tds[2].text.strip()
        rider_names.append(rider_name)
        # print(rider_name)
        hometown = row_tds[3].text.strip()
        hometowns.append(hometown)
        # print(hometown)
        bike = row_tds[4].text.strip()
        bikes.append(bike)
        # print(bike)
        quali = row_tds[5].text.strip()
        quali_pos.append(int(quali))
        # print(quali)
        holeshot = row_tds[6].text.strip()
        holeshot_bool.append(holeshot)
        # print(holeshot)
        ll = row_tds[7].text.strip()
        laps_led.append(int(ll))
        # print(ll)
        fp = row_tds[8].text.strip()
        finish_pos.append(int(fp))
        # print(fp)
        pts = row_tds[9].text.strip()
        points.append(int(pts))
        # print(pts)

    df = pd.DataFrame({'finish_pos': pos_nums, 'rider_num': rider_nums, 'rider_name': rider_names, 'hometown': hometowns,
                      'bike': bikes, 'quali_pos': quali_pos, 'holeshot': holeshot_bool, 'laps_led': laps_led, 'finish_pos': finish_pos,
                       'points': points, 'year': [year]*len(pos_nums)})

    return df

def get_ind_segments(url, year):
    segs = get_soup(url)

    event_info = get_event_info(segs)
    series, race, race_loc, round_date, sx_class = event_info

    rider_segs = segs.find_all('div', class_='rider')

    rider_names = []
    lap_nums = []
    seg1s = []
    seg2s = []
    seg3s = []
    seg4s = []
    seg5s = []
    laptimes = []
    for i in range(len(rider_segs)):
        rider = rider_segs[i]
        
        rider_name = rider.find('div', class_='rider-name')
        rider_bike = rider.find('div', class_='rider-bike')

        rider_name = rider_name.text
        rider_bike = rider_bike.text

        pattern = '#[0-9]+'
        
        rider_num = re.findall(r'#[0-9]+', rider_name)[0]
        rider_name = re.sub(r'#[0-9]+', '', rider_name)
        rider_name = rider_name.strip()

        table = rider.find('table')
        tbody = table.find('tbody')
        
        rows = tbody.find_all('tr')

        for j in range(len(rows)):
            row = rows[j]
            cells = row.find_all('td')

            row_lap_num = None

            row_text = row.text.strip()
            row_text = row_text.split(' ')
            row_text = [i for i in row_text if i != '\n']
            row_text = [i for i in row_text if i != '\n\n']
            row_text = [i for i in row_text if i != '']

            # there are always five segments
            lap_num = int(row_text[1])
            seg1_time = row_text[2]
            seg2_time = row_text[3]
            seg3_time = row_text[4]
            seg4_time = row_text[5]
            seg5_time = row_text[6]
            
            laptime = row_text[7]

            lap_nums.append(lap_num)
            rider_names.append(rider_name)
            seg1s.append(seg1_time)
            seg2s.append(seg2_time)
            seg3s.append(seg3_time)
            seg4s.append(seg4_time)
            seg5s.append(seg5_time)
            laptimes.append(laptime)

    df = pd.DataFrame({'lap_num': lap_nums, 'rider_name': rider_names, 'seg1_time': seg1s, 'seg2_time': seg2s, 'seg3_time': seg3s,
                       'seg4_time': seg4s, 'seg5_time': seg5s, 'lap_time': laptimes, 'year': [year]*len(lap_nums)})

    return df
