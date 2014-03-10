"""
Created on Dec 16, 2013

@author: M. Rafay Aleem
"""
import json
import argparse
from string import ascii_lowercase
import jinja2


class Args:
    pass


def parse(args, x, out_file):
    json_data_x = open(args.policyX).read()
    data_x = json.loads(json_data_x)

    json_protocols = open('protocols.json').read()
    prot = json.loads(json_protocols)

    policy = list(ascii_lowercase)
    rule_array = []

    def rule_case(ipprefix, protocol, time, peer, i):
        assert peer is not '*'
        assert i < 26
        if (protocol == 'HTTP' or protocol == 'SMTP') and time == '*':
            rule_array.append(
                ''+policy[i]+' = if_((match(dstip=IPPrefix("'+ipprefix+'")) & match(dstport='+str(prot[protocol])+')), fwd(participant.peers["'+peer+'"]), '+policy[i+1]+')'
            )
        elif (protocol == 'HTTP' or protocol == 'SMTP') and time != '*':
            rule_array.append(
                ''+policy[i]+' = if_((match(dstip=IPPrefix("'+ipprefix+'")) & match(dstport='+str(prot[protocol])+') & match(time=HRange('+time+'))), fwd(participant.peers["'+peer+'"]), '+policy[i+1]+')'
            )
        elif protocol != '*' and time == '*':
            rule_array.append(
                ''+policy[i]+' = if_((match(dstip=IPPrefix("'+ipprefix+'")) & match(protocol='+str(prot[protocol])+')), fwd(participant.peers["'+peer+'"]), '+policy[i+1]+')'
            )
        elif protocol != '*' and time != '*':
            rule_array.append(
                ''+policy[i]+' = if_((match(dstip=IPPrefix("'+ipprefix+'")) & match(protocol='+str(prot[protocol])+') & match(time=HRange('+time+'))), fwd(participant.peers["'+peer+'"]), '+policy[i+1]+')'
            )
        elif time == '*':
            rule_array.append(
                ''+policy[i]+' = if_(match(dstip=IPPrefix("'+ipprefix+'")), fwd(participant.peers["'+peer+'"]), '+policy[i+1]+')'
            )
        else:
            rule_array.append(
                ''+policy[i]+' = if_((match(dstip=IPPrefix("'+ipprefix+'")) & match(time=HRange('+time+'))), fwd(participant.peers["'+peer+'"]), '+policy[i+1]+')'
            )

    i = 0

    for ip_prefix, rules in data_x['outbound'].iteritems():
        for rule in rules:
            rule_case(ip_prefix, str(rule['protocol']), str(rule['time']), str(rule['peer']), i)
            i += 1

    rule_array.append(policy[len(rule_array)] + ' = drop')  # Appending the drop rule.
    rule_array.reverse()

    policy_list = []
    i = 0
    for rule in rule_array:
        policy_list.append(policy[i])
        i += 1

    template_loader = jinja2.FileSystemLoader(searchpath="/")
    template_env = jinja2.Environment(loader=template_loader)

    template_file = "/home/sdx/pyretic/policyparser/parser/policy_template.jinja"
    template = template_env.get_template(template_file)

    template_vars = {"as_x": x, "rule_array": rule_array, "policy_list": policy_list[0]}  # policy_list[0] is only neeeded.

    output_text = template.render(template_vars)

    f = open(out_file, 'w')
    f.write(output_text)
    f.close()

if __name__ == '__main__':
    args = Args()
    args.policyX = 'policies/b.policy'
    #args.policyY = 'policies/b.policy'
    parse(args, 'A', 'participant_B.py')