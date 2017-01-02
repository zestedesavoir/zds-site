# -*- coding: utf-8 -*-


def test_validate_tutorial(sel):
    sel.click("link=Demander la validation")
    sel.type("id=id_text", "Selenium")
    sel.type("id=id_source", "selenium")
    sel.click("css=div.modal-footer > button.btn")
    sel.wait_for_page_to_load("30000")
    assert(sel.get_text("//main[@id='content']/article/header/p[2]") == "Ce contenu est en attente d'un validateur.")
