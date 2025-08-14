import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle

# 1. Load the data
df = pd.read_csv('advertising.csv')

# 2. Define features (X) and target (y)
# We use TV, Radio, and Newspaper spend to predict Sales
features = ['TV', 'Radio', 'Newspaper']
X = df[features]
y = df['Sales']

# 3. Create and train the model
# A simple Linear Regression model is a great start for MMM
model = LinearRegression()
model.fit(X, y)

print("--- Model Training Complete ---")

# Print the model's learned coefficients
# This shows how much sales increase for each unit of ad spend
print(f"Coefficients: {dict(zip(features, model.coef_.round(4)))}")
print(f"Intercept: {model.intercept_.round(4)}")

# 4. Save the trained model
# We save the 'model' object to a file called 'model.pkl'
with open('model.pkl', 'wb') as file:
    pickle.dump(model, file)

print("\nModel saved as model.pkl")