#!/usr/bin/env python
# Copyright 2012 Chenjun Shen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Inspired by https://github.com/nmaupu/Apache-Cluster-Manager

from HTMLParser import HTMLParser
from urllib2 import urlopen, Request, URLError, HTTPError
import re
import sys

class Worker():
    """apache Load Balancer Worker class"""
    def __init__(self):
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
        return '    Worker: Worker_URL=%s, Route=%s, RouteRedir=%s, Factor=%s, Set=%s, Status=%s, Elected=%s, To=%s, From=%s' % \
            (self.Worker_URL, self.Route, self.RouteRedir, self.Factor, self.Set, self.Status, self.Elected, self.To, self.From)


class LoadBalancer():
    """apache Load Balancer class - contains a list of Workers"""
    def __init__(self):
        # defaultly we think lb is broken
        self.broken=True
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
        self.wattrs    = []
        self.lbptr = -1
        self.wptr    = -1

    def check_broken_lb(self):
        # defaut
        self.broken = False

        for lb in iter(self.lbs):

            # skip lb endswith "-test"
            if lb.name.lower().endswith("-test"):
                lb.broken = False
                continue

            for worker in iter(lb.workers):
                if worker.Status == "Ok" or worker.Status == "Stby_Ok":
                    lb.broken = False    

            if lb.broken:
                self.broken = True
                print lb.name,
                if lb.workers == []:
                    print "empty workers"
                    continue

                for worker in iter(lb.workers):
                    print "%s->%s" % (worker.Worker_URL, worker.Status),
        
        if not self.broken:
            print "OK" 
        
##
# Called by OpenNMS
# $1: --interface
# S2: ip
# $3: --timeout
# S4: timeout
##
if __name__ == "__main__":

    try:
        req = Request("http://%s/balancer-manager-nms" % (sys.argv[2]))
        req.add_header("Host", "opennms")
        page = urlopen(req, timeout=int(sys.argv[4])/1000)
    except URLError, err:
        print err
        sys.exit(2)
    except HTTPError, err:
        print err
        sys.exit(2)
    
    pageSrc = page.read()
    page.close()
    parser = BalancerManagerParser()
    parser.feed(pageSrc)
    parser.check_broken_lb()
