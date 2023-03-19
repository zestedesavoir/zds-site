curl "http://localhost:8108/collections/publishedcontent/documents/import" \
      -X POST \
      -H "X-TYPESENSE-API-KEY: xyz" \
      --data-binary @content.jsonl

curl "http://localhost:8108/collections/publishedcontent/documents/import" \
      -X POST \
      -H "X-TYPESENSE-API-KEY: xyz" \
      --data-binary @publishedcontent.jsonl

curl "http://localhost:8108/collections/chapter/documents/import" \
      -X POST \
      -H "X-TYPESENSE-API-KEY: xyz" \
      --data-binary @chapters.jsonl

curl "http://localhost:8108/collections/topic/documents/import" \
      -X POST \
      -H "X-TYPESENSE-API-KEY: xyz" \
      --data-binary @topics.jsonl

curl "http://localhost:8108/collections/post/documents/import" \
      -X POST \
      -H "X-TYPESENSE-API-KEY: xyz" \
      --data-binary @posts.jsonl