import functools

import pandas as pd
import geopandas as gdp

INDEX_COLUMN = 'SUBURB_CODE'


@functools.cache
def load_raw_geodata():
    geo_data = gdp.read_file('./data/SAL_2021_AUST_GDA2020_SHP.zip')
    geo_data.rename(columns={
        'SAL_CODE21': INDEX_COLUMN,
        'SAL_NAME21': 'Suburb Name',
        'STE_NAME21': 'State',
        'AREASQKM21': 'Area (Km^2)'

    }, inplace=True)
    geo_data.set_index(INDEX_COLUMN, inplace=True)

    return geo_data[[
        'Suburb Name',
        'State',
        # 'Area (Km^2)',
        'geometry'
    ]].to_crs('EPSG:3112')


def map_suburb_to_code(without_code):
    geodata = load_raw_geodata()
    suburb_to_code_mapping = pd.DataFrame(geodata.reset_index()[[INDEX_COLUMN, 'Suburb Name', 'State']])
    suburb_to_code_mapping['Suburb Name'] = suburb_to_code_mapping['Suburb Name'].str.replace(r'\s(?=\().*?\)', '')

    merged_data = without_code.merge(suburb_to_code_mapping).set_index(INDEX_COLUMN)
    return merged_data


@functools.cache
def load_finpoint_data():
    state_mapping = {
        'NSW': 'New South Wales',
        'ACT': 'Australian Capital Territory',
        'WA': 'Western Australia',
        'QLD': 'Queensland',
        'VIC': 'Victoria',
        'NT': 'Northern Territory',
        'SA': 'South Australia',
        'TAS': 'Tasmania'
    }

    finpoint_attributes = pd.read_csv('./data/finpoint attributes.csv')
    finpoint_attributes['STATE'] = finpoint_attributes['STATE'].map(state_mapping)
    finpoint_attributes['LOCALITY'] = finpoint_attributes['LOCALITY'].str.title()
    finpoint_attributes['LOCALITY'] = finpoint_attributes['LOCALITY'].str.replace(r'\s(?=\().*?\)', '')
    finpoint_attributes.rename(
        columns={
            'LOCALITY': 'Suburb Name',
            'STATE': 'State'
        },
        inplace=True
    )

    mapped_data = map_suburb_to_code(finpoint_attributes)

    return mapped_data.iloc[:, 2:]


@functools.cache
def load_seifa_data():
    seifa_data = pd.read_excel(
        'https://www.abs.gov.au/ausstats/subscriber.nsf/log?openagent&2033055001%20-%20ssc%20indexes.xls&2033.0.55.001'
        '&Data%20Cubes&863031D939DE8105CA25825D000F91D2&0&2016&27.03.2018&Latest',
        sheet_name='Table 3',
        usecols='A:D',
        skiprows=4
    )
    seifa_data.rename(
        columns={
            'Unnamed: 3': 'SEIFA Score',
            '2016 State Suburb (SSC) Code': INDEX_COLUMN
        },
        inplace=True
    )
    seifa_data[INDEX_COLUMN] = seifa_data[INDEX_COLUMN].astype(str)
    seifa_data.set_index(INDEX_COLUMN, inplace=True)

    # Add in population density
    # geo_data = load_geodata()
    # seifa_data['Population Density (Km^2 / Person)'] = geo_data['Area (Km^2)'] / seifa_data['Usual Resident Population']
    # seifa_data.drop('Usual Resident Population', axis=1, inplace=True)

    return seifa_data.iloc[1:-2, 1:]


def load_exposure_data():
    exposure_file = pd.read_csv('./data/EXPOSURE_BY_SUBURB.csv')
    exposure_file.rename(columns={
        'suburb_rated': 'Suburb Name'
    },
        inplace=True
    )
    exposure_file = exposure_file.groupby('Suburb Name').agg(Exposure=('exposure', sum))
    exposure_file.reset_index(inplace=True)
    exposure_file['Suburb Name'] = exposure_file['Suburb Name'].str.title()

    # Manually map some of these
    exposure_file['Suburb Name'] = exposure_file['Suburb Name']
    exposure_file['State'] = 'Western Australia'

    merged = map_suburb_to_code(exposure_file)
    return merged.loc[:, 'Exposure']


def load_geodata():
    geo_data = load_raw_geodata()

    indexes = load_exposure_data().index

    return geo_data.loc[indexes, :]

# attribute_data = pd.DataFrame(load_exposure_data()).join(load_finpoint_data().join(load_seifa_data()))
# attribute_data.to_parquet('./data/Suburb Attributes.parquet')
