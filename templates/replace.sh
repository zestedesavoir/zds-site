find . -type f -name '*.html' -print | while read i
do
	sed "s|$1|$2|g" $i > $i.tmp && mv $i.tmp $i
done