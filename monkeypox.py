from bs4 import BeautifulSoup
from selenium import webdriver
import re
import pandas as pd
import folium
import webbrowser


def get_data():
    """
    @return:
        date:
            date when data was last updated on webpage, with month as 3 letter abbreviation (Month Day Year)

        state_case_dict:
            Key is state and value is case amount. Dictionary contains monkeypox cases for each state in alpha order
                ie. {'Alabama': 20, 'Alaska': 40, ...}
    """
    # Creates webpage and retrieves html text
    url = "https://www.cdc.gov/poxvirus/monkeypox/response/2022/us-map.html"
    driver = webdriver.Chrome('chromedriver.exe')
    driver.get(url)

    # Searches for tags in html to find table containing states and cases
    content = driver.page_source.encode('utf-8').strip()
    soup = BeautifulSoup(content, 'lxml')
    page = soup.find('div', class_='container d-flex flex-wrap body-wrapper bg-white')
    data = page.find('div', class_='cdc-open-viz-module cdc-map-outer-container md')
    table = data.find('div', class_='table-container')

    # Searches for date when the data was last updated
    title = page.find('div', class_='syndicate')
    date = title.find('span', id='dateoutputspan').text
    date = date.split(' ')
    date = date[4] + ' ' + date[3] + ' ' + date[5]

    # Saves each state and corresponding cases into a hash map state_cases_map
    state_cases_dict = {}
    for state_cases in table.find_all('tr'):
        state_cases = state_cases.text.replace(',', '')
        state = re.findall("[a-zA-Z\s]", state_cases)
        cases = re.findall("[0-9]", state_cases)
        state = "".join(state)
        cases = "".join(cases)
        if cases != "" and state != 'District Of Columbia' and state != 'Puerto Rico':
            state_cases_dict[state] = int(cases)

    return date, state_cases_dict


def create_map(updated_date, state_cases_dict):
    """
    @param
        updated_date:
            Date when data was last updated on the website. Month Day Year, with month as 3-letter abbreviation

        state_cases_dict:
            Key is state and value is case amount. Dictionary contains monkeypox cases for each state in alpha order
                ie. {'Alabama': 20, 'Alaska': 40, ...}
    """
    # Use GeoJSON geometry found from URL to create state shapes. States are in alphabetical order
    state_shapes = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json"

    # Separate states and cases into lists, then creates Pandas DataFrame in order for Folium to map data
    states_list = list(state_cases_dict.keys())
    cases_list = list(state_cases_dict.values())
    state_cases_df = pd.DataFrame({'State': states_list, 'Cases': cases_list})

    # Note starting position of map and creates map elements (title/header, legend)
    map_center = [37.5, -95]
    map_usa = folium.Map(location=map_center, zoom_control=True, zoom_start=5)
    legend_name = "Data from CDC, last updated " + updated_date
    total_cases = f'{sum(cases_list):,}' # Adds commas to total cases number for better clarity
    loc = f"Map of {total_cases} Confirmed Monkeypox Cases in US States, by Edward Wang"
    title_html = '''
    <h3 align="center" style="font-size:16px"><b>{}</b></h3>
    '''.format(loc)
    map_usa.get_root().html.add_child(folium.Element(title_html))

    # Create Folium Choropleth with corresponding data, using GeoJSON and Pandas DataFrame
    folium.Choropleth(
        geo_data=state_shapes,
        name="Choropleth of Monkeypox in USA",
        data=state_cases_df,
        columns=['State', 'Cases'],
        key_on='feature.properties.name',
        fill_color="YlOrRd",
        fill_opacity=0.5,
        line_opacity=0.2,
        legend_name=legend_name,
        highlight=True,
        bins=8
    ).add_to(map_usa)

    # Opens new tab with map
    map_usa.save("monkeypox_map.html")
    webbrowser.open("monkeypox_map.html", new=2)


def main():
    """ Driver function that calls other functions"""
    try:
        data = get_data()
    except Exception as e:
        print(f"Could not retrieve data, {e}")

    try:
        create_map(data[0], data[1])
    except Exception as e:
        print(f"Could not create map, {e}")


if __name__ == '__main__':
    main()
