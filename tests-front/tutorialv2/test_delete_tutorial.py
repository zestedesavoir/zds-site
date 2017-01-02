# -*- coding: utf-8 -*-


def test_delete_tutorial(sel):
    sel.click("link=Supprimer le contenu")
    sel.click("css=#delete-content > div.modal-footer > button[type=\"submit\"]")
    sel.wait_for_page_to_load("30000")
