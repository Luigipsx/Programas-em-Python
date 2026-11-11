from festa.ui.common import sorted_rows, table_html


def test_money_sorting_uses_numeric_values():
    rows = [{"Nome": "A", "Preço / porção": "R$ 12,50"},
            {"Nome": "B", "Preço / porção": "R$ 5,00"},
            {"Nome": "C", "Preço / porção": "R$ 1.000,00"}]
    assert [row["Nome"] for row in sorted_rows(rows, "Preço / porção")] == ["B", "A", "C"]
    assert [row["Nome"] for row in sorted_rows(rows, "Preço / porção", True)] == ["C", "A", "B"]


def test_date_sorting_is_chronological():
    rows = [{"Início": "02/01/2027 10:00"}, {"Início": "25/12/2026 18:00"}, {"Início": "01/02/2027 09:00"}]
    assert sorted_rows(rows, "Início") == [rows[1], rows[0], rows[2]]


def test_table_escapes_user_content_and_keeps_safe_actions():
    rows = [{"Nome": '<script>alert("x")</script>', "Código": 7, "Descrição": '<img src=x onerror="alert(1)">'}]
    html = table_html(rows, list(rows[0]), namespace="alimentos")
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img src=x" in html
    assert "section=alimentos&amp;record=7&amp;action=edit" in html
    assert "action=delete" in html
    assert 'data-label="Descrição"' in html


def test_donation_status_has_text_as_well_as_color():
    rows = [{"Código": 1, "Situação": "Parcialmente recebida"}]
    html = table_html(rows, list(rows[0]))
    assert "festa-status-partial" in html
    assert "Parcialmente recebida" in html



def test_csv_export_keeps_all_columns_and_neutralizes_formulas():
    from festa.ui.common import csv_data
    import csv
    from io import StringIO
    rows = [{"Nome": "=SOMA(A1)", "Código": 1, "Descrição": "Informação; com acento"}]
    output = csv_data(rows).decode("utf-8-sig")
    exported = list(csv.DictReader(StringIO(output), delimiter=";"))
    assert exported[0]["Nome"] == "'=SOMA(A1)"
    assert exported[0]["Descrição"] == "Informação; com acento"
    assert exported[0]["Código"] == "1"
