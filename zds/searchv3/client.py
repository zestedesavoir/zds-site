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

if __name__ == "__main__":
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
