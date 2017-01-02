# -*- coding: utf-8 -*-


def test_remove_author(sel):
    sel.click(u"link=Gérer les auteurs")
    sel.click("css=button[name=\"username\"]")
    sel.wait_for_page_to_load("30000")
    sel.click(u"link=Gérer les auteurs")
    assert(sel.get_table("css=table.fullwidth.1.1") == u"Vous êtes seul !")
    sel.click("link=Fermer")
