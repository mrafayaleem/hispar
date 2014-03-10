'''
Created on Dec 20, 2013

@author: M. Rafay Aleem
'''


class ResultAggregator:

    def __init__(self, as_identifer):
        self.identifier = as_identifer
        self.complete_matches = {}
        self.partial_matches = {}
        self.no_matches = {}
        self.peered_protocols = {}
        self.un_peered_protocols = {}

    def add_complete_match(self, protocol, score):
        self.complete_matches.update({protocol: score})

    def add_partial_matches(self, protocol, score):
        self.partial_matches.update({protocol: score})

    def add_no_matches(self, protocol, score):
        self.no_matches.update({protocol: score})

    def add_peered_protocols(self, protocol, score):
        self.peered_protocols.update({protocol: score})

    def add_un_peered_protocols(self, protocol, score):
        self.un_peered_protocols.update({protocol: score})


def match(outbound_spec, inbound_spec):
    # print outbound_spec.protocols
    # print inbound_spec.protocols
    as_a = outbound_spec.identifier
    as_b = inbound_spec.identifier

    aggr = ResultAggregator(as_a)  # result aggregator for AS A

    for k, v in outbound_spec.protocols.iteritems():
        no_match = True
        if k in inbound_spec.protocols and as_b in outbound_spec.protocols[k] \
        and (as_a in inbound_spec.protocols[k] \
        or '*' in inbound_spec.protocols[k]):
            no_match = False
            #print 'complete match for key:', k
            ranking = outbound_spec.protocols[k].index(as_b) + 1
            # if a protocol matches peering, add a complete match
            aggr.add_complete_match(k, ranking)
            aggr.add_peered_protocols(k, ranking)
        elif k != '*':
            if '*' in v and not ('~' + as_b) in v:
                if k in inbound_spec.protocols \
                and (as_a in inbound_spec.protocols[k] \
                    or '*' in inbound_spec.protocols[k]):
                    no_match = False
                    #print 'partial match for key: ', k
                    ranking = outbound_spec.protocols[k].index('*') + 1
                    aggr.add_partial_matches(k, ranking)
                    aggr.add_peered_protocols(k, ranking)
                elif as_a in inbound_spec.protocols['*']:
                    no_match = False
                    #print 'partial match for key: ', k
                    ranking = outbound_spec.protocols[k].index('*')
                    aggr.add_partial_matches(k, ranking)
                    aggr.add_peered_protocols(k, ranking)
        if no_match:
            #print 'no match for key: ', k
            aggr.add_no_matches(k, 0)
            aggr.add_un_peered_protocols(k, 0)

    #print aggr.complete_matches
    #print aggr.partial_matches
    #print aggr.no_matches
    #print '-' * 50
    print 'UN PEERED:', aggr.un_peered_protocols
    print 'PEERED', aggr.peered_protocols
    return aggr
