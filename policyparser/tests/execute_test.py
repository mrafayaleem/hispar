'''
Created on Dec 20, 2013

@author: M. Rafay Aleem
'''
from parser.old.parse import Args
from parser.old import parse


class Results:

    def __init__(self):
        self.peered_protocols = {}
        self.un_peered_protocols = {}


def execute(args, X, Y, results):
    aggr = parse(args, X, Y)
    try:
        assert(aggr.un_peered_protocols == results.un_peered_protocols)
        assert(aggr.peered_protocols == results.peered_protocols)
    except AssertionError:
        print '---failed---'
        print 'UNPEERED:', aggr.un_peered_protocols, \
        results.un_peered_protocols
        print 'PEERED', aggr.peered_protocols, results.peered_protocols
        return
    print '---pass---'


if __name__ == '__main__':
    args = Args()
    expected_results = Results

    expected_results.un_peered_protocols = {'*': 0}
    expected_results.peered_protocols = {'UDP': 2, 'TCP': 2}
    args.policyX = 'testpolicies/a.policy'
    args.policyY = 'testpolicies/b.policy'
    execute(args, 'A', 'B', expected_results)

    expected_results.un_peered_protocols = {'UDP': 0}
    expected_results.peered_protocols = {'TCP': 2, '*': 1}
    args.policyX = 'testpolicies/c.policy'
    args.policyY = 'testpolicies/d.policy'
    execute(args, 'A', 'B', expected_results)

    expected_results.un_peered_protocols = {'UDP': 0, 'TCP': 0}
    expected_results.peered_protocols = {'*': 3}
    args.policyX = 'testpolicies/e.policy'
    args.policyY = 'testpolicies/f.policy'
    execute(args, 'E', 'F', expected_results)

    expected_results.un_peered_protocols = {'TCP': 0, '*': 0}
    expected_results.peered_protocols = {'UDP': 5}
    args.policyX = 'testpolicies/a.policy'
    args.policyY = 'testpolicies/f.policy'
    execute(args, 'A', 'F', expected_results)
