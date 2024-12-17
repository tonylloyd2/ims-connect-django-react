from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Idea, User, Team

@registry.register_document
class IdeaDocument(Document):
    creator = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'username': fields.TextField(),
        'email': fields.TextField(),
    })
    
    team = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    tags = fields.TextField(multi=True)
    required_expertise = fields.TextField(multi=True)
    
    class Index:
        name = 'ideas'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
    
    class Django:
        model = Idea
        fields = [
            'id',
            'title',
            'description',
            'status',
            'impact_score',
            'created_at',
            'updated_at',
        ]
        
        related_models = [User, Team]
    
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.ideas.all()
        elif isinstance(related_instance, Team):
            return related_instance.idea_set.all()

@registry.register_document
class UserDocument(Document):
    expertise = fields.TextField(multi=True)
    teams = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    class Index:
        name = 'users'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
    
    class Django:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
        ]
        
        related_models = [Team]
    
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Team):
            return related_instance.members.all()
