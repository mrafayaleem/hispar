__author__ = 'mrafay'

import json

class Generator:

    def __init__(self, peered):
        self.peered = peered

    def write_to_file(self, filename, X, Y):
        f = open(filename, 'w')

        f.write('from pyretic.sdx.lib.common import *\nimport json\nimport os\n')
        f.write('cwd = os.getcwd()\n')

        f.write('def parse_config(config_file):\n')
        f.write('\tparticipants = json.load(open(config_file, 'r'))')

        f.write('\n\tfor participant_name in participants:\n')
        f.write('\t\tfor i in range(len(participants[participant_name]["IP"])):\n')
        f.write('\t\t\tparticipants[participant_name]["IP"][i] = IP(participants[participant_name]["IP"][i])\n')

        f.write('\treturn participants\n')

        f.write('def policy(participant, fwd):\n')

        f.write('\tparticipants = parse_config(cwd + "/pyretic/sdx/policies/simple/local.cfg")\n')

        protocols_json = open('protocols.json').read()
        protocols_data = json.loads(protocols_json)
        #protocols_data = [str(protocols) for protocols in protocols_data]

        str_arr = []
        print protocols_data
        for k, v in self.peered.iteritems():
            if k in protocols_data:
                prot = protocols_data[k]
                peer = Y
                str_arr.append('if_((match(dstip=participants["' + Y + '"]["IP"][0]) & match(protocol=' + str(prot) + ')), fwd(participant.peers["' + Y + '"]), drop)')

        f.write('\treturn (\n')
        f.write('\t(parallel([match(dstip=participants["' + X + '"]["IP"][i]) for i in range(len(participants["' + Y + '"]["IP"]))]) >> fwd(participant.phys_ports[0]))')

        for value in str_arr:
            f.write(' + ')
            f.write(value)

        f.write(')')
        f.close()