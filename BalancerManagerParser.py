#!/usr/local/bin/python

from HTMLParser import HTMLParser
from urllib2 import urlopen
import re

class Worker():
  """apache Load Balancer Worker class"""
  def __init__(self):
    self.mark = False
    self.actionURL = ''
    self.Worker_URL = ''
    self.Route = ''
    self.RouteRedir = ''
    self.Factor = ''
    self.Set = ''
    self.Status = ''
    self.Elected = ''
    self.To = ''
    self.From = ''
  
  def __str__(self):
    return '  Worker: Worker_URL=%s, Route=%s, RouteRedir=%s, Factor=%s, Set=%s, Status=%s, Elected=%s, To=%s, From=%s' % \
      (self.Worker_URL, self.Route, self.RouteRedir, self.Factor, self.Set, self.Status, self.Elected, self.To, self.From)


class LoadBalancer():
  """apache Load Balancer class - contains a list of Workers"""
  def __init__(self):
    self.mark = False
    self.name = ''
    self.StickySession = ''
    self.Timeout = ''
    self.FailoverAttempts = ''
    self.Method = ''
    self.workers = []

  def __str__(self):
    return 'Load balancer (%d workers): name=%s, StickySession=%s, Timeout=%s, FailoverAttempts=%s, Method=%s' % \
      (len(self.workers), self.name, self.StickySession, self.Timeout, self.FailoverAttempts, self.Method)


class BalancerManagerParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.lbs = []
    self.curtags = []
    self.reinit()
    self.curlb = None

  def handle_starttag(self, tag, attrs):
    self.curtags.append(tag)
    self.attrs = attrs
    if tag == 'hr':
      self.reinit()
    elif tag == 'table':
      self.tables += 1
    elif tag == 'h3':
      lb = LoadBalancer()
      self.curlb = lb
      self.lbs.append(lb)
    # balancer table
    elif tag == 'tr' and self.tables == 1:
      self.lbptr = -1
    # workers table
    elif tag == 'tr' and self.tables == 2 and len(self.wattrs) > 0:
      self.wptr = -1
      w = Worker()
      self.curworker = w
      self.curlb.workers.append(w)
    elif tag == 'td' and self.tables == 1:
      self.lbptr += 1
    elif tag == 'td' and self.tables == 2:
      self.wptr += 1
    elif tag == 'a' and self.tables == 2:
      self.curworker.actionURL = self.attrs[0][1]

  def handle_endtag(self, tag):
    try:
      self.curtags.pop()
    except:
      pass

  def handle_data(self, datap):
    ## Triming data value
    data = datap.strip(' ')
    dataValue = data.replace(' ', '_')
    
    if self.get_curtag() == 'h3':
      r = re.compile('^LoadBalancer Status for balancer://(.*)$')
      str = r.search(data).group(1)
      self.curlb.name = str
    # balancer table
    elif self.get_curtag() == 'th' and self.tables == 1:
      self.lbattrs.append(dataValue)
    # workers table
    elif self.get_curtag() == 'th' and self.tables == 2:
      self.wattrs.append(dataValue)
    # balancer table
    elif self.get_curtag() == 'td' and self.tables == 1:
      attr = self.lbattrs[self.lbptr]
      setattr(self.curlb, attr, dataValue)
    # workers table
    elif self.get_curtag() == 'td' and self.tables == 2:
      attr = self.wattrs[self.wptr]
      setattr(self.curworker, attr, dataValue)
    elif self.get_curtag() == 'a' and self.tables == 2:
      attr = self.wattrs[self.wptr]
      setattr(self.curworker, attr, dataValue)

  def get_curtag(self):
    try:
      return self.curtags[-1]
    except:
      return None

  def reinit(self):
    self.tables = 0
    self.attrs = ''
    self.lbattrs = []
    self.wattrs  = []
    self.lbptr = -1
    self.wptr  = -1

  def get_broken_lb(self):
		for lb in iter(self.lbs):
			broken = True

			for worker in iter(lb.workers):
				if worker.Status == "Ok":
					broken = False	

			if broken:
				print lb.name,

				if lbs.workers == None:
					print "Empty workers"
					continue

				for worker in iter(lb.workers):
					print "%s:%s" % (worker.Worker_URL, worker.Status),
				print ""
		
    
if __name__ == "__main__":
  page = urlopen("http://localhost:8000/balancer-manager")
  pageSrc = page.read()
  page.close()
  parser = BalancerManagerParser()
  parser.feed(pageSrc)
  if parser.get_broken_lb() == None:
		print "Ok"
