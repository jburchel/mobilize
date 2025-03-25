import io
import csv
import datetime
import xlsxwriter
from flask import send_file


def generate_csv(data, columns, filename):
    """
    Generate a CSV file from data and return as a Flask response
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include
        filename: Base filename without extension
    
    Returns:
        Flask send_file response with CSV data
    """
    # Create a StringIO object to write CSV data
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    
    # Write header and data rows
    writer.writeheader()
    for row in data:
        # Filter row to only include specified columns
        filtered_row = {col: row[col] for col in columns if col in row}
        writer.writerow(filtered_row)
    
    # Create a BytesIO object to return the response
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    output.close()
    
    return send_file(
        mem,
        download_name=f"{filename}.csv",
        as_attachment=True,
        mimetype='text/csv'
    )


def generate_excel(data, columns, filename):
    """
    Generate an Excel file from data and return as a Flask response
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names to include
        filename: Base filename without extension
    
    Returns:
        Flask send_file response with Excel data
    """
    # Create a BytesIO object to store Excel data
    output = io.BytesIO()
    
    # Create a workbook and add a worksheet
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Add header formatting
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D3D3D3',
        'border': 1
    })
    
    # Write headers
    for col_idx, column in enumerate(columns):
        worksheet.write(0, col_idx, column, header_format)
    
    # Write data rows
    for row_idx, row in enumerate(data, 1):
        for col_idx, column in enumerate(columns):
            value = row.get(column, '')
            
            # Format dates as string for Excel compatibility
            if isinstance(value, (datetime.date, datetime.datetime)):
                value = value.strftime('%Y-%m-%d %H:%M:%S') if isinstance(value, datetime.datetime) else value.strftime('%Y-%m-%d')
                
            worksheet.write(row_idx, col_idx, value)
    
    # Auto-fit column widths based on data
    for col_idx, column in enumerate(columns):
        max_width = len(column) + 2  # Base width on header plus padding
        
        # Check data widths
        for row in data:
            cell_value = row.get(column, '')
            if cell_value:
                cell_width = len(str(cell_value)) + 2
                max_width = max(max_width, cell_width)
        
        worksheet.set_column(col_idx, col_idx, max_width)
    
    # Close the workbook and get the file data
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        download_name=f"{filename}.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ) 