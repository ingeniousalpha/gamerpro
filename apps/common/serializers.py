from rest_framework import serializers

from apps.common.models import Document


class AbstractNameSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        abstract = True

    def get_name(self, obj):
        try:
            language = self.context['request'].language
        except Exception:
            language = "ru"

        if obj.name:
            return getattr(obj.name, language)
        return ''


class AbstractTitleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        abstract = True

    def get_title(self, obj):
        return getattr(obj.title, self.context['request'].language)


class AbstractDescriptionSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()

    class Meta:
        abstract = True

    def get_description(self, obj):
        if obj.description:
            if self.context.get('request') is not None:
                return getattr(obj.description, self.context.get('request').language, 'ru')
            else:
                return getattr(obj.description, 'ru')
        return ''


class AbstractImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        abstract = True

    def get_image(self, obj):
        image = getattr(obj.image, self.context['request'].headers.get('language'))
        if image:
            return self.context['request'].build_absolute_uri(image.url)
        return None


class RequestPropertyMixin:
    @property
    def request(self):
        return self.context.get('request')


class RequestUserPropertyMixin(RequestPropertyMixin):
    @property
    def user(self):
        if self.request and self.request.user.is_authenticated:
            return self.request.user


class FilePathMethodMixin:

    def file_path(self, file_field):
        return self.context.get('request').build_absolute_uri(file_field.url)


class DocumentListSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'code',
            'file'
        )

    def get_file(self, obj):
        if obj.code == "privacy_policy":
            return "https://server.gamerpro.kz/api/documents/privacy_policy"
        if obj.code == "public_offer":
            return "https://server.gamerpro.kz/api/documents/public_offer"
        return self.context['request'].build_absolute_uri(obj.file.url)
