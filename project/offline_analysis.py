import numpy as np
import re, sys
from candecoder import *
from collections import defaultdict
import matplotlib.pyplot as plt

def main():
    filename = sys.argv[1]
    pat = re.compile(r"\(([0-9\.]+)\) [\w]+ ([0-9]+)#([\w]+)") 

    results = []

    with open(filename) as file:
        for l in file:
            res = pat.match(l)
            if res:
                time, id, data = res.group(1, 2, 3)
                time = float(time)
                id = int(id, 16)
                data = bytes.fromhex(data)
                results.append((time, id, data))

    decoders = [Can201Decoder, Can231Decoder]

    traces = {}

    canID = set()
    
    for res in results:
        canID.add(res[1])
        decoder = find_decoder(res, decoders)
        if not decoder:
            continue # not implemented
        

        data = decoder.decode(res[2])

        for field in data._fields:
            if not field in traces:
                traces[field] = ([], [])
            traces[field][0].append(res[0])
            traces[field][1].append(getattr(data, field))
    
    print([hex(x) for x in canID])
    print(traces.keys())

    for k in traces:
        traces[k] = np.array(traces[k])

    traces['speed'][1] = traces['speed'][1] * 0.621371


    fig = plt.figure()


    ax = fig.gca()
    ax2 = ax.twinx()
    
    ax.plot(traces['accpos'][0], traces['accpos'][1])
    ax2.plot(traces['can201unknown1'][0], traces['can201unknown1'][1], 'r')

    fig = plt.figure()


    ax = fig.gca()
    ax2 = ax.twinx()
    
    ax2.plot(traces['accpos'][1], traces['can201unknown1'][1], 'r.')


#     fig = plt.figure()


#     ax = fig.gca()
#     ax2 = ax.twinx()
    
#     ax.plot(traces['rpm'][0], traces['rpm'][1])
#     ax2.plot(traces['speed'][0], traces['speed'][1], 'r')

#     fig = plt.figure()

#     ax = fig.gca()
#     ax2 = ax.twinx()
    
#     ax.plot(traces['rpm'][0], traces['rpm'][1])



#     reference_ratios = [229, 134.5, 96.5, 68.8, 58.4, 48.75]
#     ratios = traces['rpm'][1]/traces['speed'][1]
#     ax2.plot(traces['speed'][0], ratios, 'r.')

#     observered_ratios = [[] for _ in range(6)]
# races['clutch'][0], traces['clutch'][1], 'r.')
#     ax2.plot(traces['ingear'][0], 1.1*traces['ingear'][1], 'g.')


#     ax.set_ylim([0, 250])

#     plt.show()

    # for r in ratios:
    #     errors = r / reference_ratios
    #     least_error_index = np.argmin(np.abs(errors - 1))
    #     if 0.9 < errors[least_error_index] < 1.1:
    #         observered_ratios[least_error_index].append(r)
        

    # for r in reference_ratios:
    #     ax2.plot([traces['speed'][0][0], traces['speed'][0][-1]], [r,r], 'g-')
    

    # observered_ratios_median = [np.median(rr) for rr in observered_ratios]

    # for r in observered_ratios_median:
    #     ax2.plot([traces['speed'][0][0], traces['speed'][0][-1]], [r,r], 'k-')

    # print(reference_ratios)
    # print(observered_ratios_median)
    # print([f * 0.621371 for f in observered_ratios_median])

    # ax2.set_ylim([0, 250])

    
    # fig = plt.figure()
    # ax = fig.gca()
    # ax2 = ax.twinx()

    # ax.plot(traces['rpm'][0], ratios)
    # ax2.plot(traces['clutch'][0], traces['clutch'][1], 'r.')
    # ax2.plot(traces['ingear'][0], 1.1*traces['ingear'][1], 'g.')


    # ax.set_ylim([0, 250])

    plt.show()

        

        

def find_decoder(res, decoders):
    matched = [d for d in decoders if d.id == res[1]]
    if matched:
        return matched[0]

if __name__ == '__main__':
    main()

