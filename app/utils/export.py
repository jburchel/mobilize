import io
import csv
import datetime
import xlsxwriter
from flask import send_file, current_app


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
    try:
        # Create a StringIO object to write CSV data
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        
        # Write header and data rows
        writer.writeheader()
        for row in data:
            # Filter row to only include specified columns
            filtered_row = {col: row.get(col, '') for col in columns}
            writer.writerow(filtered_row)
        
        # Create a BytesIO object to return the response
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        output.close()
        
        current_app.logger.info(f"CSV file '{filename}.csv' generated successfully with {len(data)} rows")
        
        return send_file(
            mem,
            download_name=f"{filename}.csv",
            as_attachment=True,
            mimetype='text/csv'
        )
    except Exception as e:
        current_app.logger.error(f"Error generating CSV: {str(e)}")
        # Re-raise to let the calling function handle it
        raise


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
    try:
        # Create a BytesIO object to store Excel data
        output = io.BytesIO()
        
        # Create a workbook and add a worksheet
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
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
                
                # Handle None values
                if value is None:
                    value = ''
                
                # Format datetime objects for Excel compatibility
                if isinstance(value, datetime.datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, datetime.date):
                    value = value.strftime('%Y-%m-%d')
                
                worksheet.write(row_idx, col_idx, value)
        
        # Auto-fit column widths based on data
        for col_idx, column in enumerate(columns):
            max_width = len(column) + 2  # Base width on header plus padding
            
            # Check data widths
            for row in data:
                cell_value = row.get(column, '')
                if cell_value:
                    # Ensure value is string for length calculation
                    cell_width = len(str(cell_value)) + 2
                    max_width = min(max(max_width, cell_width), 50)  # Cap width at 50
            
            worksheet.set_column(col_idx, col_idx, max_width)
        
        # Close the workbook and get the file data
        workbook.close()
        output.seek(0)
        
        current_app.logger.info(f"Excel file '{filename}.xlsx' generated successfully with {len(data)} rows")
        
        return send_file(
            output,
            download_name=f"{filename}.xlsx",
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.error(f"Error generating Excel: {str(e)}")
        # Re-raise to let the calling function handle it
        raise 