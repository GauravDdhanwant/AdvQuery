#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import streamlit as st
import sqlite3
import openai
import os
import matplotlib.pyplot as plt

class QueryBot:
    def __init__(self, csv_file=None, db_connection=None, api_key=None):
        self.csv_file = csv_file
        self.db_connection = db_connection
        self.api_key = api_key
        self.conn = None

        if csv_file:
            delimiter = self._detect_delimiter(csv_file)
            csv_file.seek(0)  # Reset the file pointer to the beginning after reading for delimiter detection
            self.data = pd.read_csv(csv_file, delimiter=delimiter)
            print("CSV Data loaded into Dataframe : ")
            print(self.data.head())
            self.conn = self._create_in_memory_db(self.data)
            self._print_table_data()
        elif db_connection:
            self.conn = sqlite3.connect(db_connection)
        else:
            raise ValueError("Either a CSV file or database connection must be provided.")

    def _detect_delimiter(self, file):
        file.seek(0)  # Ensure the file pointer is at the beginning
        sample = file.read(1024).decode('utf-8')
        file.seek(0)  # Reset the file pointer to the beginning after reading the sample
        if sample.count(',') > sample.count(';'):
            return ','
        else:
            return ';'


    def _print_table_data(self):
        query = "SELECT * FROM data"
        df = pd.read_sql_query(query, self.conn)
        print("Data in SQLite Database:")
        print(df.head())

    def _create_in_memory_db(self, df):
        conn = sqlite3.connect(":memory:")
        df.to_sql('data', conn, index=False, if_exists='replace')
        return conn

    def generate_sql_query(self, question):
        openai.api_key = self.api_key
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an SQL and 2D graph expert. Generate SQL queries that can be executed directly on an in-memory SQLite database created from a CSV file. Use 'data' as the table name. Do not include any explanations, just return the SQL query."},
                    {"role": "user", "content": f"{question}"}
                ],
                temperature=0.5,
                max_tokens=150,
                n=1,
                stop=None,
                presence_penalty=0,
                frequency_penalty=0.1,
            )
            sql_query = response['choices'][0]['message']['content'].strip()
            return sql_query
        except Exception as e:
            return f"An error occurred with the OpenAI API: {e}"

    def execute_query(self, query):
        try:
            result = pd.read_sql_query(query, self.conn)
            return result
        except Exception as e:
            return f"An error occurred while executing the SQL query: {e}"

    def ask(self, question):
        query = self.generate_sql_query(question)
        result = self.execute_query(query)
        return result, query

    def plot_graph(self, result, question):
        if "plot" in question.lower() or "graph" in question.lower():
            st.write("Plotting graph based on the result...")

            if 'line' in question.lower():
                ax = result.plot(kind='line')
            elif 'bar' in question.lower():
                ax = result.plot(kind='bar')
            elif 'scatter' in question.lower() and result.shape[1] >= 2:
                ax = result.plot(kind='scatter', x=result.columns[0], y=result.columns[1])
            elif 'histogram' in question.lower():
                ax = result.plot(kind='hist', bins=10)
            elif 'pie' in question.lower() and result.shape[1] >= 2:
                result.set_index(result.columns[0]).plot(kind='pie', y=result.columns[1], autopct='%1.1f%%')
            else:
                st.write("Graph type not recognized. Defaulting to line plot.")
                ax = result.plot(kind='line')

            if 'pie' not in question.lower():
                plt.xlabel(result.columns[0])
                plt.ylabel(result.columns[1])
            plt.title("Generated Plot")
            st.pyplot(plt.gcf())
        else:
            st.write("Graph plotting not requested.")

# Streamlit Interface
st.title('Advanced Query Bot')

# Input for OpenAI API key
api_key = st.text_input("Enter OpenAI API Key", type="password")

# File uploader for CSV
csv_file = st.file_uploader("Upload CSV", type=['csv'])

# Text input for database connection string
db_connection = st.text_input("Database Connection String (for SQL Server)")

# Text input for the question
question = st.text_input("Ask your question")

# Initialize QueryBot
if csv_file is not None and api_key:
    bot = QueryBot(csv_file=csv_file, api_key=api_key)
elif db_connection and api_key:
    bot = QueryBot(db_connection=db_connection, api_key=api_key)
else:
    bot = None
    if not api_key:
        st.write("Please enter the OpenAI API key.")
    else:
        st.write("Please upload a CSV file or provide a database connection string.")

# Process the question
if bot and question:
    try:
        result, query = bot.ask(question)
        st.write("Generated SQL Query:", query)
        st.write("Query Result:")
        if isinstance(result, pd.DataFrame):
            st.write(f'<div style="overflow-x: auto;">{result.to_html(index=False)}</div>', unsafe_allow_html=True)
            bot.plot_graph(result, question)
        else:
            st.write(result)
    except Exception as e:
        st.write(f"An error occurred: {e}")

# In[ ]:




