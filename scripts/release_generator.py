# -*- coding: utf-8 -*-
import codecs
import requests
import sys

# Script inspired from https://gist.github.com/unbracketed/3380407

OUTPUT_PATH = 'scripts/release_summary.md'


def get_milestones():
    jalons = []
    r = requests.get('https://api.github.com/repos/zestedesavoir/zds-site/milestones')
    jalons += parse_milestones(r)

    # more pages? examine the 'link' header returned
    if 'link' in r.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
                [link.split(';') for link in
                    r.headers['link'].split(',')]])
        while 'last' in pages and 'next' in pages:
            r = requests.get(pages['next'])
            jalons += parse_milestones(r)
            if pages['next'] == pages['last']:
                break

    return jalons


def parse_milestones(req):
    if not req.status_code == 200:
        raise Exception(req.status_code)

    milestones = []
    for milestone in req.json():
        milestones.append(milestone)

    return milestones


def get_issues(milestone_id):
    r = requests.get('https://api.github.com/repos/zestedesavoir/zds-site/issues?milestone={}&state=all'
                     .format(milestone_id))

    [o, cb, ce, cu] = parse_issues(r)

    openissues = []  # still open issue
    closed_bug = []  # closed bug issue
    closed_evo = []  # closed evolution issue
    closed_unk = []  # closed not bug or evo issue

    openissues += o
    closed_bug += cb
    closed_evo += ce
    closed_unk += cu

    # more pages? examine the 'link' header returned
    while 'link' in r.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
                [link.split(';') for link in
                    r.headers['link'].split(',')]])
        if 'next' in pages:
            r = requests.get(pages['next'])
            [o, cb, ce, cu] = parse_issues(r)
            openissues += o   # still open issue
            closed_bug += cb  # closed bug issue
            closed_evo += ce  # closed evolution issue
            closed_unk += cu  # closed not bug or evo issue
        else:
            break  # exit the while loop

    return (openissues, closed_bug, closed_evo, closed_unk)


def parse_issues(req):
    if not req.status_code == 200:
        raise Exception(req.status_code)

    openissues = []  # still open issue
    closed_bug = []  # closed bug issue
    closed_evo = []  # closed evolution issue
    closed_unk = []  # closed not bug or evo issue

    for issue in req.json():
        # check open issues
        if issue['state'] == 'open':
            openissues.append(issue)
        # check closed issue
        elif issue['state'] == 'closed':
            labels = []
            for l in issue['labels']:
                labels.append(l['name'])

            if 'S-BUG' in labels or u'S-Régression' in labels:
                closed_bug.append(issue)
            elif u'S-Évolution' in labels:
                closed_evo.append(issue)
            else:
                closed_unk.append(issue)

    return openissues, closed_bug, closed_evo, closed_unk


def dump_issues(milestone, openissues, closed_bug, closed_evo, closed_unk):
    # output all tables to a file
    with codecs.open(OUTPUT_PATH, 'w', 'utf-8') as out:
        out.write(u'Rapport pour le jalon **[{}](https://github.com/zestedesavoir/zds-site/milestones/{})** *({})*\n\n'
                  .format(milestone['title'], milestone['title'], milestone['description']))
        out.write(u'{} tickets sont compris dans ce jalon ({} ouverts et {} fermés)\n\n'
                  .format(len(openissues) + len(closed_bug) + len(closed_evo) + len(closed_unk),
                          len(openissues), len(closed_bug) + len(closed_evo) + len(closed_unk)))
        out.write(u'# Tickets toujours ouvert\n\n')
        out.write(mdarray(openissues))
        out.write(u'# Tickets fermé\n\n')
        out.write(u'## Corrections de bug\n\n')
        out.write(mdarray(closed_bug))
        out.write(u'## Évolutions\n\n')
        out.write(mdarray(closed_evo))
        out.write(u'## Non défini\n\n')
        out.write(mdarray(closed_unk))


def mdarray(tableau):
    if len(tableau) == 0:
        return u'Aucun ticket\n\n'
    ret = 'Ticket # | Titre | Label(s)\n'
    ret += '---------|-------|---------\n'
    for issue in tableau:
        labels = ''
        for label in issue['labels']:
            labels += label['name'] + ', '
        labels = labels[:-2]
        ret += u'[#{}]({}) | {} | {}\n' \
            .format(issue['number'],
                    issue['html_url'],
                    issue['title'],
                    labels)
    ret += '\n'
    return ret


###############################################################

milestones = get_milestones()

# print the milestones
for i in range(0, len(milestones)):
    print(u'{}. {}'.format(i + 1, milestones[i]['title']))

jalon_id = 0
while not jalon_id:
    try:
        jalon_id = raw_input(u'Quelle milestone voulez-vous generer (id) (q=quitter) ? ')
        jalon_id = int(jalon_id)
        if jalon_id > len(milestones):
            print(u'{} ne fait pas parti des milestones connues'.format(jalon_id))
            jalon_id = 0
    except:
        if jalon_id.lower() == 'q':
            sys.exit('Bye Bye !')
        print(u'{} n\'est pas un nombre !'.format(jalon_id))
        jalon_id = 0

print(u'Récuperation des tickets...')

[openissues, closed_bug, closed_evo, closed_unk] = get_issues(milestones[jalon_id - 1]['number'])
dump_issues(milestones[jalon_id - 1], openissues, closed_bug, closed_evo, closed_unk)
