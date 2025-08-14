import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import pickle

# Adstock and Saturation functions are the same
def apply_adstock(series, decay_rate):
    adstocked_series = np.zeros_like(series, dtype=float)
    adstocked_series[0] = series[0]
    for i in range(1, len(series)):
        adstocked_series[i] = series[i] + decay_rate * adstocked_series[i-1]
    return adstocked_series

def apply_saturation(series, alpha):
    return series ** alpha

df = pd.read_csv('advertising.csv')

# --- FAST DECAY / FAST SATURATION PARAMETERS ---
DECAY_RATE_TV = 0.3
DECAY_RATE_RADIO = 0.4
DECAY_RATE_NEWSPAPER = 0.1
SATURATION_ALPHA_TV = 0.7
SATURATION_ALPHA_RADIO = 0.65
SATURATION_ALPHA_NEWSPAPER = 0.55
# ---

# Apply transformations...
df['TV_adstocked'] = apply_adstock(df['TV'], DECAY_RATE_TV)
df['Radio_adstocked'] = apply_adstock(df['Radio'], DECAY_RATE_RADIO)
df['Newspaper_adstocked'] = apply_adstock(df['Newspaper'], DECAY_RATE_NEWSPAPER)
df['TV_saturated'] = apply_saturation(df['TV_adstocked'], SATURATION_ALPHA_TV)
df['Radio_saturated'] = apply_saturation(df['Radio_adstocked'], SATURATION_ALPHA_RADIO)
df['Newspaper_saturated'] = apply_saturation(df['Newspaper_adstocked'], SATURATION_ALPHA_NEWSPAPER)

features = ['TV_saturated', 'Radio_saturated', 'Newspaper_saturated']
X = df[features]
y = df['Sales']

model = LinearRegression()
model.fit(X, y)

# Save the model with a specific name
with open('model_fast_decay.pkl', 'wb') as file:
    pickle.dump(model, file)

print("--- Fast Decay Model (FMCG) Trained and Saved as model_fast_decay.pkl ---")