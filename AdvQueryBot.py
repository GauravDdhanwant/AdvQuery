#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import sqlite3
import openai
import os
import streamlit as st
import matplotlib.pyplot as plt

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY", "sk-proj-ngcTYRR6fzSFCpqzfYrPT3BlbkFJOJDriRswr40ORxAPyyHG")

class QueryBot:
    def __init__(self, csv_file=None, db_connection=None):
        self.csv_file = csv_file
        self.conn = None

        if csv_file:
            # Step 1: Read the CSV file into a DataFrame with the correct delimiter
            self.data = pd.read_csv(csv_file, delimiter=',')
            print("CSV Data Loaded into DataFrame:")
            print(self.data.head())  # Print the first few rows of the DataFrame
            
            # Step 2: Create an in-memory SQLite database and store the DataFrame
            self.conn = self._create_in_memory_db(self.data)
            
            # Print the data from the in-memory SQLite database
            self._print_table_data()
    
    def _create_in_memory_db(self, df):
        # Create an in-memory SQLite database
        conn = sqlite3.connect(":memory:")
        
        # Step 3: Store the DataFrame in SQLite
        df.to_sql('data', conn, index=False, if_exists='replace')
        
        return conn
    
    def _print_table_data(self):
        # Print the data from the in-memory SQLite database to verify
        query = "SELECT * FROM data"
        df = pd.read_sql_query(query, self.conn)
        print("Data in SQLite Database:")
        print(df.head())  # Print the first few rows of the table

    def generate_sql_query(self, question):
        # Use OpenAI's chat model to generate an SQL query from the question
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an SQL and 2D graph expert. Generate SQL queries that can be executed directly on an in-memory SQLite database created from a CSV file. Use 'data' as the table name. Do not include any markdown formatting or explanations, just return the SQL query."},
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

    def execute_query(self, query):
        try:
            result = pd.read_sql_query(query, self.conn)
            return result
        except Exception as e:
            return f"An error occurred while executing the SQL query: {e}"

    def plot_graph(self, data, plot_type, columns):
        plt.figure(figsize=(10, 6))
        
        if plot_type == 'histogram':
            plt.hist(data[columns[0]], bins=30, edgecolor='k', alpha=0.7)
            plt.xlabel(columns[0])
            plt.ylabel('Frequency')
            plt.title(f'Histogram of {columns[0]}')
        elif plot_type == 'scatter':
            plt.scatter(data[columns[0]], data[columns[1]])
            plt.xlabel(columns[0])
            plt.ylabel(columns[1])
            plt.title(f'Scatter Plot of {columns[0]} vs {columns[1]}')
        elif plot_type == 'line':
            plt.plot(data[columns[0]], data[columns[1]])
            plt.xlabel(columns[0])
            plt.ylabel(columns[1])
            plt.title(f'Line Plot of {columns[0]} vs {columns[1]}')
        elif plot_type == 'bar':
            plt.bar(data[columns[0]], data[columns[1]])
            plt.xlabel(columns[0])
            plt.ylabel(columns[1])
            plt.title(f'Bar Plot of {columns[0]} vs {columns[1]}')
        else:
            st.write(f"Plot type '{plot_type}' is not supported.")
            return
        
        plt.grid(True)
        st.pyplot(plt)
    
    def ask(self, question, plot_type=None):
        if plot_type:
            # Extract column names from question
            columns = [col.strip() for col in self.data.columns if col.strip() in question]
            if len(columns) == 0:
                st.write("No valid column names found in the question.")
                return None, None
            
            # If scatter, line or bar plot, ensure at least two columns are provided
            if plot_type in ['scatter', 'line', 'bar'] and len(columns) < 2:
                st.write(f"Plot type '{plot_type}' requires at least two columns.")
                return None, None
            
            # Generate SQL to extract the required data
            query = f"SELECT {', '.join(columns)} FROM data"
            data = self.execute_query(query)
            if isinstance(data, pd.DataFrame):
                self.plot_graph(data, plot_type, columns)
                return data, query
            else:
                return data, query
        
        # Default behavior for generating and executing SQL queries
        query = self.generate_sql_query(question)
        result = self.execute_query(query)
        return result, query

# Streamlit Interface
st.title('Advanced Query Bot')

# File uploader for CSV
csv_file = st.file_uploader("Upload CSV", type=['csv'])

# Text input for database connection string
db_connection = st.text_input("Database Connection String (for SQL Server)")

# Text input for the question
question = st.text_input("Ask your question")

# Dropdown menu for plot type
plot_type = st.selectbox("Select Plot Type", [None, 'histogram', 'scatter', 'line', 'bar'])

# Initialize QueryBot
if csv_file is not None:
    bot = QueryBot(csv_file=csv_file)
elif db_connection:
    bot = QueryBot(db_connection=db_connection)
else:
    bot = None
    st.write("Please upload a CSV file or provide a database connection string.")

# Process the question
if bot and question:
    try:
        result, query = bot.ask(question, plot_type)
        st.write("Generated SQL Query:", query)
        st.write("Query Result:")
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        else:
            st.write(result)
    except Exception as e:
        st.write(f"An error occurred: {e}")


# In[ ]:




