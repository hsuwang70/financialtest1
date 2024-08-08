import re
from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup
import time
from flask import Flask, request, Response
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)
request_methods = ["POST"]


def run(playwright: Playwright, request_data) -> None:
    browser = playwright.chromium.launch(executablePath='/home/runner/.cache/ms-playwright/chromium-1124/chrome-linux/chrome',headless=True)
    context = browser.new_context()
    # 開啟新的頁面
    page = context.new_page()
    page.goto("https://mops.twse.com.tw/mops/web/index")
        
    # Locate and fill the input field with the company code
    page.fill('#keyword', request_data['symbol_list'])

    # Click the search button
    page.click('input[name="rulesubmit"]')

    # 點擊連結以打開新視窗
    with page.expect_popup() as popup_info:
        page.click('a[href="javascript:outputNewWindow();"]')
    new_page = popup_info.value

    # 等待新視窗加載，這裡你可以根據需要調整等待時間
    new_page.wait_for_load_state('load')

    content = new_page.content()

    soup = BeautifulSoup(content, 'html.parser')
        
    thbg_rows = soup.find_all('tr', class_='thbg')

    result = {}
    # Step 2: Iterate over thbg_rows
    for thbg_row in thbg_rows:
        
        # Step 2.1: Extract data from thbg_row
        td_elements = thbg_row.find_all('td')  # Find all <td> elements
        thbg_data = []  # Initialize an empty list to store the data
        
        # Iterate over each <td> element
        for td in td_elements:
            title = td.text.strip()  # Extract text and strip whitespace
            thbg_data.append(title)  # Append cleaned text to the list
        
        # Step 2.2: Find the next 'text_center' row
        text_center_row = thbg_row.find_next('tr', class_='text_center')
        
        if text_center_row:
            # Extract data from text_center_row
            td_elements = text_center_row.find_all('td')  # Find all <td> elements
            text_center_data = []  # Initialize an empty list to store the data
        
            # # Iterate over each <td> element
            for td in td_elements:
                content = td.text.strip()  # Extract text and strip whitespace
                text_center_data.append(content)  # Append cleaned text to the list

            for item, i in zip(thbg_data, text_center_data):
                result[item] = i
    # print(result)
    # print('.............................')

    # # Step 3: Print results for debugging
    # for items in results:
    #     # Uncomment the following lines to print detailed information
    #     # print("thbg:", items['thbg'])
    #     # print("text_center:", items['text_center'])
    #     for item, i in zip(items['thbg'], items['text_center']):
    #         print(item,i)
    #         result[item].append(i)              
    #         print(result)
    #         # print(f"{item}: {i}")
    #     print(result)
    #     print('.............................')

    # Optional: Perform further actions on the new window if needed
    # For example, you can take a screenshot or extract data
    time.sleep(1)
    # 關閉新視窗
    new_page.close()

    # 關閉主頁面
    page.close()

    return result

@app.route('/getreport', methods=['POST'])
def getreport():
    try:
        request_data = request.json
        with sync_playwright() as playwright:
            result = run(playwright, request_data)
            
        # request_data = request.json
        return Response(json.dumps(result), mimetype="application/json")
    except Exception as e:
        return Response(json.dumps({"status": 0, "error_msg": str(e)}), mimetype='application/json'), 400
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=3000,debug=True)
