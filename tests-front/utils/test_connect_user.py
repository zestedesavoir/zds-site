# -*- coding: utf-8 -*-


def test_connect_user(sel):
    sel.open("/")
    sel.click("id=djHideToolBarButton")
    sel.click("link=Connexion")
    sel.wait_for_page_to_load("30000")
    sel.type("id=id_username", "user")
    sel.type("id=id_password", "user")
    sel.click("css=button.btn")
    sel.wait_for_page_to_load("30000")
