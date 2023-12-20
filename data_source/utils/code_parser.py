import pandas as pd


def parse_row(row, return_first_href=False):
    first_col = row.find_all('th')
    if first_col:
        first_col = first_col[0]
    else:
        if return_first_href:
            return None, None
        return None
    first_item = [first_col.text]

    table_items = row.find_all('td')
    if return_first_href:
        if first_col.a is not None:
            return first_col.a.attrs['href'], first_item + [x.text for x in table_items]
        else:
            return None, first_item + [x.text for x in table_items]
    return first_item + [x.text for x in table_items]


def parse_table(table, eliminate_class=None, return_first_cols=False):
    first_cols = []

    table_titles = table.find_all('thead')
    if table_titles:
        table_titles = table_titles[0]
        table_heads = table_titles.find_all('tr')[-1]
        cols = [x.text for x in table_heads.find_all('th')]
    else:
        cols = None

    contents = []
    table_rows = table.find_all('tbody')
    if table_rows:
        table_rows = table_rows[0]
        table_rows = table_rows.find_all('tr')
        for table_row in table_rows:
            if eliminate_class is not None:
                table_row_class = table_row.get("class")
                if table_row_class is not None and eliminate_class in table_row_class:
                    continue
            if return_first_cols:
                first_col, items = parse_row(table_row, return_first_href=True)
            else:
                items = parse_row(table_row)
            if items is None:
                continue
            contents.append(items)
            if return_first_cols and first_col is not None:
                first_cols.append(first_col)

    table_foots = table.find_all('tfoot')
    if table_foots:
        table_foots = table_foots[0].find_all('tr')
        for table_foot in table_foots:
            row_class = table_foot.get('class')
            if row_class is not None and "blank_table" in row_class:
                continue
            items = parse_row(table_foot)
            contents.append(items)

    if contents:
        df = pd.DataFrame(contents)
        df.columns = cols
    else:
        df = None
    if return_first_cols:
        return first_cols, df
    return df
