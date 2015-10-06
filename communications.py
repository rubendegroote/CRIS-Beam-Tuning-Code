

def voltages_loop(setpoints,readback,current,current_std,stamp):

    r0={}
    for i in range(10):
        r0['Control_' + str(i)] = 5000

    while True:
        for n in setpoints.keys():
            readback[n] = setpoints[n] + np.random.rand()
        
        currs = []
        for j in range(10):
            curr = 1
            for n,r in readback.items():
                curr *= max(0, 1 - 4*(r-r0[n])**2/10**4)
            curr = curr # + np.random.normal(0,0.051)
            currs.append(curr)

            stamp.value = time.time()

            time.sleep(0.001)

        current.value = np.mean(currs)
        current_std.value = np.std(currs)/np.sqrt(len(currs))
