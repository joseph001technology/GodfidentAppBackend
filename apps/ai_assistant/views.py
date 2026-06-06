from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework import serializers

from .models import ChatSession, ChatMessage, BibleStudySession
from . import services


class AIChatThrottle(UserRateThrottle):
    rate = '30/minute'
    scope = 'ai_chat'


# ─── Serializers ──────────────────────────────────────────────────────────────

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'message_count', 'messages', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleStudySession
        fields = ['id', 'study_type', 'query', 'response', 'translation', 'created_at']


# ─── Views ────────────────────────────────────────────────────────────────────

class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatView(APIView):
    """POST /ai/chat/ - general Bible-focused chat"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIChatThrottle]

    def post(self, request):
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')

        if not message:
            return Response({'success': False, 'message': 'Message is required.'}, status=400)

        # Get or create session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                return Response({'success': False, 'message': 'Session not found.'}, status=404)
        else:
            session = ChatSession.objects.create(
                user=request.user,
                title=message[:50] + ('...' if len(message) > 50 else ''),
            )

        # Build message history
        history = list(session.messages.values('role', 'content').order_by('created_at')[-20:])
        history.append({'role': 'user', 'content': message})

        try:
            ai_response = services.chat(history)
        except Exception as e:
            return Response({'success': False, 'message': 'AI service unavailable.'}, status=503)

        # Save messages
        ChatMessage.objects.create(session=session, role='user', content=message)
        ChatMessage.objects.create(session=session, role='assistant', content=ai_response)

        return Response({
            'success': True,
            'session_id': session.id,
            'response': ai_response,
        })


class ExplainVerseView(APIView):
    """POST /ai/explain-verse/"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIChatThrottle]

    def post(self, request):
        reference = request.data.get('reference', '')
        translation = request.data.get('translation', 'KJV')
        verse_text = request.data.get('verse_text', '')

        if not reference:
            return Response({'success': False, 'message': 'reference is required.'}, status=400)

        try:
            response = services.explain_verse(reference, translation, verse_text)
        except Exception:
            return Response({'success': False, 'message': 'AI service unavailable.'}, status=503)

        BibleStudySession.objects.create(
            user=request.user, study_type='verse',
            query=reference, response=response, translation=translation
        )
        return Response({'success': True, 'reference': reference, 'explanation': response})


class ExplainChapterView(APIView):
    """POST /ai/explain-chapter/"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIChatThrottle]

    def post(self, request):
        book = request.data.get('book', '')
        chapter = request.data.get('chapter')
        translation = request.data.get('translation', 'KJV')

        if not all([book, chapter]):
            return Response({'success': False, 'message': 'book and chapter are required.'}, status=400)

        try:
            response = services.explain_chapter(book, int(chapter), translation)
        except Exception:
            return Response({'success': False, 'message': 'AI service unavailable.'}, status=503)

        query = f'{book} {chapter}'
        BibleStudySession.objects.create(
            user=request.user, study_type='chapter',
            query=query, response=response, translation=translation
        )
        return Response({'success': True, 'chapter': query, 'study': response})


class TopicStudyView(APIView):
    """POST /ai/topic-study/"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIChatThrottle]

    def post(self, request):
        topic = request.data.get('topic', '')
        if not topic:
            return Response({'success': False, 'message': 'topic is required.'}, status=400)

        try:
            response = services.topic_study(topic)
        except Exception:
            return Response({'success': False, 'message': 'AI service unavailable.'}, status=503)

        BibleStudySession.objects.create(
            user=request.user, study_type='topic', query=topic, response=response
        )
        return Response({'success': True, 'topic': topic, 'study': response})


class CharacterStudyView(APIView):
    """POST /ai/character-study/"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIChatThrottle]

    def post(self, request):
        character = request.data.get('character', '')
        if not character:
            return Response({'success': False, 'message': 'character is required.'}, status=400)

        try:
            response = services.character_study(character)
        except Exception:
            return Response({'success': False, 'message': 'AI service unavailable.'}, status=503)

        BibleStudySession.objects.create(
            user=request.user, study_type='character', query=character, response=response
        )
        return Response({'success': True, 'character': character, 'study': response})


class DailyEncouragementView(APIView):
    """GET /ai/daily-encouragement/"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIChatThrottle]

    def get(self, request):
        user = request.user
        try:
            response = services.daily_encouragement(user.first_name or '')
        except Exception:
            return Response({'success': False, 'message': 'AI service unavailable.'}, status=503)

        return Response({'success': True, 'encouragement': response})


class PrayerAssistanceView(APIView):
    """POST /ai/prayer-assistance/"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIChatThrottle]

    def post(self, request):
        topic = request.data.get('topic', '')
        scripture = request.data.get('scripture', '')

        if not topic:
            return Response({'success': False, 'message': 'topic is required.'}, status=400)

        try:
            response = services.prayer_assistance(topic, scripture)
        except Exception:
            return Response({'success': False, 'message': 'AI service unavailable.'}, status=503)

        return Response({'success': True, 'topic': topic, 'guidance': response})


class StudyHistoryView(generics.ListAPIView):
    """GET /ai/study-history/"""
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = BibleStudySession.objects.filter(user=self.request.user)
        study_type = self.request.query_params.get('type')
        if study_type:
            qs = qs.filter(study_type=study_type)
        return qs
