from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import pandas as pd

# post_code_mapping = pl.scan_csv('./data/australian_postcodes.csv').collect().to_pandas()
modelling_df_nonprocessed = pd.read_parquet('./data/suburb attributes.parquet')
modelling_df = modelling_df_nonprocessed.drop('Exposure', axis=1)
modelling_cols = modelling_df.columns
data = SimpleImputer().fit_transform(modelling_df)

modelling_df = pd.DataFrame(
    data=StandardScaler().fit_transform(data),
    index=modelling_df_nonprocessed.index,
    columns=modelling_cols
)
