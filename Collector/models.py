from django.db import models

# Create your models here.
class Log(models.Model):
    # 日期
    created = models.DateTimeField('date happened')
    # 用户id
    user_id = models.CharField(max_length=16)
    # 内容id(电影)
    content_id = models.CharField(max_length=16)
    # 事件
    event = models.CharField(max_length=200)
    # 会话id
    session_id = models.CharField(max_length=128)

    def __str__(self):
        return "user_id: {}, content_id: {}, event: {}".format(self.user_id,
                                                               str(self.content_id),
                                                               self.event)
