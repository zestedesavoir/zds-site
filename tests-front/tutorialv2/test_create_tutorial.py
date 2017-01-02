# -*- coding: utf-8 -*-
from selenium import selenium

def test_create_tutorial(sel):
    sel.open("/")
    sel.click("//a[@id='open-my-account']/span")
    sel.click("css=body.home")
    sel.click("link=Mes tutoriels")
    sel.wait_for_page_to_load("30000")
    sel.click("link=Nouveau tutoriel")
    sel.wait_for_page_to_load("30000")
    sel.type("id=id_title", "Selenium")
    sel.type("id=id_description", "selenium")
    sel.type("id=id_tags", "selenium")
    sel.type("id=id_introduction", "Selenium")
    sel.type("id=id_conclusion", "Selenium")
    sel.select("id=id_licence", "label=Licence GNU GPL")
    sel.click("xpath=(//input[@id='id_subcategory_4'])[4]")
    sel.type("id=id_msg_commit", "selenium")
    sel.click("css=button.btn")
    sel.wait_for_page_to_load("30000")
