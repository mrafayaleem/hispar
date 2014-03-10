'''
Created on Dec 16, 2013

@author: M. Rafay Aleem
'''
import json
from parser.old import match
from parser.old.generator import Generator


class Args:
    pass


class PolicyFormatException(Exception):
    pass


class PolicySpec:

    def __init__(self, as_identifier, name):
        self.identifier = as_identifier
        self.name = name
        self.protocols = {}

    def add(self, protocol_name, peers_list):
        self.protocols.update({protocol_name: peers_list})


def parse(args, X, Y):
    json_data_x = open(args.policyX).read()
    json_data_y = open(args.policyY).read()

    data_x = json.loads(json_data_x)
    data_y = json.loads(json_data_y)

    def incrementer(n):
        while True:
            yield n
            n += 1

    def create_policy_spec(as_identifier, kind, data):
        spec = PolicySpec(as_identifier, kind)
        for protocol in data[kind]:
            protocol_name = str(protocol['protocol'])
            peers_list = protocol['peers']
            peers_list = [str(peers) for peers in peers_list]
            spec.add(protocol_name, peers_list)
        return spec

    outbound_spec = create_policy_spec(X, 'outbound', data_x)
    inbound_spec = create_policy_spec(Y, 'inbound', data_y)
    # print outbound_spec.protocols
    # print inbound_spec.protocols
    aggr = match(outbound_spec, inbound_spec)
    gen = Generator(aggr.peered_protocols)
    gen.write_to_file('testfile.py', X, Y)
    return aggr

if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description='Parse SDX policies.')
#     parser.add_argument('policyX', metavar='policyX', type=str,
#                         help='path for policy file of AS X')
#     parser.add_argument('policyY', metavar='policyY', type=str,
#                         help='path for policy file of AS Y')
#     args = parser.parse_args()
    args = Args()
    args.policyX = 'policies/b.policy'
    args.policyY = 'policies/b.policy'
    parse(args, 'A', 'B')
