"""Keep spreadsheet software from interpreting user-entered export text as formulas."""
def safe_csv_cell(value):
    if value is None:return ''
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):return "'"+value
    return value
