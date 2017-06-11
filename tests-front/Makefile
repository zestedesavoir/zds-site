EXECSTANDALONE:=java -jar server/selenium-server-standalone-2.53.1.jar

SUITECASES:=$(wildcard suite_*.py)
TESTLAUNCHER:=nosetests

all: clean install launch_selenium suite

clean:
	rm -f results_*.html

install:
	@$(SHELL) install_selenium.sh

launch_selenium:
	$(eval isRunning:=$(shell netstat -ln | grep ':4444 ' | grep -o 'LISTEN'))
	@if [ ! "$(isRunning)" == "LISTEN" ]; then \
	  $(EXECSTANDALONE)& \
	fi

suite:
ifdef suite
	$(TESTLAUNCHER) $(suite)
else
	for suite in $(SUITECASES); do \
	$(TESTLAUNCHER) "$$suite"; \
	done
endif

change:
	$(eval folders:=$(shell git diff --name-only ../templates/ | awk -F'/' '{print $$2}'))
	@for folder in $(folders); do \
		if [ -f suite_"$$folder".py ]; then \
			$(TESTLAUNCHER) suite_"$$folder".py; \
		else \
			echo "Warning! No suite test found for $$folder directory"; \
		fi \
	done
