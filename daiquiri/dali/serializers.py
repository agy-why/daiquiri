from rest_framework import serializers

from daiquiri.jobs.models import Job


class JobListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = ('id', 'phase')


class JobRetrieveSerializer(serializers.ModelSerializer):

    job_id = serializers.UUIDField(source='id')
    owner_id = serializers.UUIDField(source='owner.username')
    destruction = serializers.DateTimeField(source='destruction_time')

    class Meta:
        model = Job
        fields = (
            'job_id',
            'owner_id',
            'phase',
            'quote',
            'start_time',
            'end_time',
            'execution_duration',
            'destruction',
            'results',
            'parameters'
        )

class JobUpdateSerializer(serializers.Serializer):

    PHASE = serializers.CharField(required=False)

class SyncJobSerializer(serializers.Serializer):

    RESPONSEFORMAT = serializers.CharField(required=False)
    MAXREC = serializers.IntegerField(required=False)
    RUNID = serializers.CharField(required=False)

class AsyncJobSerializer(serializers.Serializer):

    PHASE = serializers.CharField(required=False)
    RESPONSEFORMAT = serializers.CharField(required=False)
    MAXREC = serializers.IntegerField(required=False)
    RUNID = serializers.CharField(required=False)
