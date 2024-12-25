import pandas as pd
from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

# This will display all output and messages in different colors
DO_COLOR = True


class SearchCharacter():

    def __init__(self, compare_list, database_path):
        self.compare_list = compare_list
        self.database_path = database_path
        self.compare_list_database = []
        self.error_data = []

    def get_database(self):
        found_data = []
        # Read XLSX file using pandas
        data = pd.read_excel(self.database_path, engine='openpyxl')
        for _, row_info in data.iterrows():
            for col in row_info:
                if col in self.compare_list:
                    self.compare_list_database.append(
                        [rd for rd in row_info if pd.notna(rd) and rd != '']
                    )
                    found_data.append(row_info[0])
        self.error_data = list(set(self.compare_list) - set(found_data))

    def get_common_from_multiple(self, data_list, out_list=None):
        if len(data_list) == 0:
            return out_list
        else:
            if not out_list:
                l1 = data_list.pop(0)
                try:
                    l2 = data_list.pop(0)
                except IndexError:
                    return list(set(l1) & set([]))
                out_list = list(set(l1) & set(l2))
                return self.get_common_from_multiple(data_list, out_list)
            else:
                l1 = data_list.pop(0)
                out_list = list(set(l1) & set(out_list))
                return self.get_common_from_multiple(data_list, out_list)

    def search(self):
        return_data = []
        if not self.compare_list_database:
            # Send message if entered data does not exist
            return return_data
        else:
            # If entered data exists, find common between them
            char_list = [char.pop(0) for char in self.compare_list_database]
            temp = self.compare_list_database.copy()
            similar_props = self.get_common_from_multiple(
                self.compare_list_database)
            return_data = [char_list, [
                sp for sp in similar_props if sp != ''], self.error_data]
            return return_data

    def reverse_search(self):
        return_data = []
        data = pd.read_excel(self.database_path, engine='openpyxl')

        # Clean and normalize the compare list (remove '+' signs and unwanted characters)
        compare_list = [re.sub(r'[^\w\s]', '', item.strip().lower()) for item in self.compare_list]
        print(f"Cleaned compare list: {compare_list}")  # Debugging line

        for _, row_info in data.iterrows():
            row_info = row_info.dropna()  # Remove NaN values
            # Clean and normalize the row properties (strip spaces, lower case, remove unwanted characters)
            row_properties = [re.sub(r'[^\w\s]', '', str(value).strip().lower()) for value in row_info[1:].values]
            print(f"Checking row: {row_info[0]} with properties: {row_properties}")  # Debugging line

            # Check if the compare_list is a subset of the row properties
            if set(compare_list).issubset(row_properties):
                print(f"Match found in symbol: {row_info[0]}")  # Debugging line
                # Only append the first column (row_info[0]) to return_data
                return_data.append(row_info[0])

        print(f"Final return_data: {return_data}")  # Debugging line
        return return_data


# Route to the home page of the app
# Located in templates/index.html
@app.route("/")
def home():
    return render_template('index.html')


# Route to handle search requests
# The result templates are located in
# templates/search_result.html and templates/reverse_search_result.html
@app.route("/search", methods=['POST'])
def search():
    compare_list = request.form['compare_list']
    search_type = request.form['search_type']

    # Forward search
    if search_type == 'forward':
        compare_list = compare_list.split()
        search_obj = SearchCharacter(compare_list, 'symbols&properties.xlsx')  # Change to XLSX
        search_obj.get_database()
        return_data = search_obj.search()

        return render_template('search_result.html', return_data=return_data)

    # Reverse search
    elif search_type == 'reverse':
        # Clean and normalize the input (remove '+' if present)
        compare_list = [rs if '+' not in rs else rs.strip('+') for rs in compare_list.split()]
        search_obj = SearchCharacter(compare_list, 'compare_database.xlsx')  # Change to XLSX
        return_data = search_obj.reverse_search()

        return render_template('reverse_search_result.html', return_data=return_data)

    else:
        return jsonify({"error": "Invalid search type"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
