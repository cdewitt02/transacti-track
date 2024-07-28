# secrets
from dotenv import load_dotenv
import os

# plaid
import numpy as np
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest

import datetime

# email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# db
import sqlite3

# matplot/image buffer
import matplotlib.pyplot as plt
import io


# Load secrets from .env file and assign to variables
load_dotenv()

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD =os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
db_path = 'transactions.db'


config = plaid.Configuration(
    host=plaid.Environment.Sandbox,  # or Environment.Development or Environment.Production
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)
client = plaid_api.PlaidApi(plaid.ApiClient(config))

end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(weeks=1)

 
def summary(transactions:str, db_path:str) -> None:
    
# Generates a dictionary from the transactions JSON, generating a spending total for each category  
# and and adds a total category summing the spending across all categories. Inserts the week
# into the transactions database

# params: 
#   transactions: JSON response from Plaid API endpoint /transactions/get
#   db_path: path to the sqlite3 database
# 
# Calls funtions to pull previous data from sqlite3 database and send email
    
    category_dict = {}
    total = 0
    for transaction in transactions:
        category = transaction.category[0].replace(' ', '_') #category[0] = primary category
        amount = round(transaction.amount, 2)
        if category not in category_dict and amount > 0: 
            category_dict[category] = amount
            total += amount
        elif amount > 0:
            category_dict[category] = round(category_dict.get(category) + amount, 2)
            total += amount
    
    conn=sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    
    columns = ['start_date', 'end_date', 'TOTAL'] + list(category_dict.keys())
    placeholders = ['?'] * len(columns)

    sql = f'''
    INSERT INTO transactions ({', '.join(columns)})
    VALUES ({', '.join(placeholders)})
    '''
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    values = [start_date_str, end_date_str, total] + list(category_dict.values())

    cursor.execute(sql, values)
    columns = [
        "INCOME", "TRANSFER_IN", "TRANSFER_OUT", "LOAN_PAYMENTS", "BANK_FEES", "ENTERTAINMENT",
        "FOOD_AND_DRINK", "GENERAL_MERCHANDISE", "HOME_IMPROVEMENT", "MEDICAL", "PERSONAL_CARE",
        "GENERAL_SERVICES", "GOVERNMENT_AND_NON_PROFIT", "TRANSPORTATION", "TRAVEL",
        "RENT_AND_UTILITIES", "PAYMENT", "TRANSFER", "RECREATION", "TOTAL"
    ]

    for column in columns:
        cursor.execute(f'''
            UPDATE transactions
            SET {column} = COALESCE({column}, 0)
        ''')
    conn.commit()

    conn.close()
    
    img_buffers = get_data(db_path=db_path)
    email(category_dict, img_buffers)
    
def email(summary:dict, img_buffers:list) -> None:
    
# Sends email to receiver address using Simple Mail Transfer Protocol (SMTP)
# 
# params: 
#   summary: type: dictionary
# 
#            category_dict generated from the summary function, has total spent per category and 
#            total spent across all categories for the week
# 
#   img_buffers: type: List
# 
#               list of io.BytesIO objects containing matplotlib.pyplot images comparing this week's
#               spending to the average spending/last week's spending
    
    try:
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        summary_items = '\n'.join([f"{key}: {value}" for key, value in summary.items()])
        subject = f"Weekly Transaction Report for {start_date_str} to {end_date_str}"
        body = f"""Summary: \n{summary_items}"""
    
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = subject 
        msg.attach(MIMEText(body, 'plain'))
        
        for buf in img_buffers:
            image = MIMEImage(buf.read())
            msg.attach(image)
        
        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT))
        server.starttls()
        
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        
        server.quit()
    
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def get_data(db_path:str):
    
    # Retrieves data from sqlite3 database and prepares it for pyplot functions
    # 
    # param: db_path: type: str
    # 
    #                   Path to the database
    # 
    # Calls the graphing functions to generate pyplots, also calls the function to save images to io buffers:
    #           plot_bar_chart_negative
    #           plot_bar_chart_positive
    #           plot_pie_chart
    #           save_figures_to_buffer

            
    
    figs = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    columns = [
        'ID', 'START_DATE', 'END_DATE',"INCOME", "TRANSFER_IN", "TRANSFER_OUT", "LOAN_PAYMENTS", "BANK_FEES", "ENTERTAINMENT",
        "FOOD_AND_DRINK", "GENERAL_MERCHANDISE", "HOME_IMPROVEMENT", "MEDICAL", "PERSONAL_CARE",
        "GENERAL_SERVICES", "GOVERNMENT_AND_NON_PROFIT", "TRANSPORTATION", "TRAVEL",
        "RENT_AND_UTILITIES", "PAYMENT", "TRANSFER", "RECREATION", "TOTAL"
    ]

    columns_to_select = [col for col in columns if col not in ['ID', 'START_DATE', 'END_DATE']]
    
    # Get the week
    columns_str = ', '.join(columns_to_select)
    sql_curr_week = f'SELECT {columns_str} FROM transactions WHERE id = (SELECT MAX(id) FROM transactions)'

    cursor.execute(sql_curr_week)
    curr_week = cursor.fetchone()
    curr_week_data = {
        "INCOME": curr_week[0],
        "TRANSFER_IN": curr_week[1],
        "TRANSFER_OUT": curr_week[2],
        "LOAN_PAYMENTS": curr_week[3],
        "BANK_FEES": curr_week[4],
        "ENTERTAINMENT": curr_week[5],
        "FOOD_AND_DRINK": curr_week[6],
        "GENERAL_MERCHANDISE": curr_week[7],
        "HOME_IMPROVEMENT": curr_week[8],
        "MEDICAL": curr_week[9],
        "PERSONAL_CARE": curr_week[10],
        "GENERAL_SERVICES": curr_week[11],
        "GOVERNMENT_AND_NON_PROFIT": curr_week[12],
        "TRANSPORTATION": curr_week[13],
        "TRAVEL": curr_week[14],
        "RENT_AND_UTILITIES": curr_week[15],
        "PAYMENT": curr_week[16],
        "TRANSFER": curr_week[17],
        "RECREATION": curr_week[18],
        "TOTAL": curr_week[19]
    }
    
    cursor.execute("SELECT MAX(id) FROM transactions")
    max_id = cursor.fetchone()[0]
    
    # Check if max_id is greater than 1
    if max_id and max_id > 1:
        target_id = max_id - 1
        sql_last_week = f'SELECT {columns_str} FROM transactions WHERE id = ?'
        params = (target_id,)

        cursor.execute(sql_last_week, params)

        last_week = cursor.fetchone()
        last_week_data = {
            "INCOME": last_week[0],
            "TRANSFER_IN": last_week[1],
            "TRANSFER_OUT": last_week[2],
            "LOAN_PAYMENTS": last_week[3],
            "BANK_FEES": last_week[4],
            "ENTERTAINMENT": last_week[5],
            "FOOD_AND_DRINK": last_week[6],
            "GENERAL_MERCHANDISE": last_week[7],
            "HOME_IMPROVEMENT": last_week[8],
            "MEDICAL": last_week[9],
            "PERSONAL_CARE": last_week[10],
            "GENERAL_SERVICES": last_week[11],
            "GOVERNMENT_AND_NON_PROFIT": last_week[12],
            "TRANSPORTATION": last_week[13],
            "TRAVEL": last_week[14],
            "RENT_AND_UTILITIES": last_week[15],
            "PAYMENT": last_week[16],
            "TRANSFER": last_week[17],
            "RECREATION": last_week[18],
            "TOTAL": last_week[19]
        }
        
        categories = list(curr_week_data.keys())
        diff_data = {cat: curr_week_data[cat] - last_week_data[cat] for cat in categories}     
        
        figs.append(plot_bar_chart_negative(diff_data.copy()))  
        figs.append(plot_bar_chart_positive(diff_data.copy()))

              
    else:
        print("This is the first week, no comparison made")

    # Averages of each column    
    sql_avgs = '''
        SELECT 
            AVG(INCOME) as INCOME,
            AVG(TRANSFER_IN) as TRANSFER_IN,
            AVG(TRANSFER_OUT) as TRANSFER_OUT,
            AVG(LOAN_PAYMENTS) as LOAN_PAYMENTS,
            AVG(BANK_FEES) as BANK_FEES,
            AVG(ENTERTAINMENT) as ENTERTAINMENT,
            AVG(FOOD_AND_DRINK) as FOOD_AND_DRINK,
            AVG(GENERAL_MERCHANDISE) as GENERAL_MERCHANDISE,
            AVG(HOME_IMPROVEMENT) as HOME_IMPROVEMENT,
            AVG(MEDICAL) as MEDICAL,
            AVG(PERSONAL_CARE) as PERSONAL_CARE,
            AVG(GENERAL_SERVICES) as GENERAL_SERVICES,
            AVG(GOVERNMENT_AND_NON_PROFIT) as GOVERNMENT_AND_NON_PROFIT,
            AVG(TRANSPORTATION) as TRANSPORTATION,
            AVG(TRAVEL) as TRAVEL,
            AVG(RENT_AND_UTILITIES) as RENT_AND_UTILITIES,
            AVG(PAYMENT) as PAYMENT,
            AVG(TRANSFER) as TRANSFER,
            AVG(RECREATION) as RECREATION,
            AVG(TOTAL) as TOTAL           
        FROM transactions
    '''
    
    cursor.execute(sql_avgs)
    averages_row = cursor.fetchone()
    
    averages_data = {
        "INCOME": round(averages_row[0], 2),
        "TRANSFER_IN": round(averages_row[1], 2),
        "TRANSFER_OUT": round(averages_row[2], 2),
        "LOAN_PAYMENTS": round(averages_row[3], 2),
        "BANK_FEES": round(averages_row[4], 2),
        "ENTERTAINMENT": round(averages_row[5], 2),
        "FOOD_AND_DRINK": round(averages_row[6], 2),
        "GENERAL_MERCHANDISE": round(averages_row[7], 2),
        "HOME_IMPROVEMENT": round(averages_row[8], 2),
        "MEDICAL": round(averages_row[9], 2),
        "PERSONAL_CARE": round(averages_row[10], 2) ,
        "GENERAL_SERVICES": round(averages_row[11], 2) ,
        "GOVERNMENT_AND_NON_PROFIT": round(averages_row[12], 2) ,
        "TRANSPORTATION": round(averages_row[13], 2) ,
        "TRAVEL": round(averages_row[14], 2) ,
        "RENT_AND_UTILITIES": round(averages_row[15], 2) ,
        "PAYMENT": round(averages_row[16], 2) ,
        "TRANSFER": round(averages_row[17], 2) ,
        "RECREATION": round(averages_row[18], 2) ,
        "TOTAL": round(averages_row[19], 2)
    }
    
    conn.close()

    pie_avgs = plot_pie_chart(averages_data, 'Average Spending per Category over all weeks')
    pie_curr = plot_pie_chart(curr_week_data, "This week's Spending per Category")
    
    figs.append(pie_curr)
    figs.append(pie_avgs)
    
    buffers = save_figures_to_buffer(figs)
    
    return buffers
    
def save_figures_to_buffer(figs):
    
    # Saves figures generated using matplotlib.pyplot into IO buffers
    
    # returns list of IO buffers each containing an img
    
    buffers = []
    for fig in figs:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=72)
        buf.seek(0) 
        buffers.append(buf)
    return buffers

def plot_pie_chart(data, title):
    
    # Plots and returns pie chart using input data
    # params:
    #   data: type dict
    #       keys = categories
    #       values = dollar amount
    #   title: type: string
    #       title of pyplot
    
    filtered_data = {k: v for k, v in data.items() if v != 0}
    
    total = sum(filtered_data.values())
    
    other_category_value = 0
    filtered_data_with_other = {}
    
    for label, value in filtered_data.items():
        percentage = (value / total) * 100
        if percentage < 10:
            other_category_value += value
        else:
            filtered_data_with_other[label] = value
    
    if other_category_value > 0:
        filtered_data_with_other['Other'] = other_category_value
    
    labels = filtered_data_with_other.keys()
    sizes = filtered_data_with_other.values()
    
    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(sizes, autopct='%1.1f%%', startangle=140)
    
    ax.legend(wedges, labels, title="Categories", loc="best")
    ax.axis('equal')
    ax.set_title(title)
    
    return fig

def plot_bar_chart_negative(differences):
    
    # Plots and returns bar chart using input data of the biggest increases in savings
    # params:
    #   differences: type dict
    #       keys = categories
    #       values = dollar amount
    #   title: type: string
    #       title of pyplot
    
    
    if 'TOTAL' in differences:
        total_diff = differences.pop('TOTAL')
    else:
        total_diff = 0

    sorted_differences = sorted(differences.items(), key=lambda x: x[1])
    top_3_negative = sorted_differences[:3]

    if top_3_negative:
        top_categories, top_diffs = zip(*top_3_negative)
    else:
        top_categories, top_diffs = [], []

    top_categories = list(top_categories) + ['Total']
    top_diffs = list(top_diffs) + [total_diff]

    x = np.arange(len(top_categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.bar(x, top_diffs, width, label='Difference')

    ax.set_xlabel('Categories')
    ax.set_ylabel('Difference')
    ax.set_title('Top 3 Largest Saving Increases from last week')
    ax.set_xticks(x)
    ax.set_xticklabels(top_categories, rotation=45, ha='right')
    ax.legend()

    for bar in bars:
        height = bar.get_height()
        ax.annotate('{}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    fig.tight_layout()
        
    return fig

def plot_bar_chart_positive(differences):
    
    # Plots and returns bar chart using input data of the biggest increases in spending
    # params:
    #   differences: type dict
    #       keys = categories
    #       values = dollar amount
    #   title: type: string
    #       title of pyplot
    
    
    if 'TOTAL' in differences:
        total_diff = differences.pop('TOTAL')
    else:
        total_diff = 0

    positive_differences = {k: v for k, v in differences.items() if v > 0}
    
    sorted_differences = sorted(positive_differences.items(), key=lambda x: x[1], reverse=True)
    top_3_positive = sorted_differences[:3]

    if top_3_positive:
        top_categories, top_diffs = zip(*top_3_positive)
    else:
        top_categories, top_diffs = [], []

    top_categories = list(top_categories) + ['Total']
    top_diffs = list(top_diffs) + [total_diff]

    x = np.arange(len(top_categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.bar(x, top_diffs, width, label='Difference')

    ax.set_xlabel('Categories')
    ax.set_ylabel('Difference')
    ax.set_title('Top 3 Largest Spending Increases from last week')
    ax.set_xticks(x)
    ax.set_xticklabels(top_categories, rotation=45, ha='right')
    ax.legend()

    for bar in bars:
        height = bar.get_height()
        ax.annotate('{}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), 
                    textcoords="offset points",
                    ha='center', va='bottom')

    fig.tight_layout()
    
    return fig

# Plaid API getting transactions from account
request = TransactionsGetRequest(
            access_token=ACCESS_TOKEN,
            start_date=start_date,
            end_date=end_date
)
response = client.transactions_get(request)
transactions = response['transactions']

# Kicks off function call chain that ends in email
summary(transactions=transactions, db_path=db_path)
