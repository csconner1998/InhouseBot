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


class Match():
  def __init__(self,matchID,winner,when):
    self.blue = {}
    self.red = {}
    self.matchID = matchID
    self.winner = str.capitalize(winner)
    self.tops=[]
    self.mids=[]
    self.jungles=[]
    self.adcs=[]
    self.supports=[]
    self.when=when

  def addPlayer(self, name, role, isBlue):
    if isBlue:
      self.blue[role] = name
    else:
      self.red[role] = name
  def makeList(self):
    self.tops.append(self.blue['top'])
    self.tops.append(self.red['top'])
    self.jungles.append(self.blue['jungle'])
    self.jungles.append(self.red['jungle'])
    self.mids.append(self.blue['middle'])
    self.mids.append(self.red['middle'])
    self.adcs.append(self.blue['adc'])
    self.adcs.append(self.red['adc'])
    self.supports.append(self.blue['support'])
    self.supports.append(self.red['support'])
