"""
Script to scrape the data from wikipedia about when countries have legalised same-sex marriage and
then plot it in an animated chloropleth
"""
import requests
from loguru import logger
import pandas as pd
import regex as re
from bs4 import BeautifulSoup
import pycountry
import plotly.express as px


def get_countries_from_string(string_val: str):
    """
    Extracts countries from string in the format 'Spain (2002) Canada (30)'
    Replaces '[nationwide]' with ''
    """
    string_list = re.split(pattern=r'\s\(.*?\)', string=string_val)
    cleaned_string_list = [
        string.replace('[nationwide]', '').strip()
        for string in string_list if string.strip() != '']
    return cleaned_string_list


def load_same_sex_marriage_data():
    """
    Imports same sex marriage data from https://en.wikipedia.org/wiki/Same-sex_marriage into a
    pd.DataFrame with the columns ['year','country']
    """
    response = requests.get(
        url="https://en.wikipedia.org/wiki/Same-sex_marriage"
    )
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': "wikitable"})

    raw_html = pd.read_html(str(table), flavor='html5lib')
    same_sex_df = pd.DataFrame(raw_html[0])
    same_sex_df.columns = ['year', 'country']
    logger.info(
        f'Loaded same sex marriage data. Shape {same_sex_df.shape}')
    return same_sex_df


def clean_same_sex_marriage_data(same_sex_df: pd.DataFrame):
    """
    Clean data by:
    - Splitting n countries in a single row to n rows
    - Manually renaming countries so they are compatible with the ISO code lookup
    - Removing 'Pending' legalisations
    """
    same_sex_df.dropna(axis=0, inplace=True)
    same_sex_df['country'] = same_sex_df['country'].map(
        lambda x: get_countries_from_string(x))
    same_sex_df = same_sex_df.explode('country').reset_index()
    same_sex_df.dropna(axis=0, inplace=True)
    same_sex_df['country'] = same_sex_df['country'].replace(
        {'England and Wales': 'United Kingdom',
         'Taiwan': 'Taiwan, Province of China'}
    )
    same_sex_df = same_sex_df.loc[same_sex_df['year'] != 'Pending']
    same_sex_df['year'] = same_sex_df['year'].astype(int)

    logger.info(
        f'Cleaned same sex marriage data. Shape {same_sex_df.shape}')
    return same_sex_df


def get_iso_code_from_country(country: str):
    """
    Given a country name, returns the ISO-3 code
    """
    try:
        info = pycountry.countries.get(name=country)
        return info.alpha_3
    except AttributeError:
        return None
    except Exception as error:
        logger.error(
            f"Error occured. Arguments {error.args}.")
        raise


def add_iso_code_to_data(same_sex_df: pd.DataFrame):
    """
    Adds 'iso_code' column to dataframe where value in 'country' column is a country
    """
    same_sex_df['iso_code'] = same_sex_df['country'].map(
        lambda x: get_iso_code_from_country(x))
    unmatched_countries_array = same_sex_df['iso_code'].isnull()
    unmatched_countries_str = sorted(
        list(same_sex_df[unmatched_countries_array]["country"]))
    logger.debug(
        f'Unmatched "countries" are {unmatched_countries_str}')
    same_sex_df.dropna(axis=0, inplace=True)
    logger.info('Extracted ISO codes for countries')
    return same_sex_df


def plot_chloropleth(same_sex_df: pd.DataFrame):
    """
    Returns a chloropleth map in the web browser
    """
    fig = px.choropleth(same_sex_df,
                        locations='iso_code',
                        color="year",
                        hover_data=['year', 'country'],
                        color_continuous_scale='Plasma',
                        height=600
                        )
    fig.update_layout(
        title={
            'text': 'Same Sex Marriage Legalisation By Year',
            'x': 0.5,
            'xanchor': 'center'
        })
    fig.show()


def main():
    same_sex_df = load_same_sex_marriage_data()
    same_sex_df = clean_same_sex_marriage_data(same_sex_df)
    same_sex_df = add_iso_code_to_data(same_sex_df)
    plot_chloropleth(same_sex_df)


if __name__ == "__main__":
    main()
