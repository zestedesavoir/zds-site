# coding: utf-8

import threading

from bs4 import BeautifulSoup

from zds import settings
from zds.search.models import SearchIndexExtract, SearchIndexContainer, SearchIndexContent, \
    SearchIndexTag, SearchIndexAuthors
from zds.utils.templatetags.emarkdown import emarkdown


def filter_keyword(html):
    '''
        Try to find important words in an html string. Search in all i and strong and each title
    :return: list of important words
    '''
    bs = BeautifulSoup(html)

    keywords = ''
    for tag in bs.findAll(['h1', 'h2', 'h3', 'i', 'strong']):
        keywords += ' ' + tag.text

    return keywords


def filter_text(html):
    '''
        Filter word from the html version of the text
    :param html: The content which words must be extract
    :return: extracted words
    '''
    bs = BeautifulSoup(html)
    return ' '.join(bs.findAll(text=True))


def index_extract(search_index_content, extract):
    search_index_extract = SearchIndexExtract()
    search_index_extract.search_index_content = search_index_content
    search_index_extract.title = extract.title
    search_index_extract.url_to_redirect = extract.get_absolute_url_online()

    content = emarkdown(extract.get_text())
    search_index_extract.extract_content = filter_text(content)

    search_index_extract.keywords = filter_keyword(content)

    search_index_extract.save()

    return True


def index_container(search_index_content, container, type):
    search_index_container = SearchIndexContainer()
    search_index_container.search_index_content = search_index_content
    search_index_container.title = container.title
    search_index_container.url_to_redirect = container.get_absolute_url_online()

    introduction_html = emarkdown(container.get_introduction())
    search_index_container.introduction = filter_text(introduction_html)

    conclusion_html = emarkdown(container.get_conclusion())
    search_index_container.conclusion = filter_text(conclusion_html)

    search_index_container.keywords = filter_keyword(introduction_html + conclusion_html)
    search_index_container.level = type

    search_index_container.save()

    return True


def index_content(child, search_index_content):
    from zds.tutorialv2.models.models_versioned import Container, Extract

    if isinstance(child, Container):
        if len(child.children) != 0:
            if isinstance(child.children[0], Extract):
                index_container(search_index_content, child, 'chapter')

                for extract in child.children:
                    index_extract(search_index_content, extract)

            else:
                index_container(search_index_content, child, 'part')

                for chapter in child.children:
                    index_container(search_index_content, chapter, 'chapter')

                    if len(chapter.children) != 0:
                        for extract in chapter.children:
                            index_extract(search_index_content, extract)
    else:
        index_extract(search_index_content, child)


def reindex_thread(versioned, publishable_content):

    # We just delete all index that correspond to the content
    SearchIndexContent.objects.filter(publishable_content=publishable_content).delete()

    # Index the content
    search_index_content = SearchIndexContent()
    search_index_content.publishable_content = publishable_content
    search_index_content.title = publishable_content.title
    search_index_content.description = publishable_content.description

    search_index_content.pubdate = publishable_content.pubdate
    search_index_content.update_date = publishable_content.update_date

    if publishable_content.licence:
        search_index_content.licence = publishable_content.licence.title
    else:
        search_index_content.licence = ''

    if publishable_content.image:
        search_index_content.url_image = publishable_content.image.get_absolute_url()
    else:
        search_index_content.url_image = ''

    search_index_content.save()

    # Subcategory
    for subcategory in publishable_content.subcategory.all():
        search_index_tag = SearchIndexTag()
        search_index_tag.title = subcategory.title
        search_index_tag.save()

        search_index_content.tags.add(search_index_tag)

    # Authors
    for author in publishable_content.authors.all():
        search_index_authors = SearchIndexAuthors()
        search_index_authors.username = author.username
        search_index_authors.save()

        search_index_content.authors.add(search_index_authors)

    search_index_content.url_to_redirect = versioned.get_absolute_url_online()

    # Save introduction and conclusion
    introduction_html = emarkdown(versioned.get_introduction())
    search_index_content.introduction = filter_text(introduction_html)

    conclusion_html = emarkdown(versioned.get_conclusion())
    search_index_content.conclusion = filter_text(conclusion_html)

    search_index_content.keywords = filter_keyword(introduction_html + conclusion_html)

    if publishable_content.is_article():
        search_index_content.type = 'article'
    else:
        search_index_content.type = 'tutorial'

    search_index_content.save()

    # Save extract and containers
    for child in versioned.children:
        index_content(child, search_index_content)

    return True


def reindex_content(versioned, publishable_content):
    """Index the new published version. Lot of IO, memory and cpu will be used, be warned when you use this fonction.
    Don't try to loop on it, if you not sure of what you will do.

    IO complexity is 2 + (2*number of containers) + number of extracts.
    Database query complexity is on deletion 1+number of containers+number of extracts,
                                 on addition 1+number of containers+number of extracts.

    :param versioned: version of the content to publish
    :type versioned: VersionedContent
    :param publishable_content: Database representation of the content
    :type publishable_content: PublishableContent
    :return:
    """
    if not settings.TESTING:
        thread = threading.Thread(target=reindex_thread, args=(versioned, publishable_content, ))
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
    else:
        reindex_thread(versioned, publishable_content)
