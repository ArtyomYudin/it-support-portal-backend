from django.db import models

class AccessPoint(models.Model):
    system_id = models.IntegerField(primary_key=True, default=0)
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

class CardOwner(models.Model):
    system_id = models.IntegerField(primary_key=True, default=0)
    firstname = models.CharField(max_length=50, null=True)
    secondname = models.CharField(max_length=50, null=True)
    lastname = models.CharField(max_length=250, null=True)
    #user_principal_name = models.CharField(max_length=250, null=True)
    #display_name = models.CharField(max_length=250)

    def __str__(self):
        return self.lastname

class Event(models.Model):
    created = models.DateTimeField()
    ap_id = models.ForeignKey(
        AccessPoint, on_delete=models.PROTECT, null=True, db_column='ap_id'
    )
    owner_id = models.ForeignKey(
        CardOwner, on_delete=models.PROTECT, null=True, db_column='owner_id'
    )
    #ap_id = models.IntegerField()
    #owner_id = models.IntegerField()
    card = models.IntegerField()
    code = models.IntegerField()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        pass
        #return self.ap_name