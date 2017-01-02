# -*- coding: utf-8 -*-
from selenium import selenium

def test_disconnect(sel):
    sel.click("//a[@id='open-my-account']/span")
    sel.click("css=body.home")
    sel.click("css=button[type=\"submit\"]")
    sel.wait_for_page_to_load("30000")
