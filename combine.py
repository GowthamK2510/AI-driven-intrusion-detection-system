import pandas as pd

# Load datasets
df_cic = pd.read_csv('cic_ids_2018.csv')
df_unsw = pd.read_csv('unsw_nb15.csv')

# 1. Rename columns to a standard format
df_unsw = df_unsw.rename(columns={
    'dur': 'Flow_Duration',
    'sbytes': 'Total_Fwd_Bytes',
    'dbytes': 'Total_Bwd_Bytes',
    'spkts': 'Total_Fwd_Packets',
    'dpkts': 'Total_Bwd_Packets'
})

# 2. Fix Unit Differences (Critical!)
# Example: Convert UNSW seconds to microseconds to match CIC
df_unsw['Flow_Duration'] = df_unsw['Flow_Duration'] * 1000000 

# 3. Standardize Labels
label_mapping = {
    'DoS-Hulk': 'DoS',
    'DoS-GoldenEye': 'DoS',
    'Reconnaissance': 'Probe',
    'PortScan': 'Probe'
}
df_cic['Label'] = df_cic['Label'].replace(label_mapping)
df_unsw['Label'] = df_unsw['Label'].replace(label_mapping)

# 4. Now you can merge
unified_df = pd.concat([df_cic, df_unsw], ignore_index=True)