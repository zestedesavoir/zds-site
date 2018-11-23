# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

update-configs:
	scp zestedesavoir.com:/etc/nginx/nginx.conf source/install/configs/nginx/nginx.conf
	scp zestedesavoir.com:/etc/nginx/sites-available/prod-redirect source/install/configs/nginx/sites-available/
	scp zestedesavoir.com:/etc/nginx/sites-available/zestedesavoir source/install/configs/nginx/sites-available/
	scp zestedesavoir.com:/etc/nginx/snippets/antispam.conf source/install/configs/nginx/snippets/
	scp zestedesavoir.com:/etc/nginx/snippets/gzip.conf source/install/configs/nginx/snippets/
	scp zestedesavoir.com:/etc/nginx/snippets/headers.conf source/install/configs/nginx/snippets/
	scp zestedesavoir.com:/etc/nginx/snippets/proxy.conf source/install/configs/nginx/snippets/
	scp zestedesavoir.com:/etc/nginx/snippets/ssl.conf source/install/configs/nginx/snippets/
	scp zestedesavoir.com:/etc/nginx/snippets/static-cache.conf source/install/configs/nginx/snippets/
	scp zestedesavoir.com:/opt/zds/gunicorn_config.py source/install/configs/
	scp zestedesavoir.com:/etc/systemd/system/zds.service source/install/configs/
	scp zestedesavoir.com:/etc/systemd/system/zds.socket source/install/configs/
	scp zestedesavoir.com:/etc/systemd/system/solr.service source/install/configs/
	scp zestedesavoir.com:/etc/mysql/my.cnf source/install/configs/
	scp -r zestedesavoir.com:/etc/mysql/conf.d source/install/configs/
	scp zestedesavoir.com:/etc/munin/plugin-conf.d/zds.conf source/install/configs/munin/zds.conf
	# clean all secrets
	ssh zestedesavoir.com 'cat /opt/zds/zds-site/zds/settings_prod.py' | \
	gsed "s/'PASSWORD':\(.*\),/'PASSWORD':\ 'to-fill',/" | \
	gsed "s/SECRET_KEY = \(.*\)/SECRET_KEY = 'to-fill'/" | \
	gsed "s/PASSWORD = \(.*\)/PASSWORD = 'to-fill'/" | \
	gsed "s/'dsn':\(.*\)/'dsn': 'to-fill'/" | \
	gsed "s/SOCIAL_AUTH_[^P]\(.*\)=\(.*\)/SOCIAL_AUTH_\1= 'to-fill'/" | \
	gsed "s/RECAPTCHA_[^U]\(.*\)=\(.*\)/RECAPTCHA_\1= 'to-fill'/" | \
	gsed "s/ZDS_APP\['site'\]\['google\(.*\)=\(.*\)/ZDS_APP\['site'\]\['google\1= 'to-fill'/" \
	> source/install/configs/settings_prod.py
	echo "Vérifiez manuellement les fichiers avec \`git add --all --patch\`"
	echo "pour vous assurer qu'aucun 'secret' ne sera commité\!"
