from tortoise import fields, models

class CmsMeta(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    description = fields.TextField()
    disallow_ai_learning = fields.BooleanField(default=False)
    hide_kokoromi_version = fields.BooleanField(default=False)
    noindex = fields.BooleanField(default=False)
    enable_activity_pub = fields.BooleanField(default=False)
    adsense = fields.TextField(null=True)
    giscus_enabled = fields.BooleanField(default=False)
    giscus_repo = fields.CharField(max_length=255, default="your-github-username/your-repo-name", null=True)
    giscus_repo_id = fields.CharField(max_length=255, null=True)
    giscus_category_name = fields.CharField(max_length=255, null=True)
    giscus_category_id = fields.CharField(max_length=255, null=True)
    giscus_theme_type = fields.CharField(max_length=255, default="preferred_color_scheme")
    ga4_tracking_id = fields.CharField(max_length=255, null=True)
    show_view_counts = fields.BooleanField(default=False)

class Post(models.Model):
    id = fields.CharField(pk=True, max_length=255)
    title = fields.CharField(max_length=255)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    author = fields.ForeignKeyField('models.Author', related_name='posts')
    view_count = fields.IntField(default=0)
    no_index = fields.BooleanField(default=False)

class SocialLink(models.Model):
    id = fields.UUIDField(pk=True)
    url = fields.CharField(max_length=255)
    icon = fields.CharField(max_length=255)
    author = fields.ForeignKeyField('models.Author', related_name='social_links')

class Author(models.Model):
    id = fields.CharField(pk=True, max_length=255)
    name = fields.CharField(max_length=255)
    mail = fields.CharField(max_length=255)
    display_name = fields.CharField(max_length=255)
    description = fields.TextField()
    icon = fields.CharField(max_length=255, default="")
    password = fields.CharField(max_length=255)
    is_admin = fields.BooleanField(default=False)

class Token(models.Model):
    id = fields.UUIDField(pk=True)
    token = fields.CharField(max_length=255, unique=True)
    author = fields.ForeignKeyField('models.Author', related_name='tokens')
    created_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()
