#!/bin/bash

# This script was used to convert the mysql database and all tables and fields
# to utf8mb4. It was part of the tagged release 20. It requires MySQL 5.6.
# See `update.md` for more info.

MYSQL_VERSION=$(mysql -V | awk '{print $5}')
MIN_MYSQL_VERSION="5.6"
function version { echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'; }

if [ $(version $MYSQL_VERSION) -lt $(version $MIN_MYSQL_VERSION) ]; then
    echo "This script will only work with MySQL >= 5.6" >&2
    echo "Please update MySQL. See update.md." >&2
    exit 1
fi

mysql -u zds -p zdsdb << EOF
    # General settings for our database:
    ALTER DATABASE zdsdb CHARACTER SET = utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

if [ $? -eq 0 ]; then
    echo "Database-wide settings updated."
else
    echo "Database-wide modification failed." >&2
    exit 1
fi


mysql -u zds -p zdsdb << EOF
    ### Convert each table to ROW_FORMAT=DYNAMIC, the newest MySQL default
    ALTER TABLE \`article_validation\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`auth_group\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`auth_group_permissions\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`auth_permission\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`auth_user\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`auth_user_groups\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`auth_user_user_permissions\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`corsheaders_corsmodel\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`django_admin_log\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`django_content_type\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`django_migrations\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`django_session\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`django_site\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`easy_thumbnails_source\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`easy_thumbnails_thumbnail\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`easy_thumbnails_thumbnaildimensions\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`featured_featuredmessage\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`featured_featuredresource\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`forum_category\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`forum_forum\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`forum_forum_group\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`forum_post\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`forum_topic\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`forum_topic_tags\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`forum_topicread\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`gallery_gallery\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`gallery_image\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`gallery_usergallery\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`member_ban\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`member_karmanote\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`member_profile\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`member_tokenforgotpassword\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`member_tokenregister\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`mp_privatepost\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`mp_privatetopic\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`mp_privatetopic_participants\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`mp_privatetopicread\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`munin_test\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`newsletter_newsletter\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_answersubscription\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_contentreactionanswersubscription\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_newtopicsubscription\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_notification\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_privatetopicanswersubscription\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_subscription\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_topicanswersubscription\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`notification_topicfollowed\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`oauth2_provider_accesstoken\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`oauth2_provider_application\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`oauth2_provider_grant\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`oauth2_provider_refreshtoken\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`pages_groupcontact\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`search_searchindexauthors\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`search_searchindexcontainer\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`search_searchindexcontent\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`search_searchindexcontent_authors\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`search_searchindexcontent_tags\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`search_searchindexextract\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`search_searchindextag\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`social_auth_association\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`social_auth_code\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`social_auth_nonce\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`social_auth_usersocialauth\` ROW_FORMAT=DYNAMIC;
    # south_migrationhistory # this one stays
    ALTER TABLE \`tutorial_chapter\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorial_extract\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorial_part\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorial_tutorial_helps\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorial_validation\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_contentreaction\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_contentread\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_publishablecontent\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_publishablecontent_authors\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_publishablecontent_helps\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_publishablecontent_subcategory\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_publishablecontent_tags\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_publishedcontent\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_publishedcontent_authors\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`tutorialv2_validation\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_alert\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_category\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_categorysubcategory\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_comment\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_commentvote\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_helpwriting\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_licence\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_subcategory\` ROW_FORMAT=DYNAMIC;
    ALTER TABLE \`utils_tag\` ROW_FORMAT=DYNAMIC;

    # Next, ALTER these tables to the utf8mb4 charset and collation

    ALTER TABLE \`article_validation\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`auth_group\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`auth_group_permissions\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`auth_permission\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`auth_user\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`auth_user_groups\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`auth_user_user_permissions\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`corsheaders_corsmodel\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`django_admin_log\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`django_content_type\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`django_migrations\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`django_session\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`django_site\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`easy_thumbnails_source\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`easy_thumbnails_thumbnail\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`easy_thumbnails_thumbnaildimensions\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`featured_featuredmessage\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`featured_featuredresource\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`forum_category\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`forum_forum\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`forum_forum_group\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`forum_post\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`forum_topic\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`forum_topic_tags\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`forum_topicread\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`gallery_gallery\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`gallery_image\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`gallery_usergallery\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`member_ban\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`member_karmanote\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`member_profile\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`member_tokenforgotpassword\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`member_tokenregister\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`mp_privatepost\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`mp_privatetopic\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`mp_privatetopic_participants\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`mp_privatetopicread\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`munin_test\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`newsletter_newsletter\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_answersubscription\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_contentreactionanswersubscription\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_newtopicsubscription\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_notification\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_privatetopicanswersubscription\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_subscription\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_topicanswersubscription\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`notification_topicfollowed\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`oauth2_provider_accesstoken\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`oauth2_provider_application\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`oauth2_provider_grant\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`oauth2_provider_refreshtoken\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`pages_groupcontact\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexauthors\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontainer\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontent\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontent_authors\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontent_tags\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexextract\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindextag\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`social_auth_association\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`social_auth_code\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`social_auth_nonce\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`social_auth_usersocialauth\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    # no changes: south_migrationhistory
    ALTER TABLE \`tutorial_chapter\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorial_extract\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorial_part\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorial_tutorial_helps\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorial_validation\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_contentreaction\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_contentread\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_publishablecontent\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_publishablecontent_authors\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_publishablecontent_helps\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_publishablecontent_subcategory\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_publishablecontent_tags\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_publishedcontent\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_publishedcontent_authors\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_validation\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_alert\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_category\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_categorysubcategory\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_comment\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_commentvote\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_helpwriting\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_licence\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_subcategory\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`utils_tag\` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

if [ $? -eq 0 ]; then
    echo "Tables have been successfully modified."
else
    echo "Tables modification failed." >&2
    exit 1
fi


mysql -u zds -p zdsdb << EOF
    ### Convert each text field (*text, varchar) to utf8mb4 charset and collation

    # article_validation
    ALTER TABLE \`article_validation\` CHANGE version version VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`article_validation\` CHANGE comment_authors comment_authors LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`article_validation\` CHANGE comment_validator comment_validator LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`article_validation\` CHANGE status status VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # auth_group
    ALTER TABLE \`auth_group\` CHANGE name name VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # auth_permission
    ALTER TABLE \`auth_permission\` CHANGE name name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`auth_permission\` CHANGE codename codename VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # auth_user
    ALTER TABLE \`auth_user\` CHANGE password password VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`auth_user\` CHANGE username username VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`auth_user\` CHANGE first_name first_name VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`auth_user\` CHANGE last_name last_name VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`auth_user\` CHANGE email email VARCHAR(254) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # corsheaders_corsmodel
    ALTER TABLE \`corsheaders_corsmodel\` CHANGE cors cors VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # django_admin_log
    ALTER TABLE \`django_admin_log\` CHANGE object_id object_id LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`django_admin_log\` CHANGE object_repr object_repr VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`django_admin_log\` CHANGE change_message change_message LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # django_content_type
    ALTER TABLE \`django_content_type\` CHANGE app_label app_label VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`django_content_type\` CHANGE model model VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # django_migrations
    ALTER TABLE \`django_migrations\` CHANGE app app VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`django_migrations\` CHANGE name name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # django_session
    ALTER TABLE \`django_session\` CHANGE session_key session_key VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`django_session\` CHANGE session_data session_data LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # django_site
    ALTER TABLE \`django_site\` CHANGE domain domain VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`django_site\` CHANGE name name VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # easy_thumbnails_source
    ALTER TABLE \`easy_thumbnails_source\` CHANGE name name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`easy_thumbnails_source\` CHANGE storage_hash storage_hash VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # easy_thumbnails_thumbnail
    ALTER TABLE \`easy_thumbnails_thumbnail\` CHANGE name name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`easy_thumbnails_thumbnail\` CHANGE storage_hash storage_hash VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # featured_featuredmessage
    ALTER TABLE \`featured_featuredmessage\` CHANGE message message VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`featured_featuredmessage\` CHANGE url url VARCHAR(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`featured_featuredmessage\` CHANGE hook hook VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # featured_featuredresource
    ALTER TABLE \`featured_featuredresource\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`featured_featuredresource\` CHANGE type type VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`featured_featuredresource\` CHANGE image_url image_url VARCHAR(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`featured_featuredresource\` CHANGE url url VARCHAR(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`featured_featuredresource\` CHANGE authors authors VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # forum_category
    ALTER TABLE \`forum_category\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`forum_category\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # forum_forum
    ALTER TABLE \`forum_forum\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`forum_forum\` CHANGE subtitle subtitle VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`forum_forum\` CHANGE image image VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`forum_forum\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # forum_topic
    ALTER TABLE \`forum_topic\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`forum_topic\` CHANGE subtitle subtitle VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # gallery_gallery
    ALTER TABLE \`gallery_gallery\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`gallery_gallery\` CHANGE subtitle subtitle VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`gallery_gallery\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # gallery_image
    ALTER TABLE \`gallery_image\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`gallery_image\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`gallery_image\` CHANGE physical physical VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`gallery_image\` CHANGE thumb thumb VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`gallery_image\` CHANGE medium medium VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`gallery_image\` CHANGE legend legend VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # gallery_usergallery
    ALTER TABLE \`gallery_usergallery\` CHANGE mode mode VARCHAR(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # member_ban
    ALTER TABLE \`member_ban\` CHANGE type type VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`member_ban\` CHANGE text text LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # member_karmanote
    ALTER TABLE \`member_karmanote\` CHANGE comment comment VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # member_profile
    ALTER TABLE \`member_profile\` CHANGE last_ip_address last_ip_address VARCHAR(39) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`member_profile\` CHANGE site site VARCHAR(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`member_profile\` CHANGE avatar_url avatar_url VARCHAR(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`member_profile\` CHANGE biography biography LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`member_profile\` CHANGE sign sign LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`member_profile\` CHANGE sdz_tutorial sdz_tutorial LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

    # member_tokenforgotpassword
    ALTER TABLE \`member_tokenforgotpassword\` CHANGE token token VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # member_tokenregister
    ALTER TABLE \`member_tokenregister\` CHANGE token token VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # mp_privatepost
    ALTER TABLE \`mp_privatepost\` CHANGE text text LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`mp_privatepost\` CHANGE text_html text_html LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # mp_privatetopic
    ALTER TABLE \`mp_privatetopic\` CHANGE title title VARCHAR(130) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`mp_privatetopic\` CHANGE subtitle subtitle VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # munin_test
    ALTER TABLE \`munin_test\` CHANGE name name VARCHAR(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # newsletter_newsletter
    ALTER TABLE \`newsletter_newsletter\` CHANGE email email VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`newsletter_newsletter\` CHANGE ip ip VARCHAR(39) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # notification_notification
    ALTER TABLE \`notification_notification\` CHANGE url url VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`notification_notification\` CHANGE title title VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # oauth2_provider_accesstoken
    ALTER TABLE \`oauth2_provider_accesstoken\` CHANGE token token VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_accesstoken\` CHANGE scope scope LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # oauth2_provider_application
    ALTER TABLE \`oauth2_provider_application\` CHANGE client_id client_id VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_application\` CHANGE redirect_uris redirect_uris LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_application\` CHANGE client_type client_type VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_application\` CHANGE authorization_grant_type authorization_grant_type VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_application\` CHANGE client_secret client_secret VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_application\` CHANGE name name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # oauth2_provider_grant
    ALTER TABLE \`oauth2_provider_grant\` CHANGE code code VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_grant\` CHANGE redirect_uri redirect_uri VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`oauth2_provider_grant\` CHANGE scope scope LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # oauth2_provider_refreshtoken
    ALTER TABLE \`oauth2_provider_refreshtoken\` CHANGE token token VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # pages_groupcontact
    ALTER TABLE \`pages_groupcontact\` CHANGE name name VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`pages_groupcontact\` CHANGE description description LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`pages_groupcontact\` CHANGE email email VARCHAR(254) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # search_searchindexauthors
    ALTER TABLE \`search_searchindexauthors\` CHANGE username username VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # search_searchindexcontainer
    ALTER TABLE \`search_searchindexcontainer\` CHANGE title title VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexcontainer\` CHANGE url_to_redirect url_to_redirect VARCHAR(400) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexcontainer\` CHANGE introduction introduction LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontainer\` CHANGE conclusion conclusion LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontainer\` CHANGE level level VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexcontainer\` CHANGE keywords keywords LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # search_searchindexcontent
    ALTER TABLE \`search_searchindexcontent\` CHANGE title title VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexcontent\` CHANGE description description LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontent\` CHANGE licence licence VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexcontent\` CHANGE url_image url_image VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`search_searchindexcontent\` CHANGE url_to_redirect url_to_redirect VARCHAR(400) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexcontent\` CHANGE introduction introduction LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontent\` CHANGE conclusion conclusion LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexcontent\` CHANGE keywords keywords LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexcontent\` CHANGE type type VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # search_searchindexextract
    ALTER TABLE \`search_searchindexextract\` CHANGE title title VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexextract\` CHANGE url_to_redirect url_to_redirect VARCHAR(400) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`search_searchindexextract\` CHANGE extract_content extract_content LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`search_searchindexextract\` CHANGE keywords keywords LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # search_searchindextag
    ALTER TABLE \`search_searchindextag\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # social_auth_association
    ALTER TABLE \`social_auth_association\` CHANGE server_url server_url VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`social_auth_association\` CHANGE handle handle VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`social_auth_association\` CHANGE secret secret VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`social_auth_association\` CHANGE assoc_type assoc_type VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # social_auth_code
    ALTER TABLE \`social_auth_code\` CHANGE email email VARCHAR(254) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`social_auth_code\` CHANGE code code VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # social_auth_nonce
    ALTER TABLE \`social_auth_nonce\` CHANGE server_url server_url VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`social_auth_nonce\` CHANGE salt salt VARCHAR(65) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # social_auth_usersocialauth
    ALTER TABLE \`social_auth_usersocialauth\` CHANGE provider provider VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`social_auth_usersocialauth\` CHANGE uid uid VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`social_auth_usersocialauth\` CHANGE extra_data extra_data LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # south_migrationhistory # this one stays in utf8_bin

    # tutorial_chapter
    ALTER TABLE \`tutorial_chapter\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorial_chapter\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorial_chapter\` CHANGE introduction introduction VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorial_chapter\` CHANGE conclusion conclusion VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # tutorial_extract
    ALTER TABLE \`tutorial_extract\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorial_extract\` CHANGE text text VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # tutorial_part
    ALTER TABLE \`tutorial_part\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorial_part\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorial_part\` CHANGE introduction introduction VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorial_part\` CHANGE conclusion conclusion VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # tutorial_validation
    ALTER TABLE \`tutorial_validation\` CHANGE version version VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorial_validation\` CHANGE comment_authors comment_authors LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorial_validation\` CHANGE comment_validator comment_validator LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorial_validation\` CHANGE status status VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # tutorialv2_publishablecontent
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE description description VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE source source VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE sha_public sha_public VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE sha_beta sha_beta VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE sha_validation sha_validation VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE sha_draft sha_draft VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE type type VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorialv2_publishablecontent\` CHANGE relative_images_path relative_images_path VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    # tutorialv2_publishedcontent
    ALTER TABLE \`tutorialv2_publishedcontent\` CHANGE content_type content_type VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorialv2_publishedcontent\` CHANGE content_public_slug content_public_slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`tutorialv2_publishedcontent\` CHANGE sha_public sha_public VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorialv2_publishedcontent\` CHANGE sizes sizes VARCHAR(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # tutorialv2_validation
    ALTER TABLE \`tutorialv2_validation\` CHANGE version version VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`tutorialv2_validation\` CHANGE comment_authors comment_authors LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_validation\` CHANGE comment_validator comment_validator LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE \`tutorialv2_validation\` CHANGE status status VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # utils_alert
    ALTER TABLE \`utils_alert\` CHANGE text text LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_alert\` CHANGE scope scope VARCHAR(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # utils_category
    ALTER TABLE \`utils_category\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_category\` CHANGE description description LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_category\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # utils_comment
    ALTER TABLE \`utils_comment\` CHANGE ip_address ip_address VARCHAR(39) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_comment\` CHANGE text text LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_comment\` CHANGE text_html text_html LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_comment\` CHANGE text_hidden text_hidden VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # utils_helpwriting
    ALTER TABLE \`utils_helpwriting\` CHANGE title title VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_helpwriting\` CHANGE slug slug VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_helpwriting\` CHANGE tablelabel tablelabel VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_helpwriting\` CHANGE image image VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # utils_licence
    ALTER TABLE \`utils_licence\` CHANGE code code VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_licence\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_licence\` CHANGE description description LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # utils_subcategory
    ALTER TABLE \`utils_subcategory\` CHANGE title title VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_subcategory\` CHANGE subtitle subtitle VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_subcategory\` CHANGE image image VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    ALTER TABLE \`utils_subcategory\` CHANGE slug slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    # utils_tag
    ALTER TABLE \`utils_tag\` CHANGE title title VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE \`utils_tag\` CHANGE slug slug VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
EOF

if [ $? -eq 0 ]; then
    echo "Fields have been successfully modified."
else
    echo "Fields modification failed." >&2
    exit 1
fi

echo "Database updated successfully."
echo "This script is over, here are some instructions (also available in update.md):"
echo "Next steps are:"
echo
echo "1. Add the following to the MySQL config block in your Django settings:"
echo "    'OPTIONS': {'charset': 'utf8mb4'},"
echo
read -p "Done? "
echo
echo "2. Modify /etc/mysql/my.cnf"
echo "2.2. Add to [client] section:"
echo "    default-character-set = utf8mb4"
echo
read -p "Done? "
echo
echo "2.3. Add to [mysql] section:"
echo "    default-character-set = utf8mb4"
echo
read -p "Done? "
echo
echo "2.4. Add to [mysqld] section:"
echo "    character-set-client-handshake = FALSE"
echo "    character-set-server = utf8mb4"
echo "    collation-server = utf8mb4_unicode_ci"
echo
read -p "Done? "
echo
echo "Enjoy your funky emojis."
