from collections import OrderedDict


def export_extract(extract):
    """
    Export an extract to a dictionary
    :param extract: extract to export
    :return: dictionary containing the information
    """
    dct = OrderedDict()
    dct['pk'] = extract.pk
    dct['title'] = extract.title
    dct['text'] = extract.text
    return dct


def export_container(container):
    """
    Export a container to a dictionary
    :param container: the container
    :return: dictionary containing the information
    """
    dct = OrderedDict()
    dct['pk'] = container.pk
    dct['title'] = container.title
    dct['obj_type'] = "container"
    dct['introduction'] = container.introduction
    dct['conclusion'] = container.conclusion
    dct['children'] = []

    if container.has_sub_containers():
        for child in container.children:
            dct['children'].append(export_container(child))
    elif container.has_extracts():
        for child in container.children:
            dct['children'].append(export_extract(child))

    return dct


def export_content(content):
    """
    Export a content to dictionary in order to store them in a JSON file
    :param content: content to be exported
    :return: dictionary containing the information
    """
    dct = export_container(content)

    # append metadata :
    dct['description'] = content.description
    dct['type'] = content.type
    if content.licence:
        dct['licence'] = content.licence.code

    return dct
