import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

def load_data(filepath):
    # UNSW has headers, so we don't need to define column names manually!
    df = pd.read_csv(filepath)
    return df

def preprocess(df):
    # 1. Separate Target (y) from Features (X)
    # In UNSW, the target column is named 'label' (0 for Normal, 1 for Attack)
    # There is also 'attack_cat' (the specific name of attack), but for now let's do Binary (Attack vs Normal)
    
    X = df.drop(columns=['id', 'attack_cat', 'label']) # ID is useless, attack_cat is for detail, label is target
    y = df['label']

    # 2. Define categorical and numerical columns automatically
    # (This is smarter than listing them by hand)
    categorical_cols = X.select_dtypes(include=['object']).columns
    numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns

    # 3. Create Transformers
    # For Numbers: Replace missing values with 0, then Scale them (0 to 1)
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value=0)),
        ('scaler', MinMaxScaler())
    ])

    # For Text (Protocol, Service): Turn them into numbers (OneHotEncoding)
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    # 4. Bundle them into a Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_cols),
            ('cat', categorical_transformer, categorical_cols)
        ])

    return X, y, preprocessor