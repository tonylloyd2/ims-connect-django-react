from elasticsearch_dsl import Q
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .search_indexes import IdeaDocument, UserDocument
from .serializers import IdeaSerializer, UserSerializer

class SearchViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def ideas(self, request):
        """Search ideas based on various criteria."""
        query = request.GET.get('q', '')
        tags = request.GET.getlist('tags', [])
        expertise = request.GET.getlist('expertise', [])
        status = request.GET.get('status')
        
        # Build search query
        search = IdeaDocument.search()
        if query:
            search = search.query(
                Q('multi_match',
                  query=query,
                  fields=['title^3', 'description', 'tags'],
                  fuzziness='AUTO')
            )
        
        # Apply filters
        if tags:
            search = search.filter('terms', tags=tags)
        if expertise:
            search = search.filter('terms', required_expertise=expertise)
        if status:
            search = search.filter('term', status=status)
        
        # Execute search
        response = search.execute()
        
        # Get Django models and serialize
        ideas = [hit.to_dict() for hit in response]
        return Response(ideas)
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """Search users based on expertise and other criteria."""
        query = request.GET.get('q', '')
        expertise = request.GET.getlist('expertise', [])
        role = request.GET.get('role')
        
        # Build search query
        search = UserDocument.search()
        if query:
            search = search.query(
                Q('multi_match',
                  query=query,
                  fields=['username^2', 'first_name', 'last_name', 'email', 'expertise'],
                  fuzziness='AUTO')
            )
        
        # Apply filters
        if expertise:
            search = search.filter('terms', expertise=expertise)
        if role:
            search = search.filter('term', role=role)
        
        # Execute search
        response = search.execute()
        
        # Get Django models and serialize
        users = [hit.to_dict() for hit in response]
        return Response(users)
    
    @action(detail=False, methods=['get'])
    def similar_ideas(self, request):
        """Find similar ideas based on content and tags."""
        idea_id = request.GET.get('idea_id')
        if not idea_id:
            return Response({'error': 'idea_id is required'}, status=400)
        
        # Get the source idea
        try:
            idea = IdeaDocument.get(id=idea_id)
        except:
            return Response({'error': 'Idea not found'}, status=404)
        
        # Build more-like-this query
        search = IdeaDocument.search()
        search = search.query(
            Q('more_like_this',
              fields=['title', 'description', 'tags'],
              like={
                  '_id': idea_id,
                  'doc_type': 'ideas'
              },
              min_term_freq=1,
              max_query_terms=12)
        )
        
        # Execute search
        response = search.execute()
        
        # Get Django models and serialize
        similar_ideas = [hit.to_dict() for hit in response]
        return Response(similar_ideas)
