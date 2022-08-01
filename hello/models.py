from django.db import models

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField("date created", auto_now_add=True)

class Player():
  def __init__(self, name, win, loss, ratio, sp):
    self.name = name
    self.win = win
    self.loss = loss
    self.ratio = ratio
    self.sp = sp

