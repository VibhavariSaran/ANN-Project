# -*- coding: utf-8 -*-
"""app.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1-v3SIXtwpl4sH_M4O6IOgSo4SVKL5yty
"""

import streamlit as st
import os
import gdown
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Streamlit UI
st.title('📊 Sales Prediction Dashboard - ANN Model')

# Upload dataset
TRAIN_FILE_ID = "1Isp2tA7MnXcNu9le5Lu7wwJNP7Kt67Ky"
STORE_FILE_ID = "1V8tjbvPiC0mI1AF4M4PajYPDt6orWv4e"
TRAIN_PATH = "train.csv"
STORE_PATH = "store.csv"

# Download the datasets automatically if not present
if not os.path.exists(TRAIN_PATH):
    gdown.download(f"https://drive.google.com/uc?id={TRAIN_FILE_ID}", TRAIN_PATH, quiet=False)

if not os.path.exists(STORE_PATH):
    gdown.download(f"https://drive.google.com/uc?id={STORE_FILE_ID}", STORE_PATH, quiet=False)

# Load datasets
train_df = pd.read_csv(TRAIN_PATH)
store_df = pd.read_csv(STORE_PATH)

# Merge the datasets on Store ID
df = train_df.merge(store_df, how="left", on="Store")

# Drop unnecessary columns
df.drop(columns=['Customers', 'PromoInterval'], inplace=True)

# Convert date column to datetime format
df['Date'] = pd.to_datetime(df['Date'])

# Extract date features
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['Day'] = df['Date'].dt.day
df['WeekOfYear'] = df['Date'].dt.isocalendar().week

# Handle missing values
df['CompetitionDistance'].fillna(df['CompetitionDistance'].median(), inplace=True)
df['CompetitionOpenSinceMonth'].fillna(0, inplace=True)
df['CompetitionOpenSinceYear'].fillna(0, inplace=True)
df['Promo2SinceWeek'].fillna(0, inplace=True)
df['Promo2SinceYear'].fillna(0, inplace=True)

# Encoding categorical variables
cat_cols = ['StoreType', 'Assortment', 'StateHoliday']
df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

# Scaling numerical features
num_cols = ['CompetitionDistance', 'CompetitionOpenSinceMonth', 'CompetitionOpenSinceYear',
            'Promo2SinceWeek', 'Promo2SinceYear', 'Year', 'Month', 'Day', 'WeekOfYear']

scaler = StandardScaler()
df[num_cols] = scaler.fit_transform(df[num_cols])

# Show the pre-processed dataset
st.write("### 🔍 Pre-processed Dataset Preview:", df.head())

# Save pre-processed dataset
PREPROCESSED_PATH = "Preprocessed_sales_data.csv"
df.to_csv(PREPROCESSED_PATH, index=False)

# Provide a download link in Streamlit
st.download_button(label="📥 Download Preprocessed Data",
                   data=open(PREPROCESSED_PATH, "rb"),
                   file_name="Preprocessed_sales_data.csv",
                   mime="text/csv")

# Train-Test Split
X = df.drop(columns=['Sales', 'Date'])
y = df['Sales']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

st.write("✅ Data Preprocessing Complete!")

# Sidebar for Hyperparameter Selection
st.sidebar.header("Model Hyperparameters")
num_layers = st.sidebar.slider("Number of Hidden Layers", 1, 5, 3)
neurons_per_layer = st.sidebar.slider("Neurons per Layer", 32, 256, 128)
activation = st.sidebar.selectbox("Activation Function", ['relu', 'tanh', 'sigmoid'])
dropout_rate = st.sidebar.slider("Dropout Rate", 0.0, 0.5, 0.3)
optimizer = st.sidebar.selectbox("Optimizer", ['adam', 'sgd', 'rmsprop'])
learning_rate = st.sidebar.slider("Learning Rate", 0.0001, 0.01, 0.001)
epochs = st.sidebar.slider("Number of Epochs", 10, 100, 50)

# Model Training Button
if st.button("🚀 Train Model"):
    with st.spinner('Training ANN Model... Please wait!'):
        # Build ANN Model
        model = Sequential()
        model.add(Dense(neurons_per_layer, activation=activation, input_shape=(X_train.shape[1],)))
        model.add(BatchNormalization())
        model.add(Dropout(dropout_rate))

        for _ in range(num_layers - 1):
            model.add(Dense(neurons_per_layer, activation=activation))
            model.add(BatchNormalization())
            model.add(Dropout(dropout_rate))

        model.add(Dense(1, activation='linear'))

        optimizer_dict = {"adam": Adam(learning_rate=learning_rate),
                          "sgd": SGD(learning_rate=learning_rate),
                          "rmsprop": RMSprop(learning_rate=learning_rate)}

        model.compile(loss='mse', optimizer=optimizer_dict[optimizer], metrics=['mae'])

        history = model.fit(X_train, y_train, validation_data=(X_test, y_test),
                            epochs=epochs, batch_size=64, verbose=1)

        st.success("🎉 Model Training Completed!")

        # Performance Metrics Plots (Loss & MAE)
        st.subheader("Model Performance Over Epochs")

        fig, ax = plt.subplots(1, 2, figsize=(12, 5))

        # Plot MAE (Mean Absolute Error)
        ax[0].plot(history.history['mae'], label='Training MAE', color='blue')
        ax[0].plot(history.history['val_mae'], label='Validation MAE', color='orange')
        ax[0].legend()
        ax[0].set_title('📈 Mean Absolute Error (MAE)')
        ax[0].set_xlabel('Epochs')
        ax[0].set_ylabel('MAE')

        # Plot Loss (Mean Squared Error)
        ax[1].plot(history.history['loss'], label='Training Loss (MSE)', color='blue')
        ax[1].plot(history.history['val_loss'], label='Validation Loss (MSE)', color='orange')
        ax[1].legend()
        ax[1].set_title('📉 Model Loss (MSE)')
        ax[1].set_xlabel('Epochs')
        ax[1].set_ylabel('Loss')

        st.pyplot(fig)

        # 📈 Plot Actual vs Predicted Sales
        y_pred = model.predict(X_test)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.scatter(y_test, y_pred, alpha=0.5, label='Predicted vs Actual', color='royalblue')
        ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', label='Perfect Prediction')
        ax.set_xlabel('Actual Sales')
        ax.set_ylabel('Predicted Sales')
        ax.set_title('📊 Actual vs Predicted Sales')
        ax.legend()
        st.pyplot(fig)

        # 📉 Residual Plot - difference between the actual and predicted sales
        residuals = y_test - y_pred.flatten()
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.scatter(y_pred, residuals, alpha=0.5, color='purple')
        ax.axhline(0, color='red', linestyle='--')
        ax.set_xlabel('Predicted Sales')
        ax.set_ylabel('Residuals')
        ax.set_title('📉 Residual Plot')
        st.pyplot(fig)

        # 🔥 Feature Importance Plot
        importances = np.mean(np.abs(model.get_weights()[0]), axis=1)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(X.columns, importances, color='skyblue')
        ax.set_title('🔥 Feature Importance')
        ax.set_xlabel('Features')
        ax.set_ylabel('Importance')
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)


        # 🎯 Sales Distribution Plot : How scaling impacts the data distribution
        fig, ax = plt.subplots(1, 2, figsize=(14, 6))

        # Before Scaling
        ax[0].hist(train_df['Sales'], bins=50, color='lightblue', alpha=0.7)
        ax[0].set_title('📊 Sales Distribution (Before Scaling)')
        ax[0].set_xlabel('Sales')
        ax[0].set_ylabel('Frequency')

        # After Scaling
        ax[1].hist(y_train, bins=50, color='lightgreen', alpha=0.7)
        ax[1].set_title('📈 Sales Distribution (After Scaling)')
        ax[1].set_xlabel('Scaled Sales')
        ax[1].set_ylabel('Frequency')

        st.pyplot(fig)

        # Final Evaluation
        y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100  # Mean Absolute Percentage Error
        r2 = r2_score(y_test, y_pred)

        st.write("### ✅ Model Evaluation Metrics")
        st.write(f"📈 **Mean Squared Error (MSE):** {mse:.4f}")
        st.write(f"📊 **Root Mean Squared Error (RMSE):** {rmse:.4f}")
        st.write(f"📉 **Mean Absolute Error (MAE):** {mae:.4f}")
        st.write(f"🔢 **R² Score:** {r2:.4f}")
        st.write(f"📏 **Mean Absolute Percentage Error (MAPE):** {mape:.2f}%")


        # Model Summary
        st.write("### 🔥 Model Summary")
        for layer in model.layers:
            output_shape = layer.output_shape if hasattr(layer, 'output_shape') else "N/A"
            st.write(f"Layer: {layer.name}, Output Shape: {output_shape}, Parameters: {layer.count_params()}")