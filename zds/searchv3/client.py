import typesense

client = typesense.Client(
    {
        "nodes": [
            {
                "host": "localhost",  # For Typesense Cloud use xxx.a1.typesense.net
                "port": "8108",  # For Typesense Cloud use 443
                "protocol": "http",  # For Typesense Cloud use https
            }
        ],
        "api_key": "xyz",
        "connection_timeout_seconds": 2,
    }
)


def create_collection():
    topic = {
        "name": "topic",
        "fields": [
            {"name": "title", "type": "string"},
            {"name": "subtitle", "type": "string"},
            {"name": "forum_title", "type": "string", "facet": True},
            {"name": "url", "type": "string"},
            {"name": "authors", "type": "string[]", "facet": True},
            {"name": "tags", "type": "string[]", "facet": True},
            {"name": "is_locked", "type": "int32"},
            {"name": "is_solved", "type": "int32"},
            {"name": "is_sticky", "type": "int32"},
            {"name": "pubdate", "type": "int32", "facet": True},
        ],
        "default_sorting_field": "pubdate",
    }

    post = {
        "name": "post",
        "fields": [
            {"name": "pk", "type": "int64"},
            {"name": "url", "type": "string"},
            {"name": "topic_pk", "type": "int64"},
            {"name": "topic_title", "type": "string", "facet": True},
            {"name": "forum_title", "type": "string", "facet": True},
            {"name": "position", "type": "int64"},
            {"name": "content", "type": "string"},
            {"name": "is_visible", "type": "int32"},
            {"name": "authors", "type": "string[]", "facet": True},
            {"name": "pubdate", "type": "int32"},
            {"name": "like_dislike_ratio", "type": "float"},
        ],
        "default_sorting_field": "pubdate",
    }

    chapter = {
        "name": "chapter",
        "fields": [
            {"name": "parent_pk", "type": "int32", "facet": False},
            {"name": "title", "type": "string", "facet": False},
            {"name": "parent_title", "type": "string"},
            {"name": "subcategories", "type": "string[]", "facet": True},
            {"name": "categories", "type": "string[]", "facet": True},
            {"name": "parent_publication_date", "type": "int64", "facet": False},
            {"name": "text", "type": "string[]", "facet": False},
            {"name": "get_absolute_url_online", "type": "string", "facet": False},
            {"name": "parent_get_absolute_url_online", "type": "string", "facet": False},
            {"name": "thumbnail", "type": "string", "facet": False},
        ],
    }

    publishedcontent = {
        "name": "publishedcontent",
        "fields": [
            {"name": "title", "type": "string", "facet": False},
            {"name": "content_pk", "type": "int32", "facet": False},
            {"name": "authors", "type": "string[]", "facet": False},
            {"name": "content_type", "type": "string", "facet": True},
            {"name": "publication_date", "type": "int64", "facet": False},
            {"name": "tags", "type": "string[]", "facet": True},
            {"name": "has_chapters", "type": "bool", "facet": False},
            {"name": "subcategories", "type": "string[]", "facet": True},
            {"name": "categories", "type": "string[]", "facet": True},
            {"name": "text", "type": "string[]", "facet": False},
            {"name": "description", "type": "string[]", "facet": False},
            {"name": "picked", "type": "bool", "facet": False},
            {"name": "get_absolute_url_online", "type": "string", "facet": False},
            {"name": "thumbnail", "type": "string", "facet": False},
        ],
    }

    client.collections.create(post)
    client.collections.create(topic)
    client.collections.create(chapter)
    client.collections.create(publishedcontent)


def add_content_json_l():
    with open("content.jsonl") as jsonl_file:
        documents = jsonl_file.read().encode("utf-8")
        client.collections["publishedcontent"].documents.import_(documents, {"action": "create"})


def add_content_schema():
    document = {
        "title": "Introduction to Machine Learning",
        "content_pk": 9012,
        "authors": ["Andrew Ng"],
        "content_type": "article",
        "publication_date": 1483228800,
        "tags": ["machine learning", "data science", "course"],
        "has_chapters": True,
        "subcategories": ["data science"],
        "categories": ["machine learning"],
        "text": ["Week 1: Introduction to Machine Learning", "Week 2: Linear Regression"],
        "description": ["A popular course on machine learning by Andrew Ng."],
        "picked": True,
        "get_absolute_url_online": "https://www.example.com/courses/9012",
        "thumbnail": "https://www.example.com/courses/9012/thumbnail.jpg",
    }

    document2 = {
        "title": "The Hitchhiker's Guide to the Galaxy",
        "content_pk": 5678,
        "authors": ["Douglas Adams"],
        "content_type": "tutorial",
        "publication_date": 1208112000,
        "tags": ["science fiction", "humor", "book"],
        "has_chapters": True,
        "subcategories": ["fiction"],
        "categories": ["science fiction"],
        "text": [
            "Chapter 1: The Hitchhiker's Guide to the Galaxy",
            "Chapter 2: The Restaurant at the End of the Universe",
        ],
        "description": ["A funny science fiction book about the end of the world."],
        "picked": True,
        "get_absolute_url_online": "https://www.example.com/books/5678",
        "thumbnail": "https://www.example.com/books/5678/thumbnail.jpg",
    }

    client.collections["publishedcontent"].documents.create(document)
    client.collections["publishedcontent"].documents.create(document2)


def test_search():
    search_parameters = {"q": "Introduction to Machine Learning", "query_by": "title"}

    result = client.collections["publishedcontent"].documents.search(search_parameters)

    for result in result["hits"]:
        print(result)


if __name__ == "__main__":
    # create_collection()
    # add_content_schema()
    # test_search()
    pass
