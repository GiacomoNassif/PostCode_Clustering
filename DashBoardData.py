import polars as pl
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
import pandas as pd


INDEX_COLUMN = 'Postcode'

#exposure_data = pl.scan_parquet('./data/Postcode Exposure.parquet')
#exposure_data_summarised = exposure_data.groupby('suburb_rated').agg(pl.col('exposure').sum())
# exposure_data_mapped = exposure_data_summarised.join(
#     post_code_mapping,
#     left_on='suburb_rated',
#     right_on='locality',
#     how='left'
# )


postcode_geodata = gpd.read_file('./data/1270055003_poa_2016_aust_shape.zip')
postcode_geodata.rename(columns={'POA_CODE16': INDEX_COLUMN}, inplace=True)
postcode_geodata[INDEX_COLUMN] = postcode_geodata[INDEX_COLUMN].astype(int)
postcode_geodata.set_index(INDEX_COLUMN, inplace=True)
postcode_geodata.to_parquet('./data/postcode_geodata.parquet')
# postcode_geodata.to_crs(inplace=True)


# post_code_mapping = pl.scan_csv('./data/australian_postcodes.csv').collect().to_pandas()

seifa_data = pl.read_parquet('./data/SEIFA Postcode Data.parquet').to_pandas()
seifa_data.set_index(INDEX_COLUMN, inplace=True)
seifa_data.dropna(inplace=True)

modelling_df_nonprocessed = seifa_data
modelling_df = StandardScaler().fit_transform(modelling_df_nonprocessed)

modelling_df = pd.DataFrame(
    data=StandardScaler().fit_transform(modelling_df_nonprocessed),
    index=modelling_df_nonprocessed.index,
    columns=modelling_df_nonprocessed.columns
)

modelling_df.insert(0, 'Lat', postcode_geodata.centroid.x)
modelling_df.insert(1, 'Long', postcode_geodata.centroid.y)
