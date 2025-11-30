# trains a tiny model on synthetic data and saves model.pkl
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor

def make_data(n=2000):
    t = np.arange(n)
    base = 30 + 8*np.sin(2*np.pi*t/144)  # gentle seasonality
    noise = np.random.normal(0,3,size=n)
    series = base + noise
    return pd.DataFrame({'value': series})

df = make_data(2500)
# lag features 1..10
for lag in range(1,11):
    df[f'lag_{lag}'] = df['value'].shift(lag)
df = df.dropna().reset_index(drop=True)
X = df[[f'lag_{i}' for i in range(1,11)]].values
y = df['value'].values

model = RandomForestRegressor(n_estimators=50, random_state=42)
model.fit(X, y)
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
print("Saved model.pkl")
