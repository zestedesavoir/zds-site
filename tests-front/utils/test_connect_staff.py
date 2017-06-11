# -*- coding: utf-8 -*-


def test_connect_staff(sel):
    sel.open("/")
    sel.click("id=djHideToolBarButton")
    sel.click("link=Connexion")
    sel.wait_for_page_to_load("30000")
    sel.type("id=id_username", "staff")
    sel.type("id=id_password", "staff")
    sel.click("css=button.btn")
    sel.wait_for_page_to_load("30000")
