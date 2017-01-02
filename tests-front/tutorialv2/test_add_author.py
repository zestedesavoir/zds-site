# -*- coding: utf-8 -*-
from selenium import selenium

def test_add_author(sel):
    sel.click("link=Ajouter un auteur")
    sel.type("name=username", "staff")
    sel.click("name=add_author")
    sel.wait_for_page_to_load("30000")
    sel.click("link=Ajouter un auteur")
    sel.click("link=Annuler")
