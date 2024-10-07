from django.db import models

# Create your models here.

class AccessPoint(models.Model):
    system_id = models.IntegerField(primary_key=True, default=0)
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

class CardOwner(models.Model):
    system_id = models.IntegerField(primary_key=True, default=0)
    user_principal_name = models.CharField(max_length=250, null=True)
    display_name = models.CharField(max_length=250)

    def __str__(self):
        return self.display_name

class Event(models.Model):
    created = models.DateTimeField()
    ap_id = models.ForeignKey(
        AccessPoint, on_delete=models.PROTECT
    )
    owner_id = models.ForeignKey(
        CardOwner, on_delete=models.PROTECT
    )
    card = models.IntegerField()
    code = models.IntegerField()

    def __str__(self):
        pass
        #return self.ap_name