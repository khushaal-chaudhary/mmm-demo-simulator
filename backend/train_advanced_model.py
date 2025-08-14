import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import pickle

# --- Adstock Transformation Function ---
def apply_adstock(series, decay_rate):
    adstocked_series = np.zeros_like(series, dtype=float)
    adstocked_series[0] = series[0]
    for i in range(1, len(series)):
        adstocked_series[i] = series[i] + decay_rate * adstocked_series[i-1]
    return adstocked_series

# --- Saturation Transformation Function ---
def apply_saturation(series, alpha):
    return series ** alpha

# 1. Load the data
df = pd.read_csv('advertising.csv')

# 2. Define decay and saturation parameters
# In a real-world project, these would be tuned and optimized.
# Here, we'll use common industry values.
DECAY_RATE_TV = 0.5
DECAY_RATE_RADIO = 0.6
DECAY_RATE_NEWSPAPER = 0.2

SATURATION_ALPHA_TV = 0.8
SATURATION_ALPHA_RADIO = 0.75
SATURATION_ALPHA_NEWSPAPER = 0.6

# 3. Apply Adstock Transformation
df['TV_adstocked'] = apply_adstock(df['TV'], DECAY_RATE_TV)
df['Radio_adstocked'] = apply_adstock(df['Radio'], DECAY_RATE_RADIO)
df['Newspaper_adstocked'] = apply_adstock(df['Newspaper'], DECAY_RATE_NEWSPAPER)

# 4. Apply Saturation Transformation
df['TV_saturated'] = apply_saturation(df['TV_adstocked'], SATURATION_ALPHA_TV)
df['Radio_saturated'] = apply_saturation(df['Radio_adstocked'], SATURATION_ALPHA_RADIO)
df['Newspaper_saturated'] = apply_saturation(df['Newspaper_adstocked'], SATURATION_ALPHA_NEWSPAPER)

# 5. Define features (X) and target (y) using the transformed columns
features = ['TV_saturated', 'Radio_saturated', 'Newspaper_saturated']
X = df[features]
y = df['Sales']

# 6. Create and train the model
model = LinearRegression()
model.fit(X, y)

print("--- Advanced Model Training Complete (Adstock & Saturation) ---")
print(f"Coefficients: {dict(zip(features, model.coef_.round(4)))}")
print(f"Intercept: {model.intercept_.round(4)}")

# 7. Save the new model, overwriting the old one
with open('model.pkl', 'wb') as file:
    pickle.dump(model, file)

print("\nAdvanced model saved as model.pkl")