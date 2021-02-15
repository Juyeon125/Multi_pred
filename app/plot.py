from matplotlib import pyplot as plt
n = [1, 2, 3, 4, 5]
mp_time = [35.72, 35.60, 34.56, 34.77, 35.00]
sp_time = [54.78, 58.59, 54.35, 51.15, 61.05]

plt.plot(n, mp_time)
plt.plot(n, sp_time)
plt.legend(['Multiprocess', 'Singleprocess'])
plt.xticks([1, 2, 3, 4, 5])
plt.title("Runtime")
plt.xlabel("Sequence")
plt.ylabel("Time(sec)")
plt.show()